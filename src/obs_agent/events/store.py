"""
Event Store implementation for OBS Agent.

This module provides an append-only event store with support for:
- Event persistence
- Event replay
- Snapshots
- Event streaming
- Time-travel debugging
"""

import asyncio
import json
import sqlite3
import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Set, Tuple, Type
from uuid import UUID

from .domain import DomainEvent, EventMetadata, EventType


@dataclass
class EventStream:
    """Represents a stream of events for an aggregate."""

    aggregate_id: str
    events: List[DomainEvent]
    version: int

    def get_events_since(self, version: int) -> List[DomainEvent]:
        """Get events since a specific version."""
        return [e for e in self.events if e.metadata.version > version]

    def get_events_before(self, timestamp: datetime) -> List[DomainEvent]:
        """Get events before a specific timestamp."""
        return [e for e in self.events if e.metadata.timestamp < timestamp]


@dataclass
class Snapshot:
    """Represents a snapshot of aggregate state."""

    aggregate_id: str
    version: int
    timestamp: datetime
    state: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            "aggregate_id": self.aggregate_id,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "state": self.state,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Snapshot":
        """Create snapshot from dictionary."""
        return cls(
            aggregate_id=data["aggregate_id"],
            version=data["version"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            state=data["state"],
        )


class EventStore:
    """
    Thread-safe event store with persistence.

    Features:
    - Append-only event log
    - SQLite persistence
    - Event replay
    - Snapshots for performance
    - Event subscriptions
    - Time-travel queries
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize event store."""
        self.db_path = db_path or Path.home() / ".obs_agent" / "events.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Thread-safe access
        self._lock = threading.RLock()

        # In-memory indices for fast queries
        self._events_by_aggregate: Dict[str, List[DomainEvent]] = defaultdict(list)
        self._events_by_type: Dict[EventType, List[DomainEvent]] = defaultdict(list)
        self._global_event_stream: List[DomainEvent] = []
        self._snapshots: Dict[str, List[Snapshot]] = defaultdict(list)

        # Event subscriptions
        self._subscribers: List[Callable[[DomainEvent], None]] = []
        self._async_subscribers: List[Callable[[DomainEvent], asyncio.Future]] = []

        # Initialize database
        self._init_db()
        self._load_events()

    def _init_db(self):
        """Initialize SQLite database."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    aggregate_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    correlation_id TEXT,
                    causation_id TEXT,
                    created_at REAL DEFAULT (julianday('now'))
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_aggregate_id 
                ON events(aggregate_id, version)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_event_type 
                ON events(event_type, timestamp)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON events(timestamp)
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    aggregate_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at REAL DEFAULT (julianday('now')),
                    UNIQUE(aggregate_id, version)
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_snapshot_aggregate 
                ON snapshots(aggregate_id, version DESC)
            """
            )

    def close(self):
        """Close the event store and clean up resources."""
        # Force close any remaining SQLite connections
        # This helps with Windows file locking issues
        import gc

        gc.collect()

    def _load_events(self):
        """Load all events from database into memory."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT event_data FROM events 
                ORDER BY created_at, version
            """
            )

            for row in cursor:
                event_data = json.loads(row["event_data"])
                event = DomainEvent.from_dict(event_data)

                # Update in-memory indices
                self._events_by_aggregate[event.aggregate_id].append(event)
                self._events_by_type[event.event_type].append(event)
                self._global_event_stream.append(event)

    def append(self, event: DomainEvent) -> None:
        """
        Append an event to the store.

        This is the only way to modify state in an event-sourced system.
        """
        with self._lock:
            # Persist to database
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """
                    INSERT INTO events (
                        event_id, aggregate_id, event_type, event_data,
                        timestamp, version, correlation_id, causation_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(event.metadata.event_id),
                        event.aggregate_id,
                        event.event_type.value,
                        event.to_json(),
                        event.metadata.timestamp.isoformat(),
                        event.metadata.version,
                        str(event.metadata.correlation_id) if event.metadata.correlation_id else None,
                        str(event.metadata.causation_id) if event.metadata.causation_id else None,
                    ),
                )

            # Update in-memory indices
            self._events_by_aggregate[event.aggregate_id].append(event)
            self._events_by_type[event.event_type].append(event)
            self._global_event_stream.append(event)

            # Notify subscribers
            self._notify_subscribers(event)

    def _notify_subscribers(self, event: DomainEvent):
        """Notify all subscribers of a new event."""
        for subscriber in self._subscribers:
            try:
                subscriber(event)
            except Exception as e:
                # Log error but don't stop processing
                print(f"Subscriber error: {e}")

        # Handle async subscribers
        for async_subscriber in self._async_subscribers:
            asyncio.create_task(self._notify_async(async_subscriber, event))

    async def _notify_async(self, subscriber: Callable, event: DomainEvent):
        """Notify async subscriber."""
        try:
            await subscriber(event)
        except Exception as e:
            print(f"Async subscriber error: {e}")

    def get_events(
        self, aggregate_id: str, from_version: Optional[int] = None, to_version: Optional[int] = None
    ) -> List[DomainEvent]:
        """Get events for an aggregate."""
        with self._lock:
            events = self._events_by_aggregate.get(aggregate_id, [])

            if from_version is not None:
                events = [e for e in events if e.metadata.version >= from_version]

            if to_version is not None:
                events = [e for e in events if e.metadata.version <= to_version]

            return events

    def get_events_by_type(
        self, event_type: EventType, since: Optional[datetime] = None, until: Optional[datetime] = None
    ) -> List[DomainEvent]:
        """Get events by type within a time range."""
        with self._lock:
            events = self._events_by_type.get(event_type, [])

            if since:
                events = [e for e in events if e.metadata.timestamp >= since]

            if until:
                events = [e for e in events if e.metadata.timestamp <= until]

            return events

    def replay_events(
        self,
        aggregate_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        event_types: Optional[Set[EventType]] = None,
    ) -> List[DomainEvent]:
        """
        Replay events with various filters.

        This is the core of time-travel debugging.
        """
        with self._lock:
            if aggregate_id:
                events = self._events_by_aggregate.get(aggregate_id, [])
            else:
                events = self._global_event_stream.copy()

            # Apply time filters
            if since:
                events = [e for e in events if e.metadata.timestamp >= since]

            if until:
                events = [e for e in events if e.metadata.timestamp <= until]

            # Apply type filter
            if event_types:
                events = [e for e in events if e.event_type in event_types]

            return events

    def get_aggregate_version(self, aggregate_id: str) -> int:
        """Get the current version of an aggregate."""
        with self._lock:
            events = self._events_by_aggregate.get(aggregate_id, [])
            return len(events)

    def save_snapshot(self, snapshot: Snapshot) -> None:
        """Save a snapshot for an aggregate."""
        with self._lock:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO snapshots (
                        aggregate_id, version, state, timestamp
                    ) VALUES (?, ?, ?, ?)
                """,
                    (
                        snapshot.aggregate_id,
                        snapshot.version,
                        json.dumps(snapshot.state),
                        snapshot.timestamp.isoformat(),
                    ),
                )

            self._snapshots[snapshot.aggregate_id].append(snapshot)

    def get_latest_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        """Get the latest snapshot for an aggregate."""
        with self._lock:
            snapshots = self._snapshots.get(aggregate_id, [])
            if snapshots:
                return max(snapshots, key=lambda s: s.version)

            # Try loading from database
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT * FROM snapshots 
                    WHERE aggregate_id = ? 
                    ORDER BY version DESC 
                    LIMIT 1
                """,
                    (aggregate_id,),
                )

                row = cursor.fetchone()
                if row:
                    snapshot = Snapshot(
                        aggregate_id=row["aggregate_id"],
                        version=row["version"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        state=json.loads(row["state"]),
                    )
                    self._snapshots[aggregate_id].append(snapshot)
                    return snapshot

            return None

    def subscribe(self, callback: Callable[[DomainEvent], None]) -> Callable[[], None]:
        """
        Subscribe to all events.

        Returns an unsubscribe function.
        """
        self._subscribers.append(callback)

        def unsubscribe():
            self._subscribers.remove(callback)

        return unsubscribe

    def subscribe_async(self, callback: Callable[[DomainEvent], asyncio.Future]) -> Callable[[], None]:
        """Subscribe to events with async callback."""
        self._async_subscribers.append(callback)

        def unsubscribe():
            self._async_subscribers.remove(callback)

        return unsubscribe

    async def stream_events(
        self, start_from: Optional[datetime] = None, batch_size: int = 100
    ) -> AsyncIterator[List[DomainEvent]]:
        """
        Stream events in batches for processing.

        Useful for projections and read model updates.
        """
        with self._lock:
            events = self._global_event_stream.copy()

        if start_from:
            events = [e for e in events if e.metadata.timestamp >= start_from]

        for i in range(0, len(events), batch_size):
            batch = events[i : i + batch_size]
            yield batch
            await asyncio.sleep(0)  # Allow other tasks to run

    def get_correlation_chain(self, correlation_id: UUID) -> List[DomainEvent]:
        """Get all events in a correlation chain."""
        with self._lock:
            return [e for e in self._global_event_stream if e.metadata.correlation_id == correlation_id]

    def get_causation_chain(self, event_id: UUID) -> List[DomainEvent]:
        """Get all events caused by a specific event."""
        with self._lock:
            chain = []
            to_process = [event_id]
            processed = set()

            while to_process:
                current_id = to_process.pop(0)
                if current_id in processed:
                    continue

                processed.add(current_id)

                for event in self._global_event_stream:
                    if event.metadata.causation_id == current_id:
                        chain.append(event)
                        to_process.append(event.metadata.event_id)

            return chain

    def compact(self, before: datetime, keep_snapshots: bool = True) -> int:
        """
        Compact old events by removing them from memory.

        Events remain in the database for audit purposes.
        Returns the number of events removed from memory.
        """
        with self._lock:
            removed = 0

            for aggregate_id in list(self._events_by_aggregate.keys()):
                events = self._events_by_aggregate[aggregate_id]

                if keep_snapshots:
                    # Find latest snapshot before cutoff
                    snapshot = self.get_latest_snapshot(aggregate_id)
                    if snapshot and snapshot.timestamp < before:
                        # Keep only events after snapshot
                        filtered = [e for e in events if e.metadata.version > snapshot.version]
                        removed += len(events) - len(filtered)
                        self._events_by_aggregate[aggregate_id] = filtered
                else:
                    # Remove all events before cutoff
                    filtered = [e for e in events if e.metadata.timestamp >= before]
                    removed += len(events) - len(filtered)
                    self._events_by_aggregate[aggregate_id] = filtered

            # Update other indices
            self._rebuild_indices()

            return removed

    def _rebuild_indices(self):
        """Rebuild in-memory indices from aggregate events."""
        self._events_by_type.clear()
        self._global_event_stream.clear()

        for events in self._events_by_aggregate.values():
            for event in events:
                self._events_by_type[event.event_type].append(event)
                self._global_event_stream.append(event)

        # Sort global stream by timestamp
        self._global_event_stream.sort(key=lambda e: e.metadata.timestamp)
