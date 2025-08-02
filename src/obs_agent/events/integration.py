"""
Integration module for Event Sourcing with OBS Agent.

This module provides the glue between the event sourcing system
and the existing OBS Agent functionality.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from ..obs_agent_v2 import OBSAgent

from .cqrs import CommandBus, QueryBus, ReadModel
from .domain import (
    AutomationRuleExecuted,
    AutomationRuleTriggered,
    DomainEvent,
    EventMetadata,
    EventType,
    SceneCreated,
    SceneSwitched,
    SourceCreated,
    StreamStarted,
    StreamStopped,
)
from .projections import ProjectionBuilder
from .store import EventStore
from .time_travel import DebugSession, TimeTravelDebugger


@dataclass
class EventSourcingConfig:
    """Configuration for event sourcing system."""

    db_path: Optional[Path] = None
    enable_snapshots: bool = True
    snapshot_frequency: int = 100  # Events between snapshots
    enable_projections: bool = True
    projection_update_interval: float = 1.0
    enable_time_travel: bool = True
    persist_events: bool = True


class EventSourcingSystem:
    """
    Main integration point for event sourcing with OBS Agent.

    This class:
    - Intercepts OBS operations and creates events
    - Manages the event store and projections
    - Provides debugging and analysis capabilities
    - Integrates with automation rules
    """

    def __init__(self, obs_agent: "OBSAgent", config: Optional[EventSourcingConfig] = None):
        self.obs_agent = obs_agent
        self.config = config or EventSourcingConfig()

        # Initialize event sourcing components
        self.event_store = EventStore(db_path=self.config.db_path)
        self.command_bus = CommandBus(self.event_store)
        self.read_model = ReadModel(self.event_store)
        self.query_bus = QueryBus(self.event_store, self.read_model)

        # Initialize projections
        if self.config.enable_projections:
            self.projection_builder: Optional[ProjectionBuilder] = ProjectionBuilder(self.event_store)
        else:
            self.projection_builder = None

        # Initialize time-travel debugger
        if self.config.enable_time_travel:
            self.debugger: Optional[TimeTravelDebugger] = TimeTravelDebugger(self.event_store)
        else:
            self.debugger = None

        # Current correlation context
        self._current_correlation_id: Optional[UUID] = None

        # Hook into OBS Agent operations
        self._setup_interceptors()

    def _setup_interceptors(self):
        """Set up interceptors for OBS Agent operations."""
        # Store original methods
        original_switch_scene = self.obs_agent.scenes.switch_scene  # type: ignore
        original_start_stream = self.obs_agent.streaming.start_stream  # type: ignore
        original_stop_stream = self.obs_agent.streaming.stop_stream  # type: ignore

        # Create intercepting wrappers
        async def switch_scene_interceptor(scene_name: str, *args, **kwargs):
            """Intercept scene switching."""
            # Get current scene before switch
            current_scene = await self.obs_agent.scenes.get_current_scene()  # type: ignore

            # Perform the actual switch
            result = await original_switch_scene(scene_name, *args, **kwargs)

            # Create and store event
            event = SceneSwitched(
                aggregate_id="obs_system",
                metadata=EventMetadata(correlation_id=self._current_correlation_id),
                from_scene=current_scene,
                to_scene=scene_name,
                transition_type=kwargs.get("transition_type"),
                transition_duration=kwargs.get("transition_duration"),
            )
            self.event_store.append(event)

            return result

        async def start_stream_interceptor(*args, **kwargs):
            """Intercept stream start."""
            result = await original_start_stream(*args, **kwargs)

            event = StreamStarted(
                aggregate_id="stream",
                metadata=EventMetadata(correlation_id=self._current_correlation_id),
                stream_settings=kwargs.get("settings", {}),
                service=kwargs.get("service"),
            )
            self.event_store.append(event)

            return result

        async def stop_stream_interceptor(*args, **kwargs):
            """Intercept stream stop."""
            # Get stream stats before stopping
            stats = await self.obs_agent.streaming.get_stream_status()  # type: ignore

            result = await original_stop_stream(*args, **kwargs)

            event = StreamStopped(
                aggregate_id="stream",
                metadata=EventMetadata(correlation_id=self._current_correlation_id),
                duration_seconds=stats.get("duration", 0),
                total_frames=stats.get("total_frames", 0),
                dropped_frames=stats.get("dropped_frames", 0),
                bytes_sent=stats.get("bytes_sent", 0),
            )
            self.event_store.append(event)

            return result

        # Replace methods with interceptors
        self.obs_agent.scenes.switch_scene = switch_scene_interceptor  # type: ignore
        self.obs_agent.streaming.start_stream = start_stream_interceptor  # type: ignore
        self.obs_agent.streaming.stop_stream = stop_stream_interceptor  # type: ignore

        # Hook into automation system
        self._setup_automation_interceptors()

    def _setup_automation_interceptors(self):
        """Set up interceptors for automation events."""
        if hasattr(self.obs_agent, "automation"):
            # Subscribe to automation events
            automation = self.obs_agent.automation

            # Track rule triggers
            original_trigger = automation._trigger_rule if hasattr(automation, "_trigger_rule") else None

            if original_trigger:

                async def trigger_interceptor(rule, trigger_data):
                    """Intercept rule triggers."""
                    # Create triggered event
                    triggered_event = AutomationRuleTriggered(
                        aggregate_id=f"rule:{rule.id}",
                        metadata=EventMetadata(correlation_id=uuid4()),  # New correlation for each trigger
                        rule_id=rule.id,
                        rule_name=rule.name,
                        trigger_type=str(type(rule.trigger).__name__),
                        trigger_data=trigger_data,
                    )
                    self.event_store.append(triggered_event)

                    # Execute rule
                    start_time = datetime.utcnow()
                    try:
                        result = await original_trigger(rule, trigger_data)
                        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                        # Create executed event
                        executed_event = AutomationRuleExecuted(
                            aggregate_id=f"rule:{rule.id}",
                            metadata=EventMetadata(
                                correlation_id=triggered_event.metadata.correlation_id,
                                causation_id=triggered_event.metadata.event_id,
                            ),
                            rule_id=rule.id,
                            rule_name=rule.name,
                            actions_executed=[str(a) for a in rule.actions],
                            execution_time_ms=execution_time,
                            result={"success": True},
                        )
                        self.event_store.append(executed_event)

                        return result
                    except Exception as e:
                        # Log failure event
                        from .domain import DomainEvent

                        class AutomationRuleFailed(DomainEvent):
                            def __init__(self, *args, error: str, **kwargs):
                                super().__init__(*args, **kwargs)
                                self.error = error

                            def _get_event_type(self) -> EventType:
                                return EventType.AUTOMATION_RULE_FAILED

                            def get_event_data(self) -> Dict[str, Any]:
                                return {"error": self.error}

                            @classmethod
                            def from_event_data(cls, data: Dict[str, Any], **kwargs):
                                """Deserialize from event data."""
                                return cls(error=data["error"], **kwargs)

                        failed_event = AutomationRuleFailed(
                            aggregate_id=f"rule:{rule.id}",
                            metadata=EventMetadata(
                                correlation_id=triggered_event.metadata.correlation_id,
                                causation_id=triggered_event.metadata.event_id,
                            ),
                            error=str(e),
                        )
                        self.event_store.append(failed_event)
                        raise

                automation._trigger_rule = trigger_interceptor

    def start_correlation(self) -> UUID:
        """
        Start a new correlation context.

        All events created until end_correlation() will share
        the same correlation ID.
        """
        self._current_correlation_id = uuid4()
        return self._current_correlation_id

    def end_correlation(self) -> None:
        """End the current correlation context."""
        self._current_correlation_id = None

    async def start(self) -> None:
        """Start the event sourcing system."""
        # Start projection updates if enabled
        if self.projection_builder and self.config.enable_projections:
            await self.projection_builder.start_continuous_update(self.config.projection_update_interval)

    async def stop(self) -> None:
        """Stop the event sourcing system."""
        # Stop projection updates
        if self.projection_builder:
            await self.projection_builder.stop_continuous_update()

    def get_statistics(self) -> Dict[str, Any]:
        """Get event sourcing statistics."""
        stats = {
            "total_events": len(self.event_store._global_event_stream),
            "aggregates": len(self.event_store._events_by_aggregate),
            "event_types": len(self.event_store._events_by_type),
        }

        if self.projection_builder:
            stats["projections"] = {
                name: projection.version for name, projection in self.projection_builder.projections.items()
            }

        if self.debugger and self.debugger.current_session:
            stats["debug_session"] = {
                "events_in_range": len(self.debugger.current_session.events_in_range),
                "breakpoints": len(self.debugger.current_session.breakpoints),
            }

        return stats

    def query_projection(self, projection_name: str, query: str) -> Any:
        """
        Query a projection using a simple query language.

        Examples:
            query_projection("scenes", "current_scene")
            query_projection("streaming", "is_streaming")
        """
        if not self.projection_builder:
            raise ValueError("Projections not enabled")

        projection = self.projection_builder.get_projection(projection_name)
        if not projection:
            raise ValueError(f"Projection not found: {projection_name}")

        # Simple dot notation query
        parts = query.split(".")
        result = projection.state

        for part in parts:
            if isinstance(result, dict):
                result = result.get(part)
            else:
                result = getattr(result, part, None)

            if result is None:
                break

        return result

    def start_debugging(self, hours_back: int = 24) -> DebugSession:
        """Start a debugging session for the last N hours."""
        if not self.debugger:
            raise ValueError("Time-travel debugging not enabled")

        return self.debugger.start_session(start_time=datetime.utcnow() - timedelta(hours=hours_back))

    def replay_automation(self, rule_id: str, since: Optional[datetime] = None) -> List[DomainEvent]:
        """
        Replay all events related to a specific automation rule.

        Useful for debugging automation behavior.
        """
        events = self.event_store.replay_events(aggregate_id=f"rule:{rule_id}", since=since)

        # Also get events caused by this rule
        related_events = []
        for event in events:
            if event.event_type == EventType.AUTOMATION_RULE_TRIGGERED:
                # Get all events in this correlation
                correlation_events = self.event_store.get_correlation_chain(event.metadata.correlation_id)
                related_events.extend(correlation_events)

        return events + related_events

    def export_events(
        self, format: str = "json", since: Optional[datetime] = None, until: Optional[datetime] = None
    ) -> str:
        """Export events for analysis or backup."""
        events = self.event_store.replay_events(since=since, until=until)

        if format == "json":
            import json

            data = {
                "export_time": datetime.utcnow().isoformat(),
                "event_count": len(events),
                "events": [e.to_dict() for e in events],
            }
            return json.dumps(data, indent=2, default=str)
        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow(["timestamp", "event_type", "aggregate_id", "event_id", "correlation_id", "data"])

            # Events
            for event in events:
                writer.writerow(
                    [
                        event.metadata.timestamp.isoformat(),
                        event.event_type.value,
                        event.aggregate_id,
                        str(event.metadata.event_id),
                        str(event.metadata.correlation_id) if event.metadata.correlation_id else "",
                        json.dumps(event.get_event_data()),
                    ]
                )

            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")
