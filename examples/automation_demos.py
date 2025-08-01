#!/usr/bin/env python3
"""
Smart Scene Automation Engine - Comprehensive Demo

This demo showcases the powerful automation capabilities of the OBS Agent,
including all major features:

1. Event-based triggers (@when)
2. Time-based automation (@after_delay, @every, @at_time) 
3. Conditional logic (@if_condition)
4. Action builder patterns
5. Smart pre-built automations
6. Rule management and monitoring

Usage:
    python examples/automation_demos.py

Make sure OBS is running with WebSocket server enabled!
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.obs_agent import OBSAgent
from src.obs_agent.events import (
    CurrentProgramSceneChanged,
    InputMuteStateChanged,
    RecordStateChanged,
    StreamStateChanged,
)


class AutomationDemo:
    """Comprehensive automation demo showcasing all features."""

    def __init__(self):
        self.agent = OBSAgent()

    async def run_full_demo(self):
        """Run the complete automation demo."""
        print("🚀 OBS Smart Scene Automation Engine Demo")
        print("=" * 60)
        print("This demo showcases intelligent automation workflows")
        print("=" * 60)

        try:
            # Connect to OBS
            await self.agent.connect()
            print("✅ Connected to OBS")

            # Start automation engine
            self.agent.start_automation()
            print("🤖 Automation engine started")

            # Run different demo sections
            await self.demo_basic_event_automation()
            await self.demo_smart_brb_system()
            await self.demo_action_builder_patterns()
            await self.demo_audio_ducking()
            await self.demo_scheduled_automation()
            await self.demo_stream_recording_automation()
            await self.demo_rule_management()

            # Keep running to show automation in action
            print("\n🎯 Automation Demo Active!")
            print("=" * 40)
            print("The following automations are now running:")
            print("• BRB system (mute mic → switch to BRB scene)")
            print("• Return system (unmute mic → switch back)")
            print("• Audio ducking (mic activity affects music)")
            print("• Auto-recording when streaming")
            print("• Scheduled good morning message")
            print("\nTry interacting with OBS to see automation in action!")
            print("Press Ctrl+C to stop...")

            # Wait for user to test automations
            await asyncio.sleep(300)  # 5 minutes

        except KeyboardInterrupt:
            print("\n⏹️ Demo stopped by user")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            print("\n📊 Automation Statistics:")
            stats = self.agent.get_automation_stats()
            for key, value in stats.items():
                print(f"  {key}: {value}")

            self.agent.stop_automation()
            await self.agent.disconnect()
            print("👋 Demo completed!")

    async def demo_basic_event_automation(self):
        """Demo 1: Basic event-based automation."""
        print("\n📡 Demo 1: Basic Event Automation")
        print("-" * 40)

        # Simple scene change logging
        @self.agent.automation.when(CurrentProgramSceneChanged)
        @self.agent.automation.description("Log all scene changes with timestamp")
        async def log_scene_changes(context):
            event = context.trigger_event
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"🎬 [{timestamp}] Scene changed to: {event.scene_name}")

        print("✅ Added scene change logger")

        # Demonstration
        scenes = await self.agent.get_scenes()
        if len(scenes) >= 2:
            current = await self.agent.get_current_scene()
            other_scene = next((s for s in scenes if s != current), scenes[0])

            print(f"📺 Switching to {other_scene} to demonstrate...")
            await self.agent.set_scene(other_scene)
            await asyncio.sleep(1)

            print(f"📺 Switching back to {current}...")
            await self.agent.set_scene(current)
            await asyncio.sleep(1)

    async def demo_smart_brb_system(self):
        """Demo 2: Smart Be-Right-Back system."""
        print("\n🔇 Demo 2: Smart BRB System")
        print("-" * 40)

        # BRB automation using smart actions
        brb_action = self.agent.smart_actions.create_brb_automation(
            brb_scene="BRB",  # Assumes you have a "BRB" scene
            mic_source="Microphone",  # Adjust to your mic source name
            status_text_source=None,  # Add text source name if you have one
            delay_seconds=3.0,  # Shorter delay for demo
        )

        # Register with decorator
        @self.agent.automation.when(
            InputMuteStateChanged, lambda e: "Mic" in e.input_name and e.input_muted
        )
        @self.agent.automation.description("Switch to BRB scene when mic is muted")
        async def activate_brb_mode(context):
            await brb_action(context)

        # Return automation
        return_action = self.agent.smart_actions.create_return_automation(
            main_scene="Main",  # Adjust to your main scene name
            mic_source="Microphone",
        )

        @self.agent.automation.when(
            InputMuteStateChanged, lambda e: "Mic" in e.input_name and not e.input_muted
        )
        @self.agent.automation.description("Return from BRB mode when mic is unmuted")
        async def return_from_brb(context):
            await return_action(context)

        print("✅ Added smart BRB system")
        print("   💡 Mute your microphone to see BRB automation")
        print("   💡 Unmute to return to the main scene")

    async def demo_action_builder_patterns(self):
        """Demo 3: Action builder for complex workflows."""
        print("\n🔧 Demo 3: Action Builder Patterns")
        print("-" * 40)

        # Complex workflow using action builder
        @self.agent.automation.when(StreamStateChanged, lambda e: e.output_active)
        @self.agent.automation.description("Execute complex workflow when streaming starts")
        async def stream_start_workflow(context):
            print("🎥 Stream started - executing startup workflow...")

            # Use action builder for complex sequence
            workflow = await (
                self.agent.actions.scene("Main")  # Switch to main scene
                .wait(1.0)  # Wait 1 second
                .text("StreamStatus", "🔴 LIVE")  # Update status (if you have this source)
                .if_recording(False)  # Only if not already recording
                .start_recording()  # Start recording
                .custom(
                    async lambda ctx: print("🎊 Stream workflow completed!")
                )  # Custom action
                .build()
            )

            await workflow(context)

        print("✅ Added complex stream startup workflow")
        print("   💡 Start streaming to see the action builder in action")

    async def demo_audio_ducking(self):
        """Demo 4: Audio ducking system."""
        print("\n🎵 Demo 4: Audio Ducking System")
        print("-" * 40)

        # Audio ducking using smart actions
        ducking_action = self.agent.smart_actions.create_audio_ducking(
            music_source="Music",  # Adjust to your music source
            mic_source="Microphone",
            ducked_volume_db=-20.0,  # Lower volume when mic is active
            normal_volume_db=-5.0,  # Normal music volume
        )

        @self.agent.automation.when(InputMuteStateChanged, lambda e: "Mic" in e.input_name)
        @self.agent.automation.description("Duck music volume based on mic activity")
        async def audio_ducking(context):
            await ducking_action(context)

        print("✅ Added audio ducking system")
        print("   💡 Toggle your microphone to hear music volume changes")

    async def demo_scheduled_automation(self):
        """Demo 5: Scheduled automation."""
        print("\n⏰ Demo 5: Scheduled Automation")
        print("-" * 40)

        # Good morning message (every day at 9 AM)
        @self.agent.automation.at_time(hour=9, minute=0)
        @self.agent.automation.description("Daily good morning automation")
        async def good_morning(context):
            print("🌅 Good morning! Starting daily stream setup...")
            # Switch to morning scene, update overlays, etc.
            scenes = await self.agent.get_scenes()
            if "Morning" in scenes:
                await self.agent.set_scene("Morning")

        # Demo with current time + 10 seconds
        now = datetime.now()
        demo_minute = now.minute
        demo_second = (now.second + 10) % 60

        @self.agent.automation.at_time(minute=demo_minute, second=demo_second)
        @self.agent.automation.max_executions(1)  # Only run once
        @self.agent.automation.description("Demo scheduled automation")
        async def demo_scheduled_action(context):
            print(f"⏰ Scheduled automation triggered at {datetime.now().strftime('%H:%M:%S')}!")

        print(f"✅ Added scheduled automation (will trigger at :{demo_minute}:{demo_second:02d})")

    async def demo_stream_recording_automation(self):
        """Demo 6: Stream and recording automation."""
        print("\n📹 Demo 6: Stream & Recording Automation")
        print("-" * 40)

        # Auto-record when streaming
        auto_record_action = self.agent.smart_actions.create_auto_record_stream()

        @self.agent.automation.when(StreamStateChanged, lambda e: e.output_active)
        @self.agent.automation.description("Auto-start recording when streaming begins")
        async def auto_record_with_stream(context):
            await auto_record_action(context)

        # Stream stats overlay
        stats_action = self.agent.smart_actions.create_stream_stats_overlay(
            stats_text_source="StreamStats",  # Adjust if you have this source
            update_interval=5.0,
            format_string="🔴 Live • Frames: {total_frames} • Dropped: {skipped_frames}",
        )

        @self.agent.automation.when(StreamStateChanged)
        @self.agent.automation.description("Update stream statistics overlay")
        async def update_stream_stats(context):
            await stats_action(context)

        print("✅ Added stream & recording automation")
        print("   💡 Start streaming to see auto-recording and stats")

    async def demo_rule_management(self):
        """Demo 7: Rule management and monitoring."""
        print("\n⚙️ Demo 7: Rule Management")
        print("-" * 40)

        # Show all active rules
        stats = self.agent.get_automation_stats()
        print(f"📊 Active automation rules: {stats.get('active_rules', 0)}")
        print(f"📊 Total executions: {stats.get('total_executions', 0)}")

        # Demonstrate rule control
        print("\n🔧 Rule Management Examples:")

        # Add a test rule
        @self.agent.automation.every(30.0)  # Every 30 seconds
        @self.agent.automation.description("Periodic status check")
        async def periodic_status_check(context):
            current_scene = await self.agent.get_current_scene()
            print(f"📍 Status check: Current scene is '{current_scene}'")

        print("✅ Added periodic status check rule")

        # Show how to disable/enable rules
        await asyncio.sleep(2)
        print("⏸️ Disabling periodic status check...")
        self.agent.disable_automation_rule("periodic_status_check")

        await asyncio.sleep(2)
        print("▶️ Re-enabling periodic status check...")
        self.agent.enable_automation_rule("periodic_status_check")

        # Show rule status
        rule_status = self.agent.get_automation_rule_status("periodic_status_check")
        if rule_status:
            print(f"📋 Rule status: {rule_status['state']}")

    async def demo_interactive_mode(self):
        """Interactive mode for live testing."""
        print("\n🎮 Interactive Mode")
        print("-" * 40)
        print("Commands:")
        print("  scenes - List available scenes")
        print("  switch <scene> - Switch to scene")
        print("  mute - Toggle microphone mute")
        print("  stats - Show automation statistics")
        print("  rules - List automation rules")
        print("  quit - Exit interactive mode")

        while True:
            try:
                command = input("\n> ").strip().lower()

                if command == "quit":
                    break
                elif command == "scenes":
                    scenes = await self.agent.get_scenes()
                    current = await self.agent.get_current_scene()
                    print("Available scenes:")
                    for scene in scenes:
                        marker = " (current)" if scene == current else ""
                        print(f"  • {scene}{marker}")
                elif command.startswith("switch "):
                    scene_name = command[7:]
                    try:
                        await self.agent.set_scene(scene_name)
                        print(f"✅ Switched to scene: {scene_name}")
                    except Exception as e:
                        print(f"❌ Error switching scene: {e}")
                elif command == "stats":
                    stats = self.agent.get_automation_stats()
                    print("Automation Statistics:")
                    for key, value in stats.items():
                        print(f"  {key}: {value}")
                elif command == "rules":
                    stats = self.agent.get_automation_stats()
                    print(f"Total rules: {stats.get('total_rules', 0)}")
                    print(f"Active rules: {stats.get('active_rules', 0)}")
                else:
                    print("Unknown command. Type 'quit' to exit.")

            except KeyboardInterrupt:
                break


async def main():
    """Run the automation demo."""
    demo = AutomationDemo()

    # Check if user wants full demo or specific parts
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "interactive":
            await demo.run_interactive_demo()
        elif mode == "basic":
            await demo.run_basic_demo()
        else:
            print("Usage: python automation_demos.py [interactive|basic]")
    else:
        await demo.run_full_demo()


if __name__ == "__main__":
    asyncio.run(main())