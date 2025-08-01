"""
Unit tests for input validation module.
"""

import pytest
from pathlib import Path

from obs_agent.validation import (
    sanitize_string, validate_scene_name, validate_source_name,
    validate_filter_name, validate_port, validate_host,
    validate_file_path, validate_color, validate_resolution,
    validate_volume, validate_settings, validate_transition_duration,
    validate_fps, validate_bitrate, ValidationError
)


class TestStringSanitization:
    """Test string sanitization functions."""
    
    def test_sanitize_string_valid(self):
        """Test sanitizing valid strings."""
        assert sanitize_string("Valid Name") == "Valid Name"
        assert sanitize_string("  Trimmed  ") == "Trimmed"
        assert sanitize_string("Name-with_dots.txt") == "Name-with_dots.txt"
    
    def test_sanitize_string_empty(self):
        """Test sanitizing empty strings."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            sanitize_string("")
        
        with pytest.raises(ValidationError, match="cannot be empty"):
            sanitize_string("   ")
    
    def test_sanitize_string_too_long(self):
        """Test sanitizing strings that are too long."""
        long_string = "a" * 300
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            sanitize_string(long_string, max_length=256)
    
    def test_sanitize_string_dangerous_chars(self):
        """Test removal of dangerous characters."""
        assert sanitize_string("Name<script>") == "Namescript"
        assert sanitize_string("Name\0null") == "Namenull"
        assert sanitize_string("Line\nBreak") == "LineBreak"
    
    def test_sanitize_string_pattern_validation(self):
        """Test pattern validation."""
        import re
        alpha_pattern = re.compile(r'^[a-zA-Z]+$')
        
        assert sanitize_string("ValidName", pattern=alpha_pattern) == "ValidName"
        
        with pytest.raises(ValidationError, match="invalid characters"):
            sanitize_string("Invalid123", pattern=alpha_pattern)


class TestNameValidation:
    """Test name validation functions."""
    
    def test_validate_scene_name(self):
        """Test scene name validation."""
        assert validate_scene_name("My Scene") == "My Scene"
        assert validate_scene_name("Scene-1") == "Scene-1"
        assert validate_scene_name("Scene_2.backup") == "Scene_2.backup"
        
        with pytest.raises(ValidationError, match="Invalid scene name"):
            validate_scene_name("Scene@#$")
        
        with pytest.raises(ValidationError, match="Invalid scene name"):
            validate_scene_name("Scene/With/Slash")
    
    def test_validate_source_name(self):
        """Test source name validation."""
        assert validate_source_name("Microphone") == "Microphone"
        assert validate_source_name("Webcam 1") == "Webcam 1"
        
        with pytest.raises(ValidationError, match="Invalid source name"):
            validate_source_name("Source<>")
    
    def test_validate_filter_name(self):
        """Test filter name validation."""
        assert validate_filter_name("Color Correction") == "Color Correction"
        assert validate_filter_name("Chroma-Key_v2") == "Chroma-Key_v2"
        
        with pytest.raises(ValidationError, match="Invalid filter name"):
            validate_filter_name("Filter|Pipe")


class TestNetworkValidation:
    """Test network-related validation."""
    
    def test_validate_port(self):
        """Test port validation."""
        assert validate_port(4455) == 4455
        assert validate_port("8080") == 8080
        assert validate_port(1) == 1
        assert validate_port(65535) == 65535
        
        with pytest.raises(ValidationError, match="Port must be a number"):
            validate_port("abc")
        
        with pytest.raises(ValidationError, match="Port must be between"):
            validate_port(0)
        
        with pytest.raises(ValidationError, match="Port must be between"):
            validate_port(65536)
    
    def test_validate_host(self):
        """Test host validation."""
        assert validate_host("localhost") == "localhost"
        assert validate_host("192.168.1.1") == "192.168.1.1"
        assert validate_host("example.com") == "example.com"
        assert validate_host("sub.domain.com") == "sub.domain.com"
        
        with pytest.raises(ValidationError, match="Host cannot be empty"):
            validate_host("")
        
        with pytest.raises(ValidationError, match="Host name too long"):
            validate_host("a" * 254)
        
        with pytest.raises(ValidationError, match="Contains invalid characters"):
            validate_host("host with spaces")
        
        with pytest.raises(ValidationError, match="Contains invalid characters"):
            validate_host("host@invalid")


class TestFilePathValidation:
    """Test file path validation."""
    
    def test_validate_file_path_absolute(self, temp_dir):
        """Test absolute path validation."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")
        
        # Valid absolute path
        validated = validate_file_path(str(test_file), must_exist=True)
        assert validated == test_file
        
        # Non-existent path with must_exist=False
        non_existent = temp_dir / "missing.txt"
        validated = validate_file_path(str(non_existent), must_exist=False)
        assert validated == non_existent
        
        # Non-existent path with must_exist=True
        with pytest.raises(ValidationError, match="does not exist"):
            validate_file_path(str(non_existent), must_exist=True)
    
    def test_validate_file_path_relative(self):
        """Test relative path validation."""
        # Relative paths not allowed by default
        with pytest.raises(ValidationError, match="must be absolute"):
            validate_file_path("relative/path.txt")
        
        # Relative paths allowed with flag
        validated = validate_file_path("relative/path.txt", allow_relative=True)
        assert validated == Path("relative/path.txt")
        
        # Directory traversal prevention
        with pytest.raises(ValidationError, match="cannot contain"):
            validate_file_path("../../../etc/passwd", allow_relative=True)
    
    def test_validate_file_path_length(self):
        """Test path length validation."""
        long_path = "a" * 5000
        with pytest.raises(ValidationError, match="Path too long"):
            validate_file_path(long_path, allow_relative=True)


