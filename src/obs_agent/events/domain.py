"""
Domain events for OBS Agent Event Sourcing.

This module defines all domain events that can occur in the OBS system.
Each event is immutable and represents a fact that has happened.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, List, Type
from uuid import UUID, uuid4
import json


class EventType(Enum):
    """Event type enumeration for all domain events."""

    # Scene events
    SCENE_CREATED = "scene.created"
    SCENE_SWITCHED = "scene.switched"
    SCENE_DELETED = "scene.deleted"
    SCENE_RENAMED = "scene.renamed"

    # Source events
    SOURCE_CREATED = "source.created"
    SOURCE_DELETED = "source.deleted"
    SOURCE_ENABLED = "source.enabled"
    SOURCE_DISABLED = "source.disabled"
    SOURCE_VOLUME_CHANGED = "source.volume_changed"
    SOURCE_MUTED = "source.muted"
    SOURCE_UNMUTED = "source.unmuted"
    SOURCE_SETTINGS_CHANGED = "source.settings_changed"

    # Streaming events
    STREAM_STARTED = "stream.started"
    STREAM_STOPPED = "stream.stopped"
    STREAM_PAUSED = "stream.paused"
    STREAM_RESUMED = "stream.resumed"

    # Recording events
    RECORDING_STARTED = "recording.started"
    RECORDING_STOPPED = "recording.stopped"
    RECORDING_PAUSED = "recording.paused"
    RECORDING_RESUMED = "recording.resumed"

    # Automation events
    AUTOMATION_RULE_CREATED = "automation.rule_created"
    AUTOMATION_RULE_ENABLED = "automation.rule_enabled"
    AUTOMATION_RULE_DISABLED = "automation.rule_disabled"
    AUTOMATION_RULE_TRIGGERED = "automation.rule_triggered"
    AUTOMATION_RULE_EXECUTED = "automation.rule_executed"
    AUTOMATION_RULE_FAILED = "automation.rule_failed"

    # System events
    SYSTEM_CONNECTED = "system.connected"
    SYSTEM_DISCONNECTED = "system.disconnected"
    SYSTEM_ERROR = "system.error"
    SYSTEM_PERFORMANCE_WARNING = "system.performance_warning"


@dataclass(frozen=True)
class EventMetadata:
    """Metadata attached to every event."""

    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    correlation_id: Optional[UUID] = None
    causation_id: Optional[UUID] = None
    user_id: Optional[str] = None
    source: str = "obs_agent"

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "event_id": str(self.event_id),
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "correlation_id": str(self.correlation_id) if self.correlation_id else None,
            "causation_id": str(self.causation_id) if self.causation_id else None,
            "user_id": self.user_id,
            "source": self.source,
        }


class DomainEvent(ABC):
    """Base class for all domain events."""

    def __init__(self, aggregate_id: str, metadata: Optional[EventMetadata] = None):
        self.aggregate_id = aggregate_id
        self.metadata = metadata or EventMetadata()
        self.event_type = self._get_event_type()

    @abstractmethod
    def _get_event_type(self) -> EventType:
        """Return the event type."""
        pass

    @abstractmethod
    def get_event_data(self) -> Dict[str, Any]:
        """Return the event-specific data."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for storage."""
        return {
            "event_type": self.event_type.value,
            "aggregate_id": self.aggregate_id,
            "metadata": self.metadata.to_dict(),
            "data": self.get_event_data(),
        }

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """Reconstruct event from dictionary."""
        event_type = EventType(data["event_type"])
        event_class = EVENT_CLASS_MAP.get(event_type)
        if not event_class:
            raise ValueError(f"Unknown event type: {event_type}")

        metadata_data = data["metadata"]
        metadata = EventMetadata(
            event_id=UUID(metadata_data["event_id"]),
            timestamp=datetime.fromisoformat(metadata_data["timestamp"]),
            version=metadata_data["version"],
            correlation_id=UUID(metadata_data["correlation_id"]) if metadata_data.get("correlation_id") else None,
            causation_id=UUID(metadata_data["causation_id"]) if metadata_data.get("causation_id") else None,
            user_id=metadata_data.get("user_id"),
            source=metadata_data["source"],
        )

        return event_class.from_event_data(aggregate_id=data["aggregate_id"], metadata=metadata, data=data["data"])

    @classmethod
    @abstractmethod
    def from_event_data(cls, aggregate_id: str, metadata: EventMetadata, data: Dict[str, Any]) -> "DomainEvent":
        """Create event from stored data."""
        pass


# Scene Events


