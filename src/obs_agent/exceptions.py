"""
Custom exceptions for OBS Agent.

This module defines all custom exceptions used throughout the OBS Agent,
providing better error handling and clearer error messages.
"""

from typing import Optional, Dict, Any


class OBSAgentError(Exception):
    """Base exception for all OBS Agent errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class ConnectionError(OBSAgentError):
    """Raised when connection to OBS fails or is lost."""
    pass


class AuthenticationError(ConnectionError):
    """Raised when authentication with OBS fails."""
    pass


class ConfigurationError(OBSAgentError):
    """Raised when configuration is invalid or missing."""
    pass


class ValidationError(OBSAgentError):
    """Raised when input validation fails."""
    pass


class SceneError(OBSAgentError):
    """Base exception for scene-related errors."""
    pass


class SceneNotFoundError(SceneError):
    """Raised when a requested scene doesn't exist."""
    
    def __init__(self, scene_name: str):
        super().__init__(
            f"Scene not found: {scene_name}",
            {"scene_name": scene_name}
        )
        self.scene_name = scene_name


class SceneAlreadyExistsError(SceneError):
    """Raised when trying to create a scene that already exists."""
    
    def __init__(self, scene_name: str):
        super().__init__(
            f"Scene already exists: {scene_name}",
            {"scene_name": scene_name}
        )
        self.scene_name = scene_name


class SourceError(OBSAgentError):
    """Base exception for source-related errors."""
    pass


class SourceNotFoundError(SourceError):
    """Raised when a requested source doesn't exist."""
    
    def __init__(self, source_name: str):
        super().__init__(
            f"Source not found: {source_name}",
            {"source_name": source_name}
        )
        self.source_name = source_name


class SourceAlreadyExistsError(SourceError):
    """Raised when trying to create a source that already exists."""
    
    def __init__(self, source_name: str):
        super().__init__(
            f"Source already exists: {source_name}",
            {"source_name": source_name}
        )
        self.source_name = source_name


class StreamingError(OBSAgentError):
    """Base exception for streaming-related errors."""
    pass


class StreamAlreadyActiveError(StreamingError):
    """Raised when trying to start a stream that's already active."""
    pass


class StreamNotActiveError(StreamingError):
    """Raised when trying to stop a stream that's not active."""
    pass


class RecordingError(OBSAgentError):
    """Base exception for recording-related errors."""
    pass


class RecordingAlreadyActiveError(RecordingError):
    """Raised when trying to start a recording that's already active."""
    pass


class RecordingNotActiveError(RecordingError):
    """Raised when trying to stop a recording that's not active."""
    pass


class FilterError(OBSAgentError):
    """Base exception for filter-related errors."""
    pass


class FilterNotFoundError(FilterError):
    """Raised when a requested filter doesn't exist."""
    
    def __init__(self, filter_name: str, source_name: str):
        super().__init__(
            f"Filter '{filter_name}' not found on source '{source_name}'",
            {"filter_name": filter_name, "source_name": source_name}
        )
        self.filter_name = filter_name
        self.source_name = source_name


class FilterAlreadyExistsError(FilterError):
    """Raised when trying to create a filter that already exists."""
    
    def __init__(self, filter_name: str, source_name: str):
        super().__init__(
            f"Filter '{filter_name}' already exists on source '{source_name}'",
            {"filter_name": filter_name, "source_name": source_name}
        )
        self.filter_name = filter_name
        self.source_name = source_name


class WebSocketError(OBSAgentError):
    """Base exception for WebSocket-related errors."""
    pass


class RequestTimeoutError(WebSocketError):
    """Raised when a WebSocket request times out."""
    
    def __init__(self, request_type: str, timeout: float):
        super().__init__(
            f"Request '{request_type}' timed out after {timeout}s",
            {"request_type": request_type, "timeout": timeout}
        )
        self.request_type = request_type
        self.timeout = timeout


