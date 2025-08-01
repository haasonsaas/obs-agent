import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from advanced_features import AdvancedOBSAgent, AdvancedOBSController
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)


class OBSAutomation:
    def __init__(self, password: str = None):
        self.agent = AdvancedOBSAgent(password=password or os.getenv("OBS_WEBSOCKET_PASSWORD", ""))
        self.controller = AdvancedOBSController(self.agent)
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        await self.agent.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.agent.disconnect()


async def podcast_recording_automation():
    async with OBSAutomation() as automation:
        # Setup podcast recording
        print("Setting up podcast recording...")

        # Configure audio sources
        await automation.controller.apply_noise_suppression("Host Microphone", suppression_level=-30)
        await automation.controller.apply_compressor("Host Microphone", ratio=6.0, threshold=-24.0)

        await automation.controller.apply_noise_suppression("Guest Microphone", suppression_level=-30)
        await automation.controller.apply_compressor("Guest Microphone", ratio=6.0, threshold=-24.0)

        # Balance audio levels
        await automation.controller.balance_audio_levels(target_db=-20.0)

        # Set up scenes
        scenes_sequence = [
            {"scene": "Intro", "duration": 5},
            {"scene": "Host Only", "duration": 30},
            {"scene": "Split Screen", "duration": 1800},  # 30 minutes
            {"scene": "Outro", "duration": 5},
        ]

        # Start recording
        print("Starting podcast recording...")
        await automation.agent.start_recording()

        # Execute scene sequence
        for scene_config in scenes_sequence:
            scene_name = scene_config["scene"]
            duration = scene_config["duration"]

            print(f"Switching to scene: {scene_name}")
            await automation.agent.set_scene(scene_name)

            # Monitor audio levels during recording
            monitor_task = asyncio.create_task(
                automation.controller.monitor_and_auto_adjust_audio(
                    duration_seconds=duration, target_range=(-25.0, -15.0)
                )
            )

            await asyncio.sleep(duration)
            monitor_task.cancel()

        # Stop recording
        output_path = await automation.agent.stop_recording()
        print(f"Podcast recording saved to: {output_path}")

        return output_path


async def gaming_stream_automation():
    async with OBSAutomation() as automation:
        print("Setting up gaming stream...")

        # Configure scenes
        await automation.agent.set_scene("Starting Soon")

        # Apply filters to webcam
        await automation.controller.apply_chroma_key("Webcam", key_color=0x00FF00)

        # Configure audio
        await automation.agent.set_source_volume("Game Audio", volume_db=-15.0)
        await automation.agent.set_source_volume("Microphone", volume_db=-20.0)
        await automation.controller.apply_noise_suppression("Microphone", suppression_level=-40)

        # Create PIP layout for webcam
        await automation.controller.create_pip_layout(
            main_source="Game Capture", pip_source="Webcam", pip_position=(0.75, 0.75), pip_scale=0.2
        )

        # Countdown and start stream
        print("Starting countdown...")
        await automation.controller.create_stream_starting_sequence(
            countdown_seconds=10, starting_scene="Starting Soon"
        )

        # Switch to game scene
        await automation.agent.set_scene("Gaming")

        # Enable replay buffer for highlights
        await automation.agent.start_replay_buffer()
        print("Replay buffer active - press hotkey to save highlights")

        # Monitor stream health
        def health_alert(message):
            print(f"⚠️  Stream Alert: {message}")

        monitor_task = asyncio.create_task(automation.controller.monitor_stream_health(health_alert))

        # Stream for specified duration
        stream_duration = 7200  # 2 hours
        print(f"Streaming for {stream_duration/3600} hours...")
        await asyncio.sleep(stream_duration)

        # End stream sequence
        print("Ending stream...")
        await automation.agent.set_scene("Ending Soon")
        await asyncio.sleep(30)

        # Stop everything
        monitor_task.cancel()
        await automation.agent.stop_replay_buffer()
        await automation.agent.stop_streaming()

        print("Stream ended successfully")


async def tutorial_recording_automation():
    async with OBSAutomation() as automation:
        print("Setting up tutorial recording...")

        # Configure sources
        await automation.agent.create_source(
            scene_name="Tutorial", source_name="Screen Capture", source_kind="monitor_capture", settings={"monitor": 0}
        )

        await automation.agent.create_source(
            scene_name="Tutorial",
            source_name="Mouse Highlight",
            source_kind="color_source",
            settings={"color": 0xFFFF00, "width": 50, "height": 50},
        )

        # Add text overlay for instructions
        await automation.agent.create_source(
            scene_name="Tutorial",
            source_name="Instructions",
            source_kind="text_gdiplus_v2",
            settings={
                "text": "Press Space to continue",
                "font": {"face": "Arial", "size": 36},
                "color": 0xFFFFFF,
                "outline": True,
                "outline_color": 0x000000,
                "outline_size": 2,
            },
        )

        # Tutorial sections
        sections = [
            {"title": "Introduction", "instruction": "Welcome to the tutorial", "duration": 10},
            {"title": "Setup", "instruction": "First, let's configure the settings", "duration": 30},
            {"title": "Main Content", "instruction": "Now for the main demonstration", "duration": 120},
            {"title": "Conclusion", "instruction": "Thank you for watching!", "duration": 10},
        ]

        # Start recording
        await automation.agent.start_recording()

        for section in sections:
            # Update instruction text
            await automation.agent.set_source_settings("Instructions", {"text": section["instruction"]})

            print(f"Recording section: {section['title']}")
            await asyncio.sleep(section["duration"])

        # Stop recording
        output_path = await automation.agent.stop_recording()
        print(f"Tutorial saved to: {output_path}")

        # Clean up created sources
        await automation.agent.remove_source("Instructions")
        await automation.agent.remove_source("Mouse Highlight")

        return output_path


