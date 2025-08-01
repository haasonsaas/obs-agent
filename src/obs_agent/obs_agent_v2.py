"""
Improved OBS Agent with better architecture, error handling, and type safety.

This is the main OBS Agent class that provides a high-level interface
for controlling OBS Studio via WebSocket.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, TypedDict, Union

from obswebsocket import requests

from .actions import ActionBuilder, SmartActions
from .automation import AutomationDecorator, AutomationEngine
from .config import Config, get_config
from .connection import ConnectionManager, get_connection_manager
from .events import EventHandler
from .exceptions import (
    RecordingAlreadyActiveError,
    RecordingNotActiveError,
    SceneNotFoundError,
    StreamAlreadyActiveError,
    StreamNotActiveError,
    ValidationError,
)
from .logging import (
    get_logger,
    log_performance,
    log_recording_status,
    log_scene_change,
    log_stream_status,
    setup_logging,
)
from .validation import (
    validate_file_path,
    validate_scene_name,
    validate_settings,
    validate_source_name,
    validate_transition_duration,
    validate_volume,
)


# Type definitions
class SceneInfo(TypedDict):
    sceneName: str
    sceneIndex: int


class SourceInfo(TypedDict):
    inputName: str
    inputKind: str
    inputSettings: Dict[str, Any]


class StreamStatus(TypedDict):
    is_streaming: bool
    duration: float
    bytes: int
    skipped_frames: int
    total_frames: int


class RecordingStatus(TypedDict):
    is_recording: bool
    is_paused: bool
    duration: float
    bytes: int


class VolumeInfo(TypedDict):
    volume_mul: float
    volume_db: float


class OBSAgent:
    """
    Improved OBS Agent with better architecture and error handling.

    This class provides a high-level interface for controlling OBS Studio
    via WebSocket with proper connection management, validation, and logging.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize OBS Agent.

        Args:
            config: Optional configuration. If not provided, uses global config.
        """
        self.config = config or get_config()
        self.connection: ConnectionManager = get_connection_manager()
        self.logger = get_logger(__name__)

        # Set up logging
        setup_logging(self.config.logging)

        # Cache for frequently accessed data
        self._scene_cache: Optional[List[str]] = None
        self._source_cache: Optional[List[SourceInfo]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = 60.0  # Cache TTL in seconds

        # Automation system
        self._automation_engine: Optional[AutomationEngine] = None
        self._automation_decorator: Optional[AutomationDecorator] = None
        self._action_builder: Optional[ActionBuilder] = None
        self._smart_actions: Optional[SmartActions] = None

    async def __aenter__(self) -> "OBSAgent":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()

    @log_performance
    async def connect(self) -> bool:
        """
        Connect to OBS WebSocket server.

        Returns:
            True if connection successful

        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
        """
        self.logger.info("Connecting to OBS...")
        await self.connection.connect(self.config.obs)

        # Clear cache on new connection
        self._clear_cache()

        # Log version info
        version_info = await self.get_version()
        self.logger.info(
            f"Connected to OBS {version_info['obs_version']} " f"(WebSocket {version_info['websocket_version']})"
        )

        return True

    async def disconnect(self) -> None:
        """Disconnect from OBS WebSocket server."""
        self.logger.info("Disconnecting from OBS...")
        await self.connection.disconnect()
        self._clear_cache()

    @property
    def is_connected(self) -> bool:
        """Check if connected to OBS."""
        return self.connection.is_connected

    def _clear_cache(self) -> None:
        """Clear internal cache."""
        self._scene_cache = None
        self._source_cache = None
        self._cache_timestamp = None

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._cache_timestamp is None:
            return False

        elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
        return elapsed < self._cache_ttl

    # Version and Stats Methods

    @log_performance
    async def get_version(self) -> Dict[str, Any]:
        """
        Get OBS version information.

        Returns:
            Dictionary with version information
        """
        response = await self.connection.execute(requests.GetVersion())
        return {
            "obs_version": response.datain.get("obsVersion"),
            "websocket_version": response.datain.get("obsWebSocketVersion"),
            "platform": response.datain.get("platform"),
            "platform_description": response.datain.get("platformDescription"),
        }

    @log_performance
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get OBS performance statistics.

        Returns:
            Dictionary with performance stats
        """
        response = await self.connection.execute(requests.GetStats())
        return response.datain

    # Scene Methods

    @log_performance
    async def get_scenes(self, use_cache: bool = True) -> List[str]:
        """
        Get list of available scenes.

        Args:
            use_cache: Whether to use cached data if available

        Returns:
            List of scene names
        """
        if use_cache and self._is_cache_valid() and self._scene_cache is not None:
            return self._scene_cache

        response = await self.connection.execute(requests.GetSceneList())
        scenes = response.datain.get("scenes", [])
        scene_names = [scene["sceneName"] for scene in scenes]

        # Update cache
        self._scene_cache = scene_names
        self._cache_timestamp = datetime.now()

        return scene_names

    @log_performance
    async def get_current_scene(self) -> str:
        """
        Get the current active scene.

        Returns:
            Current scene name
        """
        response = await self.connection.execute(requests.GetCurrentProgramScene())
        return response.datain.get("currentProgramSceneName", "")

    @log_performance
    async def set_scene(self, scene_name: str) -> bool:
        """
        Switch to a different scene.

        Args:
            scene_name: Name of the scene to switch to

        Returns:
            True if successful

        Raises:
            SceneNotFoundError: If scene doesn't exist
            ValidationError: If scene name is invalid
        """
        # Validate input
        scene_name = validate_scene_name(scene_name)

        # Check if scene exists
        scenes = await self.get_scenes()
        if scene_name not in scenes:
            raise SceneNotFoundError(scene_name)

        # Get current scene for logging
        current_scene = await self.get_current_scene()

        # Switch scene
        await self.connection.execute(requests.SetCurrentProgramScene(sceneName=scene_name))

        log_scene_change(current_scene, scene_name)
        return True

    @log_performance
    async def create_scene(self, scene_name: str) -> bool:
        """
        Create a new scene.

        Args:
            scene_name: Name of the scene to create

        Returns:
            True if successful

        Raises:
            SceneAlreadyExistsError: If scene already exists
            ValidationError: If scene name is invalid
        """
        # Validate input
        scene_name = validate_scene_name(scene_name)

        # Create scene
        await self.connection.execute(requests.CreateScene(sceneName=scene_name))

        # Clear cache
        self._scene_cache = None

        self.logger.info(f"Created scene: {scene_name}")
        return True

    @log_performance
    async def remove_scene(self, scene_name: str) -> bool:
        """
        Remove a scene.

        Args:
            scene_name: Name of the scene to remove

        Returns:
            True if successful

        Raises:
            SceneNotFoundError: If scene doesn't exist
            ValidationError: If scene name is invalid
        """
        # Validate input
        scene_name = validate_scene_name(scene_name)

        # Remove scene
        await self.connection.execute(requests.RemoveScene(sceneName=scene_name))

        # Clear cache
        self._scene_cache = None

        self.logger.info(f"Removed scene: {scene_name}")
        return True

    # Source Methods

    @log_performance
    async def get_sources(self, use_cache: bool = True) -> List[SourceInfo]:
        """
        Get list of all sources/inputs.

        Args:
            use_cache: Whether to use cached data if available

        Returns:
            List of source information
        """
        if use_cache and self._is_cache_valid() and self._source_cache is not None:
            return self._source_cache

        response = await self.connection.execute(requests.GetInputList())
        sources = response.datain.get("inputs", [])

        # Update cache
        self._source_cache = sources
        self._cache_timestamp = datetime.now()

        return sources

    @log_performance
    async def get_source_settings(self, source_name: str) -> Dict[str, Any]:
        """
        Get settings for a specific source.

        Args:
            source_name: Name of the source

        Returns:
            Dictionary with source settings

        Raises:
            SourceNotFoundError: If source doesn't exist
            ValidationError: If source name is invalid
        """
        # Validate input
        source_name = validate_source_name(source_name)

        response = await self.connection.execute(requests.GetInputSettings(inputName=source_name))

        return {"kind": response.datain.get("inputKind", ""), "settings": response.datain.get("inputSettings", {})}

    @log_performance
    async def set_source_settings(self, source_name: str, settings: Dict[str, Any], overlay: bool = True) -> bool:
        """
        Update settings for a source.

        Args:
            source_name: Name of the source
            settings: New settings to apply
            overlay: Whether to overlay settings (True) or replace them (False)

        Returns:
            True if successful

        Raises:
            SourceNotFoundError: If source doesn't exist
            ValidationError: If inputs are invalid
        """
        # Validate inputs
        source_name = validate_source_name(source_name)
        settings = validate_settings(settings)

        await self.connection.execute(
            requests.SetInputSettings(inputName=source_name, inputSettings=settings, overlay=overlay)
        )

        self.logger.info(f"Updated settings for source: {source_name}")
        return True

    # Audio Methods

    @log_performance
    async def get_source_mute(self, source_name: str) -> bool:
        """
        Get mute status of an audio source.

        Args:
            source_name: Name of the source

        Returns:
            True if muted, False otherwise

        Raises:
            SourceNotFoundError: If source doesn't exist
            ValidationError: If source name is invalid
        """
        # Validate input
        source_name = validate_source_name(source_name)

        response = await self.connection.execute(requests.GetInputMute(inputName=source_name))

        return response.datain.get("inputMuted", False)

    @log_performance
    async def set_source_mute(self, source_name: str, muted: bool) -> bool:
        """
        Set mute status of an audio source.

        Args:
            source_name: Name of the source
            muted: Whether to mute (True) or unmute (False)

        Returns:
            True if successful

        Raises:
            SourceNotFoundError: If source doesn't exist
            ValidationError: If source name is invalid
        """
        # Validate input
        source_name = validate_source_name(source_name)

        await self.connection.execute(requests.SetInputMute(inputName=source_name, inputMuted=muted))

        self.logger.info(f"Set mute for {source_name} to {muted}")
        return True

    @log_performance
    async def toggle_source_mute(self, source_name: str) -> bool:
        """
        Toggle mute status of an audio source.

        Args:
            source_name: Name of the source

        Returns:
            New mute status

        Raises:
            SourceNotFoundError: If source doesn't exist
            ValidationError: If source name is invalid
        """
        # Validate input
        source_name = validate_source_name(source_name)

        response = await self.connection.execute(requests.ToggleInputMute(inputName=source_name))

        new_status = response.datain.get("inputMuted", False)
        self.logger.info(f"Toggled mute for {source_name}, now: {new_status}")

        return new_status

    @log_performance
    async def get_source_volume(self, source_name: str) -> VolumeInfo:
        """
        Get volume of an audio source.

        Args:
            source_name: Name of the source

        Returns:
            Volume information

        Raises:
            SourceNotFoundError: If source doesn't exist
            ValidationError: If source name is invalid
        """
        # Validate input
        source_name = validate_source_name(source_name)

        response = await self.connection.execute(requests.GetInputVolume(inputName=source_name))

        return {
            "volume_mul": response.datain.get("inputVolumeMul", 0.0),
            "volume_db": response.datain.get("inputVolumeDb", 0.0),
        }

    @log_performance
    async def set_source_volume(
        self, source_name: str, volume_db: Optional[float] = None, volume_mul: Optional[float] = None
    ) -> bool:
        """
        Set volume of an audio source.

        Args:
            source_name: Name of the source
            volume_db: Volume in decibels (optional)
            volume_mul: Volume multiplier 0.0-20.0 (optional)

        Returns:
            True if successful

        Raises:
            SourceNotFoundError: If source doesn't exist
            ValidationError: If inputs are invalid
        """
        # Validate inputs
        source_name = validate_source_name(source_name)

        if volume_db is None and volume_mul is None:
            raise ValidationError("Must specify either volume_db or volume_mul")

        params: Dict[str, Any] = {"inputName": source_name}

        if volume_db is not None:
            params["inputVolumeDb"] = validate_volume(volume_db, as_db=True)

        if volume_mul is not None:
            params["inputVolumeMul"] = validate_volume(volume_mul, as_db=False)

        await self.connection.execute(requests.SetInputVolume(**params))

        self.logger.info(f"Set volume for {source_name}")
        return True

    # Streaming Methods

    @log_performance
    async def start_streaming(self) -> bool:
        """
        Start streaming.

        Returns:
            True if successful

        Raises:
            StreamAlreadyActiveError: If already streaming
        """
        # Check current status
        status = await self.get_streaming_status()
        if status["is_streaming"]:
            raise StreamAlreadyActiveError("Stream is already active")

        await self.connection.execute(requests.StartStream())

        log_stream_status(True)
        return True

    @log_performance
    async def stop_streaming(self) -> bool:
        """
        Stop streaming.

        Returns:
            True if successful

        Raises:
            StreamNotActiveError: If not streaming
        """
        # Check current status
        status = await self.get_streaming_status()
        if not status["is_streaming"]:
            raise StreamNotActiveError("Stream is not active")

        await self.connection.execute(requests.StopStream())

        log_stream_status(False, status.get("duration"))
        return True

    @log_performance
    async def toggle_streaming(self) -> bool:
        """
        Toggle streaming on/off.

        Returns:
            New streaming status
        """
        response = await self.connection.execute(requests.ToggleStream())
        is_active = response.datain.get("outputActive", False)

        log_stream_status(is_active)
        return is_active

    @log_performance
    async def get_streaming_status(self) -> StreamStatus:
        """
        Get current streaming status.

        Returns:
            Streaming status information
        """
        response = await self.connection.execute(requests.GetStreamStatus())

        return {
            "is_streaming": response.datain.get("outputActive", False),
            "duration": response.datain.get("outputDuration", 0),
            "bytes": response.datain.get("outputBytes", 0),
            "skipped_frames": response.datain.get("outputSkippedFrames", 0),
            "total_frames": response.datain.get("outputTotalFrames", 0),
        }

    # Recording Methods

    @log_performance
    async def start_recording(self) -> bool:
        """
        Start recording.

        Returns:
            True if successful

        Raises:
            RecordingAlreadyActiveError: If already recording
        """
        # Check current status
        status = await self.get_recording_status()
        if status["is_recording"]:
            raise RecordingAlreadyActiveError("Recording is already active")

        await self.connection.execute(requests.StartRecord())

        log_recording_status(True)
        return True

    @log_performance
    async def stop_recording(self) -> str:
        """
        Stop recording.

        Returns:
            Path to the recorded file

        Raises:
            RecordingNotActiveError: If not recording
        """
        # Check current status
        status = await self.get_recording_status()
        if not status["is_recording"]:
            raise RecordingNotActiveError("Recording is not active")

        response = await self.connection.execute(requests.StopRecord())
        output_path = response.datain.get("outputPath", "")

        log_recording_status(False, output_path)
        return output_path

    @log_performance
    async def toggle_recording(self) -> Dict[str, Any]:
        """
        Toggle recording on/off.

        Returns:
            Recording status and file path
        """
        response = await self.connection.execute(requests.ToggleRecord())

        result = {
            "output_active": response.datain.get("outputActive", False),
            "output_path": response.datain.get("outputPath", ""),
        }

        log_recording_status(result["output_active"], result.get("output_path"))
        return result

    @log_performance
    async def get_recording_status(self) -> RecordingStatus:
        """
        Get current recording status.

        Returns:
            Recording status information
        """
        response = await self.connection.execute(requests.GetRecordStatus())

        return {
            "is_recording": response.datain.get("outputActive", False),
            "is_paused": response.datain.get("outputPaused", False),
            "duration": response.datain.get("outputDuration", 0),
            "bytes": response.datain.get("outputBytes", 0),
        }

    @log_performance
    async def pause_recording(self) -> bool:
        """
        Pause current recording.

        Returns:
            True if successful

        Raises:
            RecordingNotActiveError: If not recording
        """
        status = await self.get_recording_status()
        if not status["is_recording"]:
            raise RecordingNotActiveError("Recording is not active")

        await self.connection.execute(requests.PauseRecord())

        self.logger.info("Recording paused")
        return True

    @log_performance
    async def resume_recording(self) -> bool:
        """
        Resume paused recording.

        Returns:
            True if successful

        Raises:
            RecordingNotActiveError: If not recording
        """
        status = await self.get_recording_status()
        if not status["is_recording"]:
            raise RecordingNotActiveError("Recording is not active")

        await self.connection.execute(requests.ResumeRecord())

        self.logger.info("Recording resumed")
        return True

    # Transition Methods

    @log_performance
    async def get_transitions(self) -> List[str]:
        """
        Get list of available transitions.

        Returns:
            List of transition names
        """
        response = await self.connection.execute(requests.GetSceneTransitionList())
        transitions = response.datain.get("transitions", [])
        return [t["transitionName"] for t in transitions]

    @log_performance
    async def set_transition(self, transition_name: str) -> bool:
        """
        Set the current scene transition.

        Args:
            transition_name: Name of the transition

        Returns:
            True if successful

        Raises:
            ValidationError: If transition name is invalid
        """
        await self.connection.execute(requests.SetCurrentSceneTransition(transitionName=transition_name))

        self.logger.info(f"Set transition to: {transition_name}")
        return True

    @log_performance
    async def set_transition_duration(self, duration_ms: int) -> bool:
        """
        Set transition duration.

        Args:
            duration_ms: Duration in milliseconds

        Returns:
            True if successful

        Raises:
            ValidationError: If duration is invalid
        """
        duration_ms = validate_transition_duration(duration_ms)

        await self.connection.execute(requests.SetCurrentSceneTransitionDuration(transitionDuration=duration_ms))

        self.logger.info(f"Set transition duration to: {duration_ms}ms")
        return True

    # Screenshot Methods

    @log_performance
    async def take_screenshot(
        self,
        source_name: str,
        file_path: Union[str, Path],
        width: Optional[int] = None,
        height: Optional[int] = None,
        format: str = "png",
    ) -> bool:
        """
        Take a screenshot of a source.

        Args:
            source_name: Name of the source
            file_path: Path to save the screenshot
            width: Optional width (maintains aspect ratio if height not specified)
            height: Optional height (maintains aspect ratio if width not specified)
            format: Image format (png, jpg, bmp)

        Returns:
            True if successful

        Raises:
            SourceNotFoundError: If source doesn't exist
            ValidationError: If inputs are invalid
        """
        # Validate inputs
        source_name = validate_source_name(source_name)
        file_path = validate_file_path(file_path, must_exist=False, allow_relative=True)

        if format not in ["png", "jpg", "jpeg", "bmp"]:
            raise ValidationError(f"Invalid image format: {format}")

        params: Dict[str, Any] = {"sourceName": source_name, "imageFilePath": str(file_path), "imageFormat": format}

        if width:
            params["imageWidth"] = width
        if height:
            params["imageHeight"] = height

        await self.connection.execute(requests.SaveSourceScreenshot(**params))

        self.logger.info(f"Screenshot saved to: {file_path}")
        return True

    # Event Handling

    @property
    def events(self) -> EventHandler:
        """
        Get the event handler for registering event callbacks.

        Usage:
            @agent.events.on(SceneCreated)
            async def on_scene_created(event: SceneCreated):
                print(f"Scene created: {event.scene_name}")

            @agent.events.on("InputMuteStateChanged", lambda e: e.input_name == "Mic")
            async def on_mic_mute(event: InputMuteStateChanged):
                print(f"Mic muted: {event.input_muted}")
        """
        return self.connection.event_handler

    def on(self, event_type: Union[str, type], *filters) -> Callable:
        """
        Decorator for registering event handlers.

        Args:
            event_type: Event type or class to handle
            *filters: Optional filter functions

        Usage:
            @agent.on(CurrentProgramSceneChanged)
            async def scene_changed(event: CurrentProgramSceneChanged):
                print(f"Scene changed to: {event.scene_name}")
        """
        return self.events.on(event_type, *filters)

    async def wait_for_event(self, event_type: Union[str, type], timeout: float = 30.0) -> Optional[Any]:
        """
        Wait for a specific event.

        Args:
            event_type: The event type to wait for
            timeout: Maximum time to wait

        Returns:
            The event data if received, None if timeout
        """
        event_name = event_type if isinstance(event_type, str) else event_type.__name__
        return await self.connection.event_handler.wait_for_event(event_name, timeout)

    # Automation System Properties

    @property
    def automation(self) -> AutomationDecorator:
        """
        Get the automation decorator for creating automation rules.

        Usage:
            @agent.automation.when(InputMuteStateChanged, lambda e: e.input_name == "Microphone")
            @agent.automation.after_delay(5.0)
            async def switch_to_brb(context):
                await agent.set_scene("BRB Screen")
        """
        if self._automation_decorator is None:
            self._init_automation()
        return self._automation_decorator

    @property
    def actions(self) -> ActionBuilder:
        """
        Get the action builder for creating complex automation actions.

        Usage:
            action = await agent.actions.scene("Main").mute("Microphone", True).wait(2.0).build()
        """
        if self._action_builder is None:
            self._init_automation()
        return ActionBuilder(self)  # Always return a fresh builder

    @property
    def smart_actions(self) -> SmartActions:
        """
        Get the smart actions collection for pre-built automation patterns.

        Usage:
            brb_action = agent.smart_actions.create_brb_automation()
        """
        if self._smart_actions is None:
            self._init_automation()
        return self._smart_actions

    def _init_automation(self) -> None:
        """Initialize the automation system."""
        if self._automation_engine is None:
            self._automation_engine = AutomationEngine(self)
            self._automation_decorator = AutomationDecorator(self._automation_engine)
            self._action_builder = ActionBuilder(self)
            self._smart_actions = SmartActions(self)

    def start_automation(self) -> None:
        """Start the automation engine."""
        if self._automation_engine is None:
            self._init_automation()
        self._automation_engine.start()
        self.logger.info("Automation engine started")

    def stop_automation(self) -> None:
        """Stop the automation engine."""
        if self._automation_engine:
            self._automation_engine.stop()
            self.logger.info("Automation engine stopped")

    def get_automation_stats(self) -> Dict[str, Any]:
        """Get automation engine statistics."""
        if self._automation_engine:
            return self._automation_engine.get_stats()
        return {}

    def get_automation_rule_status(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific automation rule."""
        if self._automation_engine:
            return self._automation_engine.get_rule_status(rule_name)
        return None

    def enable_automation_rule(self, rule_name: str) -> bool:
        """Enable an automation rule."""
        if self._automation_engine:
            return self._automation_engine.enable_rule(rule_name)
        return False

    def disable_automation_rule(self, rule_name: str) -> bool:
        """Disable an automation rule."""
        if self._automation_engine:
            return self._automation_engine.disable_rule(rule_name)
        return False


# Convenience function for creating OBS Agent with context manager
@asynccontextmanager
async def create_obs_agent(config: Optional[Config] = None) -> AsyncGenerator["OBSAgent", None]:
    """
    Create an OBS Agent with automatic connection management.

    Usage:
        async with create_obs_agent() as agent:
            scenes = await agent.get_scenes()
    """
    agent = OBSAgent(config)
    try:
        await agent.connect()
        yield agent
    finally:
        await agent.disconnect()
