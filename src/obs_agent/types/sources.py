"""
Type definitions for OBS source types and their settings.

This module provides comprehensive types for all OBS source kinds and their
specific settings, enabling type-safe source creation and configuration.
"""

from typing import Any, Dict, List, Literal, Union
from typing_extensions import NotRequired, TypedDict

from .base import Font


# Source Kind Literals
SourceKind = Literal[
    # Video sources
    "dshow_input",  # Video Capture Device
    "ffmpeg_source",  # Media Source
    "image_source",  # Image
    "slideshow",  # Image Slide Show
    "browser_source",  # Browser Source
    "window_capture",  # Window Capture
    "monitor_capture",  # Display Capture
    "game_capture",  # Game Capture
    "scene",  # Scene
    "group",  # Group
    "color_source",  # Color Source
    "text_gdiplus",  # Text (GDI+)
    "text_ft2_source",  # Text (FreeType 2)
    "text_ft2_source_v2",  # Text (FreeType 2) v2
    "vlc_source",  # VLC Video Source
    # Audio sources
    "wasapi_input_capture",  # Audio Input Capture
    "wasapi_output_capture",  # Audio Output Capture
    "coreaudio_input_capture",  # Audio Input Capture (macOS)
    "coreaudio_output_capture",  # Audio Output Capture (macOS)
    "pulse_input_capture",  # Audio Input Capture (Linux)
    "pulse_output_capture",  # Audio Output Capture (Linux)
    "alsa_input_capture",  # ALSA Input Capture (Linux)
    "alsa_output_capture",  # ALSA Output Capture (Linux)
    # Platform-specific
    "av_capture_input",  # Video Capture Device (macOS)
    "screen_capture",  # Screen Capture (macOS)
    "display_capture",  # Display Capture (Windows/Linux)
    "xshm_input",  # Screen Capture (Linux)
    "xcomposite_input",  # Window Capture (Linux)
    # Filters
    "mask_filter",  # Image Mask/Blend
    "crop_filter",  # Crop/Pad
    "scale_filter",  # Scaling/Aspect Ratio
    "scroll_filter",  # Scroll
    "color_filter",  # Color Correction
    "async_delay_filter",  # Video Delay (Async)
    "gpu_delay",  # Video Delay (Async)
    "color_key_filter",  # Chroma Key
    "clut_filter",  # Apply LUT
    "sharpness_filter",  # Sharpen
    "chroma_key_filter",  # Chroma Key
    "luma_key_filter",  # Luma Key
    "invert_polarity_filter",  # Invert Polarity
    "limiter_filter",  # Limiter
    "expander_filter",  # Expander
    "compressor_filter",  # Compressor
    "noise_gate_filter",  # Noise Gate
    "noise_suppress_filter",  # Noise Suppression
    "gain_filter",  # Gain
    "eq_filter",  # 3-Band Equalizer
    "vst_filter",  # VST 2.x Plugin
    "speex_noise_suppression_filter",  # Speex Noise Suppression
]


# Base source settings
class BaseSourceSettings(TypedDict, total=False):
    """Base settings for all source types."""

    pass


# Video source settings
class DisplayCaptureSettings(BaseSourceSettings):
    """Settings for display/monitor capture."""

    display: NotRequired[int]  # Display index
    show_cursor: NotRequired[bool]  # Show mouse cursor
    capture_cursor: NotRequired[bool]  # Capture cursor
    compatibility: NotRequired[bool]  # Use compatibility mode


class WindowCaptureSettings(BaseSourceSettings):
    """Settings for window capture."""

    window: NotRequired[str]  # Window identifier
    priority: NotRequired[int]  # Window matching priority
    client_area: NotRequired[bool]  # Capture client area only
    cursor: NotRequired[bool]  # Capture cursor
    compatibility: NotRequired[bool]  # Use compatibility mode


class GameCaptureSettings(BaseSourceSettings):
    """Settings for game capture."""

    capture_mode: NotRequired[str]  # "window", "any_fullscreen", "hotkey"
    window: NotRequired[str]  # Target window
    force_scaling: NotRequired[bool]  # Force scaling
    scale_res: NotRequired[str]  # Scaling resolution
    limit_framerate: NotRequired[bool]  # Limit capture framerate
    capture_cursor: NotRequired[bool]  # Capture cursor
    anti_cheat_hook: NotRequired[bool]  # Anti-cheat compatibility
    capture_third_party_overlays: NotRequired[bool]  # Capture overlays


class MediaSourceSettings(BaseSourceSettings):
    """Settings for media sources (video/audio files)."""

    local_file: NotRequired[str]  # Local file path
    is_local_file: NotRequired[bool]  # Use local file
    input: NotRequired[str]  # Input URL/path
    input_format: NotRequired[str]  # Input format
    reconnect_delay_sec: NotRequired[int]  # Reconnect delay
    restart_on_activate: NotRequired[bool]  # Restart when activated
    close_when_inactive: NotRequired[bool]  # Close when inactive
    speed_percent: NotRequired[int]  # Playback speed percentage
    color_range: NotRequired[int]  # Color range
    linear_alpha: NotRequired[bool]  # Linear alpha
    looping: NotRequired[bool]  # Loop playback
    restart: NotRequired[bool]  # Restart playback
    clear_on_media_end: NotRequired[bool]  # Clear on media end


