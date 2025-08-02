"""
Enhanced event type definitions with strict typing.

This module provides comprehensive type definitions for all OBS events
with runtime validation and type safety improvements.
"""

from typing import Any, Dict, List, Optional, Type, Union

from typing_extensions import NotRequired, TypedDict

from .base import UUID


# Event data structures
class BaseEventData(TypedDict, total=False):
    """Base event data structure."""

    event_type: str
    event_intent: int
    event_data: Dict[str, Any]


class SceneEventData(BaseEventData):
    """Event data for scene-related events."""

    scene_name: NotRequired[str]
    scene_uuid: NotRequired[UUID]
    scene_index: NotRequired[int]


class SceneItemEventData(BaseEventData):
    """Event data for scene item events."""

    scene_name: NotRequired[str]
    scene_uuid: NotRequired[UUID]
    scene_item_id: NotRequired[int]
    scene_item_index: NotRequired[int]
    source_name: NotRequired[str]
    source_uuid: NotRequired[UUID]


class SourceEventData(BaseEventData):
    """Event data for source/input events."""

    input_name: NotRequired[str]
    input_uuid: NotRequired[UUID]
    input_kind: NotRequired[str]
    unversioned_input_kind: NotRequired[str]


class AudioEventData(SourceEventData):
    """Event data for audio-related events."""

    input_muted: NotRequired[bool]
    input_volume_mul: NotRequired[float]
    input_volume_db: NotRequired[float]


class FilterEventData(BaseEventData):
    """Event data for filter events."""

    source_name: NotRequired[str]
    filter_name: NotRequired[str]
    filter_kind: NotRequired[str]
    filter_index: NotRequired[int]
    filter_enabled: NotRequired[bool]


class TransitionEventData(BaseEventData):
    """Event data for transition events."""

    transition_name: NotRequired[str]
    transition_uuid: NotRequired[UUID]
    transition_kind: NotRequired[str]


class OutputEventData(BaseEventData):
    """Event data for output events (streaming/recording)."""

    output_name: NotRequired[str]
    output_active: NotRequired[bool]
    output_state: NotRequired[str]
    output_path: NotRequired[str]


class MediaEventData(BaseEventData):
    """Event data for media input events."""

    input_name: NotRequired[str]
    input_uuid: NotRequired[UUID]
    media_state: NotRequired[str]
    media_duration: NotRequired[int]
    media_cursor: NotRequired[int]


class HotkeyEventData(BaseEventData):
    """Event data for hotkey events."""

    hotkey_name: NotRequired[str]
    hotkey_id: NotRequired[str]


class VendorEventData(BaseEventData):
    """Event data for vendor-specific events."""

    vendor_name: NotRequired[str]
    # Note: Don't redefine event_type and event_data to avoid MyPy overwrite warnings


# Complete event type definitions
class CurrentProgramSceneChangedData(SceneEventData):
    """Data for CurrentProgramSceneChanged event."""

    scene_name: str
    scene_uuid: UUID


class CurrentPreviewSceneChangedData(SceneEventData):
    """Data for CurrentPreviewSceneChanged event."""

    scene_name: str
    scene_uuid: UUID


class SceneCreatedData(SceneEventData):
    """Data for SceneCreated event."""

    scene_name: str
    scene_uuid: UUID
    is_group: bool


class SceneRemovedData(SceneEventData):
    """Data for SceneRemoved event."""

    scene_name: str
    scene_uuid: UUID
    is_group: bool


class SceneNameChangedData(BaseEventData):
    """Data for SceneNameChanged event."""

    old_scene_name: str
    scene_name: str
    scene_uuid: UUID


class SceneListChangedData(BaseEventData):
    """Data for SceneListChanged event."""

    scenes: List[Dict[str, Any]]


class InputCreatedData(SourceEventData):
    """Data for InputCreated event."""

    input_name: str
    input_uuid: UUID
    input_kind: str
    unversioned_input_kind: str
    input_settings: Dict[str, Any]
    default_input_settings: Dict[str, Any]