async def multi_camera_event_automation():
    async with OBSAutomation() as automation:
        print("Setting up multi-camera event...")

        # Camera configuration
        cameras = [
            {"name": "Camera 1 - Wide", "scene": "Wide Shot"},
            {"name": "Camera 2 - Speaker", "scene": "Speaker"},
            {"name": "Camera 3 - Audience", "scene": "Audience"},
            {"name": "Camera 4 - Slides", "scene": "Presentation"},
        ]

        # Configure transitions
        await automation.agent.set_transition("Fade")
        await automation.agent.set_transition_duration(500)

        # Start recording and streaming
        await automation.agent.start_recording()
        await automation.agent.start_streaming()

        # Event schedule
        event_schedule = [
            {"scene": "Wide Shot", "duration": 60},
            {"scene": "Speaker", "duration": 300},
            {"scene": "Presentation", "duration": 600},
            {"scene": "Speaker", "duration": 120},
            {"scene": "Audience", "duration": 60},
            {"scene": "Wide Shot", "duration": 60},
        ]

        # Execute scheduled camera switches
        for segment in event_schedule:
            scene = segment["scene"]
            duration = segment["duration"]

            print(f"Switching to: {scene} for {duration}s")
            await automation.controller.create_animated_transition(
                from_scene=await automation.agent.get_current_scene(),
                to_scene=scene,
                transition_type="Fade",
                duration_ms=500,
            )

            await asyncio.sleep(duration)

        # End event
        await automation.agent.stop_streaming()
        output_path = await automation.agent.stop_recording()

        print(f"Event recording saved to: {output_path}")
        return output_path


async def scheduled_recording_automation(schedule: List[Dict]):
    async with OBSAutomation() as automation:
        print("Starting scheduled recording automation...")

        for task in schedule:
            start_time = datetime.fromisoformat(task["start_time"])
            duration = task["duration_minutes"] * 60
            scene = task["scene"]

            # Wait until start time
            wait_time = (start_time - datetime.now()).total_seconds()
            if wait_time > 0:
                print(f"Waiting {wait_time/60:.1f} minutes until next recording...")
                await asyncio.sleep(wait_time)

            # Start recording
            print(f"Starting scheduled recording: {task['name']}")
            await automation.agent.set_scene(scene)
            await automation.agent.start_recording()

            # Record for specified duration
            await asyncio.sleep(duration)

            # Stop recording
            output_path = await automation.agent.stop_recording()
            print(f"Recording saved to: {output_path}")

            # Optional: Upload or process the recording
            if task.get("auto_upload"):
                print(f"TODO: Upload {output_path} to {task['upload_destination']}")


async def dynamic_overlay_automation():
    async with OBSAutomation() as automation:
        print("Setting up dynamic overlays...")

        # Create overlay sources
        overlays = {
            "follower_alert": {"text": "New Follower: {name}", "duration": 5, "position": (0.5, 0.1)},
            "donation_alert": {"text": "{name} donated ${amount}", "duration": 10, "position": (0.5, 0.9)},
            "chat_highlight": {"text": "{message}", "duration": 15, "position": (0.1, 0.8)},
        }

        # Create text sources for overlays
        for overlay_name, config in overlays.items():
            await automation.agent.create_source(
                scene_name="Main",
                source_name=overlay_name,
                source_kind="text_gdiplus_v2",
                settings={
                    "text": "",
                    "font": {"face": "Arial", "size": 48},
                    "color": 0xFFFFFF,
                    "outline": True,
                    "outline_color": 0x000000,
                    "outline_size": 3,
                },
            )

        # Simulate alerts (in real use, these would come from external sources)
        alerts = [
            {"type": "follower_alert", "data": {"name": "User123"}},
            {"type": "donation_alert", "data": {"name": "Supporter456", "amount": "10.00"}},
            {"type": "chat_highlight", "data": {"message": "Great stream!"}},
        ]

        # Process alerts
        for alert in alerts:
            alert_type = alert["type"]
            alert_data = alert["data"]
            overlay_config = overlays[alert_type]

            # Format text
            text = overlay_config["text"].format(**alert_data)

            # Update overlay text
            await automation.agent.set_source_settings(alert_type, {"text": text})

            # Show overlay
            scene_items = await automation.agent.get_scene_items("Main")
            for item in scene_items:
                if item.get("sourceName") == alert_type:
                    await automation.agent.set_scene_item_enabled("Main", item["sceneItemId"], True)
                    break

            print(f"Showing alert: {text}")

            # Wait for duration
            await asyncio.sleep(overlay_config["duration"])

            # Hide overlay
            for item in scene_items:
                if item.get("sourceName") == alert_type:
                    await automation.agent.set_scene_item_enabled("Main", item["sceneItemId"], False)
                    break


async def main():
    print("OBS Automation Scripts")
    print("=====================")
    print("1. Podcast Recording")
    print("2. Gaming Stream")
    print("3. Tutorial Recording")
    print("4. Multi-Camera Event")
    print("5. Dynamic Overlays Demo")

    choice = input("\nSelect automation (1-5): ")

    automations = {
        "1": podcast_recording_automation,
        "2": gaming_stream_automation,
        "3": tutorial_recording_automation,
        "4": multi_camera_event_automation,
        "5": dynamic_overlay_automation,
    }

    if choice in automations:
        await automations[choice]()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
