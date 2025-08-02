"""
Enhanced WebSocket event system for OBS Agent.

This module provides a powerful event handling system with:
- Typed event classes for all OBS events
- Decorator-based event registration
- Event filtering and middleware
- Event recording and replay
- Priority-based event handling
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)

from .logging import get_logger

logger = get_logger(__name__)

EventHandlerType = Callable[[Any], Union[None, Awaitable[None]]]
MiddlewareType = Callable[[Any, EventHandlerType], Union[None, Awaitable[None]]]
FilterType = Callable[[Any], bool]

T = TypeVar("T", bound="BaseEvent")


class EventPriority(Enum):
    """Event priority levels."""

    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()


class EventCategory(Enum):
    """Event categories for filtering."""

    GENERAL = "General"
    CONFIG = "Config"
    SCENES = "Scenes"
    INPUTS = "Inputs"
    TRANSITIONS = "Transitions"
    FILTERS = "Filters"
    OUTPUTS = "Outputs"
    MEDIA = "MediaInputs"
    UI = "Ui"


@dataclass
class BaseEvent(ABC):
    """Base class for all OBS events."""

    event_type: str = ""
    event_intent: Optional[int] = None
    event_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    category: EventCategory = EventCategory.GENERAL

    @classmethod
    @abstractmethod
    def from_raw(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create event from raw WebSocket data."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "event_intent": self.event_intent,
            "event_data": self.event_data,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.name,
            "category": self.category.value,
        }


# Scene Events


@dataclass
class CurrentProgramSceneChanged(BaseEvent):
    """Triggered when the current program scene changes."""

    scene_name: str = ""
    scene_uuid: Optional[str] = None

    def __post_init__(self):
        self.event_type = "CurrentProgramSceneChanged"
        self.category = EventCategory.SCENES

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "CurrentProgramSceneChanged":
        return cls(
            scene_name=data["eventData"]["sceneName"],
            scene_uuid=data["eventData"].get("sceneUuid"),
            event_data=data.get("eventData", {}),
        )


@dataclass
class SceneCreated(BaseEvent):
    """Triggered when a new scene is created."""

    scene_name: str = ""
    scene_uuid: Optional[str] = None
    is_group: bool = False

    def __post_init__(self):
        self.event_type = "SceneCreated"
        self.category = EventCategory.SCENES

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "SceneCreated":
        return cls(
            scene_name=data["eventData"]["sceneName"],
            scene_uuid=data["eventData"].get("sceneUuid"),
            is_group=data["eventData"].get("isGroup", False),
            event_data=data.get("eventData", {}),
        )


@dataclass
class SceneRemoved(BaseEvent):
    """Triggered when a scene is removed."""

    scene_name: str = ""
    scene_uuid: Optional[str] = None
    is_group: bool = False

    def __post_init__(self):
        self.event_type = "SceneRemoved"
        self.category = EventCategory.SCENES

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "SceneRemoved":
        return cls(
            scene_name=data["eventData"]["sceneName"],
            scene_uuid=data["eventData"].get("sceneUuid"),
            is_group=data["eventData"].get("isGroup", False),
            event_data=data.get("eventData", {}),
        )


@dataclass
class SceneNameChanged(BaseEvent):
    """Triggered when a scene name is changed."""

    old_scene_name: str = ""
    scene_name: str = ""
    scene_uuid: Optional[str] = None

    def __post_init__(self):
        self.event_type = "SceneNameChanged"
        self.category = EventCategory.SCENES

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "SceneNameChanged":
        return cls(
            old_scene_name=data["eventData"]["oldSceneName"],
            scene_name=data["eventData"]["sceneName"],
            scene_uuid=data["eventData"].get("sceneUuid"),
            event_data=data.get("eventData", {}),
        )


# Input Events


@dataclass
class InputCreated(BaseEvent):
    """Triggered when a new input is created."""

    input_name: str = ""
    input_uuid: Optional[str] = None
    input_kind: str = ""
    unversioned_input_kind: str = ""
    input_settings: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.event_type = "InputCreated"
        self.category = EventCategory.INPUTS

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "InputCreated":
        return cls(
            input_name=data["eventData"]["inputName"],
            input_uuid=data["eventData"].get("inputUuid"),
            input_kind=data["eventData"].get("inputKind", ""),
            unversioned_input_kind=data["eventData"].get("unversionedInputKind", ""),
            input_settings=data["eventData"].get("inputSettings", {}),
            event_data=data.get("eventData", {}),
        )


@dataclass
class InputRemoved(BaseEvent):
    """Triggered when an input is removed."""

    input_name: str = ""
    input_uuid: Optional[str] = None

    def __post_init__(self):
        self.event_type = "InputRemoved"
        self.category = EventCategory.INPUTS

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "InputRemoved":
        return cls(
            input_name=data["eventData"]["inputName"],
            input_uuid=data["eventData"].get("inputUuid"),
            event_data=data.get("eventData", {}),
        )


@dataclass
class InputMuteStateChanged(BaseEvent):
    """Triggered when an input's mute state changes."""

    input_name: str = ""
    input_uuid: Optional[str] = None
    input_muted: bool = False

    def __post_init__(self):
        self.event_type = "InputMuteStateChanged"
        self.category = EventCategory.INPUTS
        self.priority = EventPriority.HIGH

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "InputMuteStateChanged":
        return cls(
            input_name=data["eventData"]["inputName"],
            input_uuid=data["eventData"].get("inputUuid"),
            input_muted=data["eventData"].get("inputMuted", False),
            event_data=data.get("eventData", {}),
        )


