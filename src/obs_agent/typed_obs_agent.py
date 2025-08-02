"""
Type-safe OBS Agent wrapper with enhanced method signatures.

This module provides a wrapper around the existing OBS Agent with improved
type safety, validation, and better type inference for all operations.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import (
    Any, AsyncContextManager, Dict, List, Literal, Optional, Union, overload
)

from .config import Config
from .obs_agent_v2 import OBSAgent as BaseOBSAgent
from .types import (
    # API Response types
    OBSVersionInfo, OBSStats, SceneList, Scene, SceneItem, SourceInfo, 
    AudioInfo, VolumeInfo, FilterInfo, TransitionList, TransitionInfo,
    StreamStatus, RecordingStatus, OutputInfo,
    
    # Source types
    SourceKind, SourceSettings, CreateSourceParams, UpdateSourceParams,
    CreateFilterParams,
    
    # Base types
    UUID, Timestamp, Decibels, Milliseconds,
    
    # Generic types
    TypedResult, TypedCache, ValidationResult, OperationResult,
    
    # Event types
    EventData, CurrentProgramSceneChangedData, InputMuteStateChangedData,
    StreamStateChangedData, RecordStateChangedData,
)
from .types.generics import (
    TypedEventHandler, TypedValidator, EventHandlerProtocol,
    create_typed_handler, validate_and_cast, ensure_type, safe_cast
)


class TypedOBSAgent:
    """
    Type-safe wrapper for OBS Agent with enhanced method signatures.
    
    This class provides the same functionality as OBSAgent but with:
    - Strict type checking and validation
    - Better type inference for all operations
    - Runtime type validation where beneficial
    - Comprehensive error handling with typed results
    """
    
    def __init__(self, config: Optional[Config] = None) -> None:
        """Initialize typed OBS Agent."""
        self._agent = BaseOBSAgent(config)
        self._scene_cache: TypedCache[Scene] = TypedCache(dict)
        self._source_cache: TypedCache[SourceInfo] = TypedCache(dict)
        self._validators: Dict[str, TypedValidator[Any]] = {}
        self._setup_validators()
    
    def _setup_validators(self) -> None:
        """Set up type validators for common operations."""
        from .types.generics import create_validator
        
        self._validators['scene_name'] = create_validator(str)
        self._validators['source_name'] = create_validator(str)
        self._validators['volume_db'] = create_validator(float)
        self._validators['port'] = create_validator(int)
    
    # Context manager support
    async def __aenter__(self) -> "TypedOBSAgent":
        """Async context manager entry."""
        await self._agent.__aenter__()
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self._agent.__aexit__(exc_type, exc_val, exc_tb)
    
    # Connection methods with typed results
    async def connect(self) -> TypedResult[bool]:
        """Connect to OBS with typed result."""
        try:
            result = await self._agent.connect()
            return TypedResult(True, result)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    async def disconnect(self) -> None:
        """Disconnect from OBS."""
        await self._agent.disconnect()
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to OBS."""
        return self._agent.is_connected
    
    # Version and stats with precise types
    async def get_version(self) -> TypedResult[OBSVersionInfo]:
        """Get OBS version information with typed result."""
        try:
            data = await self._agent.get_version()
            version_info: OBSVersionInfo = {
                'obs_version': ensure_type(data.get('obs_version', ''), str),
                'obs_web_socket_version': ensure_type(data.get('websocket_version', ''), str),
                'rpc_version': ensure_type(data.get('rpc_version', 1), int),
                'available_requests': ensure_type(data.get('available_requests', []), list),
                'supported_image_formats': ensure_type(data.get('supported_image_formats', []), list),
                'platform': ensure_type(data.get('platform', ''), str),
                'platform_description': ensure_type(data.get('platform_description', ''), str),
            }
            return TypedResult(True, version_info)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    async def get_stats(self) -> TypedResult[OBSStats]:
        """Get OBS statistics with typed result."""
        try:
            data = await self._agent.get_stats()
            stats: OBSStats = {
                'cpu_usage': safe_cast(data.get('cpuUsage', 0), float) or 0.0,
                'memory_usage': safe_cast(data.get('memoryUsage', 0), int) or 0,
                'available_disk_space': safe_cast(data.get('availableDiskSpace', 0), int) or 0,
                'active_fps': safe_cast(data.get('activeFps', 0), float) or 0.0,
                'average_frame_time': safe_cast(data.get('averageFrameTime', 0), float) or 0.0,
                'render_total_frames': safe_cast(data.get('renderTotalFrames', 0), int) or 0,
                'render_missed_frames': safe_cast(data.get('renderMissedFrames', 0), int) or 0,
                'render_skipped_frames': safe_cast(data.get('renderSkippedFrames', 0), int) or 0,
                'output_total_frames': safe_cast(data.get('outputTotalFrames', 0), int) or 0,
                'output_skipped_frames': safe_cast(data.get('outputSkippedFrames', 0), int) or 0,
                'web_socket_session_incoming_messages': safe_cast(data.get('webSocketSessionIncomingMessages', 0), int) or 0,
                'web_socket_session_outgoing_messages': safe_cast(data.get('webSocketSessionOutgoingMessages', 0), int) or 0,
            }
            return TypedResult(True, stats)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    # Scene methods with enhanced type safety
    async def get_scenes(self, use_cache: bool = True) -> TypedResult[List[str]]:
        """Get list of scene names with caching."""
        try:
            scenes = await self._agent.get_scenes(use_cache)
            validated_scenes = [ensure_type(scene, str) for scene in scenes]
            return TypedResult(True, validated_scenes)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    async def get_current_scene(self) -> TypedResult[str]:
        """Get current scene name."""
        try:
            scene = await self._agent.get_current_scene()
            return TypedResult(True, ensure_type(scene, str))
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    async def set_scene(self, scene_name: str) -> TypedResult[bool]:
        """Switch to a scene with validation."""
        if not self._validators['scene_name'].validate(scene_name):
            return TypedResult(False, error="Invalid scene name")
        
        try:
            result = await self._agent.set_scene(scene_name)
            return TypedResult(True, result)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    async def create_scene(self, scene_name: str) -> TypedResult[bool]:
        """Create a new scene with validation."""
        if not self._validators['scene_name'].validate(scene_name):
            return TypedResult(False, error="Invalid scene name")
        
        try:
            result = await self._agent.create_scene(scene_name)
            return TypedResult(True, result)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    async def remove_scene(self, scene_name: str) -> TypedResult[bool]:
        """Remove a scene with validation."""
        if not self._validators['scene_name'].validate(scene_name):
            return TypedResult(False, error="Invalid scene name")
        
        try:
            result = await self._agent.remove_scene(scene_name)
            return TypedResult(True, result)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    # Source methods with typed parameters
    async def get_sources(self, use_cache: bool = True) -> TypedResult[List[SourceInfo]]:
        """Get list of sources with type validation."""
        try:
            sources = await self._agent.get_sources(use_cache)
            validated_sources: List[SourceInfo] = []
            
            for source in sources:
                validated_source: SourceInfo = {
                    'input_name': ensure_type(source.get('inputName', ''), str),
                    'input_uuid': ensure_type(source.get('inputUuid', ''), str),
                    'input_kind': ensure_type(source.get('inputKind', ''), str),
                    'unversioned_input_kind': ensure_type(source.get('unversionedInputKind', ''), str),
                }
                validated_sources.append(validated_source)
            
            return TypedResult(True, validated_sources)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    async def create_source(
        self,
        scene_name: str,
        source_name: str,
        source_kind: SourceKind,
        source_settings: Optional[SourceSettings] = None,
        scene_item_enabled: bool = True
    ) -> TypedResult[int]:
        """Create a source with full type safety."""
        # Validate parameters
        if not self._validators['scene_name'].validate(scene_name):
            return TypedResult(False, error="Invalid scene name")
        if not self._validators['source_name'].validate(source_name):
            return TypedResult(False, error="Invalid source name")
        
        try:
            # Use the underlying agent's create_source method
            # Note: This assumes the base agent has this method
            result = await self._agent.create_source(
                scene_name=scene_name,
                source_name=source_name,
                source_kind=source_kind,
                settings=source_settings or {}
            )
            return TypedResult(True, ensure_type(result, int))
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    # Audio methods with precise volume types
    async def get_source_volume(self, source_name: str) -> TypedResult[VolumeInfo]:
        """Get source volume with typed result."""
        if not self._validators['source_name'].validate(source_name):
            return TypedResult(False, error="Invalid source name")
        
        try:
            volume_data = await self._agent.get_source_volume(source_name)
            volume_info: VolumeInfo = {
                'input_volume_mul': ensure_type(volume_data.get('volume_mul', 1.0), float),
                'input_volume_db': ensure_type(volume_data.get('volume_db', 0.0), float),
            }
            return TypedResult(True, volume_info)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    @overload
    async def set_source_volume(
        self, source_name: str, *, volume_db: Decibels
    ) -> TypedResult[bool]: ...
    
    @overload
    async def set_source_volume(
        self, source_name: str, *, volume_mul: float
    ) -> TypedResult[bool]: ...
    
    async def set_source_volume(
        self,
        source_name: str,
        *,
        volume_db: Optional[Decibels] = None,
        volume_mul: Optional[float] = None
    ) -> TypedResult[bool]:
        """Set source volume with overloaded signatures for type safety."""
        if not self._validators['source_name'].validate(source_name):
            return TypedResult(False, error="Invalid source name")
        
        if volume_db is not None and not (-100.0 <= volume_db <= 26.0):
            return TypedResult(False, error="Volume dB must be between -100.0 and 26.0")
        
        if volume_mul is not None and not (0.0 <= volume_mul <= 20.0):
            return TypedResult(False, error="Volume multiplier must be between 0.0 and 20.0")
        
        try:
            result = await self._agent.set_source_volume(
                source_name, volume_db=volume_db, volume_mul=volume_mul
            )
            return TypedResult(True, result)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    async def get_source_mute(self, source_name: str) -> TypedResult[bool]:
        """Get source mute status."""
        if not self._validators['source_name'].validate(source_name):
            return TypedResult(False, error="Invalid source name")
        
        try:
            muted = await self._agent.get_source_mute(source_name)
            return TypedResult(True, ensure_type(muted, bool))
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    async def set_source_mute(self, source_name: str, muted: bool) -> TypedResult[bool]:
        """Set source mute status."""
        if not self._validators['source_name'].validate(source_name):
            return TypedResult(False, error="Invalid source name")
        
        try:
            result = await self._agent.set_source_mute(source_name, muted)
            return TypedResult(True, result)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    # Streaming methods with typed status
    async def start_streaming(self) -> TypedResult[bool]:
        """Start streaming with typed result."""
        try:
            result = await self._agent.start_streaming()
            return TypedResult(True, result)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    async def stop_streaming(self) -> TypedResult[bool]:
        """Stop streaming with typed result."""
        try:
            result = await self._agent.stop_streaming()
            return TypedResult(True, result)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    async def get_streaming_status(self) -> TypedResult[StreamStatus]:
        """Get streaming status with full type validation."""
        try:
            status_data = await self._agent.get_streaming_status()
            stream_status: StreamStatus = {
                'output_active': ensure_type(status_data.get('is_streaming', False), bool),
                'output_reconnecting': False,  # Not available in base agent
                'output_timecode': '00:00:00',  # Could be computed from duration
                'output_duration': safe_cast(status_data.get('duration', 0), int) or 0,
                'output_congestion': 0.0,  # Not available in base agent
                'output_bytes': safe_cast(status_data.get('bytes', 0), int) or 0,
                'output_skipped_frames': safe_cast(status_data.get('skipped_frames', 0), int) or 0,
                'output_total_frames': safe_cast(status_data.get('total_frames', 0), int) or 0,
            }
            return TypedResult(True, stream_status)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    # Recording methods with typed results
    async def start_recording(self) -> TypedResult[bool]:
        """Start recording with typed result."""
        try:
            result = await self._agent.start_recording()
            return TypedResult(True, result)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    async def stop_recording(self) -> TypedResult[str]:
        """Stop recording and return file path."""
        try:
            file_path = await self._agent.stop_recording()
            return TypedResult(True, ensure_type(file_path, str))
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    async def get_recording_status(self) -> TypedResult[RecordingStatus]:
        """Get recording status with full type validation."""
        try:
            status_data = await self._agent.get_recording_status()
            recording_status: RecordingStatus = {
                'output_active': ensure_type(status_data.get('is_recording', False), bool),
                'output_paused': ensure_type(status_data.get('is_paused', False), bool),
                'output_timecode': '00:00:00',  # Could be computed from duration
                'output_duration': safe_cast(status_data.get('duration', 0), int) or 0,
                'output_bytes': safe_cast(status_data.get('bytes', 0), int) or 0,
            }
            return TypedResult(True, recording_status)
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    # Screenshot with path validation
    async def take_screenshot(
        self,
        source_name: str,
        file_path: Union[str, Path],
        *,
        width: Optional[int] = None,
        height: Optional[int] = None,
        format: Literal["png", "jpg", "jpeg", "bmp"] = "png"
    ) -> TypedResult[Path]:
        """Take screenshot with type-safe parameters."""
        if not self._validators['source_name'].validate(source_name):
            return TypedResult(False, error="Invalid source name")
        
        # Convert to Path for type safety
        path_obj = Path(file_path)
        
        try:
            result = await self._agent.take_screenshot(
                source_name, path_obj, width=width, height=height, format=format
            )
            return TypedResult(True, path_obj if result else Path())
        except Exception as e:
            return TypedResult(False, error=str(e))
    
    # Event handling with typed handlers
    def on_scene_changed(
        self, handler: EventHandlerProtocol[CurrentProgramSceneChangedData]
    ) -> TypedEventHandler[CurrentProgramSceneChangedData]:
        """Register typed scene change handler."""
        from .event_handler import CurrentProgramSceneChanged
        typed_handler = create_typed_handler(CurrentProgramSceneChanged, handler)
        
        @self._agent.on(CurrentProgramSceneChanged)
        async def wrapper(event: CurrentProgramSceneChanged) -> None:
            event_data: CurrentProgramSceneChangedData = {
                'scene_name': event.scene_name,
                'scene_uuid': event.scene_uuid or '',
            }
            await typed_handler.handle(event_data)
        
        return typed_handler
    
    def on_mute_changed(
        self, handler: EventHandlerProtocol[InputMuteStateChangedData]
    ) -> TypedEventHandler[InputMuteStateChangedData]:
        """Register typed mute change handler."""
        from .event_handler import InputMuteStateChanged
        typed_handler = create_typed_handler(InputMuteStateChanged, handler)
        
        @self._agent.on(InputMuteStateChanged)
        async def wrapper(event: InputMuteStateChanged) -> None:
            event_data: InputMuteStateChangedData = {
                'input_name': event.input_name,
                'input_uuid': event.input_uuid or '',
                'input_muted': event.input_muted,
            }
            await typed_handler.handle(event_data)
        
        return typed_handler
    
    # Validation methods
    def validate_scene_name(self, scene_name: str) -> ValidationResult:
        """Validate scene name."""
        if not isinstance(scene_name, str):
            return {'valid': False, 'errors': ['Scene name must be a string']}
        if not scene_name.strip():
            return {'valid': False, 'errors': ['Scene name cannot be empty']}
        if len(scene_name) > 256:
            return {'valid': False, 'errors': ['Scene name too long (max 256 characters)']}
        return {'valid': True, 'errors': []}
    
    def validate_source_name(self, source_name: str) -> ValidationResult:
        """Validate source name."""
        if not isinstance(source_name, str):
            return {'valid': False, 'errors': ['Source name must be a string']}
        if not source_name.strip():
            return {'valid': False, 'errors': ['Source name cannot be empty']}
        if len(source_name) > 256:
            return {'valid': False, 'errors': ['Source name too long (max 256 characters)']}
        return {'valid': True, 'errors': []}
    
    def validate_volume_db(self, volume_db: float) -> ValidationResult:
        """Validate volume in decibels."""
        if not isinstance(volume_db, (int, float)):
            return {'valid': False, 'errors': ['Volume must be a number']}
        if not (-100.0 <= volume_db <= 26.0):
            return {'valid': False, 'errors': ['Volume must be between -100.0 and 26.0 dB']}
        return {'valid': True, 'errors': []}


# Factory function for convenient creation
@asynccontextmanager
async def create_typed_obs_agent(
    config: Optional[Config] = None
) -> AsyncContextManager[TypedOBSAgent]:
    """Create typed OBS agent with automatic connection management."""
    agent = TypedOBSAgent(config)
    try:
        result = await agent.connect()
        if not result.success:
            raise ConnectionError(f"Failed to connect: {result.error}")
        yield agent
    finally:
        await agent.disconnect()


# Type aliases for convenience
TypeSafeOBS = TypedOBSAgent
SafeOBSAgent = TypedOBSAgent