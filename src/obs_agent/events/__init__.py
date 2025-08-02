"""
Event Sourcing and CQRS system for OBS Agent.

This package provides a complete event sourcing implementation with:
- Domain events
- Event store with persistence
- CQRS command/query separation
- Time-travel debugging
- Event projections and read models
"""

from .cqrs import (
    Command,
    CommandBus,
    GetCurrentScene,
    GetEventHistory,
    GetStreamStatus,
    Query,
    QueryBus,
    ReadModel,
    StartStream,
    StopStream,
    SwitchScene,
)
from .domain import (
    AutomationRuleExecuted,
    AutomationRuleTriggered,
    DomainEvent,
    EventMetadata,
    EventType,
    SceneCreated,
    SceneSwitched,
    SourceCreated,
    SourceVolumeChanged,
    StreamStarted,
    StreamStopped,
)
from .integration import (
    EventSourcingConfig,
    EventSourcingSystem,
)
from .projections import (
    AutomationProjection,
    PerformanceProjection,
    Projection,
    ProjectionBuilder,
    ProjectionState,
    SceneProjection,
    StreamingProjection,
)
from .store import (
    EventStore,
    EventStream,
    Snapshot,
)
from .time_travel import (
    DebugSession,
    TimePoint,
    TimeTravelDebugger,
)

__all__ = [
    # Domain
    "DomainEvent",
    "EventType",
    "EventMetadata",
    "SceneCreated",
    "SceneSwitched",
    "SourceCreated",
    "SourceVolumeChanged",
    "StreamStarted",
    "StreamStopped",
    "AutomationRuleTriggered",
    "AutomationRuleExecuted",
    # Store
    "EventStore",
    "EventStream",
    "Snapshot",
    # CQRS
    "Command",
    "Query",
    "CommandBus",
    "QueryBus",
    "ReadModel",
    "SwitchScene",
    "StartStream",
    "StopStream",
    "GetCurrentScene",
    "GetStreamStatus",
    "GetEventHistory",
    # Time Travel
    "TimeTravelDebugger",
    "TimePoint",
    "DebugSession",
    # Projections
    "Projection",
    "ProjectionState",
    "ProjectionBuilder",
    "SceneProjection",
    "StreamingProjection",
    "AutomationProjection",
    "PerformanceProjection",
    # Integration
    "EventSourcingSystem",
    "EventSourcingConfig",
]
