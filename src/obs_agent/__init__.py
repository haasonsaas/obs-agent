"""OBS Agent - AI-powered OBS Studio automation and control system."""

from .__version__ import __author__, __description__, __email__, __version__

try:
    from .advanced_features import AdvancedOBSAgent, AdvancedOBSController
except ImportError:
    # Allow partial imports when obswebsocket is not available
    AdvancedOBSAgent = None  # type: ignore
    AdvancedOBSController = None  # type: ignore
from .config import Config, LoggingConfig, OBSConfig, StreamingConfig, get_config, set_config
from .connection import ConnectionManager, get_connection_manager, obs_connection

# Event system
from .event_handler import (  # Event classes; Middleware
    BaseEvent,
    CurrentProgramSceneChanged,
    EventCategory,
    EventHandler,
    EventPriority,
    EventSubscription,
    ExitStarted,
    InputCreated,
    InputMuteStateChanged,
    InputRemoved,
    InputVolumeChanged,
    RecordStateChanged,
    SceneCreated,
    SceneNameChanged,
    SceneRemoved,
    StreamStateChanged,
    StudioModeStateChanged,
    error_handling_middleware,
    logging_middleware,
    performance_middleware,
)
from .exceptions import (
    AuthenticationError,
    ConnectionError,
    OBSAgentError,
    SceneNotFoundError,
    SourceNotFoundError,
    ValidationError,
    handle_obs_error,
)
from .logging import get_logger, log_context, setup_logging

try:
    from .obs_agent import OBSAgent, OBSController
except ImportError:
    OBSAgent = None  # type: ignore
    OBSController = None  # type: ignore

# New improved modules
from .obs_agent_v2 import OBSAgent as OBSAgentV2
from .obs_agent_v2 import create_obs_agent

# Type-safe wrapper
try:
    from .typed_obs_agent import TypedOBSAgent, create_typed_obs_agent
except ImportError:
    TypedOBSAgent = None  # type: ignore
    create_typed_obs_agent = None  # type: ignore

# Type definitions
from . import types
from .validation import (
    validate_file_path,
    validate_host,
    validate_port,
    validate_scene_name,
    validate_settings,
    validate_source_name,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    # Legacy classes (for backward compatibility)
    "OBSAgent",
    "OBSController",
    "AdvancedOBSAgent",
    "AdvancedOBSController",
    # New improved classes
    "OBSAgentV2",
    "create_obs_agent",
    # Type-safe classes
    "TypedOBSAgent", 
    "create_typed_obs_agent",
    # Type definitions
    "types",
    # Configuration
    "Config",
    "OBSConfig",
    "StreamingConfig",
    "LoggingConfig",
    "get_config",
    "set_config",
    # Connection management
    "ConnectionManager",
    "get_connection_manager",
    "obs_connection",
    # Exceptions
    "OBSAgentError",
    "ConnectionError",
    "AuthenticationError",
    "SceneNotFoundError",
    "SourceNotFoundError",
    "ValidationError",
    "handle_obs_error",
    # Validation
    "validate_scene_name",
    "validate_source_name",
    "validate_port",
    "validate_host",
    "validate_file_path",
    "validate_settings",
    # Logging
    "setup_logging",
    "get_logger",
    "log_context",
    # Event system
    "EventHandler",
    "EventSubscription",
    "BaseEvent",
    "EventPriority",
    "EventCategory",
    # Event classes
    "CurrentProgramSceneChanged",
    "SceneCreated",
    "SceneRemoved",
    "SceneNameChanged",
    "InputCreated",
    "InputRemoved",
    "InputMuteStateChanged",
    "InputVolumeChanged",
    "StreamStateChanged",
    "RecordStateChanged",
    "ExitStarted",
    "StudioModeStateChanged",
    # Middleware
    "logging_middleware",
    "error_handling_middleware",
    "performance_middleware",
]
