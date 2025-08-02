"""
Generic types and type utilities for enhanced type inference.

This module provides generic types, protocols, and utilities that enable
better type inference and safety throughout the OBS Agent codebase.
"""

from typing import (
    Any, Awaitable, Callable, Dict, Generic, List, Optional, Protocol, 
    Type, TypeVar, Union, overload, runtime_checkable
)
from typing_extensions import ParamSpec, TypeGuard

from .api_responses import OBSResponseData
from .base import T, P, R, EventT, ConfigT, OperationResult


# Advanced generic type variables
RequestT = TypeVar("RequestT")
ResponseT = TypeVar("ResponseT", bound=OBSResponseData)
SettingsT = TypeVar("SettingsT", bound=Dict[str, Any])
EventDataT = TypeVar("EventDataT", bound=Dict[str, Any])
ValidatorT = TypeVar("ValidatorT", bound=Callable[..., bool])
FilterT = TypeVar("FilterT", bound=Callable[[Any], bool])
HandlerT = TypeVar("HandlerT", bound=Callable[..., Any])


# Parameter specifications for complex function signatures
P_Handler = ParamSpec("P_Handler")
P_Validator = ParamSpec("P_Validator")
P_Transform = ParamSpec("P_Transform")


# Protocol definitions for better structural typing
@runtime_checkable
class OBSRequestProtocol(Protocol[RequestT, ResponseT]):
    """Protocol for OBS WebSocket requests."""
    
    def __init__(self, **kwargs: Any) -> None: ...
    
    def datain(self) -> ResponseT: ...


@runtime_checkable
class EventHandlerProtocol(Protocol[EventT]):
    """Protocol for event handlers."""
    
    def __call__(self, event: EventT) -> Union[None, Awaitable[None]]: ...


@runtime_checkable
class ConfigurableProtocol(Protocol[ConfigT]):
    """Protocol for configurable objects."""
    
    def configure(self, config: ConfigT) -> None: ...
    
    def get_config(self) -> ConfigT: ...


@runtime_checkable
class ValidatableProtocol(Protocol[T]):
    """Protocol for objects that can be validated."""
    
    def validate(self) -> bool: ...
    
    def get_errors(self) -> List[str]: ...


@runtime_checkable
class SerializableProtocol(Protocol[T]):
    """Protocol for serializable objects."""
    
    def to_dict(self) -> Dict[str, Any]: ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> T: ...


@runtime_checkable
class CacheableProtocol(Protocol[T]):
    """Protocol for cacheable objects."""
    
    def cache_key(self) -> str: ...
    
    def is_cache_valid(self) -> bool: ...


@runtime_checkable
class TransformableProtocol(Protocol[T, R]):
    """Protocol for transformable objects."""
    
    def transform(self, func: Callable[[T], R]) -> R: ...


# Generic wrapper classes
class TypedRequest(Generic[RequestT, ResponseT]):
    """Type-safe wrapper for OBS requests."""
    
    def __init__(
        self, 
        request_class: Type[RequestT], 
        response_type: Type[ResponseT]
    ) -> None:
        self.request_class = request_class
        self.response_type = response_type
    
    def create(self, **kwargs: Any) -> RequestT:
        """Create a typed request instance."""
        return self.request_class(**kwargs)
    
    def validate_response(self, response: Any) -> TypeGuard[ResponseT]:
        """Validate response type."""
        return isinstance(response, dict)  # Basic validation


class TypedEventHandler(Generic[EventT]):
    """Type-safe event handler wrapper."""
    
    def __init__(
        self, 
        event_type: Type[EventT], 
        handler: EventHandlerProtocol[EventT]
    ) -> None:
        self.event_type = event_type
        self.handler = handler
    
    async def handle(self, event: EventT) -> None:
        """Handle the event with type safety."""
        result = self.handler(event)
        if result is not None:
            await result


class TypedValidator(Generic[T]):
    """Type-safe validator wrapper."""
    
    def __init__(
        self, 
        target_type: Type[T], 
        validator: Callable[[T], bool]
    ) -> None:
        self.target_type = target_type
        self.validator = validator
    
    def validate(self, value: Any) -> TypeGuard[T]:
        """Validate value with type guard."""
        if not isinstance(value, self.target_type):
            return False
        return self.validator(value)


class TypedFilter(Generic[T]):
    """Type-safe filter wrapper."""
    
    def __init__(
        self, 
        item_type: Type[T], 
        predicate: Callable[[T], bool]
    ) -> None:
        self.item_type = item_type
        self.predicate = predicate
    
    def filter(self, items: List[Any]) -> List[T]:
        """Filter items with type safety."""
        result: List[T] = []
        for item in items:
            if isinstance(item, self.item_type) and self.predicate(item):
                result.append(item)
        return result


class TypedTransformer(Generic[T, R]):
    """Type-safe transformer wrapper."""
    
    def __init__(
        self, 
        input_type: Type[T], 
        output_type: Type[R],
        transformer: Callable[[T], R]
    ) -> None:
        self.input_type = input_type
        self.output_type = output_type
        self.transformer = transformer
    
    def transform(self, value: T) -> R:
        """Transform value with type safety."""
        if not isinstance(value, self.input_type):
            raise TypeError(f"Expected {self.input_type}, got {type(value)}")
        
        result = self.transformer(value)
        
        if not isinstance(result, self.output_type):
            raise TypeError(f"Transform produced {type(result)}, expected {self.output_type}")
        
        return result


