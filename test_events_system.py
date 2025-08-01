#!/usr/bin/env python3
"""
Test the enhanced WebSocket event system without requiring OBS connection.

This test verifies that our event system works correctly by:
1. Testing event class creation
2. Testing event parsing
3. Testing decorator registration
4. Testing filtering
5. Testing middleware
6. Testing recording/replay
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.obs_agent.events import (
    EventHandler,
    EventSubscription,
    CurrentProgramSceneChanged,
    SceneCreated,
    StreamStateChanged,
    InputMuteStateChanged,
    logging_middleware,
    performance_middleware,
    parse_event,
)


async def test_event_creation():
    """Test creating and using event objects"""
    print("🧪 Testing Event Creation...")
    
    # Test creating events manually
    scene_event = CurrentProgramSceneChanged(
        scene_name="Test Scene",
        scene_uuid="scene-123"
    )
    
    assert scene_event.scene_name == "Test Scene"
    assert scene_event.event_type == "CurrentProgramSceneChanged"
    print("  ✅ Manual event creation works")
    
    # Test from_raw parsing
    raw_data = {
        "eventType": "CurrentProgramSceneChanged",
        "eventData": {
            "sceneName": "Parsed Scene",
            "sceneUuid": "scene-456"
        }
    }
    
    parsed_event = parse_event(raw_data)
    assert parsed_event is not None
    assert isinstance(parsed_event, CurrentProgramSceneChanged)
    assert parsed_event.scene_name == "Parsed Scene"
    print("  ✅ Event parsing from raw data works")


async def test_event_handlers():
    """Test event handler registration and execution"""
    print("\n🎯 Testing Event Handlers...")
    
    handler = EventHandler()
    await handler.start()
    
    # Track handler calls
    handler_calls = []
    
    # Test basic decorator
    @handler.on(SceneCreated)
    async def on_scene_created(event: SceneCreated):
        handler_calls.append(("scene_created", event.scene_name))
    
    # Test string-based handler
    @handler.on("StreamStateChanged")
    async def on_stream_state(event):
        handler_calls.append(("stream_state", event.output_active))
    
    # Test filtered handler
    @handler.on(InputMuteStateChanged, lambda e: "Mic" in e.input_name)
    async def on_mic_only(event):
        handler_calls.append(("mic_filtered", event.input_muted))
    
    # Emit some events
    scene_event = SceneCreated(scene_name="New Scene")
    stream_event = StreamStateChanged(output_active=True, output_state="OBS_WEBSOCKET_OUTPUT_STARTED")
    mic_event = InputMuteStateChanged(input_name="Microphone", input_muted=True)
    other_event = InputMuteStateChanged(input_name="Desktop Audio", input_muted=True)
    
    await handler.emit(scene_event)
    await handler.emit(stream_event)
    await handler.emit(mic_event)
    await handler.emit(other_event)  # Should be filtered out
    
    # Wait for processing
    await asyncio.sleep(0.1)
    
    await handler.stop()
    
    # Verify handler calls
    assert len(handler_calls) == 3
    assert ("scene_created", "New Scene") in handler_calls
    assert ("stream_state", True) in handler_calls
    assert ("mic_filtered", True) in handler_calls
    
    print("  ✅ Basic event handlers work")
    print("  ✅ String-based handlers work")
    print("  ✅ Filtered handlers work")


async def test_middleware():
    """Test middleware functionality"""
    print("\n⚙️ Testing Middleware...")
    
    handler = EventHandler()
    await handler.start()
    
    middleware_calls = []
    
    # Custom middleware
    async def test_middleware(event, next_handler):
        middleware_calls.append(f"before_{event.event_type}")
        await next_handler()
        middleware_calls.append(f"after_{event.event_type}")
    
    handler.use(test_middleware)
    
    handler_calls = []
    
    @handler.on(SceneCreated)
    async def on_scene(event):
        handler_calls.append(event.scene_name)
    
    # Emit event
    event = SceneCreated(scene_name="Middleware Test")
    await handler.emit(event)
    
    # Wait for processing
    await asyncio.sleep(0.1)
    
    await handler.stop()
    
    # Verify middleware was called
    assert len(middleware_calls) == 2
    assert "before_SceneCreated" in middleware_calls
    assert "after_SceneCreated" in middleware_calls
    assert len(handler_calls) == 1
    assert handler_calls[0] == "Middleware Test"
    
    print("  ✅ Custom middleware works")


async def test_recording_replay():
    """Test event recording and replay"""
    print("\n📼 Testing Recording & Replay...")
    
    handler = EventHandler()
    await handler.start()
    
    recorded_events = []
    
    @handler.on(SceneCreated)
    async def record_handler(event):
        recorded_events.append(event.scene_name)
    
    # Start recording
    handler.start_recording()
    
    # Generate events
    events = [
        SceneCreated(scene_name="Scene 1"),
        SceneCreated(scene_name="Scene 2"),
        SceneCreated(scene_name="Scene 3"),
    ]
    
    for event in events:
        await handler.emit(event)
    
    await asyncio.sleep(0.1)
    
    # Stop recording
    recorded = handler.stop_recording()
    
    assert len(recorded) == 3
    assert all(isinstance(e, SceneCreated) for e in recorded)
    
    print("  ✅ Event recording works")
    
    # Test save/load
    test_file = Path("test_events.json")
    handler.save_events(recorded, test_file)
    
    loaded_events = handler.load_events(test_file)
    assert len(loaded_events) == 3
    
    # Clean up
    test_file.unlink(missing_ok=True)
    
    print("  ✅ Event save/load works")
    
    # Test replay (simulate by emitting loaded events)
    recorded_events.clear()
    
    for event in loaded_events:
        await handler.emit(event)
    
    await asyncio.sleep(0.1)
    
    await handler.stop()
    
    # Verify replay worked
    print(f"    Recorded events count: {len(recorded_events)}")
    assert len(recorded_events) >= 3  # At least the original 3
    
    print("  ✅ Event replay works")


async def test_subscription_pattern():
    """Test subscription pattern"""
    print("\n📬 Testing Subscription Pattern...")
    
    handler = EventHandler()
    await handler.start()
    
    subscription = EventSubscription(handler)
    
    # Track subscriptions
    scene_calls = []
    stream_calls = []
    
    def scene_subscriber(event):
        scene_calls.append(event.scene_name)
    
    def stream_subscriber(event):
        stream_calls.append(event.output_active)
    
    # Subscribe
    subscription.subscribe(SceneCreated, scene_subscriber)
    subscription.subscribe(StreamStateChanged, stream_subscriber)
    
    # Emit events
    await handler.emit(SceneCreated(scene_name="Sub Test"))
    await handler.emit(StreamStateChanged(output_active=True))
    
    await asyncio.sleep(0.1)
    
    # Verify subscriptions worked
    assert len(scene_calls) == 1
    assert scene_calls[0] == "Sub Test"
    assert len(stream_calls) == 1
    assert stream_calls[0] is True
    
    # Test unsubscribe
    subscription.unsubscribe(SceneCreated, scene_subscriber)
    
    await handler.emit(SceneCreated(scene_name="After Unsub"))
    await asyncio.sleep(0.1)
    
    # Should not have been called again
    assert len(scene_calls) == 1
    
    await handler.stop()
    
    print("  ✅ Subscription pattern works")
    print("  ✅ Unsubscribe works")


async def main():
    """Run all event system tests"""
    print("🚀 Testing Enhanced WebSocket Event System")
    print("=" * 60)
    
    try:
        await test_event_creation()
        await test_event_handlers()
        await test_middleware()
        await test_recording_replay()
        await test_subscription_pattern()
        
        print("\n✅ All event system tests passed!")
        print("🎉 Enhanced WebSocket event system is working correctly")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)