# Migration Guide: OBS Agent v1 to v2

This guide helps you migrate from OBS Agent v1 to the improved v2 architecture.

## Overview of Changes

### Major Improvements
1. **Centralized Configuration Management** - Environment variables and config files
2. **Proper Exception Handling** - Custom exception hierarchy with better error messages
3. **Connection Singleton** - Efficient connection reuse and automatic reconnection
4. **Input Validation** - All inputs are validated and sanitized
5. **Structured Logging** - Replace print statements with proper logging
6. **Type Safety** - Full type hints and mypy support
7. **Comprehensive Testing** - Unit tests with high coverage
8. **Async/Await Patterns** - Proper async implementation throughout

## Quick Start

### Old Way (v1)
```python
from obs_agent import OBSAgent

agent = OBSAgent(password="your_password")
await agent.connect()
scenes = await agent.get_scenes()
await agent.set_scene("My Scene")
agent.disconnect()
```

### New Way (v2)
```python
from obs_agent import create_obs_agent

async with create_obs_agent() as agent:
    scenes = await agent.get_scenes()
    await agent.set_scene("My Scene")
# Connection automatically closed
```

## Detailed Migration Steps

### 1. Update Imports

**Before:**
```python
from obs_agent import OBSAgent, OBSController
```

**After:**
```python
# Use v2 with better features
from obs_agent import OBSAgentV2, create_obs_agent

# Or keep using v1 for compatibility
from obs_agent import OBSAgent  # Still works!
```

### 2. Configuration Management

**Before:**
```python
# Hardcoded values
agent = OBSAgent(host="localhost", port=4455, password="secret")
```

**After:**
```python
# Option 1: Use environment variables
# Set: OBS_WEBSOCKET_HOST, OBS_WEBSOCKET_PORT, OBS_WEBSOCKET_PASSWORD
from obs_agent import create_obs_agent
async with create_obs_agent() as agent:
    # Automatically uses env vars

# Option 2: Use configuration object
from obs_agent import Config, OBSConfig, OBSAgentV2

config = Config(
    obs=OBSConfig(
        host="localhost",
        port=4455,
        password="secret",
        timeout=30.0,
        max_reconnect_attempts=3
    )
)
agent = OBSAgentV2(config)

# Option 3: Load from file
config = Config.load(Path.home() / ".obs_agent" / "config.json")
agent = OBSAgentV2(config)
```

### 3. Error Handling

**Before:**
```python
try:
    await agent.set_scene("My Scene")
except Exception as e:
    print(f"Error: {e}")
```

**After:**
```python
from obs_agent import SceneNotFoundError, ValidationError

try:
    await agent.set_scene("My Scene")
except SceneNotFoundError as e:
    logger.error(f"Scene '{e.scene_name}' not found")
except ValidationError as e:
    logger.error(f"Invalid scene name: {e}")
```

### 4. Connection Management

**Before:**
```python
agent = OBSAgent()
await agent.connect()
# ... do work ...
agent.disconnect()  # Easy to forget!
```

**After:**
```python
# Option 1: Context manager (recommended)
async with create_obs_agent() as agent:
    # ... do work ...
# Automatically disconnected

# Option 2: Manual with singleton
from obs_agent import get_connection_manager

manager = get_connection_manager()
await manager.connect()
# Connection reused across your app
```

### 5. Logging

**Before:**
```python
print(f"Switching to scene: {scene_name}")
await agent.set_scene(scene_name)
print("✅ Scene switched!")
```

**After:**
```python
from obs_agent import setup_logging, get_logger

setup_logging()  # Once at startup
logger = get_logger(__name__)

logger.info(f"Switching to scene: {scene_name}")
await agent.set_scene(scene_name)
# Automatic success logging with performance metrics
```

### 6. Input Validation

**Before:**
```python
# No validation - could cause issues
scene_name = user_input
await agent.set_scene(scene_name)  # What if scene_name has invalid chars?
```

**After:**
```python
# Automatic validation
await agent.set_scene(scene_name)  # Validates automatically

# Or manual validation
from obs_agent import validate_scene_name

try:
    valid_name = validate_scene_name(user_input)
    await agent.set_scene(valid_name)
except ValidationError as e:
    logger.error(f"Invalid input: {e}")
```

### 7. Async/Await Patterns

**Before:**
```python
# Missing await - silent failure!
agent.start_recording()  # Oops, no await!
```

**After:**
```python
# Proper async/await enforced
await agent.start_recording()  # Type checker catches missing await
```

## Feature Comparison

| Feature | v1 | v2 |
|---------|----|----|
| Connection Management | Manual | Automatic with singleton |
| Error Handling | Generic exceptions | Specific exception types |
| Configuration | Hardcoded | Environment vars, files, objects |
| Logging | Print statements | Structured logging with levels |
| Input Validation | None | Automatic sanitization |
| Type Safety | Partial | Full type hints |
| Testing | Basic | Comprehensive test suite |
| Performance | Good | Better with caching and connection reuse |

## Common Patterns

### Recording with Error Recovery
```python
from obs_agent import create_obs_agent, RecordingAlreadyActiveError

async with create_obs_agent() as agent:
    try:
        await agent.start_recording()
    except RecordingAlreadyActiveError:
        logger.warning("Already recording, stopping first")
        await agent.stop_recording()
        await agent.start_recording()
```

### Streaming with Health Monitoring
```python
async with create_obs_agent() as agent:
    await agent.start_streaming()
    
    # Monitor stream health
    while True:
        status = await agent.get_streaming_status()
        if status['total_frames'] > 0:
            drop_rate = status['skipped_frames'] / status['total_frames'] * 100
            if drop_rate > 5:
                logger.warning(f"High frame drop rate: {drop_rate:.1f}%")
        
        await asyncio.sleep(5)
```

### Batch Operations with Validation
```python
from obs_agent import create_obs_agent, ValidationError

async with create_obs_agent() as agent:
    scenes_to_create = ["Scene 1", "Scene 2", "Invalid@Scene"]
    
    for scene_name in scenes_to_create:
        try:
            await agent.create_scene(scene_name)
            logger.info(f"Created scene: {scene_name}")
        except ValidationError as e:
            logger.error(f"Skipping invalid scene name: {e}")
```

## Environment Variables

Set these environment variables for v2:

```bash
# OBS Connection
export OBS_WEBSOCKET_HOST=localhost
export OBS_WEBSOCKET_PORT=4455
export OBS_WEBSOCKET_PASSWORD=your_password

# Behavior
export OBS_WEBSOCKET_TIMEOUT=30.0
export OBS_RECONNECT_INTERVAL=5.0
export OBS_MAX_RECONNECT_ATTEMPTS=3

# Features
export OBS_ENABLE_AUTO_RECONNECT=true
export OBS_ENABLE_EVENT_LOGGING=true
export OBS_ENABLE_PERFORMANCE_MONITORING=false

# Logging
export OBS_LOG_LEVEL=INFO
export OBS_LOG_FILE=/var/log/obs_agent.log
```

## Backward Compatibility

The v1 API is still available for backward compatibility:

```python
# This still works!
from obs_agent import OBSAgent

agent = OBSAgent()
await agent.connect()
# ... use as before ...
```

However, we recommend migrating to v2 for better features and maintainability.

## Need Help?

- Check the [examples/improved_example.py](examples/improved_example.py) for v2 usage patterns
- Run tests to verify your migration: `pytest tests/`
- Enable debug logging: `export OBS_LOG_LEVEL=DEBUG`