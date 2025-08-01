"""
Example usage of the improved OBS Agent v2.

This example demonstrates the new features including:
- Centralized configuration
- Better error handling
- Connection management
- Input validation
- Structured logging
"""

import asyncio
from pathlib import Path

# Import the new improved modules
from obs_agent import (
    OBSAgentV2, create_obs_agent, Config, OBSConfig,
    setup_logging, get_logger, log_context,
    OBSAgentError, SceneNotFoundError, ValidationError
)


# Set up logging
setup_logging()
logger = get_logger(__name__)


async def basic_example():
    """Basic usage example with context manager."""
    logger.info("Starting basic example")
    
    try:
        # Create OBS agent with context manager for automatic connection handling
        async with create_obs_agent() as agent:
            # Get version info
            version = await agent.get_version()
            logger.info(f"Connected to OBS {version['obs_version']}")
            
            # Get and log available scenes
            scenes = await agent.get_scenes()
            logger.info(f"Available scenes: {', '.join(scenes)}")
            
            # Get current scene
            current_scene = await agent.get_current_scene()
            logger.info(f"Current scene: {current_scene}")
            
            # Switch to a different scene with validation
            if len(scenes) > 1:
                target_scene = scenes[1] if scenes[0] == current_scene else scenes[0]
                await agent.set_scene(target_scene)
                logger.info(f"Switched to scene: {target_scene}")
            
            # Get sources with caching
            sources = await agent.get_sources()
            logger.info(f"Found {len(sources)} sources")
            
            # Audio control with validation
            for source in sources:
                if source['inputKind'] in ['wasapi_input_capture', 'wasapi_output_capture']:
                    volume = await agent.get_source_volume(source['inputName'])
                    logger.info(
                        f"Audio source '{source['inputName']}': "
                        f"{volume['volume_db']:.1f} dB"
                    )
    
    except SceneNotFoundError as e:
        logger.error(f"Scene not found: {e.scene_name}")
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
    except OBSAgentError as e:
        logger.error(f"OBS error: {e}")
    except Exception as e:
        logger.exception("Unexpected error occurred")


async def configuration_example():
    """Example with custom configuration."""
    logger.info("Starting configuration example")
    
    # Create custom configuration
    config = Config(
        obs=OBSConfig(
            host="localhost",
            port=4455,
            password="",  # Set your password here
            timeout=10.0,
            reconnect_interval=3.0,
            max_reconnect_attempts=5
        )
    )
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Invalid configuration: {e}")
        return
    
    # Save configuration
    config_file = Path.home() / ".obs_agent" / "my_config.json"
    config.save(config_file)
    logger.info(f"Saved configuration to {config_file}")
    
    # Use configuration
    agent = OBSAgentV2(config)
    await agent.connect()
    
    try:
        # Use the agent...
        stats = await agent.get_stats()
        logger.info(f"CPU usage: {stats.get('cpuUsage', 0):.1f}%")
        logger.info(f"Memory usage: {stats.get('memoryUsage', 0):.1f} MB")
    finally:
        await agent.disconnect()


async def streaming_example():
    """Example of streaming control with proper error handling."""
    logger.info("Starting streaming example")
    
    async with create_obs_agent() as agent:
        # Check streaming status
        status = await agent.get_streaming_status()
        
        if status['is_streaming']:
            logger.info(
                f"Already streaming for {status['duration'] / 1000:.1f} seconds, "
                f"skipped frames: {status['skipped_frames']}"
            )
            
            # Stop streaming
            await agent.stop_streaming()
            logger.info("Stopped streaming")
        else:
            logger.info("Starting stream...")
            
            # Start streaming
            await agent.start_streaming()
            
            # Monitor for 10 seconds
            for i in range(10):
                await asyncio.sleep(1)
                status = await agent.get_streaming_status()
                
                if status['total_frames'] > 0:
                    drop_rate = (
                        status['skipped_frames'] / status['total_frames'] * 100
                    )
                    logger.info(
                        f"Streaming [{i+1}/10s]: "
                        f"Dropped frames: {drop_rate:.1f}%"
                    )
            
            # Stop streaming
            await agent.stop_streaming()
            logger.info("Stopped streaming after demo")


async def recording_example():
    """Example of recording with contextual logging."""
    logger.info("Starting recording example")
    
    async with create_obs_agent() as agent:
        # Check if already recording
        rec_status = await agent.get_recording_status()
        
        if rec_status['is_recording']:
            logger.warning("Already recording, stopping first")
            await agent.stop_recording()
        
        # Start recording with context
        with log_context(action="recording", user="demo"):
            logger.info("Starting recording...")
            await agent.start_recording()
            
            # Record for 5 seconds
            for i in range(5):
                await asyncio.sleep(1)
                status = await agent.get_recording_status()
                logger.info(
                    f"Recording [{i+1}/5s]: "
                    f"{status['bytes'] / 1024 / 1024:.1f} MB"
                )
            
            # Stop and get file path
            output_path = await agent.stop_recording()
            logger.info(f"Recording saved to: {output_path}")


async def error_handling_example():
    """Example demonstrating error handling."""
    logger.info("Starting error handling example")
    
    async with create_obs_agent() as agent:
        # Try to switch to non-existent scene
        try:
            await agent.set_scene("This Scene Does Not Exist")
        except SceneNotFoundError as e:
            logger.warning(f"Expected error: {e}")
        
        # Try invalid scene name
        try:
            await agent.set_scene("Invalid@Scene#Name")
        except ValidationError as e:
            logger.warning(f"Validation prevented invalid input: {e}")
        
        # Try to stop streaming when not streaming
        try:
            status = await agent.get_streaming_status()
            if not status['is_streaming']:
                await agent.stop_streaming()
        except OBSAgentError as e:
            logger.warning(f"Expected error: {e}")
        
        logger.info("Error handling completed successfully")


async def screenshot_example():
    """Example of taking screenshots with validation."""
    logger.info("Starting screenshot example")
    
    async with create_obs_agent() as agent:
        # Get sources
        sources = await agent.get_sources()
        
        # Find a video source
        video_source = None
        for source in sources:
            if 'capture' in source['inputKind'].lower():
                video_source = source['inputName']
                break
        
        if video_source:
            # Take screenshot
            screenshot_path = Path.home() / "obs_screenshot.png"
            await agent.take_screenshot(
                video_source,
                screenshot_path,
                width=1280,  # Resize to 720p
                height=720
            )
            logger.info(f"Screenshot saved to: {screenshot_path}")
        else:
            logger.warning("No video source found for screenshot")


async def main():
    """Run all examples."""
    examples = [
        ("Basic Operations", basic_example),
        ("Configuration", configuration_example),
        ("Streaming Control", streaming_example),
        ("Recording", recording_example),
        ("Error Handling", error_handling_example),
        ("Screenshots", screenshot_example),
    ]
    
    for name, example_func in examples:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running example: {name}")
        logger.info(f"{'='*50}")
        
        try:
            await example_func()
        except Exception as e:
            logger.exception(f"Example '{name}' failed")
        
        # Small delay between examples
        await asyncio.sleep(2)
    
    logger.info("\nAll examples completed!")


if __name__ == "__main__":
    asyncio.run(main())