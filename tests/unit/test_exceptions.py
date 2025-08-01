"""
Unit tests for exceptions module.
"""

import pytest

from obs_agent.exceptions import (
    OBSAgentError, ConnectionError, AuthenticationError,
    ConfigurationError, ValidationError, SceneError,
    SceneNotFoundError, SceneAlreadyExistsError,
    SourceError, SourceNotFoundError, SourceAlreadyExistsError,
    StreamingError, StreamAlreadyActiveError, StreamNotActiveError,
    RecordingError, RecordingAlreadyActiveError, RecordingNotActiveError,
    FilterError, FilterNotFoundError, FilterAlreadyExistsError,
    WebSocketError, RequestTimeoutError, InvalidRequestError,
    PermissionError, ResourceLimitError, PerformanceWarning,
    handle_obs_error
)


class TestBaseExceptions:
    """Test base exception classes."""
    
    def test_obs_agent_error(self):
        """Test OBSAgentError base class."""
        error = OBSAgentError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}
        
        # With details
        error = OBSAgentError("Test error", {"key": "value", "code": 123})
        assert str(error) == "Test error (key=value, code=123)"
        assert error.details == {"key": "value", "code": 123}
    
    def test_connection_error(self):
        """Test ConnectionError."""
        error = ConnectionError("Connection failed")
        assert isinstance(error, OBSAgentError)
        assert str(error) == "Connection failed"
    
    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Invalid password")
        assert isinstance(error, ConnectionError)
        assert isinstance(error, OBSAgentError)
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Invalid config")
        assert isinstance(error, OBSAgentError)
    
    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid input")
        assert isinstance(error, OBSAgentError)


class TestSceneExceptions:
    """Test scene-related exceptions."""
    
    def test_scene_error(self):
        """Test SceneError base class."""
        error = SceneError("Scene error")
        assert isinstance(error, OBSAgentError)
    
    def test_scene_not_found_error(self):
        """Test SceneNotFoundError."""
        error = SceneNotFoundError("My Scene")
        assert isinstance(error, SceneError)
        assert str(error) == "Scene not found: My Scene (scene_name=My Scene)"
        assert error.scene_name == "My Scene"
        assert error.details["scene_name"] == "My Scene"
    
    def test_scene_already_exists_error(self):
        """Test SceneAlreadyExistsError."""
        error = SceneAlreadyExistsError("Existing Scene")
        assert isinstance(error, SceneError)
        assert str(error) == "Scene already exists: Existing Scene (scene_name=Existing Scene)"
        assert error.scene_name == "Existing Scene"


class TestSourceExceptions:
    """Test source-related exceptions."""
    
    def test_source_error(self):
        """Test SourceError base class."""
        error = SourceError("Source error")
        assert isinstance(error, OBSAgentError)
    
    def test_source_not_found_error(self):
        """Test SourceNotFoundError."""
        error = SourceNotFoundError("Microphone")
        assert isinstance(error, SourceError)
        assert str(error) == "Source not found: Microphone (source_name=Microphone)"
        assert error.source_name == "Microphone"
    
    def test_source_already_exists_error(self):
        """Test SourceAlreadyExistsError."""
        error = SourceAlreadyExistsError("Webcam")
        assert isinstance(error, SourceError)
        assert str(error) == "Source already exists: Webcam (source_name=Webcam)"
        assert error.source_name == "Webcam"


class TestStreamingExceptions:
    """Test streaming-related exceptions."""
    
    def test_streaming_error(self):
        """Test StreamingError base class."""
        error = StreamingError("Streaming error")
        assert isinstance(error, OBSAgentError)
    
    def test_stream_already_active_error(self):
        """Test StreamAlreadyActiveError."""
        error = StreamAlreadyActiveError("Stream is already active")
        assert isinstance(error, StreamingError)
    
    def test_stream_not_active_error(self):
        """Test StreamNotActiveError."""
        error = StreamNotActiveError("Stream is not active")
        assert isinstance(error, StreamingError)


class TestRecordingExceptions:
    """Test recording-related exceptions."""
    
    def test_recording_error(self):
        """Test RecordingError base class."""
        error = RecordingError("Recording error")
        assert isinstance(error, OBSAgentError)
    
    def test_recording_already_active_error(self):
        """Test RecordingAlreadyActiveError."""
        error = RecordingAlreadyActiveError("Recording is already active")
        assert isinstance(error, RecordingError)
    
    def test_recording_not_active_error(self):
        """Test RecordingNotActiveError."""
        error = RecordingNotActiveError("Recording is not active")
        assert isinstance(error, RecordingError)


class TestFilterExceptions:
    """Test filter-related exceptions."""
    
    def test_filter_error(self):
        """Test FilterError base class."""
        error = FilterError("Filter error")
        assert isinstance(error, OBSAgentError)
    
    def test_filter_not_found_error(self):
        """Test FilterNotFoundError."""
        error = FilterNotFoundError("Chroma Key", "Webcam")
        assert isinstance(error, FilterError)
        assert "Chroma Key" in str(error)
        assert "Webcam" in str(error)
        assert error.filter_name == "Chroma Key"
        assert error.source_name == "Webcam"
    
    def test_filter_already_exists_error(self):
        """Test FilterAlreadyExistsError."""
        error = FilterAlreadyExistsError("Color Correction", "Screen")
        assert isinstance(error, FilterError)
        assert "Color Correction" in str(error)
        assert "Screen" in str(error)
        assert error.filter_name == "Color Correction"
        assert error.source_name == "Screen"