class InputRemovedData(SourceEventData):
    """Data for InputRemoved event."""

    input_name: str
    input_uuid: UUID


class InputNameChangedData(BaseEventData):
    """Data for InputNameChanged event."""

    old_input_name: str
    input_name: str
    input_uuid: UUID


class InputActiveStateChangedData(SourceEventData):
    """Data for InputActiveStateChanged event."""

    input_name: str
    input_uuid: UUID
    video_active: bool


class InputShowStateChangedData(SourceEventData):
    """Data for InputShowStateChanged event."""

    input_name: str
    input_uuid: UUID
    video_showing: bool


class InputMuteStateChangedData(AudioEventData):
    """Data for InputMuteStateChanged event."""

    input_name: str
    input_uuid: UUID
    input_muted: bool


class InputVolumeChangedData(AudioEventData):
    """Data for InputVolumeChanged event."""

    input_name: str
    input_uuid: UUID
    input_volume_mul: float
    input_volume_db: float


class InputAudioBalanceChangedData(AudioEventData):
    """Data for InputAudioBalanceChanged event."""

    input_name: str
    input_uuid: UUID
    input_audio_balance: float


class InputAudioSyncOffsetChangedData(AudioEventData):
    """Data for InputAudioSyncOffsetChanged event."""

    input_name: str
    input_uuid: UUID
    input_audio_sync_offset: int


class InputAudioTracksChangedData(AudioEventData):
    """Data for InputAudioTracksChanged event."""

    input_name: str
    input_uuid: UUID
    input_audio_tracks: Dict[str, bool]


class InputAudioMonitorTypeChangedData(AudioEventData):
    """Data for InputAudioMonitorTypeChanged event."""

    input_name: str
    input_uuid: UUID
    monitor_type: str


class InputVolumeMetersData(BaseEventData):
    """Data for InputVolumeMeters event."""

    inputs: List[Dict[str, Any]]


class SceneItemCreatedData(SceneItemEventData):
    """Data for SceneItemCreated event."""

    scene_name: str
    scene_uuid: UUID
    source_name: str
    source_uuid: UUID
    scene_item_id: int
    scene_item_index: int


class SceneItemRemovedData(SceneItemEventData):
    """Data for SceneItemRemoved event."""

    scene_name: str
    scene_uuid: UUID
    source_name: str
    source_uuid: UUID
    scene_item_id: int


class SceneItemListReindexedData(BaseEventData):
    """Data for SceneItemListReindexed event."""

    scene_name: str
    scene_uuid: UUID
    scene_items: List[Dict[str, Any]]


class SceneItemEnableStateChangedData(SceneItemEventData):
    """Data for SceneItemEnableStateChanged event."""

    scene_name: str
    scene_uuid: UUID
    scene_item_id: int
    scene_item_enabled: bool


class SceneItemLockStateChangedData(SceneItemEventData):
    """Data for SceneItemLockStateChanged event."""

    scene_name: str
    scene_uuid: UUID
    scene_item_id: int
    scene_item_locked: bool


class SceneItemSelectedData(SceneItemEventData):
    """Data for SceneItemSelected event."""

    scene_name: str
    scene_uuid: UUID
    scene_item_id: int


class SceneItemTransformChangedData(SceneItemEventData):
    """Data for SceneItemTransformChanged event."""

    scene_name: str
    scene_uuid: UUID
    scene_item_id: int
    scene_item_transform: Dict[str, Any]


class SourceFilterCreatedData(FilterEventData):
    """Data for SourceFilterCreated event."""

    source_name: str
    filter_name: str
    filter_kind: str
    filter_index: int
    filter_settings: Dict[str, Any]
    default_filter_settings: Dict[str, Any]


class SourceFilterRemovedData(FilterEventData):
    """Data for SourceFilterRemoved event."""

    source_name: str
    filter_name: str


class SourceFilterListReindexedData(BaseEventData):
    """Data for SourceFilterListReindexed event."""

    source_name: str
    filters: List[Dict[str, Any]]


