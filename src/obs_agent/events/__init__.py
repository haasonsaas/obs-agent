"""
Event Sourcing and CQRS system for OBS Agent.

This package provides a complete event sourcing implementation with:
- Domain events
- Event store with persistence
- CQRS command/query separation
- Time-travel debugging
- Event projections and read models
"""

from .domain import (
    DomainEvent,
    EventType,
    EventMetadata,
    SceneCreated,
    SceneSwitched,
    SourceCreated,
    SourceVolumeChanged,
    StreamStarted,
    StreamStopped,
    AutomationRuleTriggered,
    AutomationRuleExecuted,
)

from .store import (
    EventStore,
    EventStream,
    Snapshot,
)

from .cqrs import (
    Command,
    Query,
    CommandBus,
    QueryBus,
    ReadModel,
    SwitchScene,
    StartStream,
    StopStream,
    GetCurrentScene,
    GetStreamStatus,
    GetEventHistory,
)

from .time_travel import (
    TimeTravelDebugger,
    TimePoint,
    DebugSession,
)

from .projections import (
    Projection,
    ProjectionState,
    ProjectionBuilder,
    SceneProjection,
    StreamingProjection,
    AutomationProjection,
    PerformanceProjection,
)

from .integration import (
    EventSourcingSystem,
    EventSourcingConfig,
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
