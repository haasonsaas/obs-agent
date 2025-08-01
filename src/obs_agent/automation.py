"""
Smart Scene Automation Engine for OBS Agent.

This module provides a powerful automation system that allows users to create
intelligent workflows using decorators and event-driven programming.

Features:
- Event-based triggers (@when)
- Time-based delays (@after_delay, @every)
- Conditional logic (@if_condition)
- Action chaining and complex workflows
- Rule management (enable/disable, priorities)
- Schedule-based automation

Example usage:
    @automation.when(InputMuteStateChanged, lambda e: e.input_name == "Microphone")
    @automation.after_delay(5.0)
    async def switch_to_brb():
        await agent.set_scene("BRB Screen")
        await agent.set_source_text("Status", "Microphone muted - BRB")
"""

import asyncio
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, Type, Union
import logging

from .events import BaseEvent, EventHandler
from .logging import get_logger

logger = get_logger(__name__)


class TriggerType(Enum):
    """Types of automation triggers."""

    EVENT = auto()
    TIME = auto()
    SCHEDULE = auto()
    CONDITION = auto()
    MANUAL = auto()


class RuleState(Enum):
    """States of automation rules."""

    ENABLED = auto()
    DISABLED = auto()
    PAUSED = auto()
    ERROR = auto()


class ActionResult(Enum):
    """Results of automation actions."""

    SUCCESS = auto()
    FAILED = auto()
    SKIPPED = auto()
    PENDING = auto()


@dataclass
class AutomationContext:
    """Context passed to automation actions."""

    trigger_event: Optional[BaseEvent] = None
    trigger_time: datetime = field(default_factory=datetime.now)
    rule_name: str = ""
    variables: Dict[str, Any] = field(default_factory=dict)
    execution_count: int = 0


@dataclass
class RuleExecution:
    """Record of a rule execution."""

    rule_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: ActionResult = ActionResult.PENDING
    error: Optional[str] = None
    context: Optional[AutomationContext] = None


class AutomationTrigger(ABC):
    """Base class for automation triggers."""

    def __init__(self, name: str, priority: int = 100):
        self.name = name
        self.priority = priority
        self.enabled = True

    @abstractmethod
    async def should_trigger(self, context: AutomationContext) -> bool:
        """Check if this trigger should fire."""
        pass

    @abstractmethod
    def setup(self, automation_engine: "AutomationEngine") -> None:
        """Set up the trigger (register event handlers, etc.)."""
        pass

    def cleanup(self) -> None:
        """Clean up the trigger."""
        pass


class EventTrigger(AutomationTrigger):
    """Trigger based on OBS events."""

    def __init__(
        self,
        event_type: Union[str, Type[BaseEvent]],
        condition: Optional[Callable[[BaseEvent], bool]] = None,
        name: Optional[str] = None,
        priority: int = 100,
    ):
        self.event_type = event_type
        self.condition = condition or (lambda e: True)
        event_name = event_type if isinstance(event_type, str) else event_type.__name__
        super().__init__(name or f"event:{event_name}", priority)
        self._engine: Optional["AutomationEngine"] = None

    async def should_trigger(self, context: AutomationContext) -> bool:
        """Check if event matches our criteria."""
        if not context.trigger_event:
            return False

        event_name = self.event_type if isinstance(self.event_type, str) else self.event_type.__name__

        if context.trigger_event.event_type != event_name:
            return False

        return self.condition(context.trigger_event)

    def setup(self, automation_engine: "AutomationEngine") -> None:
        """Register event handler."""
        self._engine = automation_engine

        @automation_engine.agent.on(self.event_type)
        async def on_event(event: BaseEvent):
            if self.enabled:
                context = AutomationContext(trigger_event=event, trigger_time=datetime.now())
                await automation_engine._process_trigger(self, context)


class TimeTrigger(AutomationTrigger):
    """Trigger based on time delays."""

    def __init__(self, delay_seconds: float, name: Optional[str] = None, priority: int = 100):
        self.delay_seconds = delay_seconds
        super().__init__(name or f"delay:{delay_seconds}s", priority)
        self._last_trigger: Optional[datetime] = None

    async def should_trigger(self, context: AutomationContext) -> bool:
        """Check if enough time has passed."""
        if self._last_trigger is None:
            self._last_trigger = context.trigger_time
            return False

        elapsed = (context.trigger_time - self._last_trigger).total_seconds()
        if elapsed >= self.delay_seconds:
            self._last_trigger = context.trigger_time
            return True

        return False

    def setup(self, automation_engine: "AutomationEngine") -> None:
        """Set up periodic checking."""

        async def check_trigger():
            while self.enabled:
                context = AutomationContext(trigger_time=datetime.now())
                if await self.should_trigger(context):
                    await automation_engine._process_trigger(self, context)
                await asyncio.sleep(min(1.0, self.delay_seconds / 10))

        asyncio.create_task(check_trigger())


