"""
Complete type definitions for OBS WebSocket API responses.

This module provides exhaustive TypedDict definitions for all OBS WebSocket
API responses, ensuring complete type safety when working with OBS data.
"""

from typing import Any, Dict, List, Union

from typing_extensions import NotRequired, TypedDict

from .base import (
    UUID,
    Bytes,
    Decibels,
    Frames,
    Milliseconds,
    Percentage,
    Transform,
)


# Version and General Info
class OBSVersionInfo(TypedDict):
    """OBS version information from GetVersion request."""

    obs_version: str
    obs_web_socket_version: str
    rpc_version: int
    available_requests: List[str]
    supported_image_formats: List[str]
    platform: str
    platform_description: str


class OBSStats(TypedDict):
    """OBS statistics from GetStats request."""

    cpu_usage: Percentage
    memory_usage: Bytes
    available_disk_space: Bytes
    active_fps: float
    average_frame_time: float
    render_total_frames: Frames
    render_missed_frames: Frames
    render_skipped_frames: Frames
    output_total_frames: Frames
    output_skipped_frames: Frames
    web_socket_session_incoming_messages: int
    web_socket_session_outgoing_messages: int


# Scene Types
class SceneItem(TypedDict):
    """Individual scene item information."""

    scene_item_id: int
    scene_item_index: int
    source_name: str
    source_uuid: NotRequired[UUID]
    source_type: str
    input_kind: NotRequired[str]
    is_group: NotRequired[bool]
    scene_item_enabled: bool
    scene_item_locked: bool
    scene_item_transform: Transform
    scene_item_blend_mode: NotRequired[str]


class Scene(TypedDict):
    """Scene information."""

    scene_name: str
    scene_uuid: UUID
    scene_index: int
    scene_items: NotRequired[List[SceneItem]]


class SceneList(TypedDict):
    """Complete scene list from GetSceneList."""

    current_program_scene_name: str
    current_program_scene_uuid: UUID
    current_preview_scene_name: NotRequired[str]
    current_preview_scene_uuid: NotRequired[UUID]
    scenes: List[Scene]


class SceneItemTransformInfo(TypedDict):
    """Detailed scene item transform from GetSceneItemTransform."""

    scene_item_id: int
    scene_item_transform: Transform


# Source Types
class SourceInfo(TypedDict):
    """Basic source information."""

    input_name: str
    input_uuid: UUID
    input_kind: str
    unversioned_input_kind: str


class SourceDetails(TypedDict):
    """Detailed source information from GetInputSettings."""

    input_name: str
    input_uuid: UUID
    input_kind: str
    input_settings: Dict[str, Any]
    default_settings: NotRequired[Dict[str, Any]]


class SourcePropertiesInfo(TypedDict):
    """Source properties from GetInputPropertiesListPropertyItems."""

    property_name: str
    property_description: str
    property_type: str
    property_default_value: Any
    property_item_enabled: NotRequired[bool]
    property_item_name: NotRequired[str]
    property_item_value: NotRequired[Any]


class InputList(TypedDict):
    """List of inputs from GetInputList."""

    inputs: List[SourceInfo]


# Audio Types
class VolumeInfo(TypedDict):
    """Audio volume information."""

    input_volume_mul: float  # Multiplier (0.0 - 20.0)
    input_volume_db: Decibels  # Decibels (-100.0 to 26.0)


class AudioInfo(TypedDict):
    """Complete audio source information."""

    input_name: str
    input_uuid: UUID
    input_muted: bool
    input_volume_mul: float
    input_volume_db: Decibels
    input_audio_balance: NotRequired[float]
    input_audio_sync_offset: NotRequired[Milliseconds]
    input_audio_tracks: NotRequired[List[int]]


class AudioMonitorInfo(TypedDict):
    """Audio monitoring information."""

    monitor_type: str  # "none", "monitorOnly", "monitorAndOutput"


# Filter Types
class FilterInfo(TypedDict):
    """Filter information."""

    filter_name: str
    filter_kind: str
    filter_index: int
    filter_enabled: bool
    filter_settings: Dict[str, Any]


class SourceFilterList(TypedDict):
    """List of filters on a source."""

    filters: List[FilterInfo]


# Transition Types
class TransitionInfo(TypedDict):
    """Scene transition information."""

    transition_name: str
    transition_kind: str
    transition_fixed: bool
    transition_configurable: bool


class TransitionList(TypedDict):
    """List of available transitions."""

    current_scene_transition_name: str
    current_scene_transition_uuid: UUID
    current_scene_transition_kind: str
    transitions: List[TransitionInfo]


class CurrentTransitionInfo(TypedDict):
    """Current transition information."""

    transition_name: str
    transition_uuid: UUID
    transition_kind: str
    transition_fixed: bool
    transition_duration: Milliseconds
    transition_configurable: bool
    transition_settings: Dict[str, Any]