class TestWebSocketExceptions:
    """Test WebSocket-related exceptions."""
    
    def test_websocket_error(self):
        """Test WebSocketError base class."""
        error = WebSocketError("WebSocket error")
        assert isinstance(error, OBSAgentError)
    
    def test_request_timeout_error(self):
        """Test RequestTimeoutError."""
        error = RequestTimeoutError("GetSceneList", 30.0)
        assert isinstance(error, WebSocketError)
        assert "GetSceneList" in str(error)
        assert "30" in str(error)
        assert error.request_type == "GetSceneList"
        assert error.timeout == 30.0
    
    def test_invalid_request_error(self):
        """Test InvalidRequestError."""
        error = InvalidRequestError("Invalid request")
        assert isinstance(error, WebSocketError)


class TestOtherExceptions:
    """Test other exception types."""
    
    def test_permission_error(self):
        """Test PermissionError."""
        error = PermissionError("Access denied")
        assert isinstance(error, OBSAgentError)
    
    def test_resource_limit_error(self):
        """Test ResourceLimitError."""
        error = ResourceLimitError("Too many sources")
        assert isinstance(error, OBSAgentError)
    
    def test_performance_warning(self):
        """Test PerformanceWarning."""
        error = PerformanceWarning("CPU Usage", 95.5, 80.0)
        assert isinstance(error, OBSAgentError)
        assert "CPU Usage" in str(error)
        assert "95.5" in str(error)
        assert "80" in str(error)
        assert error.metric == "CPU Usage"
        assert error.value == 95.5
        assert error.threshold == 80.0


class TestHandleOBSError:
    """Test error conversion function."""
    
    def test_handle_connection_errors(self):
        """Test handling connection-related errors."""
        # Connection refused
        error = Exception("Connection refused")
        result = handle_obs_error(error)
        assert isinstance(result, ConnectionError)
        assert "refused" in str(result)
        
        # Connection timeout
        error = Exception("Connection timeout")
        result = handle_obs_error(error)
        assert isinstance(result, ConnectionError)
        assert "timeout" in str(result)
        
        # Connection closed
        error = Exception("Connection closed")
        result = handle_obs_error(error)
        assert isinstance(result, ConnectionError)
        assert "closed" in str(result)
    
    def test_handle_authentication_errors(self):
        """Test handling authentication errors."""
        error = Exception("Authentication failed")
        result = handle_obs_error(error)
        assert isinstance(result, AuthenticationError)
        
        error = Exception("Invalid password")
        result = handle_obs_error(error)
        assert isinstance(result, AuthenticationError)
    
    def test_handle_scene_errors(self):
        """Test handling scene errors."""
        # Scene not found
        error = Exception("Scene 'My Scene' not found")
        result = handle_obs_error(error)
        assert isinstance(result, SceneNotFoundError)
        assert result.scene_name == "My Scene"
        
        # Scene already exists
        error = Exception("Scene 'New Scene' already exists")
        result = handle_obs_error(error)
        assert isinstance(result, SceneAlreadyExistsError)
        assert result.scene_name == "New Scene"
    
    def test_handle_source_errors(self):
        """Test handling source errors."""
        # Source not found
        error = Exception("Source 'Webcam' does not exist")
        result = handle_obs_error(error)
        assert isinstance(result, SourceNotFoundError)
        assert result.source_name == "Webcam"
        
        # Input not found (alternative wording)
        error = Exception("Input 'Microphone' not found")
        result = handle_obs_error(error)
        assert isinstance(result, SourceNotFoundError)
        assert result.source_name == "Microphone"
    
    def test_handle_streaming_errors(self):
        """Test handling streaming errors."""
        # Already streaming
        error = Exception("Stream already active")
        result = handle_obs_error(error)
        assert isinstance(result, StreamAlreadyActiveError)
        
        # Not streaming
        error = Exception("Stream not active")
        result = handle_obs_error(error)
        assert isinstance(result, StreamNotActiveError)
    
    def test_handle_recording_errors(self):
        """Test handling recording errors."""
        # Already recording
        error = Exception("Already recording")
        result = handle_obs_error(error)
        assert isinstance(result, RecordingAlreadyActiveError)
        
        # Not recording
        error = Exception("Not recording")
        result = handle_obs_error(error)
        assert isinstance(result, RecordingNotActiveError)
    
    def test_handle_timeout_errors(self):
        """Test handling timeout errors."""
        error = Exception("Request timeout")
        result = handle_obs_error(error)
        assert isinstance(result, RequestTimeoutError)
    
    def test_handle_permission_errors(self):
        """Test handling permission errors."""
        error = Exception("Permission denied")
        result = handle_obs_error(error)
        assert isinstance(result, PermissionError)
        
        error = Exception("Access denied to resource")
        result = handle_obs_error(error)
        assert isinstance(result, PermissionError)
    
    def test_handle_websocket_errors(self):
        """Test handling WebSocket errors."""
        class WebSocketError(Exception):
            pass
        
        error = WebSocketError("WebSocket connection failed")
        result = handle_obs_error(error)
        assert isinstance(result, WebSocketError)
        assert "WebSocket error" in str(result)
    
    def test_handle_generic_errors(self):
        """Test handling generic errors."""
        error = Exception("Unknown error")
        result = handle_obs_error(error)
        assert isinstance(result, OBSAgentError)
        assert "Unknown error" in str(result)
        assert result.details["original_error"] == "Unknown error"
        assert result.details["error_type"] == "Exception"