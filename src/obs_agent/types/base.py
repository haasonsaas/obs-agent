"""Base type definitions and common types used throughout OBS Agent."""

from typing import Any, Dict, Generic, List, NewType, TypeVar, Union

from typing_extensions import NotRequired, TypedDict

# Type variables for generics
T = TypeVar("T")
P = TypeVar("P")  # Parameters
R = TypeVar("R")  # Return type
EventT = TypeVar("EventT")  # Event type variable (unbound for flexibility)
ConfigT = TypeVar("ConfigT", bound="BaseConfig")

# Common scalar types
UUID = NewType("UUID", str)
Timestamp = NewType("Timestamp", float)
Duration = NewType("Duration", float)  # In seconds
Milliseconds = NewType("Milliseconds", int)
Bytes = NewType("Bytes", int)
Frames = NewType("Frames", int)
Decibels = NewType("Decibels", float)
Percentage = NewType("Percentage", float)  # 0.0 - 1.0
RGB = NewType("RGB", int)  # 0xRRGGBB format


class Position(TypedDict):
    """Position coordinates."""

    x: float
    y: float


class Scale(TypedDict):
    """Scale factors."""

    x: float
    y: float


class Size(TypedDict):
    """Dimensions."""

    width: int
    height: int


class Crop(TypedDict):
    """Crop settings."""

    top: int
    bottom: int
    left: int
    right: int


class Transform(TypedDict):
    """Complete transform information for scene items."""

    position: Position
    scale: Scale
    rotation: float
    crop: Crop
    bounds: NotRequired[Size]
    alignment: NotRequired[int]
    boundsAlignment: NotRequired[int]
    boundsType: NotRequired[str]


class Color(TypedDict):
    """Color definition."""

    r: int  # 0-255
    g: int  # 0-255
    b: int  # 0-255
    a: NotRequired[int]  # 0-255, alpha


class Font(TypedDict):
    """Font definition."""

    face: str
    size: int
    style: NotRequired[str]  # "Bold", "Italic", "Bold Italic", "Regular"
    flags: NotRequired[int]


class Range(TypedDict, Generic[T]):
    """Generic range type."""

    min: T
    max: T
    current: NotRequired[T]


class Bounds(TypedDict):
    """Boundary constraints."""

    min_value: float
    max_value: float
    step: NotRequired[float]


# Validation types
ValidationResult = TypedDict(
    "ValidationResult", {"valid": bool, "errors": List[str], "warnings": NotRequired[List[str]]}
)


# Result types for operations
class OperationResult(TypedDict, Generic[T]):
    """Generic operation result."""

    success: bool
    data: NotRequired[T]
    error: NotRequired[str]
    timestamp: Timestamp


class PaginatedResult(TypedDict, Generic[T]):
    """Paginated result set."""

    items: List[T]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# Connection and status types
class ConnectionInfo(TypedDict):
    """WebSocket connection information."""

    host: str
    port: int
    connected: bool
    last_connected: NotRequired[Timestamp]
    connection_id: NotRequired[str]
    protocol_version: NotRequired[str]


class HealthStatus(TypedDict):
    """System health status."""

    status: str  # "healthy", "degraded", "unhealthy"
    checks: Dict[str, bool]
    last_check: Timestamp
    uptime: Duration


# Configuration base types
class BaseConfig(TypedDict):
    """Base configuration interface."""

    version: str
    created_at: Timestamp
    updated_at: NotRequired[Timestamp]


# Error types
class ErrorInfo(TypedDict):
    """Detailed error information."""

    code: str
    message: str
    details: NotRequired[Dict[str, Any]]
    timestamp: Timestamp
    context: NotRequired[Dict[str, Any]]


# Metrics and statistics
class Metric(TypedDict):
    """Generic metric definition."""

    name: str
    value: Union[int, float, str]
    unit: NotRequired[str]
    timestamp: Timestamp
    tags: NotRequired[Dict[str, str]]


class Statistics(TypedDict):
    """Collection of metrics."""

    metrics: List[Metric]
    collected_at: Timestamp
    period: NotRequired[Duration]


# Callback and handler types
CallbackFunction = TypeVar("CallbackFunction", bound=callable)
AsyncCallbackFunction = TypeVar("AsyncCallbackFunction", bound=callable)


# Event filter types
class FilterCriteria(TypedDict):
    """Event filtering criteria."""

    event_types: NotRequired[List[str]]
    priority_min: NotRequired[str]
    source_patterns: NotRequired[List[str]]
    time_range: NotRequired[Range[Timestamp]]


# Automation types
class AutomationMetadata(TypedDict):
    """Metadata for automation rules."""

    name: str
    description: str
    author: NotRequired[str]
    version: NotRequired[str]
    tags: NotRequired[List[str]]
    created_at: Timestamp


class RuleExecution(TypedDict):
    """Automation rule execution record."""

    rule_name: str
    execution_id: str
    started_at: Timestamp
    completed_at: NotRequired[Timestamp]
    status: str  # "success", "failed", "cancelled", "pending"
    error: NotRequired[str]
    duration: NotRequired[Duration]
    context: NotRequired[Dict[str, Any]]