class TestColorValidation:
    """Test color validation."""
    
    def test_validate_color_hex_string(self):
        """Test hex string color validation."""
        assert validate_color("#FF0000") == 0xFF0000
        assert validate_color("00FF00") == 0x00FF00
        assert validate_color("#FFFFFF") == 0xFFFFFF
        assert validate_color("000000") == 0x000000
        
        # With alpha
        assert validate_color("#FF0000FF") == 0xFF0000FF
        assert validate_color("00FF00AA") == 0x00FF00AA
    
    def test_validate_color_integer(self):
        """Test integer color validation."""
        assert validate_color(0xFF0000) == 0xFF0000
        assert validate_color(0x00FF00) == 0x00FF00
        assert validate_color(0) == 0
        assert validate_color(0xFFFFFFFF) == 0xFFFFFFFF
        
        with pytest.raises(ValidationError, match="Invalid color value"):
            validate_color(-1)
        
        with pytest.raises(ValidationError, match="Invalid color value"):
            validate_color(0xFFFFFFFFF)  # Too large
    
    def test_validate_color_invalid(self):
        """Test invalid color validation."""
        with pytest.raises(ValidationError, match="Invalid color format"):
            validate_color("#GG0000")
        
        with pytest.raises(ValidationError, match="Invalid color format"):
            validate_color("red")
        
        with pytest.raises(ValidationError, match="must be string or integer"):
            validate_color(12.5)


class TestResolutionValidation:
    """Test resolution validation."""
    
    def test_validate_resolution_valid(self):
        """Test valid resolution validation."""
        assert validate_resolution("1920x1080") == (1920, 1080)
        assert validate_resolution("1280x720") == (1280, 720)
        assert validate_resolution("3840x2160") == (3840, 2160)
        assert validate_resolution("640x480") == (640, 480)
    
    def test_validate_resolution_invalid_format(self):
        """Test invalid resolution format."""
        with pytest.raises(ValidationError, match="Invalid resolution format"):
            validate_resolution("1920*1080")
        
        with pytest.raises(ValidationError, match="Invalid resolution format"):
            validate_resolution("1920x1080p")
        
        with pytest.raises(ValidationError, match="Invalid resolution format"):
            validate_resolution("FullHD")
    
    def test_validate_resolution_invalid_values(self):
        """Test invalid resolution values."""
        with pytest.raises(ValidationError, match="must be positive"):
            validate_resolution("0x1080")
        
        with pytest.raises(ValidationError, match="must be positive"):
            validate_resolution("1920x0")
        
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_resolution("8000x5000")


