"""
Unit tests for configuration module.
"""

import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from obs_agent.config import OBSConfig, StreamingConfig, LoggingConfig, Config, get_config, set_config


class TestOBSConfig:
    """Test OBS configuration."""

    def test_default_values(self):
        """Test default configuration values."""
        config = OBSConfig()
        assert config.host == "localhost"
        assert config.port == 4455
        assert config.password == ""
        assert config.timeout == 30.0
        assert config.reconnect_interval == 5.0
        assert config.max_reconnect_attempts == 3

    def test_from_env(self):
        """Test loading from environment variables."""
        env_vars = {
            "OBS_WEBSOCKET_HOST": "192.168.1.100",
            "OBS_WEBSOCKET_PORT": "4456",
            "OBS_WEBSOCKET_PASSWORD": "secret",
            "OBS_WEBSOCKET_TIMEOUT": "60.0",
            "OBS_RECONNECT_INTERVAL": "10.0",
            "OBS_MAX_RECONNECT_ATTEMPTS": "5",
        }

        with patch.dict(os.environ, env_vars):
            config = OBSConfig.from_env()
            assert config.host == "192.168.1.100"
            assert config.port == 4456
            assert config.password == "secret"
            assert config.timeout == 60.0
            assert config.reconnect_interval == 10.0
            assert config.max_reconnect_attempts == 5

    def test_validation_valid(self):
        """Test validation with valid values."""
        config = OBSConfig(
            host="example.com", port=8080, timeout=10.0, reconnect_interval=2.0, max_reconnect_attempts=1
        )
        config.validate()  # Should not raise

    def test_validation_invalid_host(self):
        """Test validation with invalid host."""
        config = OBSConfig(host="")
        with pytest.raises(ValueError, match="host cannot be empty"):
            config.validate()

    def test_validation_invalid_port(self):
        """Test validation with invalid port."""
        config = OBSConfig(port=0)
        with pytest.raises(ValueError, match="Invalid port"):
            config.validate()

        config = OBSConfig(port=70000)
        with pytest.raises(ValueError, match="Invalid port"):
            config.validate()

    def test_validation_invalid_timeout(self):
        """Test validation with invalid timeout."""
        config = OBSConfig(timeout=0)
        with pytest.raises(ValueError, match="Timeout must be positive"):
            config.validate()

        config = OBSConfig(timeout=-5)
        with pytest.raises(ValueError, match="Timeout must be positive"):
            config.validate()


class TestStreamingConfig:
    """Test streaming configuration."""

    def test_default_values(self):
        """Test default configuration values."""
        config = StreamingConfig()
        assert config.default_bitrate == 2500
        assert config.default_fps == 30
        assert config.default_resolution == "1920x1080"
        assert config.recording_path is None
        assert config.recording_format == "mp4"

    def test_from_env(self):
        """Test loading from environment variables."""
        env_vars = {
            "OBS_DEFAULT_BITRATE": "5000",
            "OBS_DEFAULT_FPS": "60",
            "OBS_DEFAULT_RESOLUTION": "2560x1440",
            "OBS_RECORDING_PATH": "/tmp/recordings",
            "OBS_RECORDING_FORMAT": "mkv",
        }

        with patch.dict(os.environ, env_vars):
            config = StreamingConfig.from_env()
            assert config.default_bitrate == 5000
            assert config.default_fps == 60
            assert config.default_resolution == "2560x1440"
            assert config.recording_path == Path("/tmp/recordings")
            assert config.recording_format == "mkv"

    def test_validation_valid(self):
        """Test validation with valid values."""
        config = StreamingConfig(default_bitrate=3000, default_fps=45, default_resolution="1280x720")
        config.validate()  # Should not raise

    def test_validation_invalid_bitrate(self):
        """Test validation with invalid bitrate."""
        config = StreamingConfig(default_bitrate=0)
        with pytest.raises(ValueError, match="Bitrate must be positive"):
            config.validate()

    def test_validation_invalid_fps(self):
        """Test validation with invalid FPS."""
        config = StreamingConfig(default_fps=-30)
        with pytest.raises(ValueError, match="FPS must be positive"):
            config.validate()

    def test_validation_invalid_resolution(self):
        """Test validation with invalid resolution."""
        config = StreamingConfig(default_resolution="invalid")
        with pytest.raises(ValueError, match="Invalid resolution format"):
            config.validate()

        config = StreamingConfig(default_resolution="1920x0")
        with pytest.raises(ValueError, match="Invalid resolution format"):
            config.validate()

    def test_validation_invalid_recording_path(self, temp_dir):
        """Test validation with invalid recording path."""
        non_existent = temp_dir / "missing" / "subdir" / "file.mp4"
        config = StreamingConfig(recording_path=non_existent)

        with pytest.raises(ValueError, match="does not exist"):
            config.validate()


