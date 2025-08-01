# Enhanced WebSocket Event System

## 🚀 Overview

The OBS Agent has been significantly enhanced with a powerful WebSocket event system that provides:

- **Typed Event Classes** - Strongly-typed events with proper validation
- **Decorator-Based Handlers** - Clean, intuitive event registration
- **Event Filtering** - Conditional event processing
- **Middleware System** - Cross-cutting concerns like logging and performance monitoring
- **Event Recording & Replay** - Debug and test event flows
- **Subscription Patterns** - Decoupled event handling

## ✨ Key Features

### 1. Typed Event Classes

All OBS WebSocket events are now represented by strongly-typed classes:

```python
from obs_agent import (
    CurrentProgramSceneChanged,
    StreamStateChanged, 
    InputMuteStateChanged
)

# Events have proper type hints and validation
event = CurrentProgramSceneChanged(
    scene_name="Gaming Scene",
    scene_uuid="scene-123"
)
```

### 2. Decorator-Based Event Handlers

Clean, intuitive event registration using decorators:

```python
from obs_agent import OBSAgentV2, CurrentProgramSceneChanged

agent = OBSAgentV2()

# Method 1: Using the agent decorator
@agent.on(CurrentProgramSceneChanged)
async def on_scene_changed(event: CurrentProgramSceneChanged):
    print(f"Scene changed to: {event.scene_name}")

# Method 2: Using the events property
@agent.events.on(StreamStateChanged)
async def on_stream_state(event: StreamStateChanged):
    print(f"Stream {'started' if event.output_active else 'stopped'}")
```

### 3. Event Filtering

Filter events with lambda functions for conditional processing:

```python
# Only handle microphone mute events
@agent.on(InputMuteStateChanged, lambda e: "Mic" in e.input_name)
async def on_mic_mute(event: InputMuteStateChanged):
    print(f"Microphone {'muted' if event.input_muted else 'unmuted'}")

# Multiple filters can be chained
@agent.on(
    SceneCreated, 
    lambda e: not e.is_group,  # Not a group
    lambda e: "Gaming" in e.scene_name  # Contains "Gaming"
)
async def on_gaming_scene_created(event: SceneCreated):
    print(f"Gaming scene created: {event.scene_name}")
```

### 4. Middleware System

Add cross-cutting concerns with middleware:

```python
from obs_agent import logging_middleware, performance_middleware

# Use built-in middleware
agent.events.use(logging_middleware)
agent.events.use(performance_middleware)

# Create custom middleware
async def auth_middleware(event, next_handler):
    if isinstance(event, StreamStateChanged) and event.output_active:
        print("🔐 Checking streaming authorization...")
    await next_handler()

agent.events.use(auth_middleware)
```

### 5. Event Recording & Replay

Record events for debugging and testing:

```python
# Start recording
agent.events.start_recording()

# ... perform actions that generate events ...

# Stop and get recorded events
recorded_events = agent.events.stop_recording()

# Save to file
agent.events.save_events(recorded_events, Path("events.json"))

# Load and replay
loaded_events = agent.events.load_events(Path("events.json"))
await agent.events.replay_events(loaded_events, speed=2.0)
```

### 6. Subscription Patterns

Decoupled event handling with pub/sub:

```python
from obs_agent import EventSubscription

subscription = EventSubscription(agent.events)

def scene_monitor(event: CurrentProgramSceneChanged):
    print(f"Scene Monitor: {event.scene_name}")

# Subscribe
subscription.subscribe(CurrentProgramSceneChanged, scene_monitor)

# Unsubscribe when done
subscription.unsubscribe(CurrentProgramSceneChanged, scene_monitor)
```

## 📋 Available Event Types

### Scene Events
- `CurrentProgramSceneChanged` - Scene switched
- `SceneCreated` - New scene created
- `SceneRemoved` - Scene deleted
- `SceneNameChanged` - Scene renamed

### Input Events
- `InputCreated` - New input/source created
- `InputRemoved` - Input/source removed
- `InputMuteStateChanged` - Audio mute toggled
- `InputVolumeChanged` - Audio volume changed