@dataclass
class InputVolumeChanged(BaseEvent):
    """Triggered when an input's volume changes."""

    input_name: str = ""
    input_uuid: Optional[str] = None
    input_volume_mul: float = 1.0
    input_volume_db: float = 0.0

    def __post_init__(self):
        self.event_type = "InputVolumeChanged"
        self.category = EventCategory.INPUTS

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "InputVolumeChanged":
        return cls(
            input_name=data["eventData"]["inputName"],
            input_uuid=data["eventData"].get("inputUuid"),
            input_volume_mul=data["eventData"].get("inputVolumeMul", 1.0),
            input_volume_db=data["eventData"].get("inputVolumeDb", 0.0),
            event_data=data.get("eventData", {}),
        )


# Output Events


@dataclass
class StreamStateChanged(BaseEvent):
    """Triggered when streaming state changes."""

    output_active: bool = False
    output_state: str = ""

    def __post_init__(self):
        self.event_type = "StreamStateChanged"
        self.category = EventCategory.OUTPUTS
        self.priority = EventPriority.CRITICAL

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "StreamStateChanged":
        return cls(
            output_active=data["eventData"]["outputActive"],
            output_state=data["eventData"]["outputState"],
            event_data=data.get("eventData", {}),
        )


@dataclass
class RecordStateChanged(BaseEvent):
    """Triggered when recording state changes."""

    output_active: bool = False
    output_state: str = ""
    output_path: Optional[str] = None

    def __post_init__(self):
        self.event_type = "RecordStateChanged"
        self.category = EventCategory.OUTPUTS
        self.priority = EventPriority.CRITICAL

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "RecordStateChanged":
        return cls(
            output_active=data["eventData"]["outputActive"],
            output_state=data["eventData"]["outputState"],
            output_path=data["eventData"].get("outputPath"),
            event_data=data.get("eventData", {}),
        )


# General Events


@dataclass
class ExitStarted(BaseEvent):
    """Triggered when OBS begins shutting down."""

    def __post_init__(self):
        self.event_type = "ExitStarted"
        self.priority = EventPriority.CRITICAL

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "ExitStarted":
        return cls(event_data=data.get("eventData", {}))


@dataclass
class StudioModeStateChanged(BaseEvent):
    """Triggered when Studio Mode is enabled or disabled."""

    studio_mode_enabled: bool = False

    def __post_init__(self):
        self.event_type = "StudioModeStateChanged"
        self.category = EventCategory.UI

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> "StudioModeStateChanged":
        return cls(
            studio_mode_enabled=data["eventData"]["studioModeEnabled"],
            event_data=data.get("eventData", {}),
        )


# Event Registry
EVENT_CLASSES: Dict[str, Type[BaseEvent]] = {
    "CurrentProgramSceneChanged": CurrentProgramSceneChanged,
    "SceneCreated": SceneCreated,
    "SceneRemoved": SceneRemoved,
    "SceneNameChanged": SceneNameChanged,
    "InputCreated": InputCreated,
    "InputRemoved": InputRemoved,
    "InputMuteStateChanged": InputMuteStateChanged,
    "InputVolumeChanged": InputVolumeChanged,
    "StreamStateChanged": StreamStateChanged,
    "RecordStateChanged": RecordStateChanged,
    "ExitStarted": ExitStarted,
    "StudioModeStateChanged": StudioModeStateChanged,
}


