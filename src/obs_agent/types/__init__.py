"""
Comprehensive type definitions for OBS Agent.

This module provides complete type safety for all OBS WebSocket API responses,
internal data structures, and function signatures.
"""

from .api_responses import (
    AudioInfo,
    FilterInfo,
    OBSStats,
    OBSVersionInfo,
    OutputInfo,
    RecordingStatus,
    Scene,
    SceneItem,
    SceneList,
    SourceInfo,
    StreamStatus,
    TransitionInfo,
    VolumeInfo,
)

# Import specific types to avoid F403/F405 flake8 errors
from .base import UUID, Color, ConfigT, Duration, EventT, Font, P, Position, R, Scale, Size, T, Timestamp, Transform
from .config import AudioConfig
from .config import OBSConnectionConfig as OBSConfig
from .config import RecordingConfig, StreamingConfig, VideoConfig
from .events import AudioEventData, EventData, OutputEventData, SceneEventData, SourceEventData
from .sources import (
    AudioInputSettings,
    BrowserSourceSettings,
    DisplayCaptureSettings,
    ImageSourceSettings,
    SourceKind,
    SourceSettings,
    TextSourceSettings,
    WindowCaptureSettings,
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
    "BrowserSourceSettings",
    # Generic types
    "T",
    "P",
    "R",
    "EventT",
    "ConfigT",
]
