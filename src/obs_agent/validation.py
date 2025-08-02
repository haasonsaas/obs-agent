"""
Input validation and sanitization for OBS Agent.

This module provides functions to validate and sanitize user input
to prevent security issues and ensure data integrity.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .exceptions import ValidationError

# Regular expressions for validation
SCENE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9\s\-_\.]+$")
SOURCE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9\s\-_\.]+$")
FILTER_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9\s\-_\.]+$")
COLOR_HEX_PATTERN = re.compile(r"^#?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})$")
RESOLUTION_PATTERN = re.compile(r"^\d+x\d+$")

# Maximum lengths
MAX_NAME_LENGTH = 256
MAX_PATH_LENGTH = 4096
MAX_TEXT_LENGTH = 10000

# Dangerous characters that could be used for injection
DANGEROUS_CHARS = ["<", ">", '"', "'", "&", "\0", "\n", "\r", "\t"]


def sanitize_string(
    value: str, max_length: int = MAX_NAME_LENGTH, allow_spaces: bool = True, pattern: Optional[re.Pattern] = None
) -> str:
    """
    Sanitize a string value for safe use.

    Args:
        value: The string to sanitize
        max_length: Maximum allowed length
        allow_spaces: Whether to allow spaces
        pattern: Optional regex pattern to validate against

    Returns:
        Sanitized string

    Raises:
        ValidationError: If the string is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(f"Expected string, got {type(value).__name__}")

    # Strip whitespace
    value = value.strip()

    if not value:
        raise ValidationError("Value cannot be empty")

    # Check length
    if len(value) > max_length:
        raise ValidationError(f"Value exceeds maximum length of {max_length} characters")

    # Remove dangerous characters
    for char in DANGEROUS_CHARS:
        if char in value and (char != " " or not allow_spaces):
            value = value.replace(char, "")

    # Validate against pattern if provided
    if pattern and not pattern.match(value):
        raise ValidationError("Value contains invalid characters")

    return value


def validate_scene_name(name: str) -> str:
    """
    Validate and sanitize a scene name.

    Args:
        name: The scene name to validate

    Returns:
        Sanitized scene name

    Raises:
        ValidationError: If the scene name is invalid
    """
    try:
        return sanitize_string(name, pattern=SCENE_NAME_PATTERN)
    except ValidationError:
        raise ValidationError(
            f"Invalid scene name: '{name}'. "
            "Scene names can only contain letters, numbers, spaces, hyphens, underscores, and dots."
        )


def validate_source_name(name: str) -> str:
    """
    Validate and sanitize a source name.

    Args:
        name: The source name to validate

    Returns:
        Sanitized source name

    Raises:
        ValidationError: If the source name is invalid
    """
    try:
        return sanitize_string(name, pattern=SOURCE_NAME_PATTERN)
    except ValidationError:
        raise ValidationError(
            f"Invalid source name: '{name}'. "
            "Source names can only contain letters, numbers, spaces, hyphens, underscores, and dots."
        )


def validate_filter_name(name: str) -> str:
    """
    Validate and sanitize a filter name.

    Args:
        name: The filter name to validate

    Returns:
        Sanitized filter name

    Raises:
        ValidationError: If the filter name is invalid
    """
    try:
        return sanitize_string(name, pattern=FILTER_NAME_PATTERN)
    except ValidationError:
        raise ValidationError(
            f"Invalid filter name: '{name}'. "
            "Filter names can only contain letters, numbers, spaces, hyphens, underscores, and dots."
        )


def validate_port(port: Union[int, str]) -> int:
    """
    Validate a port number.

    Args:
        port: The port number to validate

    Returns:
        Valid port number

    Raises:
        ValidationError: If the port is invalid
    """
    try:
        port_int = int(port)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid port: '{port}'. Port must be a number.")

    if not 1 <= port_int <= 65535:
        raise ValidationError(f"Invalid port: {port_int}. Port must be between 1 and 65535.")

    return port_int


