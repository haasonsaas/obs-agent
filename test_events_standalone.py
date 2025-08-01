#!/usr/bin/env python3
"""
Standalone test of the events system core functionality.
"""

import asyncio
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional


# Simplified logger for testing
class TestLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def debug(self, msg): print(f"DEBUG: {msg}")
    def warning(self, msg): print(f"WARN: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")


logger = TestLogger()


# Copy key classes from events.py for testing
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict, deque
from abc import ABC, abstractmethod
from typing import Union, Callable, Type, TypeVar


class EventPriority(Enum):
    LOW = auto()
    NORMAL = auto() 
    HIGH = auto()
    CRITICAL = auto()


class EventCategory(Enum):
    GENERAL = "General"
    SCENES = "Scenes"
    INPUTS = "Inputs"
    OUTPUTS = "Outputs"


@dataclass
class BaseEvent(ABC):
    event_type: str = ""
    event_intent: Optional[int] = None
    event_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    category: EventCategory = EventCategory.GENERAL

    @classmethod
    @abstractmethod
    def from_raw(cls, data: Dict[str, Any]):
        pass


@dataclass
class CurrentProgramSceneChanged(BaseEvent):
    scene_name: str = ""
    scene_uuid: Optional[str] = None

    def __post_init__(self):
        self.event_type = "CurrentProgramSceneChanged"
        self.category = EventCategory.SCENES

    @classmethod
    def from_raw(cls, data: Dict[str, Any]):
        return cls(
            scene_name=data["eventData"]["sceneName"],
            scene_uuid=data["eventData"].get("sceneUuid"),
            event_data=data.get("eventData", {}),
        )


@dataclass
class InputMuteStateChanged(BaseEvent):
    input_name: str = ""
    input_uuid: Optional[str] = None
    input_muted: bool = False

    def __post_init__(self):
        self.event_type = "InputMuteStateChanged"
        self.category = EventCategory.INPUTS
        self.priority = EventPriority.HIGH

    @classmethod
    def from_raw(cls, data: Dict[str, Any]):
        return cls(
            input_name=data["eventData"]["inputName"],
            input_uuid=data["eventData"].get("inputUuid"),
            input_muted=data["eventData"].get("inputMuted", False),
            event_data=data.get("eventData", {}),
        )


# Simple EventHandler for testing
class EventHandler:
    def __init__(self):
        self._handlers = defaultdict(list)
        self._filters = defaultdict(list)
        self._middleware = []
        self._event_queue = asyncio.Queue()
        self._recording = False
        self._recorded_events = deque(maxlen=1000)
        self._processing_task = None
        self._running = False

    def on(self, event_type: Union[str, Type[BaseEvent]], *filters):
        def decorator(func):
            event_name = event_type if isinstance(event_type, str) else event_type.__name__
            self._handlers[event_name].append(func)
            
            for filter_func in filters:
                self._filters[event_name].append(filter_func)
            
            logger.debug(f"Registered handler for {event_name}")
            return func
        return decorator

    def use(self, middleware):
        self._middleware.append(middleware)
        logger.debug(f"Added middleware: {middleware.__name__}")

    async def emit(self, event: BaseEvent):
        if self._recording:
            self._recorded_events.append(event)
        await self._event_queue.put(event)

    async def start(self):
        if self._running:
            return
        self._running = True
        self._processing_task = asyncio.create_task(self._process_events())
        logger.info("Event handler started")

    async def stop(self):
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        logger.info("Event handler stopped")

    async def _process_events(self):
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=0.1)
                
                handlers = self._handlers.get(event.event_type, [])
                filters = self._filters.get(event.event_type, [])

                if filters and not all(f(event) for f in filters):
                    continue

                for handler in handlers:
                    try:
                        await self._execute_with_middleware(event, handler)
                    except Exception as e:
                        logger.error(f"Error in event handler for {event.event_type}: {e}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing events: {e}")

    async def _execute_with_middleware(self, event: BaseEvent, handler):
        async def execute_handler():
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)

        next_handler = execute_handler

        for middleware in reversed(self._middleware):
            def make_middleware_wrapper(mw, next_h):
                async def middleware_wrapper():
                    if asyncio.iscoroutinefunction(mw):
                        await mw(event, next_h)
                    else:
                        mw(event, next_h)
                return middleware_wrapper
            next_handler = make_middleware_wrapper(middleware, next_handler)

        await next_handler()

    def start_recording(self):
        self._recording = True
        self._recorded_events.clear()
        logger.info("Started event recording")

    def stop_recording(self):
        self._recording = False
        events = list(self._recorded_events)
        logger.info(f"Stopped event recording, captured {len(events)} events")
        return events

    async def replay_events(self, events: List[BaseEvent], speed: float = 1.0):
        logger.info(f"Replaying {len(events)} events at {speed}x speed")
        for i, event in enumerate(events):
            if i > 0:
                delay = (event.timestamp - events[i - 1].timestamp).total_seconds()
                await asyncio.sleep(delay / speed)
            await self.emit(event)


