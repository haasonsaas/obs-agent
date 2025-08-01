"""OBS Agent - AI-powered OBS Studio automation and control system."""

from .__version__ import __version__, __author__, __email__, __description__
from .obs_agent import OBSAgent, OBSController
from .advanced_features import AdvancedOBSAgent, AdvancedOBSController

# New improved modules
from .obs_agent_v2 import OBSAgent as OBSAgentV2, create_obs_agent
from .config import Config, OBSConfig, StreamingConfig, LoggingConfig, get_config, set_config
from .connection import ConnectionManager, get_connection_manager, obs_connection
from .exceptions import (
    OBSAgentError,
    ConnectionError,
    AuthenticationError,
    SceneNotFoundError,
    SourceNotFoundError,
    ValidationError,
    handle_obs_error,
)
from .validation import (
    validate_scene_name,
    validate_source_name,
    validate_port,
    validate_host,
    validate_file_path,
    validate_settings,
)
from .logging import setup_logging, get_logger, log_context

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
]