class ScheduleTrigger(AutomationTrigger):
    """Trigger based on schedule (cron-like)."""

    def __init__(
        self,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        second: Optional[int] = None,
        weekday: Optional[int] = None,
        name: Optional[str] = None,
        priority: int = 100,
    ):
        self.hour = hour
        self.minute = minute
        self.second = second
        self.weekday = weekday  # 0=Monday, 6=Sunday
        super().__init__(name or f"schedule:{hour}:{minute}", priority)
        self._last_trigger: Optional[datetime] = None

    async def should_trigger(self, context: AutomationContext) -> bool:
        """Check if current time matches schedule."""
        now = context.trigger_time

        # Check if we already triggered this minute
        if self._last_trigger and self._last_trigger.replace(second=0, microsecond=0) == now.replace(
            second=0, microsecond=0
        ):
            return False

        # Check schedule criteria
        if self.hour is not None and now.hour != self.hour:
            return False
        if self.minute is not None and now.minute != self.minute:
            return False
        if self.second is not None and now.second != self.second:
            return False
        if self.weekday is not None and now.weekday() != self.weekday:
            return False

        self._last_trigger = now
        return True

    def setup(self, automation_engine: "AutomationEngine") -> None:
        """Set up periodic schedule checking."""

        async def check_schedule():
            while self.enabled:
                context = AutomationContext(trigger_time=datetime.now())
                if await self.should_trigger(context):
                    await automation_engine._process_trigger(self, context)
                await asyncio.sleep(1.0)  # Check every second

        asyncio.create_task(check_schedule())


class ConditionTrigger(AutomationTrigger):
    """Trigger based on custom conditions."""

    def __init__(
        self,
        condition: Callable[[], Awaitable[bool]],
        check_interval: float = 1.0,
        name: Optional[str] = None,
        priority: int = 100,
    ):
        self.condition = condition
        self.check_interval = check_interval
        super().__init__(name or "condition", priority)

    async def should_trigger(self, context: AutomationContext) -> bool:
        """Evaluate the condition function."""
        try:
            return await self.condition()
        except Exception as e:
            logger.error(f"Error evaluating condition trigger {self.name}: {e}")
            return False

    def setup(self, automation_engine: "AutomationEngine") -> None:
        """Set up periodic condition checking."""

        async def check_condition():
            while self.enabled:
                context = AutomationContext(trigger_time=datetime.now())
                if await self.should_trigger(context):
                    await automation_engine._process_trigger(self, context)
                await asyncio.sleep(self.check_interval)

        asyncio.create_task(check_condition())


@dataclass
class AutomationRule:
    """Represents a complete automation rule."""

    name: str
    triggers: List[AutomationTrigger]
    action: Callable[[AutomationContext], Awaitable[Any]]
    description: str = ""
    enabled: bool = True
    priority: int = 100
    max_executions: Optional[int] = None
    cooldown_seconds: float = 0.0

    # Runtime state
    execution_count: int = 0
    last_execution: Optional[datetime] = None
    state: RuleState = RuleState.ENABLED
    error_count: int = 0