class InvalidRequestError(WebSocketError):
    """Raised when an invalid request is made to OBS."""
    pass


class PermissionError(OBSAgentError):
    """Raised when an operation is not permitted."""
    pass


class ResourceLimitError(OBSAgentError):
    """Raised when a resource limit is exceeded."""
    pass


class PerformanceWarning(OBSAgentError):
    """Raised as a warning when performance issues are detected."""
    
    def __init__(self, metric: str, value: float, threshold: float):
        super().__init__(
            f"Performance warning: {metric} ({value}) exceeded threshold ({threshold})",
            {"metric": metric, "value": value, "threshold": threshold}
        )
        self.metric = metric
        self.value = value
        self.threshold = threshold


def handle_obs_error(error: Exception) -> OBSAgentError:
    """
    Convert OBS WebSocket errors to OBS Agent exceptions.
    
    Args:
        error: The original exception from obs-websocket-py
        
    Returns:
        An appropriate OBSAgentError subclass
    """
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    # Connection errors
    if "connection" in error_str or "connect" in error_str:
        if "refused" in error_str:
            return ConnectionError("Connection refused by OBS", {"original_error": str(error)})
        elif "timeout" in error_str:
            return ConnectionError("Connection timed out", {"original_error": str(error)})
        elif "closed" in error_str:
            return ConnectionError("Connection closed unexpectedly", {"original_error": str(error)})
        else:
            return ConnectionError(f"Connection error: {error}", {"original_error": str(error)})
    
    # Authentication errors
    if "auth" in error_str or "password" in error_str:
        return AuthenticationError("Authentication failed", {"original_error": str(error)})
    
    # Scene errors
    if "scene" in error_str:
        if "not found" in error_str or "does not exist" in error_str:
            # Try to extract scene name
            scene_name = "unknown"
            if "'" in error_str:
                parts = error_str.split("'")
                if len(parts) >= 2:
                    scene_name = parts[1]
            return SceneNotFoundError(scene_name)
        elif "already exists" in error_str:
            scene_name = "unknown"
            if "'" in error_str:
                parts = error_str.split("'")
                if len(parts) >= 2:
                    scene_name = parts[1]
            return SceneAlreadyExistsError(scene_name)
    
    # Source errors
    if "source" in error_str or "input" in error_str:
        if "not found" in error_str or "does not exist" in error_str:
            source_name = "unknown"
            if "'" in error_str:
                parts = error_str.split("'")
                if len(parts) >= 2:
                    source_name = parts[1]
            return SourceNotFoundError(source_name)
        elif "already exists" in error_str:
            source_name = "unknown"
            if "'" in error_str:
                parts = error_str.split("'")
                if len(parts) >= 2:
                    source_name = parts[1]
            return SourceAlreadyExistsError(source_name)
    
    # Streaming errors
    if "stream" in error_str:
        if "already active" in error_str or "already streaming" in error_str:
            return StreamAlreadyActiveError("Stream is already active")
        elif "not active" in error_str or "not streaming" in error_str:
            return StreamNotActiveError("Stream is not active")
    
    # Recording errors
    if "record" in error_str:
        if "already active" in error_str or "already recording" in error_str:
            return RecordingAlreadyActiveError("Recording is already active")
        elif "not active" in error_str or "not recording" in error_str:
            return RecordingNotActiveError("Recording is not active")
    
    # Timeout errors
    if "timeout" in error_str:
        return RequestTimeoutError("unknown", 30.0)
    
    # Permission errors
    if "permission" in error_str or "access denied" in error_str:
        return PermissionError(f"Permission denied: {error}")
    
    # Generic WebSocket error
    if error_type.endswith("Error") and "websocket" in error_type.lower():
        return WebSocketError(f"WebSocket error: {error}", {"original_error": str(error)})
    
    # Fallback to generic error
    return OBSAgentError(f"OBS error: {error}", {"original_error": str(error), "error_type": error_type})