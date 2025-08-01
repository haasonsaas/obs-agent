#!/usr/bin/env python3
"""Awesome OBS Agent Demo - Shows advanced capabilities"""

import asyncio
import os
import random

from advanced_features import AdvancedOBSAgent, AdvancedOBSController
from dotenv import load_dotenv

from obs_agent import OBSAgent

load_dotenv()


async def create_professional_stream_setup():
    """Create a professional streaming setup automatically"""
    print("🎬 OBS Agent - Professional Stream Setup Demo")
    print("=" * 50)

    agent = AdvancedOBSAgent(password=os.getenv("OBS_WEBSOCKET_PASSWORD"))
    controller = AdvancedOBSController(agent)

    if not await agent.connect():
        print("❌ Failed to connect")
        return

    try:
        # 1. Create professional scene collection
        print("\n📋 Creating Professional Scene Collection...")

        scenes = {
            "🎬 Main": "Main content scene",
            "📺 Starting Soon": "Pre-stream countdown",
            "☕ Be Right Back": "Break screen",
            "💬 Just Chatting": "Interaction scene",
            "🎮 Gaming": "Gaming layout",
            "🎉 Ending": "Stream ending",
        }

        for scene_name, desc in scenes.items():
            if scene_name not in await agent.get_scenes():
                await agent.create_scene(scene_name)
                print(f"  ✅ Created: {scene_name} - {desc}")

        # 2. Add dynamic text overlays
        print("\n📝 Adding Dynamic Text Overlays...")

        # Starting Soon countdown
        await agent.set_scene("📺 Starting Soon")
        await agent.create_source(
            scene_name="📺 Starting Soon",
            source_name="Countdown Text",
            source_kind="text_ft2_source_v2",
            settings={
                "text": "🚀 Stream Starting Soon! Get Ready! 🎉",
                "font": {"face": "Arial", "size": 72, "style": "Bold"},
                "color1": 0xFFFF00FF,  # Yellow
                "color2": 0xFFFF00FF,
            },
        )

        # Be Right Back message
        await agent.set_scene("☕ Be Right Back")
        await agent.create_source(
            scene_name="☕ Be Right Back",
            source_name="BRB Text",
            source_kind="text_ft2_source_v2",
            settings={
                "text": "☕ Quick Break - Be Right Back! ☕",
                "font": {"face": "Arial", "size": 64, "style": "Regular"},
                "color1": 0xFF00FFFF,  # Cyan
                "color2": 0xFF00FFFF,
            },
        )

        # 3. Audio setup simulation
        print("\n🎤 Setting Up Audio (Simulation)...")
        sources = await agent.get_sources()
        audio_sources = [s for s in sources if "Audio" in s.get("inputKind", "")]

        if audio_sources:
            print("  🔊 Balancing audio levels...")
            for source in audio_sources[:2]:  # Limit to 2 sources
                await agent.set_source_volume(source["inputName"], volume_db=-20.0)
                print(f"    ✅ {source['inputName']} set to -20dB")

        # 4. Automated scene tour
        print("\n🎬 Automated Scene Tour (20 seconds)...")
        print("  Watch OBS as I demonstrate scene transitions!\n")

        tour_sequence = [
            ("📺 Starting Soon", "Get ready for the stream!", 3),
            ("🎬 Main", "Welcome to the main show!", 4),
            ("💬 Just Chatting", "Time to interact with chat!", 3),
            ("🎮 Gaming", "Let's play some games!", 3),
            ("☕ Be Right Back", "Quick break!", 3),
            ("🎬 Main", "And we're back!", 3),
            ("🎉 Ending", "Thanks for watching!", 3),
        ]

        for scene, message, duration in tour_sequence:
            print(f"  ➡️  {scene}: {message}")
            await agent.set_scene(scene)

            # Update text if in main scene
            if scene == "🎬 Main":
                try:
                    await agent.create_source(
                        scene_name=scene,
                        source_name="Status Text",
                        source_kind="text_ft2_source_v2",
                        settings={"text": message, "font": {"face": "Arial", "size": 48}, "color1": 0xFFFFFFFF},
                    )
                except:
                    pass

            await asyncio.sleep(duration)

        # 5. Recording demo
        print("\n🔴 Quick Recording Demo...")
        await agent.set_scene("🎬 Main")

        # Update text for recording
        try:
            await agent.set_source_settings("Status Text", {"text": "🔴 Recording Demo in Progress! 🎬"})
        except:
            pass

        await agent.start_recording()
        print("  🔴 Recording started!")

        # Animate through some scenes
        for i in range(3):
            scene = random.choice(list(scenes.keys()))
            print(f"    📹 Recording scene: {scene}")
            await agent.set_scene(scene)
            await asyncio.sleep(2)

        output_path = await agent.stop_recording()
        print(f"  ✅ Recording saved to: {output_path}")

        # 6. Final statistics
        print("\n📊 Stream Setup Complete!")
        print(f"  ✅ Created {len(scenes)} professional scenes")
        print(f"  ✅ Added dynamic text overlays")
        print(f"  ✅ Configured audio settings")
        print(f"  ✅ Demonstrated scene automation")
        print(f"  ✅ Created test recording")

        print("\n🚀 Your OBS is now set up for professional streaming!")
        print("   You can use these scenes for your actual streams.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        agent.disconnect()
        print("\n👋 Demo complete!")


async def intelligent_stream_assistant():
    """Demonstrate intelligent stream management"""
    print("🤖 Intelligent Stream Assistant Demo")
    print("=" * 50)

    agent = AdvancedOBSAgent(password=os.getenv("OBS_WEBSOCKET_PASSWORD"))
    controller = AdvancedOBSController(agent)

    if not await agent.connect():
        return

    try:
        print("\n🧠 AI Assistant analyzing your OBS setup...")

        # Analyze current setup
        scenes = await agent.get_scenes()
        sources = await agent.get_sources()
        stats = await agent.get_stats()

        print(f"\n📊 Current Setup Analysis:")
        print(f"  📋 Scenes: {len(scenes)}")
        print(f"  🎤 Sources: {len(sources)}")
        print(f"  💻 CPU Usage: {stats.get('cpuUsage', 0):.1f}%")
        print(f"  🎯 FPS: {stats.get('activeFps', 0):.1f}")

        # Provide recommendations
        print("\n💡 AI Recommendations:")

        if len(scenes) < 3:
            print("  ⚠️  You should have at least 3 scenes for a dynamic stream")
            print("     Creating essential scenes now...")

            essential = ["Main", "BRB", "Starting Soon", "Ending"]
            for scene in essential:
                if scene not in scenes:
                    await agent.create_scene(scene)
                    print(f"     ✅ Added {scene} scene")

        audio_sources = [s for s in sources if "Audio" in s.get("inputKind", "")]
        if audio_sources:
            print("\n  🎤 Checking audio levels...")
            for source in audio_sources:
                volume = await agent.get_source_volume(source["inputName"])
                current_db = volume["volume_db"]

                if current_db < -30:
                    print(f"     ⚠️  {source['inputName']} is too quiet ({current_db:.1f}dB)")
                    await agent.set_source_volume(source["inputName"], volume_db=-20)
                    print(f"     ✅ Adjusted to -20dB")
                elif current_db > -10:
                    print(f"     ⚠️  {source['inputName']} might clip ({current_db:.1f}dB)")
                    await agent.set_source_volume(source["inputName"], volume_db=-15)
                    print(f"     ✅ Adjusted to -15dB")

        # Smart scene management demo
        print("\n🎯 Smart Scene Management Demo...")

        if len(scenes) >= 2:
            print("  🤖 AI will manage scene transitions based on timing...")

            start_scene = scenes[0]
            await agent.set_scene(start_scene)
            print(f"  Started with: {start_scene}")

            # Simulate intelligent transitions
            for i in range(3):
                await asyncio.sleep(3)

                # AI decides next scene
                current_idx = scenes.index(await agent.get_current_scene())
                next_idx = (current_idx + 1) % len(scenes)
                next_scene = scenes[next_idx]

                print(f"  🧠 AI: Time to switch! Moving to: {next_scene}")
                await agent.set_scene(next_scene)

        print("\n✅ Intelligent assistance complete!")
        print("   The AI has optimized your stream setup.")

    finally:
        agent.disconnect()


async def main():
    print("🎮 OBS Agent - Advanced Demos")
    print("=" * 50)
    print("1. Professional Stream Setup (creates complete streaming environment)")
    print("2. Intelligent Stream Assistant (AI-powered optimization)")
    print("\nWhich demo? (1 or 2): ", end="", flush=True)

    # Run first demo by default since we can't get input
    print("1")  # Simulate selection
    await create_professional_stream_setup()

    print("\n" + "=" * 50)
    print("Want to see the AI assistant too? Running demo 2...")
    await asyncio.sleep(2)

    await intelligent_stream_assistant()


if __name__ == "__main__":
    asyncio.run(main())