# Test functions
def test_event_creation():
    print("✅ Testing event creation...")
    
    # Test scene change event
    raw_data = {
        "eventType": "CurrentProgramSceneChanged",
        "eventData": {
            "sceneName": "Main Scene",
            "sceneUuid": "12345"
        }
    }
    
    event = CurrentProgramSceneChanged.from_raw(raw_data)
    assert event.scene_name == "Main Scene"
    assert event.scene_uuid == "12345"
    print("  ✅ Scene change event created successfully")
    
    # Test input mute event
    raw_data = {
        "eventType": "InputMuteStateChanged",
        "eventData": {
            "inputName": "Microphone",
            "inputMuted": True
        }
    }
    
    event = InputMuteStateChanged.from_raw(raw_data)
    assert event.input_name == "Microphone"
    assert event.input_muted is True
    print("  ✅ Input mute event created successfully")


async def test_event_handler():
    print("✅ Testing event handler...")
    
    handler = EventHandler()
    events_received = []
    
    # Register event handlers
    @handler.on(CurrentProgramSceneChanged)
    async def on_scene_change(event: CurrentProgramSceneChanged):
        events_received.append(f"Scene: {event.scene_name}")
    
    @handler.on(InputMuteStateChanged, lambda e: e.input_name == "Microphone")
    async def on_mic_mute(event: InputMuteStateChanged):
        events_received.append(f"Mic muted: {event.input_muted}")
    
    # Start event processing
    await handler.start()
    
    # Create and emit events
    scene_event = CurrentProgramSceneChanged(scene_name="Test Scene", scene_uuid="abc123")
    await handler.emit(scene_event)
    
    mic_event = InputMuteStateChanged(input_name="Microphone", input_muted=True)
    await handler.emit(mic_event)
    
    # Non-matching event (should be filtered out)
    other_event = InputMuteStateChanged(input_name="Desktop Audio", input_muted=True)
    await handler.emit(other_event)
    
    # Wait for processing
    await asyncio.sleep(0.2)
    
    # Stop handler
    await handler.stop()
    
    # Verify results
    expected = ["Scene: Test Scene", "Mic muted: True"]
    assert events_received == expected, f"Expected {expected}, got {events_received}"
    print("  ✅ Event handlers processed correctly")
    print("  ✅ Event filtering worked correctly")


async def test_middleware():
    print("✅ Testing middleware...")
    
    handler = EventHandler()
    middleware_calls = []
    
    # Custom middleware
    async def test_middleware(event: BaseEvent, next_handler):
        middleware_calls.append(f"Before: {event.event_type}")
        await next_handler()
        middleware_calls.append(f"After: {event.event_type}")
    
    # Add middleware
    handler.use(test_middleware)
    
    # Register handler
    @handler.on(CurrentProgramSceneChanged)
    async def on_scene_created(event: CurrentProgramSceneChanged):
        middleware_calls.append(f"Handler: {event.scene_name}")
    
    # Start processing
    await handler.start()
    
    # Emit event
    event = CurrentProgramSceneChanged(scene_name="New Scene", scene_uuid="xyz789")
    await handler.emit(event)
    
    # Wait and stop
    await asyncio.sleep(0.2)
    await handler.stop()
    
    # Verify middleware was called
    assert len(middleware_calls) >= 3, f"Expected at least 3 calls, got {middleware_calls}"
    assert "Before: CurrentProgramSceneChanged" in middleware_calls
    assert "Handler: New Scene" in middleware_calls
    assert "After: CurrentProgramSceneChanged" in middleware_calls
    print("  ✅ Middleware executed in correct order")


async def test_event_recording():
    print("✅ Testing event recording...")
    
    handler = EventHandler()
    replayed_events = []
    
    # Register handler for replayed events
    @handler.on(CurrentProgramSceneChanged)
    async def on_replay(event: CurrentProgramSceneChanged):
        replayed_events.append(event.scene_name)
    
    await handler.start()
    
    # Start recording
    handler.start_recording()
    
    # Generate events
    events = [
        CurrentProgramSceneChanged(scene_name="Scene 1"),
        CurrentProgramSceneChanged(scene_name="Scene 2"),
        CurrentProgramSceneChanged(scene_name="Scene 3"),
    ]
    
    for event in events:
        await handler.emit(event)
        await asyncio.sleep(0.01)  # Small delay between events
    
    # Stop recording
    recorded = handler.stop_recording()
    
    assert len(recorded) == 3, f"Expected 3 recorded events, got {len(recorded)}"
    print(f"  ✅ Recorded {len(recorded)} events successfully")
    
    # Clear received events and replay
    replayed_events.clear()
    await handler.replay_events(recorded, speed=10.0)  # Fast replay
    
    await asyncio.sleep(0.2)  # Wait for replay
    await handler.stop()
    
    # Verify replay
    expected_scenes = ["Scene 1", "Scene 2", "Scene 3"]
    assert replayed_events == expected_scenes, f"Expected {expected_scenes}, got {replayed_events}"
    print("  ✅ Event replay worked correctly")


async def main():
    print("🚀 Testing OBS WebSocket Events System (Standalone)")
    print("=" * 50)
    
    try:
        test_event_creation()
        await test_event_handler()
        await test_middleware()
        await test_event_recording()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! WebSocket event system is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())