def validate_host(host: str) -> str:
    """
    Validate a hostname or IP address.

    Args:
        host: The hostname or IP to validate

    Returns:
        Sanitized host

    Raises:
        ValidationError: If the host is invalid
    """
    if not isinstance(host, str):
        raise ValidationError(f"Host must be a string, got {type(host).__name__}")

    host = host.strip()

    if not host:
        raise ValidationError("Host cannot be empty")

    # Basic validation - more complex validation could use socket.gethostbyname
    if len(host) > 253:  # Maximum hostname length
        raise ValidationError("Host name too long")

    # Check for invalid characters
    if not all(c.isalnum() or c in ".-:" for c in host):
        raise ValidationError(f"Invalid host: '{host}'. Contains invalid characters.")

    return host


def validate_file_path(path: Union[str, Path], must_exist: bool = False, allow_relative: bool = False) -> Path:
    """
    Validate a file path.

    Args:
        path: The file path to validate
        must_exist: Whether the path must exist
        allow_relative: Whether to allow relative paths

    Returns:
        Valid Path object

    Raises:
        ValidationError: If the path is invalid
    """
    try:
        path_obj = Path(path) if isinstance(path, str) else path
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid path: {e}")

    # Check length
    if len(str(path_obj)) > MAX_PATH_LENGTH:
        raise ValidationError(f"Path too long (max {MAX_PATH_LENGTH} characters)")

    # Check if absolute path is required
    if not allow_relative and not path_obj.is_absolute():
        raise ValidationError("Path must be absolute")

    # Check existence if required
    if must_exist and not path_obj.exists():
        raise ValidationError(f"Path does not exist: {path_obj}")

    # Prevent directory traversal
    try:
        path_obj.resolve()
        if allow_relative:
            # For relative paths, ensure they don't go outside current directory
            if ".." in path_obj.parts:
                raise ValidationError("Path cannot contain '..' for security reasons")
    except (OSError, RuntimeError) as e:
        raise ValidationError(f"Invalid path: {e}")

    return path_obj


def validate_color(color: Union[str, int]) -> int:
    """
    Validate a color value (hex string or integer).

    Args:
        color: Color as hex string (#RRGGBB) or integer

    Returns:
        Color as integer (0xRRGGBB)

    Raises:
        ValidationError: If the color is invalid
    """
    if isinstance(color, int):
        if not 0 <= color <= 0xFFFFFFFF:
            raise ValidationError(f"Invalid color value: {color}")
        return color

    if isinstance(color, str):
        color = color.strip()
        if not COLOR_HEX_PATTERN.match(color):
            raise ValidationError(f"Invalid color format: '{color}'. " "Use hex format like #RRGGBB or RRGGBB")

        # Remove # if present
        if color.startswith("#"):
            color = color[1:]

        try:
            return int(color, 16)
        except ValueError:
            raise ValidationError(f"Invalid color value: {color}")

    raise ValidationError(f"Color must be string or integer, got {type(color).__name__}")


def validate_resolution(resolution: str) -> tuple[int, int]:
    """
    Validate a resolution string.

    Args:
        resolution: Resolution in format "WIDTHxHEIGHT"

    Returns:
        Tuple of (width, height)

    Raises:
        ValidationError: If the resolution is invalid
    """
    if not isinstance(resolution, str):
        raise ValidationError(f"Resolution must be string, got {type(resolution).__name__}")

    resolution = resolution.strip()

    if not RESOLUTION_PATTERN.match(resolution):
        raise ValidationError(
            f"Invalid resolution format: '{resolution}'. " "Use format WIDTHxHEIGHT (e.g., 1920x1080)"
        )

    try:
        width, height = resolution.split("x")
        width_int = int(width)
        height_int = int(height)

        if width_int <= 0 or height_int <= 0:
            raise ValidationError("Resolution dimensions must be positive")

        if width_int > 7680 or height_int > 4320:  # 8K maximum
            raise ValidationError("Resolution exceeds maximum supported (7680x4320)")

        return (width_int, height_int)
    except ValueError as e:
        raise ValidationError(f"Invalid resolution: {e}")