def parse_event(raw_data: Dict[str, Any]) -> Optional[BaseEvent]:
    """Parse raw WebSocket data into typed event."""
    event_type = raw_data.get("eventType")
    if not event_type:
        return None

    event_class = EVENT_CLASSES.get(event_type)
    if not event_class:
        logger.warning(f"Unknown event type: {event_type}")
        return None

    try:
        return event_class.from_raw(raw_data)
    except Exception as e:
        logger.error(f"Failed to parse event {event_type}: {e}")
        return None


class EventHandler:
    """Enhanced event handler with filtering and middleware support."""

    def __init__(self):
        self._handlers: Dict[str, List[EventHandlerType]] = defaultdict(list)
        self._filters: Dict[str, List[FilterType]] = defaultdict(list)
        self._middleware: List[MiddlewareType] = []
        self._event_queue: asyncio.Queue[BaseEvent] = asyncio.Queue()
        self._recording: bool = False
        self._recorded_events: deque[BaseEvent] = deque(maxlen=1000)
        self._processing_task: Optional[asyncio.Task] = None
        self._running: bool = False

    def on(self, event_type: Union[str, Type[BaseEvent]], *filters: FilterType):
        """
        Decorator to register event handlers.

        Usage:
            @handler.on(SceneCreated)
            async def on_scene_created(event: SceneCreated):
                print(f"Scene created: {event.scene_name}")

            @handler.on("InputMuteStateChanged", lambda e: e.input_name == "Microphone")
            async def on_mic_mute(event: InputMuteStateChanged):
                print(f"Mic muted: {event.input_muted}")
        """

        def decorator(func: EventHandlerType) -> EventHandlerType:
            event_name = event_type if isinstance(event_type, str) else event_type.__name__
            self._handlers[event_name].append(func)

            for filter_func in filters:
                self._filters[event_name].append(filter_func)

            logger.debug(f"Registered handler for {event_name}")
            return func

        return decorator

    def use(self, middleware: MiddlewareType):
        """Add middleware to the event processing pipeline."""
        self._middleware.append(middleware)
        logger.debug(f"Added middleware: {middleware.__name__}")

    async def emit(self, event: BaseEvent):
        """Emit an event to be processed."""
        if self._recording:
            self._recorded_events.append(event)

        await self._event_queue.put(event)

    async def start(self):
        """Start the event processing loop."""
        if self._running:
            return

        self._running = True
        self._processing_task = asyncio.create_task(self._process_events())
        logger.info("Event handler started")

    async def stop(self):
        """Stop the event processing loop."""
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        logger.info("Event handler stopped")

    async def _process_events(self):
        """Process events from the queue."""
        while self._running:
            try:
                # Get event with priority handling
                event = await asyncio.wait_for(self._event_queue.get(), timeout=0.1)

                # Get handlers for this event type
                handlers = self._handlers.get(event.event_type, [])
                filters = self._filters.get(event.event_type, [])

                # Apply filters
                if filters and not all(f(event) for f in filters):
                    continue

                # Execute handlers with middleware
                for handler in handlers:
                    try:
                        # Execute handler with middleware chain
                        await self._execute_with_middleware(event, handler)

                    except Exception as e:
                        logger.error(f"Error in event handler for {event.event_type}: {e}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing events: {e}")

    async def _execute_with_middleware(self, event: BaseEvent, handler: EventHandlerType):
        """Execute handler with middleware chain."""

        async def execute_handler():
            """Execute the actual handler."""
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)

        # Build middleware chain from right to left
        next_handler = execute_handler

        for middleware in reversed(self._middleware):
            # Use default parameters to capture the current values
            def make_middleware_wrapper(mw, next_h):
                async def middleware_wrapper():
                    if asyncio.iscoroutinefunction(mw):
                        await mw(event, next_h)
                    else:
                        mw(event, next_h)

                return middleware_wrapper

            next_handler = make_middleware_wrapper(middleware, next_handler)

        # Execute the chain
        await next_handler()

    def start_recording(self):
        """Start recording events."""
        self._recording = True
        self._recorded_events.clear()
        logger.info("Started event recording")

    def stop_recording(self) -> List[BaseEvent]:
        """Stop recording and return recorded events."""
        self._recording = False
        events = list(self._recorded_events)
        logger.info(f"Stopped event recording, captured {len(events)} events")
        return events

    async def replay_events(self, events: List[BaseEvent], speed: float = 1.0):
        """Replay recorded events."""
        logger.info(f"Replaying {len(events)} events at {speed}x speed")

        for i, event in enumerate(events):
            if i > 0:
                # Calculate delay between events
                delay = (event.timestamp - events[i - 1].timestamp).total_seconds()
                await asyncio.sleep(delay / speed)

            await self.emit(event)

    def save_events(self, events: List[BaseEvent], file_path: Path):
        """Save events to file."""
        data = [event.to_dict() for event in events]
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(events)} events to {file_path}")

    def load_events(self, file_path: Path) -> List[BaseEvent]:
        """Load events from file."""
        with open(file_path, "r") as f:
            data = json.load(f)

        events = []
        for item in data:
            event_type = item.get("event_type")
            event_class = EVENT_CLASSES.get(event_type)
            if event_class:
                # Reconstruct event
                event = event_class(**{k: v for k, v in item.items() if k not in ["event_type", "timestamp"]})
                event.timestamp = datetime.fromisoformat(item["timestamp"])
                events.append(event)

        logger.info(f"Loaded {len(events)} events from {file_path}")
        return events

    async def wait_for_event(self, event_name: str, timeout: float = 30.0) -> Optional[BaseEvent]:
        """
        Wait for a specific event.

        Args:
            event_name: The event name to wait for
            timeout: Maximum time to wait

        Returns:
            The event data if received, None if timeout
        """
        future: asyncio.Future[BaseEvent] = asyncio.Future()

        def handler(event: BaseEvent) -> None:
            if not future.done():
                future.set_result(event)

        # Register temporary handler
        self._handlers[event_name].append(handler)

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            # Remove temporary handler
            if handler in self._handlers[event_name]:
                self._handlers[event_name].remove(handler)


