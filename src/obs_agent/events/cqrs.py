"""
CQRS (Command Query Responsibility Segregation) implementation.

This module provides command handlers, query handlers, and the command bus
for separating write and read operations in the event-sourced system.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, Union
from uuid import UUID, uuid4

from .domain import DomainEvent, EventMetadata, SceneSwitched, StreamStarted
from .store import EventStore


class Command(ABC):
    """Base class for all commands."""

    def __init__(self):
        self.command_id: UUID = uuid4()
        self.timestamp: datetime = datetime.utcnow()
        self.correlation_id: Optional[UUID] = None
        self.user_id: Optional[str] = None

    @abstractmethod
    def get_aggregate_id(self) -> str:
        """Return the aggregate ID this command targets."""
        pass


class Query(ABC):
    """Base class for all queries."""

    def __init__(self):
        self.query_id: UUID = uuid4()
        self.timestamp: datetime = datetime.utcnow()


# Commands


class SwitchScene(Command):
    """Command to switch the active scene."""

    def __init__(
        self, to_scene: str, transition_type: Optional[str] = None, transition_duration: Optional[int] = None, **kwargs
    ):
        super().__init__()
        self.to_scene = to_scene
        self.transition_type = transition_type
        self.transition_duration = transition_duration
        # Allow setting correlation_id and user_id via kwargs
        if "correlation_id" in kwargs:
            self.correlation_id = kwargs["correlation_id"]
        if "user_id" in kwargs:
            self.user_id = kwargs["user_id"]

    def get_aggregate_id(self) -> str:
        return "obs_system"


class StartStream(Command):
    """Command to start streaming."""

    def __init__(self, stream_settings: Optional[Dict[str, Any]] = None, service: Optional[str] = None, **kwargs):
        super().__init__()
        self.stream_settings = stream_settings or {}
        self.service = service
        if "correlation_id" in kwargs:
            self.correlation_id = kwargs["correlation_id"]
        if "user_id" in kwargs:
            self.user_id = kwargs["user_id"]

    def get_aggregate_id(self) -> str:
        return "stream"


class StopStream(Command):
    """Command to stop streaming."""

    def __init__(self, **kwargs):
        super().__init__()
        if "correlation_id" in kwargs:
            self.correlation_id = kwargs["correlation_id"]
        if "user_id" in kwargs:
            self.user_id = kwargs["user_id"]

    def get_aggregate_id(self) -> str:
        return "stream"


class CreateScene(Command):
    """Command to create a new scene."""

    def __init__(self, scene_name: str, scene_settings: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__()
        self.scene_name = scene_name
        self.scene_settings = scene_settings or {}
        if "correlation_id" in kwargs:
            self.correlation_id = kwargs["correlation_id"]
        if "user_id" in kwargs:
            self.user_id = kwargs["user_id"]

    def get_aggregate_id(self) -> str:
        return f"scene:{self.scene_name}"


class SetSourceVolume(Command):
    """Command to set source volume."""

    def __init__(self, source_name: str, volume: float, **kwargs):
        super().__init__()
        self.source_name = source_name
        self.volume = volume
        if "correlation_id" in kwargs:
            self.correlation_id = kwargs["correlation_id"]
        if "user_id" in kwargs:
            self.user_id = kwargs["user_id"]

    def get_aggregate_id(self) -> str:
        return f"source:{self.source_name}"


# Queries


class GetCurrentScene(Query):
    """Query to get the current active scene."""

    pass


class GetStreamStatus(Query):
    """Query to get streaming status."""

    pass


class GetSceneList(Query):
    """Query to get all scenes."""

    pass


class GetEventHistory(Query):
    """Query to get event history."""

    def __init__(
        self,
        aggregate_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ):
        super().__init__()
        self.aggregate_id = aggregate_id
        self.since = since
        self.until = until
        self.limit = limit


class GetAggregateState(Query):
    """Query to get the current state of an aggregate."""

    def __init__(self, aggregate_id: str, at_timestamp: Optional[datetime] = None):
        super().__init__()
        self.aggregate_id = aggregate_id
        self.at_timestamp = at_timestamp


# Command Handlers


class CommandHandler(ABC):
    """Base class for command handlers."""

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    @abstractmethod
    async def handle(self, command: Command) -> List[DomainEvent]:
        """
        Handle a command and return the events to be stored.

        This is where business logic and validation happens.
        """
        pass

    @abstractmethod
    def can_handle(self, command: Command) -> bool:
        """Check if this handler can handle the command."""
        pass


class SwitchSceneHandler(CommandHandler):
    """Handler for scene switching commands."""

    def can_handle(self, command: Command) -> bool:
        return isinstance(command, SwitchScene)

    async def handle(self, command: SwitchScene) -> List[DomainEvent]:
        """Handle scene switch command."""
        # Get current scene from event history
        events = self.event_store.get_events("obs_system")
        current_scene = "Unknown"

        for event in reversed(events):
            if isinstance(event, SceneSwitched):
                current_scene = event.to_scene
                break

        # Create scene switched event
        event = SceneSwitched(
            aggregate_id=command.get_aggregate_id(),
            metadata=EventMetadata(
                correlation_id=command.correlation_id, causation_id=command.command_id, user_id=command.user_id
            ),
            from_scene=current_scene,
            to_scene=command.to_scene,
            transition_type=command.transition_type,
            transition_duration=command.transition_duration,
        )

        return [event]


class StartStreamHandler(CommandHandler):
    """Handler for start stream commands."""

    def can_handle(self, command: Command) -> bool:
        return isinstance(command, StartStream)

    async def handle(self, command: StartStream) -> List[DomainEvent]:
        """Handle start stream command."""
        # Check if already streaming
        events = self.event_store.get_events("stream")
        is_streaming = False

        for event in reversed(events):
            if isinstance(event, StreamStarted):
                is_streaming = True
                break
            elif event.event_type.value == "stream.stopped":
                is_streaming = False
                break

        if is_streaming:
            raise ValueError("Stream is already active")

        # Create stream started event
        event = StreamStarted(
            aggregate_id=command.get_aggregate_id(),
            metadata=EventMetadata(
                correlation_id=command.correlation_id, causation_id=command.command_id, user_id=command.user_id
            ),
            stream_settings=command.stream_settings,
            service=command.service,
        )

        return [event]


# Query Handlers


class QueryHandler(ABC):
    """Base class for query handlers."""

    def __init__(self, event_store: EventStore, read_model: "ReadModel"):
        self.event_store = event_store
        self.read_model = read_model

    @abstractmethod
    async def handle(self, query: Query) -> Any:
        """Handle a query and return the result."""
        pass

    @abstractmethod
    def can_handle(self, query: Query) -> bool:
        """Check if this handler can handle the query."""
        pass


class GetCurrentSceneHandler(QueryHandler):
    """Handler for getting current scene."""

    def can_handle(self, query: Query) -> bool:
        return isinstance(query, GetCurrentScene)

    async def handle(self, query: GetCurrentScene) -> str:
        """Get the current scene from read model."""
        return self.read_model.get_current_scene()


class GetEventHistoryHandler(QueryHandler):
    """Handler for event history queries."""

    def can_handle(self, query: Query) -> bool:
        return isinstance(query, GetEventHistory)

    async def handle(self, query: GetEventHistory) -> List[Dict[str, Any]]:
        """Get event history."""
        events = self.event_store.replay_events(aggregate_id=query.aggregate_id, since=query.since, until=query.until)

        if query.limit:
            events = events[: query.limit]

        return [event.to_dict() for event in events]


# Command Bus


class CommandBus:
    """
    Command bus for routing commands to handlers.

    This is the write side of CQRS.
    """

    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.handlers: List[CommandHandler] = []
        self._middleware: List[Callable] = []

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default command handlers."""
        self.register_handler(SwitchSceneHandler(self.event_store))
        self.register_handler(StartStreamHandler(self.event_store))

    def register_handler(self, handler: CommandHandler):
        """Register a command handler."""
        self.handlers.append(handler)

    def add_middleware(self, middleware: Callable):
        """Add middleware for command processing."""
        self._middleware.append(middleware)

    async def send(self, command: Command) -> None:
        """
        Send a command for processing.

        This will find the appropriate handler, execute it,
        and store the resulting events.
        """
        # Apply middleware
        for middleware in self._middleware:
            command = await middleware(command)

        # Find handler
        handler = None
        for h in self.handlers:
            if h.can_handle(command):
                handler = h
                break

        if not handler:
            raise ValueError(f"No handler found for command: {type(command).__name__}")

        # Handle command
        events = await handler.handle(command)

        # Store events
        for event in events:
            self.event_store.append(event)


