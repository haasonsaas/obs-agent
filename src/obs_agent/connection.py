"""
Connection management for OBS Agent.

This module provides a singleton connection manager for OBS WebSocket
connections with automatic reconnection, health monitoring, and
connection pooling capabilities.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

import obswebsocket.exceptions
from obswebsocket import obsws, requests

from .config import OBSConfig, get_config
from .exceptions import AuthenticationError, ConnectionError, RequestTimeoutError, handle_obs_error
from .events import EventHandler, parse_event, BaseEvent

logger = logging.getLogger(__name__)


@dataclass
class ConnectionStats:
    """Statistics for a connection."""

    connected_at: Optional[datetime] = None
    disconnected_at: Optional[datetime] = None
    total_requests: int = 0
    failed_requests: int = 0
    total_events: int = 0
    reconnect_count: int = 0
    last_error: Optional[str] = None

    @property
    def uptime(self) -> Optional[timedelta]:
        """Get connection uptime."""
        if self.connected_at:
            end_time = self.disconnected_at or datetime.now()
            return end_time - self.connected_at
        return None

    @property
    def success_rate(self) -> float:
        """Get request success rate."""
        if self.total_requests == 0:
            return 1.0
        return (self.total_requests - self.failed_requests) / self.total_requests


class ConnectionManager:
    """
    Singleton connection manager for OBS WebSocket connections.

    This class ensures only one connection to OBS exists at a time
    and provides automatic reconnection, health monitoring, and
    connection statistics.
    """

    _instance: Optional["ConnectionManager"] = None
    _lock: Lock = Lock()

    def __new__(cls) -> "ConnectionManager":
        """Ensure singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize connection manager."""
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._connection: Optional[obsws] = None
        self._config: Optional[OBSConfig] = None
        self._connected: bool = False
        self._reconnecting: bool = False
        self._shutdown: bool = False
        self._stats: ConnectionStats = ConnectionStats()
        self._event_handler: EventHandler = EventHandler()
        self._event_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._connection_lock = asyncio.Lock()

    async def connect(self, config: Optional[OBSConfig] = None) -> None:
        """
        Connect to OBS WebSocket server.

        Args:
            config: Optional OBS configuration. If not provided, uses global config.

        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
        """
        async with self._connection_lock:
            if self._connected and self._connection:
                logger.info("Already connected to OBS")
                return

            self._config = config or get_config().obs
            self._shutdown = False

            try:
                logger.info(f"Connecting to OBS at {self._config.host}:{self._config.port}")

                self._connection = obsws(
                    self._config.host, self._config.port, self._config.password, timeout=self._config.timeout
                )

                self._connection.connect()
                self._connected = True
                self._stats.connected_at = datetime.now()
                self._stats.reconnect_count = 0

                # Register internal event handlers
                self._register_internal_handlers()

                # Start event handler
                await self._event_handler.start()
                
                # Start event processing task
                self._event_task = asyncio.create_task(self._process_websocket_events())

                # Start health check if enabled
                if get_config().enable_performance_monitoring:
                    self._health_check_task = asyncio.create_task(self._health_check_loop())

                logger.info("Successfully connected to OBS")

            except obswebsocket.exceptions.ConnectionFailure as e:
                self._handle_connection_error(e)
            except obswebsocket.exceptions.MessageTimeout:
                raise RequestTimeoutError("Connection", self._config.timeout)
            except Exception as e:
                raise handle_obs_error(e)

    async def disconnect(self) -> None:
        """Disconnect from OBS WebSocket server."""
        async with self._connection_lock:
            self._shutdown = True

            # Stop event handler
            await self._event_handler.stop()

            # Cancel background tasks
            if self._event_task:
                self._event_task.cancel()
                try:
                    await self._event_task
                except asyncio.CancelledError:
                    pass
                    
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            if self._reconnect_task:
                self._reconnect_task.cancel()
                try:
                    await self._reconnect_task
                except asyncio.CancelledError:
                    pass

            if self._connection and self._connected:
                try:
                    self._connection.disconnect()
                except Exception as e:
                    logger.warning(f"Error during disconnect: {e}")

                self._connected = False
                self._stats.disconnected_at = datetime.now()
                logger.info("Disconnected from OBS")

            self._connection = None

    @property
    def is_connected(self) -> bool:
        """Check if connected to OBS."""
        return self._connected and self._connection is not None

    @property
    def stats(self) -> ConnectionStats:
        """Get connection statistics."""
        return self._stats

    async def execute(self, request: Any, timeout: Optional[float] = None) -> Any:
        """
        Execute a request on the OBS WebSocket connection.

        Args:
            request: The OBS WebSocket request to execute
            timeout: Optional timeout override

        Returns:
            Response from OBS

        Raises:
            ConnectionError: If not connected
            Various OBS exceptions based on the request
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to OBS")

        self._stats.total_requests += 1

        try:
            start_time = time.time()

            if timeout:
                # Create a timeout context
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, self._connection.call, request), timeout=timeout
                )
            else:
                response = self._connection.call(request)

            elapsed = time.time() - start_time

            if elapsed > 1.0:  # Log slow requests
                logger.warning(f"Slow request: {type(request).__name__} took {elapsed:.2f}s")

            return response

        except obswebsocket.exceptions.MessageTimeout:
            self._stats.failed_requests += 1
            raise RequestTimeoutError(type(request).__name__, timeout or self._config.timeout)
        except Exception as e:
            self._stats.failed_requests += 1
            self._stats.last_error = str(e)

            # Check if we need to reconnect
            if self._should_reconnect(e):
                asyncio.create_task(self._auto_reconnect())

            raise handle_obs_error(e)

    @property
    def event_handler(self) -> EventHandler:
        """Get the event handler instance."""
        return self._event_handler

    async def _process_websocket_events(self) -> None:
        """Process incoming WebSocket events."""
        while self._connected and not self._shutdown:
            try:
                # This would need to be implemented based on the actual obs-websocket-py API
                # For now, this is a placeholder showing the pattern
                # In reality, you'd register a callback with the WebSocket connection
                
                # Example pattern:
                # raw_event = await self._connection.get_event()  # This doesn't exist in current API
                # if raw_event:
                #     event = parse_event(raw_event)
                #     if event:
                #         self._stats.total_events += 1
                #         await self._event_handler.emit(event)
                
                await asyncio.sleep(0.1)  # Placeholder
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket events: {e}")

    def _register_internal_handlers(self) -> None:
        """Register internal event handlers."""

        # Register disconnect handler
        def on_disconnect(event):
            logger.warning("OBS WebSocket disconnected")
            self._connected = False
            self._stats.disconnected_at = datetime.now()

            if not self._shutdown and get_config().enable_auto_reconnect:
                asyncio.create_task(self._auto_reconnect())

        # Register error handler
        def on_error(event):
            error_msg = getattr(event, "message", "Unknown error")
            logger.error(f"OBS WebSocket error: {error_msg}")
            self._stats.last_error = error_msg

        # Note: Actual event registration would depend on obs-websocket-py API
        # This is a placeholder for the actual implementation

    def _handle_connection_error(self, error: Exception) -> None:
        """Handle connection errors."""
        error_str = str(error).lower()

        if "auth" in error_str or "password" in error_str:
            raise AuthenticationError("Authentication failed. Check your OBS WebSocket password.")
        elif "refused" in error_str:
            raise ConnectionError(
                f"Connection refused by OBS at {self._config.host}:{self._config.port}. "
                "Ensure OBS is running and WebSocket server is enabled."
            )
        elif "timeout" in error_str:
            raise ConnectionError(f"Connection timeout to OBS at {self._config.host}:{self._config.port}")
        else:
            raise ConnectionError(f"Failed to connect to OBS: {error}")

    def _should_reconnect(self, error: Exception) -> bool:
        """Check if we should attempt to reconnect after an error."""
        if self._shutdown or self._reconnecting:
            return False

        error_str = str(error).lower()

        # Reconnect on connection errors
        if any(term in error_str for term in ["connection", "closed", "timeout"]):
            return True

        return False

    async def _auto_reconnect(self) -> None:
        """Automatically reconnect to OBS."""
        if self._reconnecting or self._shutdown:
            return

        self._reconnecting = True
        self._reconnect_task = asyncio.current_task()

        for attempt in range(1, self._config.max_reconnect_attempts + 1):
            if self._shutdown:
                break

            logger.info(f"Reconnection attempt {attempt}/{self._config.max_reconnect_attempts}")

            try:
                await asyncio.sleep(self._config.reconnect_interval)
                await self.connect(self._config)
                self._stats.reconnect_count += 1
                logger.info("Successfully reconnected to OBS")
                break
            except Exception as e:
                logger.warning(f"Reconnection attempt {attempt} failed: {e}")

                if attempt == self._config.max_reconnect_attempts:
                    logger.error("Max reconnection attempts reached")
                    self._stats.last_error = "Max reconnection attempts reached"

        self._reconnecting = False
        self._reconnect_task = None

    async def _health_check_loop(self) -> None:
        """Periodically check connection health."""
        while not self._shutdown:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                if self.is_connected:
                    # Send a simple request to check connection
                    try:
                        await self.execute(requests.GetVersion())
                    except Exception as e:
                        logger.warning(f"Health check failed: {e}")
                        if self._should_reconnect(e):
                            await self._auto_reconnect()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


@asynccontextmanager
async def obs_connection(config: Optional[OBSConfig] = None):
    """
    Context manager for OBS connections.

    Usage:
        async with obs_connection() as conn:
            response = await conn.execute(requests.GetVersion())
    """
    manager = get_connection_manager()

    try:
        await manager.connect(config)
        yield manager
    finally:
        # Don't disconnect in context manager - allow connection reuse
        pass


async def ensure_connected(func: Callable) -> Callable:
    """
    Decorator to ensure OBS connection before executing a method.

    Usage:
        @ensure_connected
        async def my_method(self):
            # Method implementation
    """

    async def wrapper(*args, **kwargs):
        manager = get_connection_manager()
        if not manager.is_connected:
            await manager.connect()
        return await func(*args, **kwargs)

    return wrapper