# Middleware Examples


async def logging_middleware(event: BaseEvent, next_handler: Callable):
    """Log all events."""
    logger.info(f"Event: {event.event_type} - {event.event_data}")
    if asyncio.iscoroutinefunction(next_handler):
        await next_handler()
    else:
        next_handler()


async def error_handling_middleware(event: BaseEvent, next_handler: Callable):
    """Handle errors in event handlers."""
    try:
        if asyncio.iscoroutinefunction(next_handler):
            await next_handler()
        else:
            next_handler()
    except Exception as e:
        logger.error(f"Error handling {event.event_type}: {e}", exc_info=True)


async def performance_middleware(event: BaseEvent, next_handler: Callable):
    """Measure event handler performance."""
    start_time = time.time()

    if asyncio.iscoroutinefunction(next_handler):
        await next_handler()
    else:
        next_handler()

    elapsed = time.time() - start_time
    if elapsed > 0.1:  # Log slow handlers
        logger.warning(f"Slow handler for {event.event_type}: {elapsed:.3f}s")


# Event Subscription Patterns


class EventSubscription:
    """Subscription pattern for event handling."""

    def __init__(self, handler: EventHandler):
        self.handler = handler
        self._subscriptions: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event_type: Union[str, Type[BaseEvent]], callback: Callable) -> Callable:
        """Subscribe to an event type."""
        event_name = event_type if isinstance(event_type, str) else event_type.__name__
        self._subscriptions[event_name].append(callback)

        # Register with handler
        @self.handler.on(event_type)
        async def wrapper(event):
            for cb in self._subscriptions[event_name]:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event)
                else:
                    cb(event)

        return callback

    def unsubscribe(self, event_type: Union[str, Type[BaseEvent]], callback: Callable):
        """Unsubscribe from an event type."""
        event_name = event_type if isinstance(event_type, str) else event_type.__name__
        if callback in self._subscriptions[event_name]:
            self._subscriptions[event_name].remove(callback)

    def clear(self, event_type: Optional[Union[str, Type[BaseEvent]]] = None):
        """Clear subscriptions."""
        if event_type:
            event_name = event_type if isinstance(event_type, str) else event_type.__name__
            self._subscriptions[event_name].clear()
        else:
            self._subscriptions.clear()
