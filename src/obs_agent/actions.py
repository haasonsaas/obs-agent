"""
Pre-built automation actions for the Smart Scene Automation Engine.

This module provides a comprehensive set of ready-to-use actions that can be
combined to create powerful automation workflows.

Categories:
- Scene Management: Switch scenes, create/remove scenes
- Source Control: Mute/unmute, volume control, visibility
- Recording/Streaming: Start/stop operations
- Text & Media: Update text sources, media playback
- Advanced: Multi-step workflows, conditional actions
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union
from pathlib import Path

from .automation import AutomationContext
from .events import BaseEvent
from .logging import get_logger

logger = get_logger(__name__)


class ActionBuilder:
    """Builder class for creating complex automation actions."""

    def __init__(self, agent):
        self.agent = agent
        self._actions: List[Callable[[AutomationContext], Awaitable[Any]]] = []
        self._conditions: List[Callable[[AutomationContext], Awaitable[bool]]] = []

    def scene(self, scene_name: str):
        """Switch to a scene."""

        async def action(context: AutomationContext):
            await self.agent.set_scene(scene_name)
            logger.info(f"Automation: Switched to scene '{scene_name}'")

        self._actions.append(action)
        return self

    def mute(self, source_name: str, muted: bool = True):
        """Mute or unmute a source."""

        async def action(context: AutomationContext):
            await self.agent.set_source_mute(source_name, muted)
            status = "muted" if muted else "unmuted"
            logger.info(f"Automation: {status.capitalize()} source '{source_name}'")

        self._actions.append(action)
        return self

    def volume(self, source_name: str, volume_db: Optional[float] = None, volume_mul: Optional[float] = None):
        """Set source volume."""

        async def action(context: AutomationContext):
            await self.agent.set_source_volume(source_name, volume_db=volume_db, volume_mul=volume_mul)
            level = f"{volume_db}dB" if volume_db is not None else f"{volume_mul}x"
            logger.info(f"Automation: Set '{source_name}' volume to {level}")

        self._actions.append(action)
        return self

    def start_recording(self):
        """Start recording."""

        async def action(context: AutomationContext):
            if not (await self.agent.get_recording_status())["is_recording"]:
                await self.agent.start_recording()
                logger.info("Automation: Started recording")

        self._actions.append(action)
        return self

    def stop_recording(self):
        """Stop recording."""

        async def action(context: AutomationContext):
            if (await self.agent.get_recording_status())["is_recording"]:
                file_path = await self.agent.stop_recording()
                logger.info(f"Automation: Stopped recording, saved to {file_path}")

        self._actions.append(action)
        return self

    def start_streaming(self):
        """Start streaming."""

        async def action(context: AutomationContext):
            if not (await self.agent.get_streaming_status())["is_streaming"]:
                await self.agent.start_streaming()
                logger.info("Automation: Started streaming")

        self._actions.append(action)
        return self

    def stop_streaming(self):
        """Stop streaming."""

        async def action(context: AutomationContext):
            if (await self.agent.get_streaming_status())["is_streaming"]:
                await self.agent.stop_streaming()
                logger.info("Automation: Stopped streaming")

        self._actions.append(action)
        return self

    def text(self, source_name: str, text: str):
        """Update text source."""

        async def action(context: AutomationContext):
            await self.agent.set_source_settings(source_name, {"text": text})
            logger.info(f"Automation: Updated text source '{source_name}' to '{text}'")

        self._actions.append(action)
        return self

    def wait(self, seconds: float):
        """Add a delay."""

        async def action(context: AutomationContext):
            await asyncio.sleep(seconds)
            logger.debug(f"Automation: Waited {seconds} seconds")

        self._actions.append(action)
        return self

    def custom(self, action_func: Callable[[AutomationContext], Awaitable[Any]]):
        """Add a custom action function."""
        self._actions.append(action_func)
        return self

    def if_condition(self, condition: Callable[[AutomationContext], Awaitable[bool]]):
        """Add a condition that must be met for subsequent actions."""
        self._conditions.append(condition)
        return self

    def if_scene_is(self, scene_name: str):
        """Only execute if current scene matches."""

        async def condition(context: AutomationContext):
            current = await self.agent.get_current_scene()
            return current == scene_name

        return self.if_condition(condition)

    def if_source_muted(self, source_name: str, muted: bool = True):
        """Only execute if source mute state matches."""

        async def condition(context: AutomationContext):
            current_muted = await self.agent.get_source_mute(source_name)
            return current_muted == muted

        return self.if_condition(condition)

    def if_recording(self, recording: bool = True):
        """Only execute if recording state matches."""

        async def condition(context: AutomationContext):
            status = await self.agent.get_recording_status()
            return status["is_recording"] == recording

        return self.if_condition(condition)

    def if_streaming(self, streaming: bool = True):
        """Only execute if streaming state matches."""

        async def condition(context: AutomationContext):
            status = await self.agent.get_streaming_status()
            return status["is_streaming"] == streaming

        return self.if_condition(condition)

    async def build(self) -> Callable[[AutomationContext], Awaitable[Any]]:
        """Build the final action function."""
        actions = self._actions.copy()
        conditions = self._conditions.copy()

        async def combined_action(context: AutomationContext):
            # Check all conditions first
            for condition in conditions:
                if not await condition(context):
                    logger.debug("Automation: Condition not met, skipping actions")
                    return

            # Execute all actions in sequence
            for action in actions:
                await action(context)

        return combined_action


class SmartActions:
    """Collection of smart, pre-built automation actions."""

    def __init__(self, agent):
        self.agent = agent

    def create_brb_automation(
        self,
        brb_scene: str = "BRB",
        mic_source: str = "Microphone",
        status_text_source: Optional[str] = None,
        delay_seconds: float = 5.0,
    ) -> Callable[[AutomationContext], Awaitable[Any]]:
        """
        Create a 'Be Right Back' automation that switches to BRB scene when mic is muted.

        Args:
            brb_scene: Name of the BRB scene
            mic_source: Name of the microphone source
            status_text_source: Optional text source to update with status
            delay_seconds: Delay before switching to BRB scene
        """

        async def brb_action(context: AutomationContext):
            # Only trigger if microphone was muted
            if (
                context.trigger_event
                and hasattr(context.trigger_event, "input_muted")
                and context.trigger_event.input_muted
            ):

                # Wait for the delay
                await asyncio.sleep(delay_seconds)

                # Check if mic is still muted
                if await self.agent.get_source_mute(mic_source):
                    # Switch to BRB scene
                    await self.agent.set_scene(brb_scene)

                    # Update status text if provided
                    if status_text_source:
                        timestamp = datetime.now().strftime("%H:%M")
                        await self.agent.set_source_settings(
                            status_text_source, {"text": f"Be Right Back - Away since {timestamp}"}
                        )

                    logger.info("Automation: Activated BRB mode")

        return brb_action

    def create_return_automation(
        self, main_scene: str = "Main", mic_source: str = "Microphone", status_text_source: Optional[str] = None
    ) -> Callable[[AutomationContext], Awaitable[Any]]:
        """
        Create a return automation that switches back to main scene when mic is unmuted.
        """

        async def return_action(context: AutomationContext):
            # Only trigger if microphone was unmuted
            if (
                context.trigger_event
                and hasattr(context.trigger_event, "input_muted")
                and not context.trigger_event.input_muted
            ):

                # Switch back to main scene
                await self.agent.set_scene(main_scene)

                # Clear status text if provided
                if status_text_source:
                    await self.agent.set_source_settings(status_text_source, {"text": "Welcome back!"})

                logger.info("Automation: Returned from BRB mode")

        return return_action

    def create_auto_record_stream(self) -> Callable[[AutomationContext], Awaitable[Any]]:
        """
        Create automation that automatically starts recording when streaming begins.
        """

        async def auto_record_action(context: AutomationContext):
            if (
                context.trigger_event
                and hasattr(context.trigger_event, "output_active")
                and context.trigger_event.output_active
            ):

                # Wait a moment for stream to stabilize
                await asyncio.sleep(2.0)

                # Start recording if not already recording
                recording_status = await self.agent.get_recording_status()
                if not recording_status["is_recording"]:
                    await self.agent.start_recording()
                    logger.info("Automation: Auto-started recording with stream")

        return auto_record_action

    def create_audio_ducking(
        self,
        music_source: str = "Music",
        mic_source: str = "Microphone",
        ducked_volume_db: float = -20.0,
        normal_volume_db: float = -5.0,
    ) -> Callable[[AutomationContext], Awaitable[Any]]:
        """
        Create audio ducking automation that lowers music when mic is active.
        """

        async def ducking_action(context: AutomationContext):
            if context.trigger_event and hasattr(context.trigger_event, "input_muted"):

                if context.trigger_event.input_muted:
                    # Mic muted - restore music volume
                    await self.agent.set_source_volume(music_source, volume_db=normal_volume_db)
                    logger.info(f"Automation: Restored {music_source} volume (mic muted)")
                else:
                    # Mic active - duck music
                    await self.agent.set_source_volume(music_source, volume_db=ducked_volume_db)
                    logger.info(f"Automation: Ducked {music_source} volume (mic active)")

        return ducking_action

    def create_scene_timer(
        self, timer_text_source: str, format_string: str = "Time in scene: {minutes}:{seconds:02d}"
    ) -> Callable[[AutomationContext], Awaitable[Any]]:
        """
        Create a scene timer that updates a text source with time spent in current scene.
        """
        scene_start_times = {}

        async def timer_action(context: AutomationContext):
            if context.trigger_event and hasattr(context.trigger_event, "scene_name"):

                scene_name = context.trigger_event.scene_name
                current_time = datetime.now()
                scene_start_times[scene_name] = current_time

                # Start timer task for this scene
                async def update_timer():
                    while True:
                        try:
                            # Check if we're still in the same scene
                            current_scene = await self.agent.get_current_scene()
                            if current_scene != scene_name:
                                break

                            # Calculate elapsed time
                            elapsed = datetime.now() - scene_start_times[scene_name]
                            minutes = int(elapsed.total_seconds() // 60)
                            seconds = int(elapsed.total_seconds() % 60)

                            # Update text source
                            timer_text = format_string.format(
                                minutes=minutes, seconds=seconds, elapsed=elapsed.total_seconds()
                            )

                            await self.agent.set_source_settings(timer_text_source, {"text": timer_text})

                            await asyncio.sleep(1.0)

                        except Exception as e:
                            logger.error(f"Error in scene timer: {e}")
                            break

                # Start the timer task
                asyncio.create_task(update_timer())
                logger.info(f"Automation: Started timer for scene '{scene_name}'")

        return timer_action

    def create_auto_screenshot(
        self, source_name: str, save_directory: str = "screenshots", filename_format: str = "screenshot_{timestamp}.png"
    ) -> Callable[[AutomationContext], Awaitable[Any]]:
        """
        Create automation that takes screenshots of a source.
        """

        async def screenshot_action(context: AutomationContext):
            try:
                # Create directory if it doesn't exist
                Path(save_directory).mkdir(parents=True, exist_ok=True)

                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = filename_format.format(timestamp=timestamp)
                file_path = Path(save_directory) / filename

                # Take screenshot
                await self.agent.take_screenshot(source_name, file_path)
                logger.info(f"Automation: Screenshot saved to {file_path}")

            except Exception as e:
                logger.error(f"Error taking screenshot: {e}")

        return screenshot_action

    def create_stream_stats_overlay(
        self,
        stats_text_source: str,
        update_interval: float = 5.0,
        format_string: str = "🔴 Live • Frames: {total_frames} • Dropped: {skipped_frames}",
    ) -> Callable[[AutomationContext], Awaitable[Any]]:
        """
        Create automation that updates a text overlay with stream statistics.
        """

        async def stats_action(context: AutomationContext):
            # Start stats update task
            async def update_stats():
                while True:
                    try:
                        # Check if still streaming
                        stream_status = await self.agent.get_streaming_status()
                        if not stream_status["is_streaming"]:
                            # Clear stats when not streaming
                            await self.agent.set_source_settings(stats_text_source, {"text": ""})
                            break

                        # Update stats text
                        stats_text = format_string.format(**stream_status)
                        await self.agent.set_source_settings(stats_text_source, {"text": stats_text})

                        await asyncio.sleep(update_interval)

                    except Exception as e:
                        logger.error(f"Error updating stream stats: {e}")
                        break

            # Only start if streaming started
            if (
                context.trigger_event
                and hasattr(context.trigger_event, "output_active")
                and context.trigger_event.output_active
            ):

                asyncio.create_task(update_stats())
                logger.info("Automation: Started stream stats overlay")

        return stats_action


def create_action_builder(agent) -> ActionBuilder:
    """Create a new action builder instance."""
    return ActionBuilder(agent)


def create_smart_actions(agent) -> SmartActions:
    """Create a new smart actions instance."""
    return SmartActions(agent)
