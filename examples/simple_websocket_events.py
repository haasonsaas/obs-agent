#!/usr/bin/env python3
"""
Simple WebSocket Events Example

Shows the basic usage of the enhanced WebSocket event system.
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.obs_agent import OBSAgentV2, create_obs_agent
from src.obs_agent.events import (
    CurrentProgramSceneChanged,
    InputMuteStateChanged,
    RecordStateChanged,
    StreamStateChanged,
)


async def main():
    """Simple example of using WebSocket events"""

    # Create OBS agent
    async with create_obs_agent() as agent:
        print("✅ Connected to OBS")

        # Method 1: Using decorator on the agent
        @agent.on(CurrentProgramSceneChanged)
        async def on_scene_changed(event: CurrentProgramSceneChanged):
            print(f"📺 Scene changed to: {event.scene_name}")

        # Method 2: Using the events property
        @agent.events.on(StreamStateChanged)
        async def on_stream_state(event: StreamStateChanged):
            if event.output_active:
                print("🔴 Stream started!")
            else:
                print("⏹️ Stream stopped!")

        # Method 3: With filters
        @agent.on(InputMuteStateChanged, lambda e: "Mic" in e.input_name)
        async def on_mic_mute(event: InputMuteStateChanged):
            status = "muted" if event.input_muted else "unmuted"
            print(f"🎤 Microphone {status}")

        # Method 4: Multiple handlers for same event
        @agent.on(RecordStateChanged)
        async def log_recording(event: RecordStateChanged):
            print(f"📝 Recording state: {event.output_state}")

        @agent.on(RecordStateChanged)
        async def notify_recording(event: RecordStateChanged):
            if event.output_active:
                print("🎬 Recording started - Be professional!")
            elif event.output_path:
                print(f"💾 Recording saved to: {event.output_path}")

        # Interact with OBS to trigger events
        print("\n🎮 Testing event system...")

        # Get current scene
        current_scene = await agent.get_current_scene()
        print(f"Current scene: {current_scene}")

        # Get all scenes
        scenes = await agent.get_scenes()
        print(f"Available scenes: {scenes}")

        # Switch scenes if there are multiple
        if len(scenes) > 1:
            other_scene = next(s for s in scenes if s != current_scene)
            print(f"\nSwitching to: {other_scene}")
            await agent.set_scene(other_scene)

            await asyncio.sleep(1)

            print(f"Switching back to: {current_scene}")
            await agent.set_scene(current_scene)

        # Test audio mute if there are audio sources
        sources = await agent.get_sources()
        audio_sources = [s for s in sources if "audio" in s.get("inputKind", "").lower()]

        if audio_sources:
            audio_source = audio_sources[0]["inputName"]
            print(f"\nToggling mute on: {audio_source}")
            await agent.toggle_source_mute(audio_source)
            await asyncio.sleep(0.5)
            await agent.toggle_source_mute(audio_source)

        # Wait for any async events to complete
        await asyncio.sleep(1)

        print("\n✅ Event demo completed!")


if __name__ == "__main__":
    asyncio.run(main())
