#!/usr/bin/env python3
"""
WebSocket Events Demo - Demonstrates the enhanced event handling system

This example shows how to use:
- Typed event classes
- Decorator-based event handlers
- Event filtering
- Middleware
- Event recording and replay
- Subscription patterns
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.obs_agent import OBSAgent
from src.obs_agent.config import get_config
from src.obs_agent.events import (
    CurrentProgramSceneChanged,
    EventHandler,
    EventSubscription,
    InputMuteStateChanged,
    InputVolumeChanged,
    RecordStateChanged,
    SceneCreated,
    SceneRemoved,
    StreamStateChanged,
    error_handling_middleware,
    logging_middleware,
    performance_middleware,
)


class EventDemo:
    """Demonstrates various event handling patterns"""

    def __init__(self):
        self.agent = OBSAgent()
        self.event_count = 0
        self.scene_changes = []

    async def run(self):
        """Run the event demo"""
        try:
            # Connect to OBS
            await self.agent.connect()
            print("✅ Connected to OBS")
            print("=" * 60)

            # Set up event handlers
            self.setup_event_handlers()

            # Demonstrate different features
            await self.demonstrate_basic_events()
            await self.demonstrate_filtered_events()
            await self.demonstrate_event_recording()
            await self.demonstrate_middleware()
            await self.demonstrate_subscription_pattern()

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await self.agent.disconnect()

    def setup_event_handlers(self):
        """Set up various event handlers"""

        # 1. Basic event handler using decorator
        @self.agent.on(CurrentProgramSceneChanged)
        async def on_scene_changed(event: CurrentProgramSceneChanged):
            self.scene_changes.append(event)
            print(f"📺 Scene changed to: {event.scene_name}")
            self.event_count += 1

        # 2. Multiple events with same handler
        @self.agent.on(SceneCreated)
        @self.agent.on(SceneRemoved)
        async def on_scene_crud(event):
            action = "created" if isinstance(event, SceneCreated) else "removed"
            print(f"🎬 Scene {action}: {event.scene_name}")
            self.event_count += 1

        # 3. Stream/Recording state changes
        @self.agent.on(StreamStateChanged)
        async def on_stream_state(event: StreamStateChanged):
            status = "started" if event.output_active else "stopped"
            print(f"📡 Stream {status} - State: {event.output_state}")
            self.event_count += 1

        @self.agent.on(RecordStateChanged)
        async def on_record_state(event: RecordStateChanged):
            status = "started" if event.output_active else "stopped"
            print(f"🔴 Recording {status} - State: {event.output_state}")
            if event.output_path:
                print(f"   File: {event.output_path}")
            self.event_count += 1

        # 4. Audio events
        @self.agent.on(InputMuteStateChanged)
        async def on_mute_change(event: InputMuteStateChanged):
            mute_icon = "🔇" if event.input_muted else "🔊"
            print(f"{mute_icon} {event.input_name} muted: {event.input_muted}")
            self.event_count += 1

        @self.agent.on(InputVolumeChanged)
        async def on_volume_change(event: InputVolumeChanged):
            print(f"🎚️ {event.input_name} volume: {event.input_volume_db:.1f}dB")
            self.event_count += 1

    async def demonstrate_basic_events(self):
        """Demonstrate basic event handling"""
        print("\n🎯 Basic Event Handling Demo")
        print("-" * 40)

        # Get current scene
        current_scene = await self.agent.get_current_scene()
        print(f"Current scene: {current_scene}")

        # Create a test scene
        test_scene = f"Event Test {datetime.now().strftime('%H%M%S')}"
        await self.agent.create_scene(test_scene)

        # Switch to it
        await self.agent.set_scene(test_scene)
        await asyncio.sleep(0.5)  # Wait for events

        # Switch back
        await self.agent.set_scene(current_scene)
        await asyncio.sleep(0.5)

        # Remove test scene
        await self.agent.remove_scene(test_scene)
        await asyncio.sleep(0.5)

        print(f"\n📊 Processed {self.event_count} events")

    async def demonstrate_filtered_events(self):
        """Demonstrate event filtering"""
        print("\n🔍 Filtered Events Demo")
        print("-" * 40)

        # Handler that only responds to specific sources
        @self.agent.on(InputMuteStateChanged, lambda e: "Mic" in e.input_name or "Microphone" in e.input_name)
        async def on_mic_mute_only(event: InputMuteStateChanged):
            print(f"🎤 Microphone mute changed: {event.input_muted}")

        # Get audio sources
        sources = await self.agent.get_sources()
        audio_sources = [s for s in sources if "audio" in s.get("inputKind", "").lower()]

        if audio_sources:
            source = audio_sources[0]["inputName"]
            print(f"Testing with audio source: {source}")

            # Toggle mute
            await self.agent.toggle_source_mute(source)
            await asyncio.sleep(0.5)
            await self.agent.toggle_source_mute(source)
            await asyncio.sleep(0.5)

    async def demonstrate_event_recording(self):
        """Demonstrate event recording and replay"""
        print("\n📼 Event Recording Demo")
        print("-" * 40)

        # Start recording events
        self.agent.events.start_recording()
        print("Started recording events...")

        # Generate some events
        scenes = await self.agent.get_scenes()
        if len(scenes) >= 2:
            # Switch between scenes
            for i in range(3):
                scene = scenes[i % len(scenes)]
                await self.agent.set_scene(scene)
                await asyncio.sleep(0.5)

        # Stop recording
        recorded_events = self.agent.events.stop_recording()
        print(f"Recorded {len(recorded_events)} events")

        # Save events
        event_file = Path("recorded_events.json")
        self.agent.events.save_events(recorded_events, event_file)
        print(f"Saved events to {event_file}")

        # Replay events
        print("\nReplaying events at 2x speed...")
        await self.agent.events.replay_events(recorded_events, speed=2.0)

        # Clean up
        event_file.unlink(missing_ok=True)

    async def demonstrate_middleware(self):
        """Demonstrate middleware usage"""
        print("\n⚙️ Middleware Demo")
        print("-" * 40)

        # Add middleware
        self.agent.events.use(logging_middleware)
        self.agent.events.use(performance_middleware)
        self.agent.events.use(error_handling_middleware)

        print("Added logging, performance, and error handling middleware")

        # Custom middleware
        async def auth_middleware(event, next_handler):
            """Example: Check if user is authorized for certain events"""
            if isinstance(event, StreamStateChanged) and event.output_active:
                print("🔐 Checking streaming authorization...")
            await next_handler()

        self.agent.events.use(auth_middleware)

        # Trigger some events
        scenes = await self.agent.get_scenes()
        if scenes:
            await self.agent.set_scene(scenes[0])
            await asyncio.sleep(0.5)

    async def demonstrate_subscription_pattern(self):
        """Demonstrate subscription pattern"""
        print("\n📬 Subscription Pattern Demo")
        print("-" * 40)

        # Create subscription manager
        subscription = EventSubscription(self.agent.events)

        # Subscribe to events
        def scene_monitor(event: CurrentProgramSceneChanged):
            print(f"📊 Scene Monitor: Scene is now {event.scene_name}")

        subscription.subscribe(CurrentProgramSceneChanged, scene_monitor)

        # Analytics subscriber
        analytics_data = {"scene_changes": 0, "recording_time": 0}

        def analytics_tracker(event):
            if isinstance(event, CurrentProgramSceneChanged):
                analytics_data["scene_changes"] += 1
            elif isinstance(event, RecordStateChanged):
                if event.output_active:
                    analytics_data["recording_start"] = datetime.now()
                else:
                    start = analytics_data.get("recording_start")
                    if start:
                        analytics_data["recording_time"] += (datetime.now() - start).seconds

        subscription.subscribe(CurrentProgramSceneChanged, analytics_tracker)
        subscription.subscribe(RecordStateChanged, analytics_tracker)

        # Trigger events
        scenes = await self.agent.get_scenes()
        if len(scenes) >= 2:
            await self.agent.set_scene(scenes[0])
            await asyncio.sleep(0.5)
            await self.agent.set_scene(scenes[1])
            await asyncio.sleep(0.5)

        print(f"\n📈 Analytics: {analytics_data}")

        # Unsubscribe
        subscription.unsubscribe(CurrentProgramSceneChanged, scene_monitor)
        print("Unsubscribed scene monitor")


async def main():
    """Run the WebSocket events demo"""
    print("🚀 OBS WebSocket Events Demo")
    print("=" * 60)
    print("This demo showcases the enhanced event handling system")
    print("=" * 60)

    demo = EventDemo()
    await demo.run()

    print("\n✅ Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())