class ImageSourceSettings(BaseSourceSettings):
    """Settings for image sources."""

    file: str  # Image file path
    unload: NotRequired[bool]  # Unload when not showing
    linear_alpha: NotRequired[bool]  # Linear alpha


class SlideshowSettings(BaseSourceSettings):
    """Settings for image slideshow."""

    files: List[Dict[str, str]]  # List of image files
    loop: NotRequired[bool]  # Loop slideshow
    slide_time: NotRequired[int]  # Time per slide (ms)
    transition_time: NotRequired[int]  # Transition time (ms)
    randomize: NotRequired[bool]  # Randomize order
    restart_on_activate: NotRequired[bool]  # Restart when activated
    pause_on_end: NotRequired[bool]  # Pause on end
    play_pause_hotkey: NotRequired[str]  # Play/pause hotkey
    restart_hotkey: NotRequired[str]  # Restart hotkey
    stop_hotkey: NotRequired[str]  # Stop hotkey
    next_hotkey: NotRequired[str]  # Next slide hotkey
    previous_hotkey: NotRequired[str]  # Previous slide hotkey


class ColorSourceSettings(BaseSourceSettings):
    """Settings for color sources."""

    color: int  # RGB color value
    width: NotRequired[int]  # Width in pixels
    height: NotRequired[int]  # Height in pixels


class TextSourceSettings(BaseSourceSettings):
    """Settings for text sources (GDI+ and FreeType)."""

    text: str  # Text content
    font: Font  # Font settings
    color: NotRequired[int]  # Text color (RGB)
    color1: NotRequired[int]  # Primary text color
    color2: NotRequired[int]  # Secondary text color (gradient)
    opacity: NotRequired[int]  # Text opacity (0-100)
    gradient: NotRequired[bool]  # Use gradient
    gradient_color: NotRequired[int]  # Gradient color
    gradient_dir: NotRequired[float]  # Gradient direction
    gradient_opacity: NotRequired[int]  # Gradient opacity
    align: NotRequired[str]  # Text alignment ("left", "center", "right")
    valign: NotRequired[str]  # Vertical alignment ("top", "center", "bottom")
    outline: NotRequired[bool]  # Use outline
    outline_size: NotRequired[int]  # Outline size
    outline_color: NotRequired[int]  # Outline color
    outline_opacity: NotRequired[int]  # Outline opacity
    chatlog: NotRequired[bool]  # Chat log mode
    chatlog_lines: NotRequired[int]  # Number of chat log lines
    extents: NotRequired[bool]  # Use text extents
    extents_cx: NotRequired[int]  # Text extents width
    extents_cy: NotRequired[int]  # Text extents height
    extents_wrap: NotRequired[bool]  # Wrap text in extents
    read_from_file: NotRequired[bool]  # Read text from file
    file: NotRequired[str]  # Text file path
    log_mode: NotRequired[bool]  # Log mode (monitor file)
    log_lines: NotRequired[int]  # Number of log lines


class BrowserSourceSettings(BaseSourceSettings):
    """Settings for browser sources."""

    url: str  # Source URL
    width: NotRequired[int]  # Browser width
    height: NotRequired[int]  # Browser height
    fps: NotRequired[int]  # Frames per second
    css: NotRequired[str]  # Custom CSS
    shutdown: NotRequired[bool]  # Shutdown source when not visible
    restart_when_active: NotRequired[bool]  # Restart when active
    reroute_audio: NotRequired[bool]  # Reroute audio


class VLCSourceSettings(BaseSourceSettings):
    """Settings for VLC video sources."""

    playlist: List[Dict[str, str]]  # Playlist of media files
    loop: NotRequired[bool]  # Loop playlist
    shuffle: NotRequired[bool]  # Shuffle playlist
    playback_behavior: NotRequired[str]  # Playback behavior
    network_caching: NotRequired[int]  # Network caching (ms)
    track: NotRequired[int]  # Audio track
    subtitle: NotRequired[int]  # Subtitle track


# Audio source settings
class AudioInputSettings(BaseSourceSettings):
    """Settings for audio input capture."""

    device_id: NotRequired[str]  # Audio device ID
    use_device_timing: NotRequired[bool]  # Use device timing


class AudioOutputSettings(BaseSourceSettings):
    """Settings for audio output capture."""

    device_id: NotRequired[str]  # Audio device ID
    use_device_timing: NotRequired[bool]  # Use device timing


# Platform-specific settings
class AVCaptureSettings(BaseSourceSettings):
    """Settings for AV capture (macOS)."""

    device: NotRequired[str]  # Capture device
    device_name: NotRequired[str]  # Device name
    preset: NotRequired[str]  # Capture preset
    use_preset: NotRequired[bool]  # Use preset
    color_space: NotRequired[str]  # Color space
    video_range: NotRequired[str]  # Video range
    frame_rate: NotRequired[str]  # Frame rate
    resolution: NotRequired[str]  # Resolution
    buffering: NotRequired[bool]  # Enable buffering