### Output Events
- `StreamStateChanged` - Streaming start/stop
- `RecordStateChanged` - Recording start/stop

### General Events
- `ExitStarted` - OBS shutting down
- `StudioModeStateChanged` - Studio mode toggled

## 🛠️ Usage Examples

### Basic Usage

```python
import asyncio
from obs_agent import create_obs_agent, CurrentProgramSceneChanged

async def main():
    async with create_obs_agent() as agent:
        
        @agent.on(CurrentProgramSceneChanged)
        async def on_scene_changed(event):
            print(f"📺 Scene: {event.scene_name}")
        
        # Your OBS operations here
        await agent.set_scene("Gaming")
        await asyncio.sleep(1)

asyncio.run(main())
```

### Advanced Usage with Middleware and Filtering

```python
import asyncio
from obs_agent import (
    create_obs_agent,
    StreamStateChanged,
    InputMuteStateChanged,
    logging_middleware,
    performance_middleware
)

async def main():
    async with create_obs_agent() as agent:
        
        # Add middleware
        agent.events.use(logging_middleware)
        agent.events.use(performance_middleware)
        
        # Stream monitoring
        @agent.on(StreamStateChanged)
        async def on_stream_state(event: StreamStateChanged):
            if event.output_active:
                print("🔴 LIVE!")
            else:
                print("⏹️ Stream ended")
        
        # Filtered audio monitoring
        @agent.on(
            InputMuteStateChanged,
            lambda e: "Mic" in e.input_name or "Microphone" in e.input_name
        )
        async def on_mic_mute(event: InputMuteStateChanged):
            status = "🔇 MUTED" if event.input_muted else "🎤 LIVE"
            print(f"Microphone: {status}")
        
        # Your streaming workflow here
        await agent.start_streaming()
        await asyncio.sleep(5)
        await agent.stop_streaming()

asyncio.run(main())
```

## 🧪 Testing

The event system includes comprehensive tests that work without requiring OBS:

```bash
# Test the event system
python3 test_events_system.py

# Test the overall improvements
python3 test_improvements.py
```

## 🔧 Technical Details

### Architecture

- **EventHandler**: Core event processing engine with async queue
- **BaseEvent**: Abstract base class for all event types
- **EventSubscription**: Pub/sub pattern implementation
- **Middleware Pipeline**: Ordered execution of cross-cutting concerns

### Performance

- Async event processing with priority queuing
- Non-blocking event emission
- Efficient middleware pipeline
- Configurable event recording buffer

### Type Safety

- Full type hints throughout
- MyPy compatible
- IDE autocomplete support
- Runtime type validation

## 🔄 Backward Compatibility

The enhanced event system is fully backward compatible with existing code. The old event handler methods still work:

```python
# Old way (still works)
agent.register_event_handler("CurrentProgramSceneChanged", my_handler)

# New way (recommended)
@agent.on(CurrentProgramSceneChanged)
async def my_handler(event): ...
```

## 🚀 Benefits

1. **Developer Experience**: Clean, intuitive API with excellent IDE support
2. **Type Safety**: Catch errors at development time, not runtime
3. **Debugging**: Event recording and replay for complex scenarios
4. **Performance**: Efficient async processing with middleware pipeline
5. **Flexibility**: Filtering, middleware, and subscription patterns
6. **Maintainability**: Well-structured, testable event handling code

## 📚 Examples

Complete examples are available in the `examples/` directory:

- `simple_websocket_events.py` - Basic usage patterns
- `websocket_events_demo.py` - Comprehensive feature demonstration

## ✅ Status

All major event system features have been implemented and tested:

- ✅ Typed event classes for all OBS events
- ✅ Decorator-based event handler system  
- ✅ Event filtering and middleware support
- ✅ Event replay/recording mechanism
- ✅ Event priority and queuing system
- ✅ Event subscription patterns
- ✅ Comprehensive examples and tests

The WebSocket event system is production-ready and provides a solid foundation for building sophisticated OBS automation workflows.