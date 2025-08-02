"""
Configuration type definitions with runtime validation.

This module provides Pydantic models for configuration validation
and TypedDict definitions for configuration structures.
"""

from typing import Any, Dict, List, Optional, Union

from typing_extensions import NotRequired, TypedDict

from .base import BaseConfig


# Configuration TypedDicts
class OBSConnectionConfig(TypedDict):
    """OBS WebSocket connection configuration."""

    host: str
    port: int
    password: str
    timeout: NotRequired[float]
    reconnect_attempts: NotRequired[int]
    reconnect_delay: NotRequired[float]


class LoggingConfig(TypedDict):
    """Logging configuration."""

    level: str  # "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    format: NotRequired[str]
    file_path: NotRequired[str]
    max_file_size: NotRequired[int]
    backup_count: NotRequired[int]
    console_output: NotRequired[bool]
    structured_logging: NotRequired[bool]


class StreamingConfig(TypedDict):
    """Streaming configuration."""

    service: NotRequired[str]  # Streaming service
    server: NotRequired[str]  # RTMP server URL
    key: NotRequired[str]  # Stream key
    video_bitrate: NotRequired[int]  # Video bitrate (kbps)
    audio_bitrate: NotRequired[int]  # Audio bitrate (kbps)
    fps: NotRequired[int]  # Frames per second
    resolution: NotRequired[str]  # Resolution (e.g., "1920x1080")
    encoder: NotRequired[str]  # Video encoder
    preset: NotRequired[str]  # Encoder preset
    profile: NotRequired[str]  # Encoder profile
    keyframe_interval: NotRequired[int]  # Keyframe interval (seconds)
    auto_start: NotRequired[bool]  # Auto-start streaming
    auto_stop: NotRequired[bool]  # Auto-stop streaming


class RecordingConfig(TypedDict):
    """Recording configuration."""

    format: NotRequired[str]  # Recording format
    quality: NotRequired[str]  # Recording quality
    encoder: NotRequired[str]  # Recording encoder
    path: NotRequired[str]  # Recording output path
    filename_pattern: NotRequired[str]  # Filename pattern
    auto_start: NotRequired[bool]  # Auto-start recording
    auto_stop: NotRequired[bool]  # Auto-stop recording
    max_file_size: NotRequired[int]  # Max file size (MB)
    split_files: NotRequired[bool]  # Split large files


class AudioConfig(TypedDict):
    """Audio configuration."""

    sample_rate: NotRequired[int]  # Sample rate (Hz)
    channels: NotRequired[str]  # Channel configuration
    default_volume: NotRequired[float]  # Default volume (dB)
    monitoring_device: NotRequired[str]  # Audio monitoring device
    disable_audio_ducking: NotRequired[bool]  # Disable Windows audio ducking


class VideoConfig(TypedDict):
    """Video configuration."""

    base_resolution: NotRequired[str]  # Base (canvas) resolution
    output_resolution: NotRequired[str]  # Output (scaled) resolution
    fps_common: NotRequired[int]  # Common FPS value
    fps_integer: NotRequired[int]  # Integer FPS value
    fps_numerator: NotRequired[int]  # FPS numerator
    fps_denominator: NotRequired[int]  # FPS denominator
    downscale_filter: NotRequired[str]  # Downscale filter
    color_format: NotRequired[str]  # Color format
    color_space: NotRequired[str]  # Color space
    color_range: NotRequired[str]  # Color range


class AutomationConfig(TypedDict):
    """Automation engine configuration."""

    enabled: NotRequired[bool]  # Enable automation
    max_rules: NotRequired[int]  # Maximum automation rules
    max_executions_per_minute: NotRequired[int]  # Rate limiting
    rule_timeout: NotRequired[float]  # Rule execution timeout
    enable_error_recovery: NotRequired[bool]  # Enable error recovery
    persistence_path: NotRequired[str]  # Path for rule persistence
    metrics_enabled: NotRequired[bool]  # Enable metrics collection


class SecurityConfig(TypedDict):
    """Security configuration."""

    enable_authentication: NotRequired[bool]  # Enable authentication
    api_key: NotRequired[str]  # API key for remote access
    allowed_hosts: NotRequired[List[str]]  # Allowed host IPs
    rate_limit: NotRequired[int]  # Rate limit per minute
    enable_encryption: NotRequired[bool]  # Enable encryption
    cert_path: NotRequired[str]  # SSL certificate path
    key_path: NotRequired[str]  # SSL key path


class PerformanceConfig(TypedDict):
    """Performance configuration."""

    max_connections: NotRequired[int]  # Maximum concurrent connections
    connection_pool_size: NotRequired[int]  # Connection pool size
    request_timeout: NotRequired[float]  # Request timeout
    cache_ttl: NotRequired[float]  # Cache TTL in seconds
    enable_compression: NotRequired[bool]  # Enable response compression
    max_memory_usage: NotRequired[int]  # Max memory usage (MB)
    gc_threshold: NotRequired[float]  # Garbage collection threshold


