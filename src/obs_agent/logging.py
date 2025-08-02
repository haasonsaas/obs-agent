"""
Logging configuration and utilities for OBS Agent.

This module provides structured logging with proper formatting,
log rotation, and different handlers for various use cases.
"""

import json
import logging
import logging.handlers
import sys
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, MutableMapping, Optional

from .config import LoggingConfig, get_config


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for terminal output."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    # Icons for different log levels
    ICONS = {"DEBUG": "🔍", "INFO": "✅", "WARNING": "⚠️", "ERROR": "❌", "CRITICAL": "🚨"}

    def __init__(self, fmt: Optional[str] = None, use_colors: bool = True, use_icons: bool = True):
        super().__init__(fmt)
        self.use_colors = use_colors and sys.stdout.isatty()
        self.use_icons = use_icons

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and icons."""
        # Save original values
        orig_fmt = self._style._fmt
        orig_levelname = record.levelname

        if self.use_icons:
            icon = self.ICONS.get(record.levelname, "")
            record.levelname = f"{icon} {record.levelname}"

        if self.use_colors:
            color = self.COLORS.get(orig_levelname, "")
            reset = self.COLORS["RESET"]

            # Colorize the entire line
            self._style._fmt = f"{color}{orig_fmt}{reset}"

        # Format the record
        result = super().format(record)

        # Restore original values
        self._style._fmt = orig_fmt
        record.levelname = orig_levelname

        return result


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "msecs",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "funcName",
                "lineno",
                "exc_info",
                "exc_text",
                "stack_info",
                "processName",
                "process",
                "threadName",
                "thread",
                "getMessage",
            ]:
                log_data[key] = value

        return json.dumps(log_data)


class ContextFilter(logging.Filter):
    """Filter that adds contextual information to log records."""

    def __init__(self, context: Dict[str, Any]):
        super().__init__()
        self.context = context

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """
    Set up logging configuration.

    Args:
        config: Optional logging configuration. If not provided, uses global config.
    """
    if config is None:
        config = get_config().logging

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.level.upper()))

    # Use colored formatter for console
    console_formatter = ColoredFormatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", use_colors=True, use_icons=True
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    if config.file_path:
        config.file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(config.file_path), maxBytes=config.max_file_size, backupCount=config.backup_count
        )
        file_handler.setLevel(getattr(logging, config.level.upper()))

        # Use JSON formatter for file
        file_formatter = JSONFormatter()
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Set up specific loggers

    # Reduce verbosity of third-party libraries
    logging.getLogger("obswebsocket").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Set up OBS Agent loggers
    obs_logger = logging.getLogger("obs_agent")
    obs_logger.setLevel(getattr(logging, config.level.upper()))


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding contextual information to logs."""

    def __init__(self, **kwargs):
        self.context = kwargs
        self.filter = ContextFilter(self.context)
        self.loggers = []

    def __enter__(self):
        """Add context filter to all loggers."""
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addFilter(self.filter)
        self.loggers.append(root_logger)

        # Add to OBS Agent loggers
        obs_logger = logging.getLogger("obs_agent")
        obs_logger.addFilter(self.filter)
        self.loggers.append(obs_logger)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Remove context filter from all loggers."""
        for logger in self.loggers:
            logger.removeFilter(self.filter)


@contextmanager
def log_context(**kwargs):
    """
    Context manager for adding contextual information to logs.

    Usage:
        with log_context(user_id=123, request_id='abc'):
            logger.info("Processing request")
    """
    with LogContext(**kwargs):
        yield


def log_performance(func):
    """
    Decorator to log function performance.

    Usage:
        @log_performance
        async def my_function():
            # Function implementation
    """
    import functools
    import time

    logger = get_logger(func.__module__)

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time

            logger.debug(
                f"{func.__name__} completed",
                extra={"function": func.__name__, "duration": elapsed, "status": "success"},
            )

            if elapsed > 1.0:  # Log slow operations
                logger.warning(
                    f"{func.__name__} took {elapsed:.2f}s",
                    extra={"function": func.__name__, "duration": elapsed, "slow": True},
                )

            return result

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"{func.__name__} failed",
                extra={"function": func.__name__, "duration": elapsed, "status": "error", "error": str(e)},
                exc_info=True,
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time

            logger.debug(
                f"{func.__name__} completed",
                extra={"function": func.__name__, "duration": elapsed, "status": "success"},
            )

            if elapsed > 1.0:  # Log slow operations
                logger.warning(
                    f"{func.__name__} took {elapsed:.2f}s",
                    extra={"function": func.__name__, "duration": elapsed, "slow": True},
                )

            return result

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"{func.__name__} failed",
                extra={"function": func.__name__, "duration": elapsed, "status": "error", "error": str(e)},
                exc_info=True,
            )
            raise

    # Return appropriate wrapper based on function type
    import inspect

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


class LoggerAdapter(logging.LoggerAdapter):
    """
    Custom logger adapter for adding consistent context.

    Usage:
        logger = LoggerAdapter(get_logger(__name__), {'component': 'MyComponent'})
        logger.info("Starting component")
    """

    def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> tuple[str, MutableMapping[str, Any]]:
        """Process the logging message and keyword arguments."""
        # Add extra context to all log messages
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra

        return msg, kwargs


# Convenience functions for common logging patterns


def log_obs_request(request_type: str, **params):
    """Log an OBS WebSocket request."""
    logger = get_logger("obs_agent.connection")
    logger.debug(f"OBS Request: {request_type}", extra={"obs_request": request_type, "params": params})


def log_obs_response(request_type: str, response: Any, duration: float):
    """Log an OBS WebSocket response."""
    logger = get_logger("obs_agent.connection")
    logger.debug(
        f"OBS Response: {request_type}", extra={"obs_request": request_type, "duration": duration, "success": True}
    )


def log_obs_error(request_type: str, error: Exception, duration: float):
    """Log an OBS WebSocket error."""
    logger = get_logger("obs_agent.connection")
    logger.error(
        f"OBS Error: {request_type} - {error}",
        extra={"obs_request": request_type, "duration": duration, "success": False, "error_type": type(error).__name__},
    )


def log_scene_change(from_scene: str, to_scene: str):
    """Log a scene change."""
    logger = get_logger("obs_agent.scenes")
    logger.info(
        f"Scene changed: {from_scene} → {to_scene}",
        extra={"from_scene": from_scene, "to_scene": to_scene, "event": "scene_change"},
    )


def log_stream_status(is_streaming: bool, duration: Optional[float] = None):
    """Log streaming status."""
    logger = get_logger("obs_agent.streaming")

    if is_streaming:
        logger.info("Stream started", extra={"event": "stream_start"})
    else:
        logger.info("Stream stopped", extra={"event": "stream_stop", "duration": duration})


def log_recording_status(is_recording: bool, file_path: Optional[str] = None):
    """Log recording status."""
    logger = get_logger("obs_agent.recording")

    if is_recording:
        logger.info("Recording started", extra={"event": "recording_start"})
    else:
        logger.info(f"Recording stopped: {file_path}", extra={"event": "recording_stop", "file_path": file_path})
