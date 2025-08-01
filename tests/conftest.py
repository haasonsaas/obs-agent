"""
Pytest configuration and fixtures for OBS Agent tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from pathlib import Path
import tempfile
import shutil

from obs_agent.config import Config, OBSConfig, StreamingConfig, LoggingConfig
from obs_agent.connection import ConnectionManager
from obs_agent.obs_agent_v2 import OBSAgent


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config() -> Config:
    """Create test configuration."""
    return Config(
        obs=OBSConfig(
            host="localhost",
            port=4455,
            password="test_password",
            timeout=5.0,
            reconnect_interval=1.0,
            max_reconnect_attempts=2
        ),
        streaming=StreamingConfig(
            default_bitrate=2500,
            default_fps=30,
            default_resolution="1920x1080"
        ),
        logging=LoggingConfig(
            level="DEBUG",
            file_path=None
        ),
        enable_auto_reconnect=False,
        enable_event_logging=False,
        enable_performance_monitoring=False
    )


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_obsws():
    """Mock obs-websocket connection."""
    with patch('obs_agent.connection.obsws') as mock:
        # Create mock instance
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        
        # Mock connection methods
        mock_instance.connect = MagicMock()
        mock_instance.disconnect = MagicMock()
        mock_instance.call = MagicMock()
        
        yield mock_instance


@pytest.fixture
def mock_connection_manager(mock_obsws):
    """Mock connection manager."""
    manager = ConnectionManager()
    manager._connection = mock_obsws
    manager._connected = True
    manager._config = OBSConfig()
    return manager


@pytest.fixture
async def mock_obs_agent(test_config, mock_connection_manager) -> AsyncGenerator[OBSAgent, None]:
    """Create mock OBS Agent."""
    with patch('obs_agent.obs_agent_v2.get_connection_manager', return_value=mock_connection_manager):
        agent = OBSAgent(test_config)
        yield agent


# Mock responses for common OBS requests

@pytest.fixture
def mock_version_response():
    """Mock GetVersion response."""
    response = MagicMock()
    response.datain = {
        "obsVersion": "29.0.0",
        "obsWebSocketVersion": "5.1.0",
        "platform": "macos",
        "platformDescription": "macOS 13.0"
    }
    return response


@pytest.fixture
def mock_scene_list_response():
    """Mock GetSceneList response."""
    response = MagicMock()
    response.datain = {
        "currentProgramSceneName": "Scene 1",
        "currentPreviewSceneName": "Scene 2",
        "scenes": [
            {"sceneName": "Scene 1", "sceneIndex": 0},
            {"sceneName": "Scene 2", "sceneIndex": 1},
            {"sceneName": "Scene 3", "sceneIndex": 2}
        ]
    }
    return response


@pytest.fixture
def mock_source_list_response():
    """Mock GetInputList response."""
    response = MagicMock()
    response.datain = {
        "inputs": [
            {
                "inputName": "Microphone",
                "inputKind": "wasapi_input_capture",
                "inputSettings": {"device_id": "default"}
            },
            {
                "inputName": "Webcam",
                "inputKind": "dshow_input",
                "inputSettings": {"video_device_id": "0"}
            },
            {
                "inputName": "Screen Capture",
                "inputKind": "monitor_capture",
                "inputSettings": {"monitor": 0}
            }
        ]
    }
    return response


@pytest.fixture
def mock_stream_status_response():
    """Mock GetStreamStatus response."""
    response = MagicMock()
    response.datain = {
        "outputActive": True,
        "outputDuration": 1234567,
        "outputBytes": 123456789,
        "outputSkippedFrames": 5,
        "outputTotalFrames": 73800
    }
    return response


@pytest.fixture
def mock_record_status_response():
    """Mock GetRecordStatus response."""
    response = MagicMock()
    response.datain = {
        "outputActive": True,
        "outputPaused": False,
        "outputDuration": 600000,
        "outputBytes": 50000000
    }
    return response


# Helper functions for tests

def create_mock_response(data: Dict[str, Any]):
    """Create a mock OBS response."""
    response = MagicMock()
    response.datain = data
    return response


def create_mock_error(error_type: str, message: str):
    """Create a mock OBS error."""
    error = Exception(message)
    error.__class__.__name__ = error_type
    return error


# Async helpers

async def async_return(value):
    """Helper to return async value."""
    return value


# Test data

TEST_SCENES = ["Scene 1", "Scene 2", "Scene 3"]
TEST_SOURCES = ["Microphone", "Webcam", "Screen Capture"]
TEST_TRANSITIONS = ["Fade", "Cut", "Slide", "Stinger"]