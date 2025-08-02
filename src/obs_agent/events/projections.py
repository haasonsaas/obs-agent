"""
Event projections for building read models.

This module provides a framework for creating projections that transform
the event stream into optimized read models for different use cases.
"""

import asyncio
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Callable, TypeVar, Generic

from .domain import DomainEvent, EventType
from .store import EventStore


T = TypeVar('T')


@dataclass
class ProjectionState(Generic[T]):
    """State of a projection at a point in time."""
    
    projection_name: str
    last_event_timestamp: Optional[datetime]
    last_event_id: Optional[str]
    version: int
    data: T
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "projection_name": self.projection_name,
            "last_event_timestamp": self.last_event_timestamp.isoformat() if self.last_event_timestamp else None,
            "last_event_id": self.last_event_id,
            "version": self.version,
            "data": self.data if isinstance(self.data, dict) else str(self.data)
        }


class Projection(ABC, Generic[T]):
    """
    Base class for event projections.
    
    Projections transform the event stream into read models
    optimized for specific query patterns.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.state: T = self._initial_state()
        self.version = 0
        self.last_event_timestamp: Optional[datetime] = None
        self.last_event_id: Optional[str] = None
    
    @abstractmethod
    def _initial_state(self) -> T:
        """Return the initial state of the projection."""
        pass
    
    @abstractmethod
    def handle_event(self, event: DomainEvent) -> None:
        """Update projection state based on an event."""
        pass
    
    def can_handle(self, event: DomainEvent) -> bool:
        """Check if this projection handles the event."""
        return True  # Override in subclasses for filtering
    
    def apply(self, event: DomainEvent) -> None:
        """Apply an event to the projection."""
        if self.can_handle(event):
            self.handle_event(event)
            self.version += 1
            self.last_event_timestamp = event.metadata.timestamp
            self.last_event_id = str(event.metadata.event_id)
    
    def get_state(self) -> ProjectionState[T]:
        """Get the current projection state."""
        return ProjectionState(
            projection_name=self.name,
            last_event_timestamp=self.last_event_timestamp,
            last_event_id=self.last_event_id,
            version=self.version,
            data=self.state
        )
    
    def reset(self) -> None:
        """Reset projection to initial state."""
        self.state = self._initial_state()
        self.version = 0
        self.last_event_timestamp = None
        self.last_event_id = None


# Concrete Projections

class SceneProjection(Projection[Dict[str, Any]]):
    """Projection for scene-related data."""
    
    def _initial_state(self) -> Dict[str, Any]:
        return {
            "current_scene": "Unknown",
            "previous_scene": None,
            "scenes": [],
            "scene_switch_count": 0,
            "last_switch_time": None,
            "scene_durations": defaultdict(float),
            "most_used_scene": None
        }
    
    def handle_event(self, event: DomainEvent) -> None:
        if event.event_type == EventType.SCENE_CREATED:
            data = event.get_event_data()
            scene_name = data["scene_name"]
            if scene_name not in self.state["scenes"]:
                self.state["scenes"].append(scene_name)
        
        elif event.event_type == EventType.SCENE_SWITCHED:
            data = event.get_event_data()
            
            # Update scene tracking
            self.state["previous_scene"] = self.state["current_scene"]
            self.state["current_scene"] = data["to_scene"]
            self.state["scene_switch_count"] += 1
            
            # Track duration in previous scene
            if self.state["last_switch_time"] and self.state["previous_scene"]:
                duration = (event.metadata.timestamp - self.state["last_switch_time"]).total_seconds()
                self.state["scene_durations"][self.state["previous_scene"]] += duration
            
            self.state["last_switch_time"] = event.metadata.timestamp
            
            # Update most used scene
            if self.state["scene_durations"]:
                self.state["most_used_scene"] = max(
                    self.state["scene_durations"].items(),
                    key=lambda x: x[1]
                )[0]
        
        elif event.event_type == EventType.SCENE_DELETED:
            data = event.get_event_data()
            scene_name = data.get("scene_name")
            if scene_name in self.state["scenes"]:
                self.state["scenes"].remove(scene_name)


class StreamingProjection(Projection[Dict[str, Any]]):
    """Projection for streaming statistics."""
    
    def _initial_state(self) -> Dict[str, Any]:
        return {
            "is_streaming": False,
            "stream_start_time": None,
            "total_stream_time": 0,
            "stream_count": 0,
            "total_frames": 0,
            "dropped_frames": 0,
            "bytes_sent": 0,
            "average_stream_duration": 0,
            "longest_stream_duration": 0,
            "stream_history": []
        }
    
    def handle_event(self, event: DomainEvent) -> None:
        if event.event_type == EventType.STREAM_STARTED:
            self.state["is_streaming"] = True
            self.state["stream_start_time"] = event.metadata.timestamp
            self.state["stream_count"] += 1
        
        elif event.event_type == EventType.STREAM_STOPPED:
            data = event.get_event_data()
            
            self.state["is_streaming"] = False
            
            # Update statistics
            duration = data["duration_seconds"]
            self.state["total_stream_time"] += duration
            self.state["total_frames"] += data["total_frames"]
            self.state["dropped_frames"] += data["dropped_frames"]
            self.state["bytes_sent"] += data["bytes_sent"]
            
            # Update averages
            if self.state["stream_count"] > 0:
                self.state["average_stream_duration"] = (
                    self.state["total_stream_time"] / self.state["stream_count"]
                )
            
            # Track longest stream
            if duration > self.state["longest_stream_duration"]:
                self.state["longest_stream_duration"] = duration
            
            # Add to history
            self.state["stream_history"].append({
                "start_time": self.state["stream_start_time"].isoformat() if self.state["stream_start_time"] else None,
                "end_time": event.metadata.timestamp.isoformat(),
                "duration": duration,
                "frames": data["total_frames"],
                "dropped": data["dropped_frames"]
            })
            
            # Keep only last 100 streams in history
            if len(self.state["stream_history"]) > 100:
                self.state["stream_history"] = self.state["stream_history"][-100:]
            
            self.state["stream_start_time"] = None


class AutomationProjection(Projection[Dict[str, Any]]):
    """Projection for automation rule execution statistics."""
    
    def _initial_state(self) -> Dict[str, Any]:
        return {
            "rules": {},
            "total_executions": 0,
            "total_failures": 0,
            "average_execution_time": 0,
            "most_triggered_rule": None,
            "recent_executions": []
        }
    
    def handle_event(self, event: DomainEvent) -> None:
        if event.event_type == EventType.AUTOMATION_RULE_CREATED:
            data = event.get_event_data()
            rule_id = data.get("rule_id")
            if rule_id:
                self.state["rules"][rule_id] = {
                    "name": data.get("rule_name"),
                    "trigger_count": 0,
                    "execution_count": 0,
                    "failure_count": 0,
                    "total_execution_time": 0,
                    "enabled": True
                }
        
        elif event.event_type == EventType.AUTOMATION_RULE_TRIGGERED:
            data = event.get_event_data()
            rule_id = data["rule_id"]
            if rule_id in self.state["rules"]:
                self.state["rules"][rule_id]["trigger_count"] += 1
        
        elif event.event_type == EventType.AUTOMATION_RULE_EXECUTED:
            data = event.get_event_data()
            rule_id = data["rule_id"]
            
            self.state["total_executions"] += 1
            
            if rule_id in self.state["rules"]:
                rule = self.state["rules"][rule_id]
                rule["execution_count"] += 1
                rule["total_execution_time"] += data["execution_time_ms"]
            
            # Update average execution time
            total_time = sum(
                r["total_execution_time"] 
                for r in self.state["rules"].values()
            )
            if self.state["total_executions"] > 0:
                self.state["average_execution_time"] = (
                    total_time / self.state["total_executions"]
                )
            
            # Track most triggered rule
            if self.state["rules"]:
                self.state["most_triggered_rule"] = max(
                    self.state["rules"].items(),
                    key=lambda x: x[1]["trigger_count"]
                )[0]
            
            # Add to recent executions
            self.state["recent_executions"].append({
                "rule_id": rule_id,
                "rule_name": data["rule_name"],
                "timestamp": event.metadata.timestamp.isoformat(),
                "execution_time_ms": data["execution_time_ms"],
                "actions": data["actions_executed"]
            })
            
            # Keep only last 50 executions
            if len(self.state["recent_executions"]) > 50:
                self.state["recent_executions"] = self.state["recent_executions"][-50:]
        
        elif event.event_type == EventType.AUTOMATION_RULE_FAILED:
            data = event.get_event_data()
            rule_id = data.get("rule_id")
            
            self.state["total_failures"] += 1
            
            if rule_id in self.state["rules"]:
                self.state["rules"][rule_id]["failure_count"] += 1


class PerformanceProjection(Projection[Dict[str, Any]]):
    """Projection for system performance metrics."""
    
    def _initial_state(self) -> Dict[str, Any]:
        return {
            "event_rate": {
                "last_minute": 0,
                "last_hour": 0,
                "last_day": 0
            },
            "event_counts_by_type": defaultdict(int),
            "busiest_hour": None,
            "peak_event_rate": 0,
            "error_count": 0,
            "warning_count": 0,
            "time_windows": defaultdict(lambda: defaultdict(int))
        }
    
    def handle_event(self, event: DomainEvent) -> None:
        # Count events by type
        self.state["event_counts_by_type"][event.event_type.value] += 1
        
        # Track hourly patterns
        hour = event.metadata.timestamp.hour
        self.state["time_windows"]["hourly"][hour] += 1
        
        # Find busiest hour
        if self.state["time_windows"]["hourly"]:
            busiest = max(
                self.state["time_windows"]["hourly"].items(),
                key=lambda x: x[1]
            )
            self.state["busiest_hour"] = busiest[0]
        
        # Track errors and warnings
        if event.event_type == EventType.SYSTEM_ERROR:
            self.state["error_count"] += 1
        elif event.event_type == EventType.SYSTEM_PERFORMANCE_WARNING:
            self.state["warning_count"] += 1


# Projection Manager

class ProjectionBuilder:
    """
    Manages projections and keeps them updated with the event stream.
    
    This is responsible for:
    - Managing multiple projections
    - Keeping projections in sync with events
    - Providing query interfaces to projections
    - Handling projection rebuilds
    """
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.projections: Dict[str, Projection] = {}
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        
        # Register default projections
        self._register_default_projections()
        
        # Subscribe to new events
        self.event_store.subscribe(self._handle_new_event)
    
    def _register_default_projections(self):
        """Register default projections."""
        self.register_projection(SceneProjection("scenes"))
        self.register_projection(StreamingProjection("streaming"))
        self.register_projection(AutomationProjection("automation"))
        self.register_projection(PerformanceProjection("performance"))
    
    def register_projection(self, projection: Projection) -> None:
        """Register a new projection."""
        self.projections[projection.name] = projection
        
        # Rebuild projection from existing events
        self._rebuild_projection(projection)
    
    def _rebuild_projection(self, projection: Projection) -> None:
        """Rebuild a projection from the event stream."""
        projection.reset()
        
        # Get all events from the beginning
        events = self.event_store.replay_events()
        
        # Apply each event
        for event in events:
            projection.apply(event)
    
    def _handle_new_event(self, event: DomainEvent) -> None:
        """Handle a new event by updating all projections."""
        for projection in self.projections.values():
            projection.apply(event)
    
    def get_projection(self, name: str) -> Optional[Projection]:
        """Get a projection by name."""
        return self.projections.get(name)
    
    def get_projection_state(self, name: str) -> Optional[ProjectionState]:
        """Get the state of a projection."""
        projection = self.projections.get(name)
        return projection.get_state() if projection else None
    
    def query(self, projection_name: str, query_func: Callable[[Any], T]) -> Optional[T]:
        """
        Query a projection with a custom function.
        
        Example:
            result = builder.query("scenes", lambda s: s["current_scene"])
        """
        projection = self.projections.get(projection_name)
        if projection:
            return query_func(projection.state)
        return None
    
    async def start_continuous_update(self, interval: float = 1.0) -> None:
        """Start continuous projection updates."""
        self._running = True
        self._update_task = asyncio.create_task(
            self._continuous_update_loop(interval)
        )
    
    async def _continuous_update_loop(self, interval: float) -> None:
        """Continuously update projections."""
        last_update = datetime.utcnow()
        
        while self._running:
            # Get new events since last update
            events = self.event_store.replay_events(since=last_update)
            
            # Apply to all projections
            for event in events:
                for projection in self.projections.values():
                    projection.apply(event)
            
            last_update = datetime.utcnow()
            await asyncio.sleep(interval)
    
    async def stop_continuous_update(self) -> None:
        """Stop continuous updates."""
        self._running = False
        if self._update_task:
            await self._update_task
    
    def get_all_states(self) -> Dict[str, ProjectionState]:
        """Get states of all projections."""
        return {
            name: projection.get_state()
            for name, projection in self.projections.items()
        }