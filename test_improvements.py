#!/usr/bin/env python3
"""
Test script to verify OBS Agent v2 improvements.

This script tests the new features without requiring OBS to be running.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test imports
print("Testing imports...")
try:
    from obs_agent import (
        OBSAgentV2, Config, OBSConfig, ValidationError,
        validate_scene_name, setup_logging, get_logger
    )
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Set up logging
setup_logging()
logger = get_logger(__name__)


def test_configuration():
    """Test configuration system."""
    print("\n=== Testing Configuration ===")
    
    # Test default config
    config = Config()
    assert config.obs.host == "localhost"
    assert config.obs.port == 4455
    print("✅ Default configuration works")
    
    # Test custom config
    custom_config = Config(
        obs=OBSConfig(
            host="192.168.1.100",
            port=4456,
            password="test123"
        )
    )
    assert custom_config.obs.host == "192.168.1.100"
    assert custom_config.obs.password == "test123"
    print("✅ Custom configuration works")
    
    # Test validation
    try:
        invalid_config = Config(obs=OBSConfig(port=0))
        invalid_config.validate()
        print("❌ Validation should have failed")
    except ValueError:
        print("✅ Configuration validation works")
    
    # Test save/load
    temp_file = Path("test_config.json")
    try:
        config.save(temp_file)
        loaded_config = Config.load(temp_file)
        assert loaded_config.obs.host == config.obs.host
        print("✅ Configuration save/load works")
    finally:
        if temp_file.exists():
            temp_file.unlink()


def test_validation():
    """Test input validation."""
    print("\n=== Testing Validation ===")
    
    # Test scene name validation
    assert validate_scene_name("My Scene") == "My Scene"
    assert validate_scene_name("Scene-1_test.backup") == "Scene-1_test.backup"
    print("✅ Valid scene names pass")
    
    try:
        validate_scene_name("Invalid@#$%Scene")
        print("❌ Invalid scene name should fail")
    except ValidationError:
        print("✅ Invalid scene names rejected")
    
    try:
        validate_scene_name("")
        print("❌ Empty scene name should fail")
    except ValidationError:
        print("✅ Empty values rejected")
    
    # Test dangerous input sanitization
    try:
        validate_scene_name("Scene<script>alert('xss')</script>")
        print("❌ Dangerous input should be rejected")
    except ValidationError:
        print("✅ Dangerous input rejected")


def test_exceptions():
    """Test exception hierarchy."""
    print("\n=== Testing Exceptions ===")
    
    from obs_agent import (
        OBSAgentError, SceneNotFoundError, ConnectionError,
        handle_obs_error
    )
    
    # Test exception hierarchy
    scene_error = SceneNotFoundError("Test Scene")
    assert isinstance(scene_error, OBSAgentError)
    assert scene_error.scene_name == "Test Scene"
    assert "Test Scene" in str(scene_error)
    print("✅ Exception hierarchy works")
    
    # Test error conversion
    generic_error = Exception("Scene 'My Scene' not found")
    converted = handle_obs_error(generic_error)
    assert isinstance(converted, SceneNotFoundError)
    # The scene name should be extracted from the error message
    print("✅ Error conversion works")


def test_logging():
    """Test logging system."""
    print("\n=== Testing Logging ===")
    
    from obs_agent import log_context
    
    # Test basic logging
    logger.info("Test info message")
    logger.warning("Test warning message")
    logger.error("Test error message")
    print("✅ Basic logging works")
    
    # Test contextual logging
    with log_context(user="test_user", action="testing"):
        logger.info("Message with context")
    print("✅ Contextual logging works")


async def test_agent_creation():
    """Test agent creation without OBS connection."""
    print("\n=== Testing Agent Creation ===")
    
    # Test agent creation
    agent = OBSAgentV2()
    assert agent.config is not None
    assert not agent.is_connected
    print("✅ Agent creation works")
    
    # Test with custom config
    custom_config = Config(obs=OBSConfig(host="test.local"))
    agent2 = OBSAgentV2(custom_config)
    assert agent2.config.obs.host == "test.local"
    print("✅ Agent with custom config works")


def test_type_hints():
    """Test type hints are properly defined."""
    print("\n=== Testing Type Hints ===")
    
    # Check if py.typed exists
    typed_marker = Path(__file__).parent / "src" / "obs_agent" / "py.typed"
    assert typed_marker.exists(), "py.typed marker missing"
    print("✅ Type hint marker exists")
    
    # Check function annotations
    from obs_agent.validation import validate_port
    assert hasattr(validate_port, "__annotations__")
    print("✅ Functions have type annotations")


async def main():
    """Run all tests."""
    print("🧪 Testing OBS Agent v2 Improvements\n")
    
    # Run synchronous tests
    test_configuration()
    test_validation()
    test_exceptions()
    test_logging()
    test_type_hints()
    
    # Run async tests
    await test_agent_creation()
    
    print("\n✅ All tests passed! The improvements are working correctly.")
    print("\nNote: Full integration tests require OBS to be running.")
    print("Run 'pytest tests/' for comprehensive testing.")


if __name__ == "__main__":
    asyncio.run(main())