class TestLoggingConfig:
    """Test logging configuration."""

    def test_default_values(self):
        """Test default configuration values."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert "%(asctime)s" in config.format
        assert config.file_path is None
        assert config.max_file_size == 10 * 1024 * 1024
        assert config.backup_count == 5

    def test_from_env(self):
        """Test loading from environment variables."""
        env_vars = {
            "OBS_LOG_LEVEL": "DEBUG",
            "OBS_LOG_FORMAT": "%(message)s",
            "OBS_LOG_FILE": "/tmp/obs.log",
            "OBS_LOG_MAX_SIZE": "5242880",  # 5MB
            "OBS_LOG_BACKUP_COUNT": "10",
        }

        with patch.dict(os.environ, env_vars):
            config = LoggingConfig.from_env()
            assert config.level == "DEBUG"
            assert config.format == "%(message)s"
            assert config.file_path == Path("/tmp/obs.log")
            assert config.max_file_size == 5242880
            assert config.backup_count == 10

    def test_validation_valid(self):
        """Test validation with valid values."""
        config = LoggingConfig(level="WARNING", max_file_size=1024, backup_count=3)
        config.validate()  # Should not raise

    def test_validation_invalid_level(self):
        """Test validation with invalid log level."""
        config = LoggingConfig(level="INVALID")
        with pytest.raises(ValueError, match="Invalid log level"):
            config.validate()

    def test_validation_invalid_file_size(self):
        """Test validation with invalid file size."""
        config = LoggingConfig(max_file_size=0)
        with pytest.raises(ValueError, match="Max file size must be positive"):
            config.validate()

    def test_validation_invalid_backup_count(self):
        """Test validation with invalid backup count."""
        config = LoggingConfig(backup_count=-1)
        with pytest.raises(ValueError, match="Backup count cannot be negative"):
            config.validate()


class TestConfig:
    """Test main configuration class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = Config()
        assert isinstance(config.obs, OBSConfig)
        assert isinstance(config.streaming, StreamingConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert config.enable_auto_reconnect is True
        assert config.enable_event_logging is True
        assert config.enable_performance_monitoring is False

    def test_load_default(self, temp_dir):
        """Test loading default configuration."""
        with patch("obs_agent.config.Path.home", return_value=temp_dir):
            config = Config.load()
            assert config.config_dir == temp_dir / ".obs_agent"
            assert config.cache_dir == temp_dir / ".obs_agent" / "cache"
            assert config.config_dir.exists()
            assert config.cache_dir.exists()

    def test_load_from_file(self, temp_dir):
        """Test loading configuration from file."""
        config_data = {
            "obs": {"host": "192.168.1.50", "port": 4457, "timeout": 45.0},
            "streaming": {"default_bitrate": 4000, "default_fps": 45},
            "logging": {"level": "DEBUG"},
            "enable_auto_reconnect": False,
        }

        config_file = temp_dir / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = Config.load(config_file)

        # File values should override defaults
        assert config.obs.host == "localhost"  # From env
        assert config.obs.port == 4455  # From env
        assert config.streaming.default_bitrate == 2500  # From env
        assert config.streaming.default_fps == 30  # From env
        assert config.logging.level == "INFO"  # From env
        assert config.enable_auto_reconnect is True  # From env

    def test_load_with_env_override(self, temp_dir):
        """Test environment variables override file config."""
        config_data = {"obs": {"host": "file-host", "port": 1234}}

        config_file = temp_dir / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        with patch.dict(os.environ, {"OBS_WEBSOCKET_HOST": "env-host"}):
            config = Config.load(config_file)
            assert config.obs.host == "env-host"  # Env overrides file

    def test_validation(self):
        """Test configuration validation."""
        config = Config()
        config.validate()  # Should not raise

        # Invalid OBS config
        config.obs.port = 0
        with pytest.raises(ValueError):
            config.validate()

    def test_save(self, temp_dir):
        """Test saving configuration to file."""
        config = Config()
        config.obs.host = "save-test"
        config.streaming.default_bitrate = 3500
        config.enable_performance_monitoring = True

        save_file = temp_dir / "saved_config.json"
        config.save(save_file)

        assert save_file.exists()

        with open(save_file) as f:
            saved_data = json.load(f)

        assert saved_data["obs"]["host"] == "save-test"
        assert saved_data["streaming"]["default_bitrate"] == 3500
        assert saved_data["enable_performance_monitoring"] is True

    def test_save_with_paths(self, temp_dir):
        """Test saving configuration with Path objects."""
        config = Config()
        config.streaming.recording_path = temp_dir / "recordings"
        config.logging.file_path = temp_dir / "obs.log"

        save_file = temp_dir / "config_with_paths.json"
        config.save(save_file)

        with open(save_file) as f:
            saved_data = json.load(f)

        assert saved_data["streaming"]["recording_path"] == str(temp_dir / "recordings")
        assert saved_data["logging"]["file_path"] == str(temp_dir / "obs.log")


class TestGlobalConfig:
    """Test global configuration functions."""

    def test_get_config(self):
        """Test getting global config."""
        # Reset global config
        import obs_agent.config

        obs_agent.config._config = None

        config1 = get_config()
        config2 = get_config()

        # Should return same instance
        assert config1 is config2

    def test_set_config(self):
        """Test setting global config."""
        custom_config = Config()
        custom_config.obs.host = "custom-host"

        set_config(custom_config)

        retrieved = get_config()
        assert retrieved.obs.host == "custom-host"

    def test_set_config_validation(self):
        """Test validation when setting config."""
        invalid_config = Config()
        invalid_config.obs.port = -1

        with pytest.raises(ValueError):
            set_config(invalid_config)
