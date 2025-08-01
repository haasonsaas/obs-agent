#!/usr/bin/env python3
"""OBS Agent Demo - Interactive control of OBS"""

import asyncio
import os

from advanced_features import AdvancedOBSAgent
from dotenv import load_dotenv

from obs_agent import OBSAgent

load_dotenv()


async def demo_menu():
    """Interactive demo menu"""
    agent = AdvancedOBSAgent(host="localhost", port=4455, password=os.getenv("OBS_WEBSOCKET_PASSWORD", ""))

    if not await agent.connect():
        print("❌ Failed to connect to OBS")
        return

    print("\n🎬 OBS Agent Demo")
    print("=" * 40)

    while True:
        print("\n📋 Options:")
        print("1. Show current status")
        print("2. Create demo scenes")
        print("3. Start/Stop recording")
        print("4. Add text overlay")
        print("5. Audio level check")
        print("6. Take screenshot")
        print("7. Scene automation demo")
        print("8. Exit")

        choice = input("\nSelect option (1-8): ").strip()

        try:
            if choice == "1":
                # Show status
                current_scene = await agent.get_current_scene()
                scenes = await agent.get_scenes()
                sources = await agent.get_sources()
                recording = await agent.get_recording_status()

                print(f"\n📊 Current Status:")
                print(f"🎬 Scene: {current_scene}")
                print(f"📋 Total Scenes: {len(scenes)}")
                print(f"🎤 Total Sources: {len(sources)}")
                print(f"🔴 Recording: {'Yes' if recording['is_recording'] else 'No'}")

            elif choice == "2":
                # Create demo scenes
                print("\n🎨 Creating demo scenes...")

                demo_scenes = ["Main", "Gaming", "Starting Soon", "Be Right Back", "Ending"]
                for scene_name in demo_scenes:
                    if scene_name not in await agent.get_scenes():
                        await agent.create_scene(scene_name)
                        print(f"✅ Created scene: {scene_name}")
                    else:
                        print(f"ℹ️  Scene already exists: {scene_name}")

            elif choice == "3":
                # Toggle recording
                status = await agent.get_recording_status()
                if status["is_recording"]:
                    output_path = await agent.stop_recording()
                    print(f"\n⏹️  Recording stopped")
                    print(f"📁 File saved to: {output_path}")
                else:
                    await agent.start_recording()
                    print("\n🔴 Recording started!")

            elif choice == "4":
                # Add text overlay
                current_scene = await agent.get_current_scene()
                text = input("\nEnter text for overlay: ")

                item_id = await agent.create_source(
                    scene_name=current_scene,
                    source_name="Demo Text Overlay",
                    source_kind="text_gdiplus_v2" if os.name == "nt" else "text_ft2_source_v2",
                    settings={"text": text, "font": {"face": "Arial", "size": 72}, "color": 0xFFFFFF},
                )

                if item_id > 0:
                    print(f"✅ Added text overlay: '{text}'")
                else:
                    print("❌ Failed to add text overlay")

            elif choice == "5":
                # Check audio levels
                print("\n🎤 Audio Sources:")
                sources = await agent.get_sources()
                audio_sources = [s for s in sources if "Audio" in s.get("inputKind", "")]

                if not audio_sources:
                    print("No audio sources found")
                else:
                    for source in audio_sources:
                        name = source["inputName"]
                        volume = await agent.get_source_volume(name)
                        muted = await agent.get_source_mute(name)
                        status = "🔇 MUTED" if muted else "🔊 Active"
                        print(f"{name}: {volume['volume_db']:.1f} dB {status}")

            elif choice == "6":
                # Take screenshot
                sources = await agent.get_sources()
                if sources:
                    source_name = sources[0]["inputName"]
                    filename = f"obs_screenshot_{asyncio.get_event_loop().time():.0f}.png"
                    success = await agent.take_screenshot(source_name, filename)
                    if success:
                        print(f"📸 Screenshot saved: {filename}")
                    else:
                        print("❌ Failed to take screenshot")
                else:
                    print("No sources available for screenshot")

            elif choice == "7":
                # Scene automation demo
                print("\n🤖 Starting scene automation demo...")
                scenes = await agent.get_scenes()

                if len(scenes) < 2:
                    print("Please create at least 2 scenes first (option 2)")
                else:
                    print("Switching scenes every 3 seconds...")
                    print("Press Ctrl+C to stop")

                    try:
                        for i in range(10):  # Switch 10 times
                            scene = scenes[i % len(scenes)]
                            print(f"➡️  Switching to: {scene}")
                            await agent.set_scene(scene)
                            await asyncio.sleep(3)
                        print("\n✅ Demo complete!")
                    except KeyboardInterrupt:
                        print("\n⏹️  Demo stopped")

            elif choice == "8":
                print("\n👋 Goodbye!")
                break

            else:
                print("❌ Invalid option")

        except Exception as e:
            print(f"❌ Error: {str(e)}")

    agent.disconnect()


async def quick_demo():
    """Quick automated demo"""
    print("🚀 Running quick OBS demo...")

    agent = AdvancedOBSAgent(password=os.getenv("OBS_WEBSOCKET_PASSWORD"))

    if await agent.connect():
        # Create a demo scene with text
        if "Demo Scene" not in await agent.get_scenes():
            await agent.create_scene("Demo Scene")

        await agent.set_scene("Demo Scene")

        # Add animated text
        messages = [
            "Hello from OBS Agent! 👋",
            "I can control OBS programmatically 🤖",
            "Watch me change this text! ✨",
            "Recording, streaming, and more! 🎬",
            "Thanks for testing! 🎉",
        ]

        # Create text source
        await agent.create_source(
            scene_name="Demo Scene",
            source_name="Demo Message",
            source_kind="text_gdiplus_v2" if os.name == "nt" else "text_ft2_source_v2",
            settings={"text": messages[0], "font": {"face": "Arial", "size": 60}, "color": 0xFFFFFF},
        )

        print("\n🎬 Watch OBS - text will change every 2 seconds!")

        # Animate text
        for i, message in enumerate(messages):
            print(f"{i+1}/5: {message}")
            await agent.set_source_settings("Demo Message", {"text": message})
            await asyncio.sleep(2)

        print("\n✅ Demo complete!")
        agent.disconnect()
    else:
        print("❌ Failed to connect to OBS")


async def main():
    print("🎬 OBS Agent Demo")
    print("=" * 40)
    print("1. Interactive demo (control OBS manually)")
    print("2. Quick automated demo")

    choice = input("\nSelect demo type (1 or 2): ").strip()

    if choice == "1":
        await demo_menu()
    elif choice == "2":
        await quick_demo()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