# Query Bus


class QueryBus:
    """
    Query bus for routing queries to handlers.

    This is the read side of CQRS.
    """

    def __init__(self, event_store: EventStore, read_model: "ReadModel"):
        self.event_store = event_store
        self.read_model = read_model
        self.handlers: List[QueryHandler] = []

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default query handlers."""
        self.register_handler(GetCurrentSceneHandler(self.event_store, self.read_model))
        self.register_handler(GetEventHistoryHandler(self.event_store, self.read_model))

    def register_handler(self, handler: QueryHandler):
        """Register a query handler."""
        self.handlers.append(handler)

    async def send(self, query: Query) -> Any:
        """Send a query for processing."""
        # Find handler
        handler = None
        for h in self.handlers:
            if h.can_handle(query):
                handler = h
                break

        if not handler:
            raise ValueError(f"No handler found for query: {type(query).__name__}")

        # Handle query
        return await handler.handle(query)


# Read Model


class ReadModel:
    """
    Read model that maintains denormalized views of the event stream.

    This is optimized for queries and is eventually consistent.
    """

    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self._current_scene = "Unknown"
        self._is_streaming = False
        self._scenes: List[str] = []
        self._sources: Dict[str, Dict[str, Any]] = {}

        # Subscribe to events to update read model
        self.event_store.subscribe(self._handle_event)

        # Rebuild from events
        self._rebuild()

    def _rebuild(self):
        """Rebuild read model from event stream."""
        events = self.event_store.replay_events()
        for event in events:
            self._handle_event(event)

    def _handle_event(self, event: DomainEvent):
        """Update read model based on events."""
        if isinstance(event, SceneSwitched):
            self._current_scene = event.to_scene
        elif isinstance(event, StreamStarted):
            self._is_streaming = True
        elif event.event_type.value == "stream.stopped":
            self._is_streaming = False
        elif event.event_type.value == "scene.created":
            scene_name = event.get_event_data().get("scene_name")
            if scene_name and scene_name not in self._scenes:
                self._scenes.append(scene_name)

    def get_current_scene(self) -> str:
        """Get current scene."""
        return self._current_scene

    def is_streaming(self) -> bool:
        """Check if streaming."""
        return self._is_streaming

    def get_scenes(self) -> List[str]:
        """Get all scenes."""
        return self._scenes.copy()

    def get_source_state(self, source_name: str) -> Dict[str, Any]:
        """Get source state."""
        return self._sources.get(source_name, {})