class SourceFilterEnableStateChangedData(FilterEventData):
    """Data for SourceFilterEnableStateChanged event."""

    source_name: str
    filter_name: str
    filter_enabled: bool


class SourceFilterNameChangedData(BaseEventData):
    """Data for SourceFilterNameChanged event."""

    source_name: str
    old_filter_name: str
    filter_name: str


class CurrentSceneTransitionChangedData(TransitionEventData):
    """Data for CurrentSceneTransitionChanged event."""

    transition_name: str
    transition_uuid: UUID


class CurrentSceneTransitionDurationChangedData(BaseEventData):
    """Data for CurrentSceneTransitionDurationChanged event."""

    transition_duration: int


class SceneTransitionStartedData(TransitionEventData):
    """Data for SceneTransitionStarted event."""

    transition_name: str
    transition_uuid: UUID


class SceneTransitionEndedData(TransitionEventData):
    """Data for SceneTransitionEnded event."""

    transition_name: str
    transition_uuid: UUID


class SceneTransitionVideoEndedData(TransitionEventData):
    """Data for SceneTransitionVideoEnded event."""

    transition_name: str
    transition_uuid: UUID


class StreamStateChangedData(OutputEventData):
    """Data for StreamStateChanged event."""

    output_active: bool
    output_state: str


class RecordStateChangedData(OutputEventData):
    """Data for RecordStateChanged event."""

    output_active: bool
    output_state: str
    output_path: NotRequired[str]


class ReplayBufferStateChangedData(OutputEventData):
    """Data for ReplayBufferStateChanged event."""

    output_active: bool
    output_state: str


class VirtualcamStateChangedData(OutputEventData):
    """Data for VirtualcamStateChanged event."""

    output_active: bool
    output_state: str


class ReplayBufferSavedData(BaseEventData):
    """Data for ReplayBufferSaved event."""

    saved_replay_path: str


class MediaInputPlaybackStartedData(MediaEventData):
    """Data for MediaInputPlaybackStarted event."""

    input_name: str
    input_uuid: UUID


class MediaInputPlaybackEndedData(MediaEventData):
    """Data for MediaInputPlaybackEnded event."""

    input_name: str
    input_uuid: UUID


class MediaInputActionTriggeredData(MediaEventData):
    """Data for MediaInputActionTriggered event."""

    input_name: str
    input_uuid: UUID
    media_action: str


class StudioModeStateChangedData(BaseEventData):
    """Data for StudioModeStateChanged event."""

    studio_mode_enabled: bool


class ScreenshotSavedData(BaseEventData):
    """Data for ScreenshotSaved event."""

    saved_screenshot_path: str


class ExitStartedData(BaseEventData):
    """Data for ExitStarted event."""

    pass  # No additional data


# Union type for all event data
EventData = Union[
    CurrentProgramSceneChangedData,
    CurrentPreviewSceneChangedData,
    SceneCreatedData,
    SceneRemovedData,
    SceneNameChangedData,
    SceneListChangedData,
    InputCreatedData,
    InputRemovedData,
    InputNameChangedData,
    InputActiveStateChangedData,
    InputShowStateChangedData,
    InputMuteStateChangedData,
    InputVolumeChangedData,
    InputAudioBalanceChangedData,
    InputAudioSyncOffsetChangedData,
    InputAudioTracksChangedData,
    InputAudioMonitorTypeChangedData,
    InputVolumeMetersData,
    SceneItemCreatedData,
    SceneItemRemovedData,
    SceneItemListReindexedData,
    SceneItemEnableStateChangedData,
    SceneItemLockStateChangedData,
    SceneItemSelectedData,
    SceneItemTransformChangedData,
    SourceFilterCreatedData,
    SourceFilterRemovedData,
    SourceFilterListReindexedData,
    SourceFilterEnableStateChangedData,
    SourceFilterNameChangedData,
    CurrentSceneTransitionChangedData,
    CurrentSceneTransitionDurationChangedData,
    SceneTransitionStartedData,
    SceneTransitionEndedData,
    SceneTransitionVideoEndedData,
    StreamStateChangedData,
    RecordStateChangedData,
    ReplayBufferStateChangedData,
    VirtualcamStateChangedData,
    ReplayBufferSavedData,
    MediaInputPlaybackStartedData,
    MediaInputPlaybackEndedData,
    MediaInputActionTriggeredData,
    StudioModeStateChangedData,
    ScreenshotSavedData,
    ExitStartedData,
    HotkeyEventData,
    VendorEventData,
]


