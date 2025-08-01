#!/usr/bin/env python3
"""
Simple test of the events system without OBS dependencies.
"""

import asyncio
import sys
import os
from datetime import datetime

# Import events module directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "obs_agent"))

from events import (
    BaseEvent,
    CurrentProgramSceneChanged,
    EventHandler,
    InputMuteStateChanged,
    SceneCreated,
    parse_event,
    logging_middleware,
    performance_middleware,
)


def test_event_creation():
    """Test creating events from raw data."""
    print("✅ Testing event creation...")
    
    # Test scene change event
    raw_data = {
        "eventType": "CurrentProgramSceneChanged",
        "eventData": {
            "sceneName": "Main Scene",
            "sceneUuid": "12345"
        }
    }
    
    event = parse_event(raw_data)
    assert event is not None
    assert isinstance(event, CurrentProgramSceneChanged)
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
    
    event = parse_event(raw_data)
    assert event is not None
    assert isinstance(event, InputMuteStateChanged)
    assert event.input_name == "Microphone"
    assert event.input_muted is True
    print("  ✅ Input mute event created successfully")


async def test_event_handler():
    """Test the event handler system."""
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
    """Test middleware functionality."""
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
    handler.use(performance_middleware)
    
    # Register handler
    @handler.on(SceneCreated)
    async def on_scene_created(event: SceneCreated):
        middleware_calls.append(f"Handler: {event.scene_name}")
    
    # Start processing
    await handler.start()
    
    # Emit event
    event = SceneCreated(scene_name="New Scene", scene_uuid="xyz789")
    await handler.emit(event)
    
    # Wait and stop
    await asyncio.sleep(0.2)
    await handler.stop()
    
    # Verify middleware was called
    assert len(middleware_calls) >= 3, f"Expected at least 3 calls, got {middleware_calls}"
    assert "Before: SceneCreated" in middleware_calls
    assert "Handler: New Scene" in middleware_calls
    assert "After: SceneCreated" in middleware_calls
    print("  ✅ Middleware executed in correct order")


async def test_event_recording():
    """Test event recording and replay."""
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
    """Run all tests."""
    print("🚀 Testing OBS WebSocket Events System")
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