class AutomationEngine:
    """Main automation engine that manages rules and triggers."""

    def __init__(self, agent):
        self.agent = agent
        self.rules: Dict[str, AutomationRule] = {}
        self.executions: List[RuleExecution] = []
        self.variables: Dict[str, Any] = {}
        self._running = False
        self._stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "rules_created": 0,
        }

    def start(self) -> None:
        """Start the automation engine."""
        if self._running:
            return

        self._running = True
        logger.info("Automation engine started")

        # Set up all triggers
        for rule in self.rules.values():
            if rule.enabled:
                for trigger in rule.triggers:
                    trigger.setup(self)

    def stop(self) -> None:
        """Stop the automation engine."""
        self._running = False
        logger.info("Automation engine stopped")

        # Clean up triggers
        for rule in self.rules.values():
            for trigger in rule.triggers:
                trigger.cleanup()

    def add_rule(self, rule: AutomationRule) -> None:
        """Add an automation rule."""
        self.rules[rule.name] = rule
        self._stats["rules_created"] += 1
        logger.info(f"Added automation rule: {rule.name}")

        # Set up triggers if engine is running
        if self._running and rule.enabled:
            for trigger in rule.triggers:
                trigger.setup(self)

    def remove_rule(self, name: str) -> bool:
        """Remove an automation rule."""
        if name not in self.rules:
            return False

        rule = self.rules[name]

        # Clean up triggers
        for trigger in rule.triggers:
            trigger.cleanup()

        del self.rules[name]
        logger.info(f"Removed automation rule: {name}")
        return True

    def enable_rule(self, name: str) -> bool:
        """Enable an automation rule."""
        if name not in self.rules:
            return False

        rule = self.rules[name]
        rule.enabled = True
        rule.state = RuleState.ENABLED

        # Set up triggers if engine is running
        if self._running:
            for trigger in rule.triggers:
                trigger.setup(self)

        logger.info(f"Enabled automation rule: {name}")
        return True

    def disable_rule(self, name: str) -> bool:
        """Disable an automation rule."""
        if name not in self.rules:
            return False

        rule = self.rules[name]
        rule.enabled = False
        rule.state = RuleState.DISABLED

        # Clean up triggers
        for trigger in rule.triggers:
            trigger.cleanup()

        logger.info(f"Disabled automation rule: {name}")
        return True

    async def _process_trigger(self, trigger: AutomationTrigger, context: AutomationContext) -> None:
        """Process a triggered automation."""
        if not self._running:
            return

        # Find rules that use this trigger
        matching_rules = [rule for rule in self.rules.values() if rule.enabled and trigger in rule.triggers]

        # Sort by priority
        matching_rules.sort(key=lambda r: r.priority, reverse=True)

        for rule in matching_rules:
            await self._execute_rule(rule, context)

    async def _execute_rule(self, rule: AutomationRule, context: AutomationContext) -> None:
        """Execute an automation rule."""
        # Check cooldown
        if rule.last_execution and (datetime.now() - rule.last_execution).total_seconds() < rule.cooldown_seconds:
            logger.debug(f"Rule {rule.name} in cooldown, skipping")
            return

        # Check max executions
        if rule.max_executions and rule.execution_count >= rule.max_executions:
            logger.debug(f"Rule {rule.name} reached max executions, skipping")
            return

        # Check if all triggers should fire
        trigger_results = []
        for trigger in rule.triggers:
            should_fire = await trigger.should_trigger(context)
            trigger_results.append(should_fire)

        # All triggers must be satisfied (AND logic)
        if not all(trigger_results):
            return

        # Create execution record
        execution = RuleExecution(rule_name=rule.name, started_at=datetime.now(), context=context)

        context.rule_name = rule.name
        context.execution_count = rule.execution_count
        context.variables = self.variables.copy()

        self.executions.append(execution)
        self._stats["total_executions"] += 1

        try:
            logger.info(f"Executing automation rule: {rule.name}")

            # Execute the action
            result = await rule.action(context)

            # Update execution record
            execution.completed_at = datetime.now()
            execution.result = ActionResult.SUCCESS

            # Update rule state
            rule.execution_count += 1
            rule.last_execution = execution.started_at
            rule.error_count = 0  # Reset error count on success

            self._stats["successful_executions"] += 1

            logger.info(f"Successfully executed rule: {rule.name}")

        except Exception as e:
            # Update execution record
            execution.completed_at = datetime.now()
            execution.result = ActionResult.FAILED
            execution.error = str(e)

            # Update rule state
            rule.error_count += 1
            if rule.error_count >= 5:  # Disable after 5 consecutive errors
                rule.state = RuleState.ERROR
                rule.enabled = False
                logger.error(f"Rule {rule.name} disabled due to repeated errors")

            self._stats["failed_executions"] += 1

            logger.error(f"Error executing rule {rule.name}: {e}", exc_info=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get automation engine statistics."""
        return {
            **self._stats,
            "active_rules": len([r for r in self.rules.values() if r.enabled]),
            "total_rules": len(self.rules),
            "recent_executions": len(
                [e for e in self.executions if (datetime.now() - e.started_at).total_seconds() < 3600]
            ),
        }

    def get_rule_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific rule."""
        if name not in self.rules:
            return None

        rule = self.rules[name]
        recent_executions = [e for e in self.executions if e.rule_name == name][-10:]

        return {
            "name": rule.name,
            "description": rule.description,
            "enabled": rule.enabled,
            "state": rule.state.name,
            "execution_count": rule.execution_count,
            "last_execution": rule.last_execution.isoformat() if rule.last_execution else None,
            "error_count": rule.error_count,
            "recent_executions": [
                {"started_at": e.started_at.isoformat(), "result": e.result.name, "error": e.error}
                for e in recent_executions
            ],
        }


# Decorator-based DSL for creating automation rules
class AutomationDecorator:
    """Decorator class for building automation rules."""

    def __init__(self, engine: AutomationEngine):
        self.engine = engine
        self._current_triggers: List[AutomationTrigger] = []
        self._current_priority = 100
        self._current_description = ""
        self._current_cooldown = 0.0
        self._current_max_executions: Optional[int] = None

    def when(
        self,
        event_type: Union[str, Type[BaseEvent]],
        condition: Optional[Callable[[BaseEvent], bool]] = None,
        priority: int = 100,
    ):
        """Add an event trigger."""

        def decorator(func):
            trigger = EventTrigger(event_type, condition, priority=priority)
            self._current_triggers.append(trigger)
            self._current_priority = priority
            return self._create_rule(func)

        return decorator

    def after_delay(self, seconds: float, priority: int = 100):
        """Add a time delay trigger."""

        def decorator(func):
            trigger = TimeTrigger(seconds, priority=priority)
            self._current_triggers.append(trigger)
            self._current_priority = priority
            return self._create_rule(func)

        return decorator

    def every(self, seconds: float, priority: int = 100):
        """Add a recurring time trigger."""

        def decorator(func):
            trigger = TimeTrigger(seconds, priority=priority)
            self._current_triggers.append(trigger)
            self._current_priority = priority
            return self._create_rule(func)

        return decorator

    def at_time(
        self,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        second: Optional[int] = None,
        weekday: Optional[int] = None,
        priority: int = 100,
    ):
        """Add a schedule trigger."""

        def decorator(func):
            trigger = ScheduleTrigger(hour, minute, second, weekday, priority=priority)
            self._current_triggers.append(trigger)
            self._current_priority = priority
            return self._create_rule(func)

        return decorator

    def if_condition(self, condition: Callable[[], Awaitable[bool]], check_interval: float = 1.0, priority: int = 100):
        """Add a condition trigger."""

        def decorator(func):
            trigger = ConditionTrigger(condition, check_interval, priority=priority)
            self._current_triggers.append(trigger)
            self._current_priority = priority
            return self._create_rule(func)

        return decorator

    def description(self, desc: str):
        """Add description to the rule."""

        def decorator(func):
            self._current_description = desc
            return func

        return decorator

    def cooldown(self, seconds: float):
        """Add cooldown to the rule."""

        def decorator(func):
            self._current_cooldown = seconds
            return func

        return decorator

    def max_executions(self, count: int):
        """Set maximum executions for the rule."""

        def decorator(func):
            self._current_max_executions = count
            return func

        return decorator

    def _create_rule(self, func: Callable[[AutomationContext], Awaitable[Any]]):
        """Create and register the automation rule."""
        if not self._current_triggers:
            raise ValueError("No triggers defined for automation rule")

        rule_name = func.__name__
        rule = AutomationRule(
            name=rule_name,
            triggers=self._current_triggers.copy(),
            action=func,
            description=self._current_description,
            priority=self._current_priority,
            cooldown_seconds=self._current_cooldown,
            max_executions=self._current_max_executions,
        )

        self.engine.add_rule(rule)

        # Reset current state
        self._current_triggers.clear()
        self._current_description = ""
        self._current_cooldown = 0.0
        self._current_max_executions = None
        self._current_priority = 100

        return func


# Integration with OBSAgent
def add_automation_to_agent(agent_class):
    """Add automation capabilities to an OBS Agent class."""

    def init_automation(self):
        """Initialize automation engine."""
        if not hasattr(self, "_automation_engine"):
            self._automation_engine = AutomationEngine(self)
            self._automation_decorator = AutomationDecorator(self._automation_engine)

    def automation_property(self):
        """Get the automation decorator."""
        if not hasattr(self, "_automation_engine"):
            self.init_automation()
        return self._automation_decorator

    def start_automation(self):
        """Start the automation engine."""
        if not hasattr(self, "_automation_engine"):
            self.init_automation()
        self._automation_engine.start()

    def stop_automation(self):
        """Stop the automation engine."""
        if hasattr(self, "_automation_engine"):
            self._automation_engine.stop()

    # Add methods to the agent class
    agent_class.init_automation = init_automation
    agent_class.automation = property(automation_property)
    agent_class.start_automation = start_automation
    agent_class.stop_automation = stop_automation

    return agent_class