def validate_volume(volume: Union[float, int], as_db: bool = False) -> float:
    """
    Validate a volume value.

    Args:
        volume: Volume value
        as_db: Whether the value is in decibels

    Returns:
        Valid volume as float

    Raises:
        ValidationError: If the volume is invalid
    """
    try:
        volume_float = float(volume)
    except (ValueError, TypeError):
        raise ValidationError(f"Volume must be a number, got {type(volume).__name__}")

    if as_db:
        # Decibel range: typically -inf to +20 dB
        if volume_float > 20:
            raise ValidationError(f"Volume in dB cannot exceed 20 dB, got {volume_float}")
    else:
        # Multiplier range: 0.0 to 20.0 (0% to 2000%)
        if not 0.0 <= volume_float <= 20.0:
            raise ValidationError(f"Volume multiplier must be between 0.0 and 20.0, got {volume_float}")

    return volume_float


def validate_settings(settings: Dict[str, Any], allowed_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Validate a settings dictionary.

    Args:
        settings: Settings dictionary to validate
        allowed_keys: Optional list of allowed keys

    Returns:
        Validated settings

    Raises:
        ValidationError: If settings are invalid
    """
    if not isinstance(settings, dict):
        raise ValidationError(f"Settings must be a dictionary, got {type(settings).__name__}")

    # Check for dangerous keys
    dangerous_keys = ["__proto__", "constructor", "prototype"]
    for key in settings:
        if key in dangerous_keys:
            raise ValidationError(f"Settings contain dangerous key: {key}")

    # Validate allowed keys if specified
    if allowed_keys:
        invalid_keys = set(settings.keys()) - set(allowed_keys)
        if invalid_keys:
            raise ValidationError(
                f"Settings contain invalid keys: {', '.join(invalid_keys)}. " f"Allowed keys: {', '.join(allowed_keys)}"
            )

    # Recursively validate nested dictionaries
    validated: Dict[str, Any] = {}
    for key, value in settings.items():
        if isinstance(value, dict):
            validated[key] = validate_settings(value)
        elif isinstance(value, str):
            # Sanitize string values
            sanitized: Any = sanitize_string(value, max_length=MAX_TEXT_LENGTH, pattern=None)
            validated[key] = sanitized
        else:
            validated[key] = value

    return validated


def validate_transition_duration(duration: Union[int, float]) -> int:
    """
    Validate a transition duration in milliseconds.

    Args:
        duration: Duration in milliseconds

    Returns:
        Valid duration as integer

    Raises:
        ValidationError: If duration is invalid
    """
    try:
        duration_int = int(duration)
    except (ValueError, TypeError):
        raise ValidationError(f"Duration must be a number, got {type(duration).__name__}")

    if duration_int < 0:
        raise ValidationError("Duration cannot be negative")

    if duration_int > 60000:  # 60 seconds maximum
        raise ValidationError("Duration cannot exceed 60 seconds (60000 ms)")

    return duration_int


def validate_fps(fps: Union[int, float]) -> int:
    """
    Validate frames per second value.

    Args:
        fps: Frames per second

    Returns:
        Valid FPS as integer

    Raises:
        ValidationError: If FPS is invalid
    """
    try:
        fps_int = int(fps)
    except (ValueError, TypeError):
        raise ValidationError(f"FPS must be a number, got {type(fps).__name__}")

    if not 1 <= fps_int <= 240:
        raise ValidationError(f"FPS must be between 1 and 240, got {fps_int}")

    return fps_int


def validate_bitrate(bitrate: Union[int, float]) -> int:
    """
    Validate bitrate in Kbps.

    Args:
        bitrate: Bitrate in Kbps

    Returns:
        Valid bitrate as integer

    Raises:
        ValidationError: If bitrate is invalid
    """
    try:
        bitrate_int = int(bitrate)
    except (ValueError, TypeError):
        raise ValidationError(f"Bitrate must be a number, got {type(bitrate).__name__}")

    if not 100 <= bitrate_int <= 50000:  # 100 Kbps to 50 Mbps
        raise ValidationError(f"Bitrate must be between 100 and 50000 Kbps, got {bitrate_int}")

    return bitrate_int