class IntegrationConfig(TypedDict):
    """External integration configuration."""

    twitch: NotRequired[Dict[str, Any]]  # Twitch integration config
    youtube: NotRequired[Dict[str, Any]]  # YouTube integration config
    discord: NotRequired[Dict[str, Any]]  # Discord integration config
    streamlabs: NotRequired[Dict[str, Any]]  # StreamLabs integration config
    custom_webhooks: NotRequired[List[str]]  # Custom webhook URLs


class PluginConfig(TypedDict):
    """Plugin configuration."""

    enabled_plugins: NotRequired[List[str]]  # Enabled plugin names
    plugin_paths: NotRequired[List[str]]  # Plugin search paths
    auto_load: NotRequired[bool]  # Auto-load plugins
    sandbox_mode: NotRequired[bool]  # Run plugins in sandbox


class OBSAgentConfig(BaseConfig):
    """Complete OBS Agent configuration."""

    obs: OBSConnectionConfig
    logging: NotRequired[LoggingConfig]
    streaming: NotRequired[StreamingConfig]
    recording: NotRequired[RecordingConfig]
    audio: NotRequired[AudioConfig]
    video: NotRequired[VideoConfig]
    automation: NotRequired[AutomationConfig]
    security: NotRequired[SecurityConfig]
    performance: NotRequired[PerformanceConfig]
    integrations: NotRequired[IntegrationConfig]
    plugins: NotRequired[PluginConfig]


# Runtime validation with Pydantic (optional dependency)
try:
    from pydantic import BaseModel, Field, validator
    from pydantic.types import PositiveInt, constr

    class OBSConnectionConfigModel(BaseModel):
        """Pydantic model for OBS connection configuration."""

        host: constr(min_length=1) = "localhost"
        port: PositiveInt = 4455
        password: str = ""
        timeout: float = Field(30.0, gt=0)
        reconnect_attempts: PositiveInt = 3
        reconnect_delay: float = Field(1.0, gt=0)

        @validator("host")
        def validate_host(cls, v):
            if not v or v.isspace():
                raise ValueError("Host cannot be empty")
            return v.strip()

    class LoggingConfigModel(BaseModel):
        """Pydantic model for logging configuration."""

        level: str = Field("INFO", regex=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
        format: Optional[str] = None
        file_path: Optional[str] = None
        max_file_size: PositiveInt = 10 * 1024 * 1024  # 10MB
        backup_count: PositiveInt = 5
        console_output: bool = True
        structured_logging: bool = False

    class StreamingConfigModel(BaseModel):
        """Pydantic model for streaming configuration."""

        service: Optional[str] = None
        server: Optional[str] = None
        key: Optional[str] = None
        video_bitrate: PositiveInt = 2500
        audio_bitrate: PositiveInt = 160
        fps: PositiveInt = Field(30, le=60)
        resolution: str = Field("1920x1080", regex=r"^\d+x\d+$")
        encoder: str = "x264"
        preset: str = "veryfast"
        profile: str = "main"
        keyframe_interval: PositiveInt = 2
        auto_start: bool = False
        auto_stop: bool = False

        @validator("resolution")
        def validate_resolution(cls, v):
            try:
                width, height = map(int, v.split("x"))
                if width < 1 or height < 1:
                    raise ValueError("Resolution dimensions must be positive")
                return v
            except ValueError:
                raise ValueError('Resolution must be in format "WIDTHxHEIGHT"')

    class RecordingConfigModel(BaseModel):
        """Pydantic model for recording configuration."""

        format: str = "mp4"
        quality: str = "high"
        encoder: str = "x264"
        path: str = "./recordings"
        filename_pattern: str = "%CCYY-%MM-%DD_%hh-%mm-%ss"
        auto_start: bool = False
        auto_stop: bool = False
        max_file_size: PositiveInt = 2048  # 2GB
        split_files: bool = True

    class AutomationConfigModel(BaseModel):
        """Pydantic model for automation configuration."""

        enabled: bool = True
        max_rules: PositiveInt = 100
        max_executions_per_minute: PositiveInt = 60
        rule_timeout: float = Field(30.0, gt=0)
        enable_error_recovery: bool = True
        persistence_path: str = "./automation_rules.json"
        metrics_enabled: bool = True

    class SecurityConfigModel(BaseModel):
        """Pydantic model for security configuration."""

        enable_authentication: bool = False
        api_key: Optional[str] = None
        allowed_hosts: List[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])
        rate_limit: PositiveInt = 100
        enable_encryption: bool = False
        cert_path: Optional[str] = None
        key_path: Optional[str] = None

        @validator("api_key")
        def validate_api_key(cls, v, values):
            if values.get("enable_authentication") and not v:
                raise ValueError("API key required when authentication is enabled")
            return v

    class OBSAgentConfigModel(BaseModel):
        """Complete Pydantic model for OBS Agent configuration."""

        obs: OBSConnectionConfigModel
        logging: LoggingConfigModel = Field(default_factory=LoggingConfigModel)
        streaming: StreamingConfigModel = Field(default_factory=StreamingConfigModel)
        recording: RecordingConfigModel = Field(default_factory=RecordingConfigModel)
        automation: AutomationConfigModel = Field(default_factory=AutomationConfigModel)
        security: SecurityConfigModel = Field(default_factory=SecurityConfigModel)

        class Config:
            extra = "forbid"  # Don't allow extra fields
            validate_assignment = True  # Validate on assignment

    # Type aliases for validated configs
    ValidatedOBSConfig = OBSConnectionConfigModel
    ValidatedLoggingConfig = LoggingConfigModel
    ValidatedStreamingConfig = StreamingConfigModel
    ValidatedRecordingConfig = RecordingConfigModel
    ValidatedAutomationConfig = AutomationConfigModel
    ValidatedSecurityConfig = SecurityConfigModel
    ValidatedOBSAgentConfig = OBSAgentConfigModel

