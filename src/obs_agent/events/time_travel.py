"""
Time-travel debugging system for OBS Agent.

This module provides the ability to replay events, inspect system state
at any point in time, and debug automation rules with perfect reproducibility.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from .domain import DomainEvent, EventType
from .projections import Projection, ProjectionBuilder
from .store import EventStore, Snapshot


@dataclass
class TimePoint:
    """Represents a specific point in time for debugging."""

    timestamp: datetime
    event_count: int
    aggregate_versions: Dict[str, int] = field(default_factory=dict)
    active_correlations: Set[UUID] = field(default_factory=set)

    def __str__(self) -> str:
        return f"TimePoint(time={self.timestamp.isoformat()}, events={self.event_count})"


@dataclass
class DebugSession:
    """Represents a time-travel debugging session."""

    session_id: UUID
    start_time: datetime
    end_time: datetime
    current_position: datetime
    events_in_range: List[DomainEvent]
    breakpoints: List[TimePoint] = field(default_factory=list)
    watch_expressions: Dict[str, Callable] = field(default_factory=dict)


class TimeTravelDebugger:
    """
    Time-travel debugger for event-sourced systems.

    Features:
    - Replay events from any point in time
    - Step forward/backward through events
    - Set breakpoints on specific conditions
    - Inspect system state at any moment
    - Analyze causation chains
    - What-if scenarios
    """

    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.current_session: Optional[DebugSession] = None
        self._projections: Dict[str, Projection] = {}
        self._state_cache: Dict[datetime, Dict[str, Any]] = {}

    def start_session(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> DebugSession:
        """Start a new debugging session."""
        # Default to last 24 hours if not specified
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)

        # Get events in range
        events = self.event_store.replay_events(since=start_time, until=end_time)

        session = DebugSession(
            session_id=uuid4(),
            start_time=start_time,
            end_time=end_time,
            current_position=start_time,
            events_in_range=events,
        )

        self.current_session = session
        return session

    def goto(self, timestamp: datetime) -> Dict[str, Any]:
        """
        Jump to a specific point in time.

        Returns the system state at that moment.
        """
        if not self.current_session:
            raise ValueError("No active debugging session")

        # Check cache first
        if timestamp in self._state_cache:
            return self._state_cache[timestamp]

        # Replay events up to timestamp
        events = [e for e in self.current_session.events_in_range if e.metadata.timestamp <= timestamp]

        # Build state from events
        state = self._build_state_from_events(events)

        # Cache for faster access
        self._state_cache[timestamp] = state

        # Update session position
        self.current_session.current_position = timestamp

        return state

    def step_forward(self, count: int = 1) -> Tuple[List[DomainEvent], Dict[str, Any]]:
        """
        Step forward through events.

        Returns the events processed and the resulting state.
        """
        if not self.current_session:
            raise ValueError("No active debugging session")

        current_pos = self.current_session.current_position

        # Find next events
        future_events = [e for e in self.current_session.events_in_range if e.metadata.timestamp > current_pos]

        if not future_events:
            return [], self.goto(current_pos)

        # Take the next 'count' events
        next_events = future_events[:count]

        # Move to timestamp of last event
        new_position = next_events[-1].metadata.timestamp
        state = self.goto(new_position)

        return next_events, state

    def step_backward(self, count: int = 1) -> Tuple[List[DomainEvent], Dict[str, Any]]:
        """
        Step backward through events.

        Returns the events that were "undone" and the resulting state.
        """
        if not self.current_session:
            raise ValueError("No active debugging session")

        current_pos = self.current_session.current_position

        # Find previous events
        past_events = [e for e in self.current_session.events_in_range if e.metadata.timestamp <= current_pos]

        if len(past_events) <= count:
            # Go to beginning
            undone_events = past_events
            state = self.goto(self.current_session.start_time)
        else:
            # Remove last 'count' events
            undone_events = past_events[-count:]
            remaining_events = past_events[:-count]
            new_position = remaining_events[-1].metadata.timestamp
            state = self.goto(new_position)

        return undone_events, state

    def set_breakpoint(self, condition: Callable[[DomainEvent], bool]) -> TimePoint:
        """
        Set a breakpoint that triggers when condition is met.

        Returns the TimePoint where the breakpoint would trigger.
        """
        if not self.current_session:
            raise ValueError("No active debugging session")

        for event in self.current_session.events_in_range:
            if condition(event):
                timepoint = TimePoint(
                    timestamp=event.metadata.timestamp,
                    event_count=len(
                        [
                            e
                            for e in self.current_session.events_in_range
                            if e.metadata.timestamp <= event.metadata.timestamp
                        ]
                    ),
                )
                self.current_session.breakpoints.append(timepoint)
                return timepoint

        raise ValueError("Breakpoint condition never met")

    def continue_to_breakpoint(self) -> Tuple[TimePoint, Dict[str, Any]]:
        """Continue execution until next breakpoint."""
        if not self.current_session:
            raise ValueError("No active debugging session")

        if not self.current_session.breakpoints:
            raise ValueError("No breakpoints set")

        # Find next breakpoint after current position
        next_breakpoint = None
        for bp in sorted(self.current_session.breakpoints, key=lambda x: x.timestamp):
            if bp.timestamp > self.current_session.current_position:
                next_breakpoint = bp
                break

        if not next_breakpoint:
            raise ValueError("No breakpoints ahead")

        state = self.goto(next_breakpoint.timestamp)
        return next_breakpoint, state

    def analyze_causation_chain(self, event_id: UUID) -> List[DomainEvent]:
        """
        Analyze the chain of events caused by a specific event.

        Useful for understanding the ripple effects of actions.
        """
        return self.event_store.get_causation_chain(event_id)

    def analyze_correlation_chain(self, correlation_id: UUID) -> List[DomainEvent]:
        """
        Analyze all events in a correlation chain.

        Useful for tracking a complete user interaction.
        """
        return self.event_store.get_correlation_chain(correlation_id)

    def what_if(
        self, modify_events: Callable[[List[DomainEvent]], List[DomainEvent]], at_timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Run a what-if scenario by modifying the event stream.

        This doesn't affect the actual event store, only the debugging session.
        """
        if not self.current_session:
            raise ValueError("No active debugging session")

        timestamp = at_timestamp or self.current_session.current_position

        # Get events up to timestamp
        events = [e for e in self.current_session.events_in_range if e.metadata.timestamp <= timestamp]

        # Apply modifications
        modified_events = modify_events(events)

        # Build state from modified events
        state = self._build_state_from_events(modified_events)

        return state

    def find_event_pattern(
        self, pattern: List[EventType], within: Optional[timedelta] = None
    ) -> List[List[DomainEvent]]:
        """
        Find sequences of events matching a pattern.

        Useful for detecting specific scenarios or problems.
        """
        if not self.current_session:
            raise ValueError("No active debugging session")

        matches = []
        events = self.current_session.events_in_range

        for i in range(len(events) - len(pattern) + 1):
            candidate = events[i : i + len(pattern)]

            # Check if types match
            if all(e.event_type == p for e, p in zip(candidate, pattern)):
                # Check timing constraint if specified
                if within:
                    time_span = candidate[-1].metadata.timestamp - candidate[0].metadata.timestamp
                    if time_span <= within:
                        matches.append(candidate)
                else:
                    matches.append(candidate)

        return matches

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics for the current debugging session."""
        if not self.current_session:
            raise ValueError("No active debugging session")

        events = self.current_session.events_in_range

        # Count events by type
        event_counts: Dict[str, int] = {}
        for event in events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        # Find most active aggregates
        aggregate_counts: Dict[str, int] = {}
        for event in events:
            agg_id = event.aggregate_id
            aggregate_counts[agg_id] = aggregate_counts.get(agg_id, 0) + 1

        # Calculate event rate
        if len(events) > 1:
            time_span = events[-1].metadata.timestamp - events[0].metadata.timestamp
            event_rate = len(events) / max(time_span.total_seconds(), 1)
        else:
            event_rate = 0

        return {
            "total_events": len(events),
            "event_types": event_counts,
            "most_active_aggregates": sorted(aggregate_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "event_rate_per_second": event_rate,
            "unique_correlations": len(set(e.metadata.correlation_id for e in events if e.metadata.correlation_id)),
            "time_span": str(events[-1].metadata.timestamp - events[0].metadata.timestamp) if events else "0:00:00",
        }

    def export_session(self, format: str = "json") -> str:
        """Export the debugging session for sharing or analysis."""
        if not self.current_session:
            raise ValueError("No active debugging session")

        if format == "json":
            import json

            data = {
                "session_id": str(self.current_session.session_id),
                "start_time": self.current_session.start_time.isoformat(),
                "end_time": self.current_session.end_time.isoformat(),
                "current_position": self.current_session.current_position.isoformat(),
                "event_count": len(self.current_session.events_in_range),
                "breakpoints": [
                    {"timestamp": bp.timestamp.isoformat(), "event_count": bp.event_count}
                    for bp in self.current_session.breakpoints
                ],
                "statistics": self.get_statistics(),
            }

            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _build_state_from_events(self, events: List[DomainEvent]) -> Dict[str, Any]:
        """Build system state from a list of events."""
        state: Dict[str, Any] = {
            "current_scene": "Unknown",
            "is_streaming": False,
            "is_recording": False,
            "scenes": [],
            "sources": {},
            "automation_rules": {},
            "event_count": len(events),
            "last_event": events[-1].to_dict() if events else None,
        }

        # Apply each event to build state
        for event in events:
            if event.event_type == EventType.SCENE_SWITCHED:
                state["current_scene"] = event.get_event_data()["to_scene"]
            elif event.event_type == EventType.SCENE_CREATED:
                scene_name = event.get_event_data()["scene_name"]
                if scene_name not in state["scenes"]:
                    state["scenes"].append(scene_name)
            elif event.event_type == EventType.STREAM_STARTED:
                state["is_streaming"] = True
            elif event.event_type == EventType.STREAM_STOPPED:
                state["is_streaming"] = False
            elif event.event_type == EventType.RECORDING_STARTED:
                state["is_recording"] = True
            elif event.event_type == EventType.RECORDING_STOPPED:
                state["is_recording"] = False
            elif event.event_type == EventType.SOURCE_CREATED:
                data = event.get_event_data()
                state["sources"][data["source_name"]] = {
                    "type": data["source_type"],
                    "settings": data["source_settings"],
                }

        return state
