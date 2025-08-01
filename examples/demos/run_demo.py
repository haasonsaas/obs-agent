#!/usr/bin/env python3
"""Run OBS demo automatically"""

import asyncio
from obs_agent import OBSAgent
from advanced_features import AdvancedOBSAgent
import os
from dotenv import load_dotenv

load_dotenv()


async def run_demo():
    """Run a quick OBS demo"""
    print("🚀 OBS Agent Demo - Automatic Control")
    print("=" * 50)
    
    agent = AdvancedOBSAgent(password=os.getenv("OBS_WEBSOCKET_PASSWORD"))
    
    if not await agent.connect():
        print("❌ Failed to connect to OBS")
        return
    
    try:
        # 1. Show current status
        print("\n📊 Current OBS Status:")
        current_scene = await agent.get_current_scene()
        scenes = await agent.get_scenes()
        sources = await agent.get_sources()
        
        print(f"🎬 Current Scene: {current_scene}")
        print(f"📋 Available Scenes: {', '.join(scenes)}")
        print(f"🎤 Sources: {len(sources)}")
        
        # 2. Create demo scenes
        print("\n🎨 Creating demo scenes...")
        demo_scenes = ["Main", "Starting Soon", "Be Right Back", "Ending"]
        
        for scene_name in demo_scenes:
            if scene_name not in scenes:
                await agent.create_scene(scene_name)
                print(f"✅ Created scene: {scene_name}")
        
        # 3. Add text to Main scene
        print("\n📝 Adding text overlay to Main scene...")
        await agent.set_scene("Main")
        
        # Remove old demo text if exists
        try:
            await agent.remove_source("Demo Text")
        except:
            pass
        
        await agent.create_source(
            scene_name="Main",
            source_name="Demo Text",
            source_kind="text_ft2_source_v2",  # macOS text source
            settings={
                "text": "🎬 OBS Controlled by AI Agent! 🤖",
                "font": {
                    "face": "Arial",
                    "size": 48,
                    "style": "Regular"
                },
                "color1": 0xFFFFFFFF,  # White color with alpha
                "color2": 0xFFFFFFFF
            }
        )
        print("✅ Added text overlay")
        
        # 4. Scene switching demo
        print("\n🎬 Scene Switching Demo (15 seconds)...")
        print("Watch OBS as I switch scenes automatically!")
        
        scene_sequence = [
            ("Starting Soon", 3),
            ("Main", 5),
            ("Be Right Back", 3),
            ("Main", 4)
        ]
        
        for scene, duration in scene_sequence:
            print(f"  ➡️  Switching to: {scene} (for {duration}s)")
            await agent.set_scene(scene)
            await asyncio.sleep(duration)
        
        # 5. Audio check
        print("\n🎤 Checking audio sources...")
        audio_sources = [s for s in await agent.get_sources() 
                        if "Audio" in s.get("inputKind", "")]
        
        if audio_sources:
            for source in audio_sources:
                name = source["inputName"]
                volume = await agent.get_source_volume(name)
                print(f"  {name}: {volume['volume_db']:.1f} dB")
        else:
            print("  No audio sources found")
        
        # 6. Recording demo
        print("\n🔴 Recording Demo...")
        confirm = input("Start a 5-second test recording? (y/n): ").lower()
        
        if confirm == 'y':
            print("🔴 Recording started...")
            await agent.start_recording()
            
            # Count down
            for i in range(5, 0, -1):
                print(f"  {i}...")
                await asyncio.sleep(1)
            
            output_path = await agent.stop_recording()
            print(f"✅ Recording saved to: {output_path}")
        
        print("\n✨ Demo Complete!")
        print("You can now:")
        print("- Use the examples.py file for more demos")
        print("- Try the CrewAI agents for autonomous control")
        print("- Build your own automations!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    finally:
        agent.disconnect()
        print("\n👋 Disconnected from OBS")


if __name__ == "__main__":
    asyncio.run(run_demo())