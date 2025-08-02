"""
Comprehensive type definitions for OBS Agent.

This module provides complete type safety for all OBS WebSocket API responses,
internal data structures, and function signatures.
"""

# Import specific types to avoid F403/F405 flake8 errors
from .base import UUID, Timestamp, Duration, Position, Scale, Transform, Size, Color, Font, T, P, R, EventT, ConfigT
from .api_responses import (
    OBSVersionInfo,
    OBSStats,
    SceneList,
    Scene,
    SceneItem,
    SourceInfo,
    AudioInfo,
    VolumeInfo,
    FilterInfo,
    TransitionInfo,
    OutputInfo,
    StreamStatus,
    RecordingStatus,
)
from .config import OBSConnectionConfig as OBSConfig, StreamingConfig, RecordingConfig, AudioConfig, VideoConfig
from .events import EventData, SceneEventData, SourceEventData, AudioEventData, OutputEventData
from .sources import (
    SourceKind,
    SourceSettings,
    DisplayCaptureSettings,
    WindowCaptureSettings,
    AudioInputSettings,
    TextSourceSettings,
    ImageSourceSettings,
    VideoSourceSettings,
    BrowserSourceSettings,
)

__all__ = [
    # Base types
    "UUID",
    "Timestamp",
    "Duration",
    "Position",
    "Scale",
    "Transform",
    "Size",
    "Color",
    "Font",
    # API Response types
    "OBSVersionInfo",
    "OBSStats",
    "SceneList",
    "Scene",
    "SceneItem",
    "SourceInfo",
    "AudioInfo",
    "VolumeInfo",
    "FilterInfo",
    "TransitionInfo",
    "OutputInfo",
    "StreamStatus",
    "RecordingStatus",
    # Configuration types
    "OBSConfig",
    "StreamingConfig",
    "RecordingConfig",
    "AudioConfig",
    "VideoConfig",
    # Event types
    "EventData",
    "SceneEventData",
    "SourceEventData",
    "AudioEventData",
    "OutputEventData",
    # Source types
    "SourceKind",
    "SourceSettings",
    "DisplayCaptureSettings",
    "WindowCaptureSettings",
    "AudioInputSettings",
    "TextSourceSettings",
    "ImageSourceSettings",
    "VideoSourceSettings",
    "BrowserSourceSettings",
    # Generic types
    "T",
    "P",
    "R",
    "EventT",
    "ConfigT",
]