# Output Types (Streaming/Recording)
class StreamStatus(TypedDict):
    """Streaming status information."""

    output_active: bool
    output_reconnecting: bool
    output_timecode: str
    output_duration: Milliseconds
    output_congestion: float
    output_bytes: Bytes
    output_skipped_frames: Frames
    output_total_frames: Frames


class RecordingStatus(TypedDict):
    """Recording status information."""

    output_active: bool
    output_paused: bool
    output_timecode: str
    output_duration: Milliseconds
    output_bytes: Bytes


class RecordingInfo(TypedDict):
    """Recording information with file path."""

    output_path: str


class OutputInfo(TypedDict):
    """Generic output information."""

    output_name: str
    output_kind: str
    output_active: bool
    output_flags: Dict[str, bool]


class OutputList(TypedDict):
    """List of outputs."""

    outputs: List[OutputInfo]


# Media and Replay Buffer Types
class MediaInputStatus(TypedDict):
    """Media input status."""

    media_state: str  # "playing", "paused", "stopped", "ended", "error"
    media_duration: NotRequired[Milliseconds]
    media_cursor: NotRequired[Milliseconds]


class ReplayBufferStatus(TypedDict):
    """Replay buffer status."""

    output_active: bool


class ReplayBufferSaved(TypedDict):
    """Replay buffer save information."""

    saved_replay_path: str


# Hotkey Types
class HotkeyInfo(TypedDict):
    """Hotkey information."""

    hotkey_name: str
    hotkey_keys: List[str]


class HotkeyList(TypedDict):
    """List of hotkeys."""

    hotkeys: List[HotkeyInfo]


# Studio Mode Types
class StudioModeInfo(TypedDict):
    """Studio mode status."""

    studio_mode_enabled: bool


# Profile and Scene Collection Types
class ProfileInfo(TypedDict):
    """Profile information."""

    profile_name: str


class ProfileList(TypedDict):
    """List of profiles."""

    current_profile_name: str
    profiles: List[str]


class SceneCollectionInfo(TypedDict):
    """Scene collection information."""

    scene_collection_name: str


class SceneCollectionList(TypedDict):
    """List of scene collections."""

    current_scene_collection_name: str
    scene_collections: List[str]


# Screenshot Types
class ScreenshotInfo(TypedDict):
    """Screenshot information."""

    image_data: str  # Base64 encoded
    image_format: str  # "png", "jpg", etc.


# Virtual Camera Types
class VirtualCameraStatus(TypedDict):
    """Virtual camera status."""

    output_active: bool


# Monitor Types
class MonitorInfo(TypedDict):
    """Monitor information."""

    monitor_index: int
    monitor_name: str
    monitor_width: int
    monitor_height: int


class MonitorList(TypedDict):
    """List of monitors."""

    monitors: List[MonitorInfo]


# Custom types for specific operations
class BulkSceneItemOperation(TypedDict):
    """Bulk scene item operation result."""

    scene_item_id: int
    success: bool
    error: NotRequired[str]


class BulkOperationResult(TypedDict):
    """Result of bulk operations."""

    results: List[BulkSceneItemOperation]
    total_count: int
    success_count: int
    failed_count: int


# WebSocket Event Types (for event data)
class EventData(TypedDict, total=False):
    """Base event data structure."""

    event_type: str
    event_intent: int
    event_data: Dict[str, Any]


# Request/Response wrapper types
class OBSRequest(TypedDict):
    """OBS WebSocket request structure."""

    request_type: str
    request_id: str
    request_data: NotRequired[Dict[str, Any]]


class OBSResponse(TypedDict):
    """OBS WebSocket response structure."""

    request_type: str
    request_id: str
    request_status: Dict[str, Any]
    response_data: NotRequired[Dict[str, Any]]


class OBSEvent(TypedDict):
    """OBS WebSocket event structure."""

    event_type: str
    event_intent: int
    event_data: Dict[str, Any]


# Union types for common response patterns
SceneItemReference = Union[int, str]  # Can be ID or name
SourceReference = Union[str, UUID]  # Can be name or UUID
SceneReference = Union[str, UUID]  # Can be name or UUID

# Complete response type mapping
OBSResponseData = Union[
    OBSVersionInfo,
    OBSStats,
    SceneList,
    Scene,
    SceneItem,
    InputList,
    SourceInfo,
    SourceDetails,
    VolumeInfo,
    AudioInfo,
    FilterInfo,
    SourceFilterList,
    TransitionList,
    TransitionInfo,
    CurrentTransitionInfo,
    StreamStatus,
    RecordingStatus,
    RecordingInfo,
    OutputList,
    OutputInfo,
    MediaInputStatus,
    ReplayBufferStatus,
    ReplayBufferSaved,
    HotkeyList,
    StudioModeInfo,
    ProfileList,
    SceneCollectionList,
    ScreenshotInfo,
    VirtualCameraStatus,
    MonitorList,
    BulkOperationResult,
]