@dataclass(frozen=True)
class SceneCreated(DomainEvent):
    """Event fired when a scene is created."""

    aggregate_id: str
    scene_name: str
    metadata: EventMetadata = field(default_factory=EventMetadata)
    scene_settings: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Call parent init logic since dataclasses don't call parent __init__
        object.__setattr__(self, "event_type", self._get_event_type())

    def _get_event_type(self) -> EventType:
        return EventType.SCENE_CREATED

    def get_event_data(self) -> Dict[str, Any]:
        return {"scene_name": self.scene_name, "scene_settings": self.scene_settings}

    @classmethod
    def from_event_data(cls, aggregate_id: str, metadata: EventMetadata, data: Dict[str, Any]) -> "SceneCreated":
        return cls(
            aggregate_id=aggregate_id,
            metadata=metadata,
            scene_name=data["scene_name"],
            scene_settings=data.get("scene_settings", {}),
        )


@dataclass(frozen=True)
class SceneSwitched(DomainEvent):
    """Event fired when the active scene is switched."""

    aggregate_id: str
    from_scene: str
    to_scene: str
    metadata: EventMetadata = field(default_factory=EventMetadata)
    transition_type: Optional[str] = None
    transition_duration: Optional[int] = None

    def __post_init__(self):
        # Call parent init logic since dataclasses don't call parent __init__
        object.__setattr__(self, "event_type", self._get_event_type())

    def _get_event_type(self) -> EventType:
        return EventType.SCENE_SWITCHED

    def get_event_data(self) -> Dict[str, Any]:
        return {
            "from_scene": self.from_scene,
            "to_scene": self.to_scene,
            "transition_type": self.transition_type,
            "transition_duration": self.transition_duration,
        }

    @classmethod
    def from_event_data(cls, aggregate_id: str, metadata: EventMetadata, data: Dict[str, Any]) -> "SceneSwitched":
        return cls(
            aggregate_id=aggregate_id,
            metadata=metadata,
            from_scene=data["from_scene"],
            to_scene=data["to_scene"],
            transition_type=data.get("transition_type"),
            transition_duration=data.get("transition_duration"),
        )


# Source Events


@dataclass(frozen=True)
class SourceCreated(DomainEvent):
    """Event fired when a source is created."""

    aggregate_id: str
    source_name: str
    source_type: str
    metadata: EventMetadata = field(default_factory=EventMetadata)
    source_settings: Dict[str, Any] = field(default_factory=dict)
    scene_name: Optional[str] = None

    def __post_init__(self):
        # Call parent init logic since dataclasses don't call parent __init__
        object.__setattr__(self, "event_type", self._get_event_type())

    def _get_event_type(self) -> EventType:
        return EventType.SOURCE_CREATED

    def get_event_data(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "source_type": self.source_type,
            "source_settings": self.source_settings,
            "scene_name": self.scene_name,
        }

    @classmethod
    def from_event_data(cls, aggregate_id: str, metadata: EventMetadata, data: Dict[str, Any]) -> "SourceCreated":
        return cls(
            aggregate_id=aggregate_id,
            metadata=metadata,
            source_name=data["source_name"],
            source_type=data["source_type"],
            source_settings=data.get("source_settings", {}),
            scene_name=data.get("scene_name"),
        )


@dataclass(frozen=True)
class SourceVolumeChanged(DomainEvent):
    """Event fired when a source volume is changed."""

    aggregate_id: str
    source_name: str
    old_volume: float
    new_volume: float
    metadata: EventMetadata = field(default_factory=EventMetadata)
    volume_db: Optional[float] = None

    def __post_init__(self):
        # Call parent init logic since dataclasses don't call parent __init__
        object.__setattr__(self, "event_type", self._get_event_type())

    def _get_event_type(self) -> EventType:
        return EventType.SOURCE_VOLUME_CHANGED

    def get_event_data(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "old_volume": self.old_volume,
            "new_volume": self.new_volume,
            "volume_db": self.volume_db,
        }

    @classmethod
    def from_event_data(cls, aggregate_id: str, metadata: EventMetadata, data: Dict[str, Any]) -> "SourceVolumeChanged":
        return cls(
            aggregate_id=aggregate_id,
            metadata=metadata,
            source_name=data["source_name"],
            old_volume=data["old_volume"],
            new_volume=data["new_volume"],
            volume_db=data.get("volume_db"),
        )


# Streaming Events


@dataclass(frozen=True)
class StreamStarted(DomainEvent):
    """Event fired when streaming starts."""

    aggregate_id: str
    metadata: EventMetadata = field(default_factory=EventMetadata)
    stream_settings: Dict[str, Any] = field(default_factory=dict)
    stream_key: Optional[str] = None  # Redacted for security
    service: Optional[str] = None

    def __post_init__(self):
        # Call parent init logic since dataclasses don't call parent __init__
        object.__setattr__(self, "event_type", self._get_event_type())

    def _get_event_type(self) -> EventType:
        return EventType.STREAM_STARTED

    def get_event_data(self) -> Dict[str, Any]:
        return {
            "stream_settings": self.stream_settings,
            "service": self.service,
            # Never store stream key
        }

    @classmethod
    def from_event_data(cls, aggregate_id: str, metadata: EventMetadata, data: Dict[str, Any]) -> "StreamStarted":
        return cls(
            aggregate_id=aggregate_id,
            metadata=metadata,
            stream_settings=data.get("stream_settings", {}),
            service=data.get("service"),
        )


