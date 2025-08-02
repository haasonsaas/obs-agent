"""
Comprehensive type definitions for OBS Agent.

This module provides complete type safety for all OBS WebSocket API responses,
internal data structures, and function signatures.
"""

from .api_responses import *
from .base import *
from .config import *
from .events import *
from .sources import *

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
    "Source",
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