class TestVolumeValidation:
    """Test volume validation."""
    
    def test_validate_volume_multiplier(self):
        """Test volume multiplier validation."""
        assert validate_volume(1.0, as_db=False) == 1.0
        assert validate_volume(0.5, as_db=False) == 0.5
        assert validate_volume(0, as_db=False) == 0.0
        assert validate_volume(20.0, as_db=False) == 20.0
        
        with pytest.raises(ValidationError, match="must be between"):
            validate_volume(-0.1, as_db=False)
        
        with pytest.raises(ValidationError, match="must be between"):
            validate_volume(20.1, as_db=False)
    
    def test_validate_volume_decibels(self):
        """Test volume in decibels validation."""
        assert validate_volume(0, as_db=True) == 0.0
        assert validate_volume(-10.5, as_db=True) == -10.5
        assert validate_volume(20, as_db=True) == 20.0
        assert validate_volume(-100, as_db=True) == -100.0  # -inf allowed
        
        with pytest.raises(ValidationError, match="cannot exceed 20 dB"):
            validate_volume(20.1, as_db=True)
    
    def test_validate_volume_invalid_type(self):
        """Test invalid volume type."""
        with pytest.raises(ValidationError, match="must be a number"):
            validate_volume("loud", as_db=False)


class TestSettingsValidation:
    """Test settings dictionary validation."""
    
    def test_validate_settings_valid(self):
        """Test valid settings validation."""
        settings = {
            "key1": "value1",
            "key2": 123,
            "key3": True,
            "nested": {
                "subkey": "subvalue"
            }
        }
        validated = validate_settings(settings)
        assert validated == settings
    
    def test_validate_settings_dangerous_keys(self):
        """Test dangerous key detection."""
        with pytest.raises(ValidationError, match="dangerous key"):
            validate_settings({"__proto__": "value"})
        
        with pytest.raises(ValidationError, match="dangerous key"):
            validate_settings({"constructor": "value"})
    
    def test_validate_settings_allowed_keys(self):
        """Test allowed keys validation."""
        settings = {"allowed": "value", "also_allowed": 123}
        allowed = ["allowed", "also_allowed"]
        
        validated = validate_settings(settings, allowed_keys=allowed)
        assert validated == settings
        
        # Invalid key
        settings["not_allowed"] = "value"
        with pytest.raises(ValidationError, match="invalid keys"):
            validate_settings(settings, allowed_keys=allowed)
    
    def test_validate_settings_string_sanitization(self):
        """Test string value sanitization."""
        settings = {
            "clean": "value",
            "dirty": "value<script>alert('xss')</script>"
        }
        validated = validate_settings(settings)
        assert validated["clean"] == "value"
        assert "<script>" not in validated["dirty"]


class TestOtherValidations:
    """Test other validation functions."""
    
    def test_validate_transition_duration(self):
        """Test transition duration validation."""
        assert validate_transition_duration(1000) == 1000
        assert validate_transition_duration(0) == 0
        assert validate_transition_duration(60000) == 60000
        
        with pytest.raises(ValidationError, match="cannot be negative"):
            validate_transition_duration(-1)
        
        with pytest.raises(ValidationError, match="cannot exceed 60 seconds"):
            validate_transition_duration(60001)
    
    def test_validate_fps(self):
        """Test FPS validation."""
        assert validate_fps(30) == 30
        assert validate_fps(60) == 60
        assert validate_fps(1) == 1
        assert validate_fps(240) == 240
        
        with pytest.raises(ValidationError, match="must be between"):
            validate_fps(0)
        
        with pytest.raises(ValidationError, match="must be between"):
            validate_fps(241)
    
    def test_validate_bitrate(self):
        """Test bitrate validation."""
        assert validate_bitrate(2500) == 2500
        assert validate_bitrate(100) == 100
        assert validate_bitrate(50000) == 50000
        
        with pytest.raises(ValidationError, match="must be between"):
            validate_bitrate(99)
        
        with pytest.raises(ValidationError, match="must be between"):
            validate_bitrate(50001)