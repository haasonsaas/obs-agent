"""
Configuration management for OBS Agent.

This module provides centralized configuration with validation,
environment variable support, and type safety.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class OBSConfig:
    """OBS WebSocket connection configuration."""

    host: str = "localhost"
    port: int = 4455
    password: str = ""
    timeout: float = 30.0
    reconnect_interval: float = 5.0
    max_reconnect_attempts: int = 3

    @classmethod
    def from_env(cls) -> "OBSConfig":
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("OBS_WEBSOCKET_HOST", "localhost"),
            port=int(os.getenv("OBS_WEBSOCKET_PORT", "4455")),
            password=os.getenv("OBS_WEBSOCKET_PASSWORD", ""),
            timeout=float(os.getenv("OBS_WEBSOCKET_TIMEOUT", "30.0")),
            reconnect_interval=float(os.getenv("OBS_RECONNECT_INTERVAL", "5.0")),
            max_reconnect_attempts=int(os.getenv("OBS_MAX_RECONNECT_ATTEMPTS", "3")),
        )

    def validate(self) -> None:
        """Validate configuration values."""
        if not self.host:
            raise ValueError("OBS host cannot be empty")

        if not 1 <= self.port <= 65535:
            raise ValueError(f"Invalid port number: {self.port}")

        if self.timeout <= 0:
            raise ValueError(f"Timeout must be positive: {self.timeout}")

        if self.reconnect_interval <= 0:
            raise ValueError(f"Reconnect interval must be positive: {self.reconnect_interval}")

        if self.max_reconnect_attempts < 0:
            raise ValueError(f"Max reconnect attempts cannot be negative: {self.max_reconnect_attempts}")


@dataclass
class StreamingConfig:
    """Streaming-specific configuration."""

    default_bitrate: int = 2500
    default_fps: int = 30
    default_resolution: str = "1920x1080"
    recording_path: Optional[Path] = None
    recording_format: str = "mp4"

    @classmethod
    def from_env(cls) -> "StreamingConfig":
        """Create configuration from environment variables."""
        recording_path = os.getenv("OBS_RECORDING_PATH")
        return cls(
            default_bitrate=int(os.getenv("OBS_DEFAULT_BITRATE", "2500")),
            default_fps=int(os.getenv("OBS_DEFAULT_FPS", "30")),
            default_resolution=os.getenv("OBS_DEFAULT_RESOLUTION", "1920x1080"),
            recording_path=Path(recording_path) if recording_path else None,
            recording_format=os.getenv("OBS_RECORDING_FORMAT", "mp4"),
        )

    def validate(self) -> None:
        """Validate streaming configuration."""
        if self.default_bitrate <= 0:
            raise ValueError(f"Bitrate must be positive: {self.default_bitrate}")

        if self.default_fps <= 0:
            raise ValueError(f"FPS must be positive: {self.default_fps}")

        # Validate resolution format
        try:
            width, height = self.default_resolution.split("x")
            if int(width) <= 0 or int(height) <= 0:
                raise ValueError
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid resolution format: {self.default_resolution}. Use WIDTHxHEIGHT")

        if self.recording_path and not self.recording_path.parent.exists():
            raise ValueError(f"Recording path parent directory does not exist: {self.recording_path.parent}")


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[Path] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Create configuration from environment variables."""
        file_path = os.getenv("OBS_LOG_FILE")
        return cls(
            level=os.getenv("OBS_LOG_LEVEL", "INFO"),
            format=os.getenv("OBS_LOG_FORMAT", cls.format),
            file_path=Path(file_path) if file_path else None,
            max_file_size=int(os.getenv("OBS_LOG_MAX_SIZE", str(10 * 1024 * 1024))),
            backup_count=int(os.getenv("OBS_LOG_BACKUP_COUNT", "5")),
        )

    def validate(self) -> None:
        """Validate logging configuration."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {self.level}. Must be one of {valid_levels}")

        if self.max_file_size <= 0:
            raise ValueError(f"Max file size must be positive: {self.max_file_size}")

        if self.backup_count < 0:
            raise ValueError(f"Backup count cannot be negative: {self.backup_count}")


@dataclass
class Config:
    """Main configuration container."""

    obs: OBSConfig = field(default_factory=OBSConfig)
    streaming: StreamingConfig = field(default_factory=StreamingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Feature flags
    enable_auto_reconnect: bool = True
    enable_event_logging: bool = True
    enable_performance_monitoring: bool = False

    # Paths
    config_dir: Path = Path.home() / ".obs_agent"
    cache_dir: Path = Path.home() / ".obs_agent" / "cache"

    @classmethod
    def load(cls, config_file: Optional[Path] = None) -> "Config":
        """
        Load configuration from file and environment variables.

        Priority order:
        1. Environment variables (highest)
        2. Config file
        3. Default values (lowest)
        """
        config = cls()

        # Load from config file if provided
        if config_file and config_file.exists():
            try:
                with open(config_file, "r") as f:
                    data = json.load(f)

                # Update OBS config
                if "obs" in data:
                    for key, value in data["obs"].items():
                        if hasattr(config.obs, key):
                            setattr(config.obs, key, value)

                # Update streaming config
                if "streaming" in data:
                    for key, value in data["streaming"].items():
                        if hasattr(config.streaming, key):
                            if key == "recording_path" and value:
                                value = Path(value)
                            setattr(config.streaming, key, value)

                # Update logging config
                if "logging" in data:
                    for key, value in data["logging"].items():
                        if hasattr(config.logging, key):
                            if key == "file_path" and value:
                                value = Path(value)
                            setattr(config.logging, key, value)

                # Update feature flags
                for key in ["enable_auto_reconnect", "enable_event_logging", "enable_performance_monitoring"]:
                    if key in data:
                        setattr(config, key, data[key])

                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")

        # Override with environment variables
        config.obs = OBSConfig.from_env()
        config.streaming = StreamingConfig.from_env()
        config.logging = LoggingConfig.from_env()

        # Load feature flags from environment
        config.enable_auto_reconnect = os.getenv("OBS_ENABLE_AUTO_RECONNECT", "true").lower() == "true"
        config.enable_event_logging = os.getenv("OBS_ENABLE_EVENT_LOGGING", "true").lower() == "true"
        config.enable_performance_monitoring = os.getenv("OBS_ENABLE_PERFORMANCE_MONITORING", "false").lower() == "true"

        # Create directories if they don't exist
        config.config_dir.mkdir(parents=True, exist_ok=True)
        config.cache_dir.mkdir(parents=True, exist_ok=True)

        return config

    def validate(self) -> None:
        """Validate all configuration sections."""
        self.obs.validate()
        self.streaming.validate()
        self.logging.validate()

    def save(self, config_file: Path) -> None:
        """Save configuration to file."""
        data = {
            "obs": {
                "host": self.obs.host,
                "port": self.obs.port,
                "timeout": self.obs.timeout,
                "reconnect_interval": self.obs.reconnect_interval,
                "max_reconnect_attempts": self.obs.max_reconnect_attempts,
            },
            "streaming": {
                "default_bitrate": self.streaming.default_bitrate,
                "default_fps": self.streaming.default_fps,
                "default_resolution": self.streaming.default_resolution,
                "recording_path": str(self.streaming.recording_path) if self.streaming.recording_path else None,
                "recording_format": self.streaming.recording_format,
            },
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format,
                "file_path": str(self.logging.file_path) if self.logging.file_path else None,
                "max_file_size": self.logging.max_file_size,
                "backup_count": self.logging.backup_count,
            },
            "enable_auto_reconnect": self.enable_auto_reconnect,
            "enable_event_logging": self.enable_event_logging,
            "enable_performance_monitoring": self.enable_performance_monitoring,
        }

        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved configuration to {config_file}")


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.load()
        try:
            _config.validate()
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    config.validate()
    _config = config