# Result and operation types
class TypedResult(Generic[T]):
    """Type-safe operation result."""
    
    def __init__(self, success: bool, data: Optional[T] = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error
    
    def is_success(self) -> TypeGuard[T]:
        """Check if result is successful with type guard."""
        return self.success and self.data is not None
    
    def unwrap(self) -> T:
        """Unwrap result data or raise exception."""
        if not self.success:
            raise ValueError(f"Operation failed: {self.error}")
        if self.data is None:
            raise ValueError("No data available")
        return self.data
    
    def unwrap_or(self, default: T) -> T:
        """Unwrap result data or return default."""
        return self.data if self.success and self.data is not None else default


class TypedCache(Generic[T]):
    """Type-safe cache implementation."""
    
    def __init__(self, item_type: Type[T]) -> None:
        self.item_type = item_type
        self._cache: Dict[str, T] = {}
    
    def get(self, key: str) -> Optional[T]:
        """Get item from cache with type safety."""
        return self._cache.get(key)
    
    def set(self, key: str, value: T) -> None:
        """Set item in cache with type validation."""
        if not isinstance(value, self.item_type):
            raise TypeError(f"Expected {self.item_type}, got {type(value)}")
        self._cache[key] = value
    
    def has(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._cache
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()


# Function overloads for better type inference
@overload
def create_typed_handler(
    event_type: Type[EventT], 
    handler: Callable[[EventT], None]
) -> TypedEventHandler[EventT]: ...

@overload
def create_typed_handler(
    event_type: Type[EventT], 
    handler: Callable[[EventT], Awaitable[None]]
) -> TypedEventHandler[EventT]: ...

def create_typed_handler(
    event_type: Type[EventT], 
    handler: Union[Callable[[EventT], None], Callable[[EventT], Awaitable[None]]]
) -> TypedEventHandler[EventT]:
    """Create a typed event handler with proper overloads."""
    return TypedEventHandler(event_type, handler)


@overload
def validate_and_cast(value: Any, target_type: Type[T]) -> T: ...

@overload
def validate_and_cast(value: Any, target_type: Type[T], default: T) -> T: ...

def validate_and_cast(value: Any, target_type: Type[T], default: Optional[T] = None) -> T:
    """Validate and cast value to target type."""
    if isinstance(value, target_type):
        return value
    
    if default is not None:
        return default
    
    raise TypeError(f"Cannot cast {type(value)} to {target_type}")


# Type utilities
def is_instance_of(value: Any, type_class: Type[T]) -> TypeGuard[T]:
    """Type guard for isinstance checks."""
    return isinstance(value, type_class)


def ensure_type(value: Any, expected_type: Type[T]) -> T:
    """Ensure value is of expected type or raise TypeError."""
    if not isinstance(value, expected_type):
        raise TypeError(f"Expected {expected_type}, got {type(value)}")
    return value


def safe_cast(value: Any, target_type: Type[T]) -> Optional[T]:
    """Safely cast value to target type, returning None on failure."""
    try:
        if isinstance(value, target_type):
            return value
        return target_type(value)
    except (TypeError, ValueError):
        return None


# Collection type utilities
def filter_by_type(items: List[Any], target_type: Type[T]) -> List[T]:
    """Filter list items by type."""
    return [item for item in items if isinstance(item, target_type)]


def find_by_type(items: List[Any], target_type: Type[T]) -> Optional[T]:
    """Find first item of target type."""
    for item in items:
        if isinstance(item, target_type):
            return item
    return None


def group_by_type(items: List[Any]) -> Dict[Type[Any], List[Any]]:
    """Group items by their type."""
    groups: Dict[Type[Any], List[Any]] = {}
    for item in items:
        item_type = type(item)
        if item_type not in groups:
            groups[item_type] = []
        groups[item_type].append(item)
    return groups


# Async type utilities
class AsyncTypedResult(Generic[T]):
    """Async version of TypedResult."""
    
    def __init__(self, success: bool, data: Optional[T] = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error
    
    async def unwrap_async(self) -> T:
        """Async unwrap - useful for chaining async operations."""
        return self.unwrap()
    
    async def map_async(self, func: Callable[[T], Awaitable[R]]) -> "AsyncTypedResult[R]":
        """Map result through async function."""
        if not self.success or self.data is None:
            return AsyncTypedResult(False, error=self.error)
        
        try:
            new_data = await func(self.data)
            return AsyncTypedResult(True, new_data)
        except Exception as e:
            return AsyncTypedResult(False, error=str(e))


# Factory functions for common patterns
def create_validator(target_type: Type[T]) -> TypedValidator[T]:
    """Create a basic type validator."""
    return TypedValidator(target_type, lambda x: True)


def create_filter(item_type: Type[T], predicate: Callable[[T], bool]) -> TypedFilter[T]:
    """Create a typed filter."""
    return TypedFilter(item_type, predicate)


def create_transformer(
    input_type: Type[T], 
    output_type: Type[R], 
    func: Callable[[T], R]
) -> TypedTransformer[T, R]:
    """Create a typed transformer."""
    return TypedTransformer(input_type, output_type, func)


def create_cache(item_type: Type[T]) -> TypedCache[T]:
    """Create a typed cache."""
    return TypedCache(item_type)


# Type aliases for common patterns
StringValidator = TypedValidator[str]
IntValidator = TypedValidator[int]
DictValidator = TypedValidator[Dict[str, Any]]
ListValidator = TypedValidator[List[Any]]

StringFilter = TypedFilter[str]
DictFilter = TypedFilter[Dict[str, Any]]

StringCache = TypedCache[str]
DictCache = TypedCache[Dict[str, Any]]