# Event mapping for type inference
EVENT_DATA_MAP: Dict[str, Type[EventData]] = {
    "CurrentProgramSceneChanged": CurrentProgramSceneChangedData,
    "CurrentPreviewSceneChanged": CurrentPreviewSceneChangedData,
    "SceneCreated": SceneCreatedData,
    "SceneRemoved": SceneRemovedData,
    "SceneNameChanged": SceneNameChangedData,
    "SceneListChanged": SceneListChangedData,
    "InputCreated": InputCreatedData,
    "InputRemoved": InputRemovedData,
    "InputNameChanged": InputNameChangedData,
    "InputActiveStateChanged": InputActiveStateChangedData,
    "InputShowStateChanged": InputShowStateChangedData,
    "InputMuteStateChanged": InputMuteStateChangedData,
    "InputVolumeChanged": InputVolumeChangedData,
    "InputAudioBalanceChanged": InputAudioBalanceChangedData,
    "InputAudioSyncOffsetChanged": InputAudioSyncOffsetChangedData,
    "InputAudioTracksChanged": InputAudioTracksChangedData,
    "InputAudioMonitorTypeChanged": InputAudioMonitorTypeChangedData,
    "InputVolumeMeters": InputVolumeMetersData,
    "SceneItemCreated": SceneItemCreatedData,
    "SceneItemRemoved": SceneItemRemovedData,
    "SceneItemListReindexed": SceneItemListReindexedData,
    "SceneItemEnableStateChanged": SceneItemEnableStateChangedData,
    "SceneItemLockStateChanged": SceneItemLockStateChangedData,
    "SceneItemSelected": SceneItemSelectedData,
    "SceneItemTransformChanged": SceneItemTransformChangedData,
    "SourceFilterCreated": SourceFilterCreatedData,
    "SourceFilterRemoved": SourceFilterRemovedData,
    "SourceFilterListReindexed": SourceFilterListReindexedData,
    "SourceFilterEnableStateChanged": SourceFilterEnableStateChangedData,
    "SourceFilterNameChanged": SourceFilterNameChangedData,
    "CurrentSceneTransitionChanged": CurrentSceneTransitionChangedData,
    "CurrentSceneTransitionDurationChanged": CurrentSceneTransitionDurationChangedData,
    "SceneTransitionStarted": SceneTransitionStartedData,
    "SceneTransitionEnded": SceneTransitionEndedData,
    "SceneTransitionVideoEnded": SceneTransitionVideoEndedData,
    "StreamStateChanged": StreamStateChangedData,
    "RecordStateChanged": RecordStateChangedData,
    "ReplayBufferStateChanged": ReplayBufferStateChangedData,
    "VirtualcamStateChanged": VirtualcamStateChangedData,
    "ReplayBufferSaved": ReplayBufferSavedData,
    "MediaInputPlaybackStarted": MediaInputPlaybackStartedData,
    "MediaInputPlaybackEnded": MediaInputPlaybackEndedData,
    "MediaInputActionTriggered": MediaInputActionTriggeredData,
    "StudioModeStateChanged": StudioModeStateChangedData,
    "ScreenshotSaved": ScreenshotSavedData,
    "ExitStarted": ExitStartedData,
}


def get_event_data_type(event_type: str) -> Optional[Type[EventData]]:
    """Get the appropriate event data type for an event type string."""
    return EVENT_DATA_MAP.get(event_type)