class ScreenCaptureSettings(BaseSourceSettings):
    """Settings for screen capture (macOS)."""

    display: NotRequired[int]  # Display ID
    show_cursor: NotRequired[bool]  # Show cursor
    crop: NotRequired[bool]  # Crop to window
    window: NotRequired[int]  # Window ID


# Filter settings
class ColorCorrectionSettings(BaseSourceSettings):
    """Settings for color correction filter."""

    gamma: NotRequired[float]  # Gamma correction
    contrast: NotRequired[float]  # Contrast adjustment
    brightness: NotRequired[float]  # Brightness adjustment
    saturation: NotRequired[float]  # Saturation adjustment
    hue_shift: NotRequired[float]  # Hue shift
    opacity: NotRequired[float]  # Opacity


class ChromaKeySettings(BaseSourceSettings):
    """Settings for chroma key filter."""

    key_color_type: NotRequired[str]  # Key color type
    key_color: NotRequired[int]  # Key color (RGB)
    similarity: NotRequired[int]  # Similarity threshold
    smoothness: NotRequired[int]  # Smoothness
    key_color_spill_reduction: NotRequired[int]  # Spill reduction


class CropSettings(BaseSourceSettings):
    """Settings for crop filter."""

    left: NotRequired[int]  # Left crop
    top: NotRequired[int]  # Top crop
    right: NotRequired[int]  # Right crop
    bottom: NotRequired[int]  # Bottom crop
    relative: NotRequired[bool]  # Relative positioning


class AudioFilterSettings(BaseSourceSettings):
    """Base settings for audio filters."""

    db: NotRequired[float]  # Decibel adjustment


class NoiseSuppressionSettings(AudioFilterSettings):
    """Settings for noise suppression filter."""

    suppress_level: NotRequired[int]  # Suppression level (-60 to 0)


class NoiseGateSettings(AudioFilterSettings):
    """Settings for noise gate filter."""

    open_threshold: NotRequired[float]  # Open threshold (dB)
    close_threshold: NotRequired[float]  # Close threshold (dB)
    attack_time: NotRequired[int]  # Attack time (ms)
    hold_time: NotRequired[int]  # Hold time (ms)
    release_time: NotRequired[int]  # Release time (ms)


class CompressorSettings(AudioFilterSettings):
    """Settings for compressor filter."""

    ratio: NotRequired[float]  # Compression ratio
    threshold: NotRequired[float]  # Threshold (dB)
    attack_time: NotRequired[float]  # Attack time (ms)
    release_time: NotRequired[float]  # Release time (ms)
    output_gain: NotRequired[float]  # Output gain (dB)
    sidechain_source: NotRequired[str]  # Sidechain source


class LimiterSettings(AudioFilterSettings):
    """Settings for limiter filter."""

    threshold: NotRequired[float]  # Threshold (dB)
    release_time: NotRequired[float]  # Release time (ms)


class GainSettings(AudioFilterSettings):
    """Settings for gain filter."""

    db: float  # Gain in decibels


# Union type for all source settings
SourceSettings = Union[
    # Video sources
    DisplayCaptureSettings,
    WindowCaptureSettings,
    GameCaptureSettings,
    MediaSourceSettings,
    ImageSourceSettings,
    SlideshowSettings,
    ColorSourceSettings,
    TextSourceSettings,
    BrowserSourceSettings,
    VLCSourceSettings,
    # Audio sources
    AudioInputSettings,
    AudioOutputSettings,
    # Platform-specific
    AVCaptureSettings,
    ScreenCaptureSettings,
    # Filters
    ColorCorrectionSettings,
    ChromaKeySettings,
    CropSettings,
    NoiseSuppressionSettings,
    NoiseGateSettings,
    CompressorSettings,
    LimiterSettings,
    GainSettings,
    # Generic fallback
    Dict[str, Any],
]


# Source creation parameters
class CreateSourceParams(TypedDict):
    """Parameters for creating a source."""

    scene_name: str
    source_name: str
    source_kind: SourceKind
    source_settings: NotRequired[SourceSettings]
    scene_item_enabled: NotRequired[bool]


# Source update parameters
class UpdateSourceParams(TypedDict):
    """Parameters for updating source settings."""

    source_name: str
    source_settings: SourceSettings
    overlay: NotRequired[bool]  # Whether to overlay or replace settings


# Filter creation parameters
class CreateFilterParams(TypedDict):
    """Parameters for creating a filter."""

    source_name: str
    filter_name: str
    filter_kind: str
    filter_settings: NotRequired[SourceSettings]


# Source validation info
class SourceValidationInfo(TypedDict):
    """Source validation information."""

    source_kind: SourceKind
    required_settings: List[str]
    optional_settings: List[str]
    setting_types: Dict[str, str]
    validation_rules: Dict[str, Any]