except ImportError:
    # Pydantic not available, use None placeholders
    ValidatedOBSConfig = None
    ValidatedLoggingConfig = None
    ValidatedStreamingConfig = None
    ValidatedRecordingConfig = None
    ValidatedAutomationConfig = None
    ValidatedSecurityConfig = None
    ValidatedOBSAgentConfig = None


# Default configurations
DEFAULT_OBS_CONFIG: OBSConnectionConfig = {
    "host": "localhost",
    "port": 4455,
    "password": "",
    "timeout": 30.0,
    "reconnect_attempts": 3,
    "reconnect_delay": 1.0,
}

DEFAULT_LOGGING_CONFIG: LoggingConfig = {
    "level": "INFO",
    "console_output": True,
    "structured_logging": False,
}

DEFAULT_STREAMING_CONFIG: StreamingConfig = {
    "video_bitrate": 2500,
    "audio_bitrate": 160,
    "fps": 30,
    "resolution": "1920x1080",
    "encoder": "x264",
    "preset": "veryfast",
    "profile": "main",
    "keyframe_interval": 2,
    "auto_start": False,
    "auto_stop": False,
}

DEFAULT_RECORDING_CONFIG: RecordingConfig = {
    "format": "mp4",
    "quality": "high",
    "encoder": "x264",
    "path": "./recordings",
    "filename_pattern": "%CCYY-%MM-%DD_%hh-%mm-%ss",
    "auto_start": False,
    "auto_stop": False,
    "max_file_size": 2048,
    "split_files": True,
}

DEFAULT_AUTOMATION_CONFIG: AutomationConfig = {
    "enabled": True,
    "max_rules": 100,
    "max_executions_per_minute": 60,
    "rule_timeout": 30.0,
    "enable_error_recovery": True,
    "persistence_path": "./automation_rules.json",
    "metrics_enabled": True,
}

DEFAULT_SECURITY_CONFIG: SecurityConfig = {
    "enable_authentication": False,
    "allowed_hosts": ["localhost", "127.0.0.1"],
    "rate_limit": 100,
    "enable_encryption": False,
}

DEFAULT_PERFORMANCE_CONFIG: PerformanceConfig = {
    "max_connections": 10,
    "connection_pool_size": 5,
    "request_timeout": 30.0,
    "cache_ttl": 60.0,
    "enable_compression": True,
    "max_memory_usage": 512,
    "gc_threshold": 0.7,
}

DEFAULT_OBS_AGENT_CONFIG: OBSAgentConfig = {
    "version": "2.0.0",
    "created_at": 0.0,  # Will be set at runtime
    "obs": DEFAULT_OBS_CONFIG,
    "logging": DEFAULT_LOGGING_CONFIG,
    "streaming": DEFAULT_STREAMING_CONFIG,
    "recording": DEFAULT_RECORDING_CONFIG,
    "automation": DEFAULT_AUTOMATION_CONFIG,
    "security": DEFAULT_SECURITY_CONFIG,
    "performance": DEFAULT_PERFORMANCE_CONFIG,
}


# Configuration validation functions
def validate_config(config: Dict[str, Any]) -> Union[OBSAgentConfig, Dict[str, str]]:
    """
    Validate configuration dictionary.

    Args:
        config: Configuration dictionary to validate

    Returns:
        Validated configuration or validation errors
    """
    if ValidatedOBSAgentConfig is None:
        # Basic validation without Pydantic
        errors = {}

        # Check required fields
        if "obs" not in config:
            errors["obs"] = "OBS configuration is required"
        elif not isinstance(config["obs"], dict):
            errors["obs"] = "OBS configuration must be a dictionary"
        else:
            obs_config = config["obs"]
            if "host" not in obs_config:
                errors["obs.host"] = "Host is required"
            if "port" not in obs_config:
                errors["obs.port"] = "Port is required"
            elif not isinstance(obs_config["port"], int) or obs_config["port"] <= 0:
                errors["obs.port"] = "Port must be a positive integer"

        if errors:
            return errors

        return config  # type: ignore

    try:
        validated = ValidatedOBSAgentConfig(**config)
        return validated.dict()
    except Exception as e:
        return {"validation_error": str(e)}


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple configuration dictionaries.

    Args:
        *configs: Configuration dictionaries to merge

    Returns:
        Merged configuration dictionary
    """
    result = {}

    for config in configs:
        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_configs(result[key], value)
            else:
                result[key] = value

    return result