@dataclass(frozen=True)
class StreamStopped(DomainEvent):
    """Event fired when streaming stops."""

    aggregate_id: str
    duration_seconds: int
    total_frames: int
    dropped_frames: int
    bytes_sent: int
    metadata: EventMetadata = field(default_factory=EventMetadata)

    def __post_init__(self):
        # Call parent init logic since dataclasses don't call parent __init__
        object.__setattr__(self, "event_type", self._get_event_type())

    def _get_event_type(self) -> EventType:
        return EventType.STREAM_STOPPED

    def get_event_data(self) -> Dict[str, Any]:
        return {
            "duration_seconds": self.duration_seconds,
            "total_frames": self.total_frames,
            "dropped_frames": self.dropped_frames,
            "bytes_sent": self.bytes_sent,
        }

    @classmethod
    def from_event_data(cls, aggregate_id: str, metadata: EventMetadata, data: Dict[str, Any]) -> "StreamStopped":
        return cls(
            aggregate_id=aggregate_id,
            metadata=metadata,
            duration_seconds=data["duration_seconds"],
            total_frames=data["total_frames"],
            dropped_frames=data["dropped_frames"],
            bytes_sent=data["bytes_sent"],
        )


# Automation Events


@dataclass(frozen=True)
class AutomationRuleTriggered(DomainEvent):
    """Event fired when an automation rule is triggered."""

    aggregate_id: str
    rule_id: str
    rule_name: str
    trigger_type: str
    metadata: EventMetadata = field(default_factory=EventMetadata)
    trigger_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Call parent init logic since dataclasses don't call parent __init__
        object.__setattr__(self, "event_type", self._get_event_type())

    def _get_event_type(self) -> EventType:
        return EventType.AUTOMATION_RULE_TRIGGERED

    def get_event_data(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "trigger_type": self.trigger_type,
            "trigger_data": self.trigger_data,
        }

    @classmethod
    def from_event_data(
        cls, aggregate_id: str, metadata: EventMetadata, data: Dict[str, Any]
    ) -> "AutomationRuleTriggered":
        return cls(
            aggregate_id=aggregate_id,
            metadata=metadata,
            rule_id=data["rule_id"],
            rule_name=data["rule_name"],
            trigger_type=data["trigger_type"],
            trigger_data=data.get("trigger_data", {}),
        )


@dataclass(frozen=True)
class AutomationRuleExecuted(DomainEvent):
    """Event fired when an automation rule executes successfully."""

    aggregate_id: str
    rule_id: str
    rule_name: str
    actions_executed: List[str]
    execution_time_ms: float
    metadata: EventMetadata = field(default_factory=EventMetadata)
    result: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Call parent init logic since dataclasses don't call parent __init__
        object.__setattr__(self, "event_type", self._get_event_type())

    def _get_event_type(self) -> EventType:
        return EventType.AUTOMATION_RULE_EXECUTED

    def get_event_data(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "actions_executed": self.actions_executed,
            "execution_time_ms": self.execution_time_ms,
            "result": self.result,
        }

    @classmethod
    def from_event_data(
        cls, aggregate_id: str, metadata: EventMetadata, data: Dict[str, Any]
    ) -> "AutomationRuleExecuted":
        return cls(
            aggregate_id=aggregate_id,
            metadata=metadata,
            rule_id=data["rule_id"],
            rule_name=data["rule_name"],
            actions_executed=data["actions_executed"],
            execution_time_ms=data["execution_time_ms"],
            result=data.get("result", {}),
        )


# Event class mapping for deserialization
EVENT_CLASS_MAP: Dict[EventType, Type[DomainEvent]] = {
    EventType.SCENE_CREATED: SceneCreated,
    EventType.SCENE_SWITCHED: SceneSwitched,
    EventType.SOURCE_CREATED: SourceCreated,
    EventType.SOURCE_VOLUME_CHANGED: SourceVolumeChanged,
    EventType.STREAM_STARTED: StreamStarted,
    EventType.STREAM_STOPPED: StreamStopped,
    EventType.AUTOMATION_RULE_TRIGGERED: AutomationRuleTriggered,
    EventType.AUTOMATION_RULE_EXECUTED: AutomationRuleExecuted,
}
