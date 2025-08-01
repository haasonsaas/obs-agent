#!/usr/bin/env python3
"""
Quick Programming Stream Setup - Simple version that works immediately
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from obswebsocket import obsws, requests

load_dotenv()


async def setup_programming_stream():
    """Set up a complete programming livestream environment"""
    print("🚀 Programming Stream Setup")
    print("=" * 50)
    
    password = os.getenv("OBS_WEBSOCKET_PASSWORD", "")
    
    try:
        # Connect
        print("🔌 Connecting to OBS...")
        ws = obsws("localhost", 4455, password)
        ws.connect()
        print("✅ Connected!")
        
        # Create programming scenes
        print("\n📋 Creating Programming Scenes...")
        
        scenes = [
            "💻 Code Editor",
            "🖥️ Terminal", 
            "📄 Documentation",
            "🔀 Split View",
            "🎯 Focus Mode",
            "💭 Explaining",
            "🚀 Running Code",
            "☕ Break",
            "📺 Starting Soon",
            "🎉 Ending"
        ]
        
        existing_scenes = ws.call(requests.GetSceneList()).datain["scenes"]
        existing_names = [s["sceneName"] for s in existing_scenes]
        
        for scene in scenes:
            if scene not in existing_names:
                ws.call(requests.CreateScene(sceneName=scene))
                print(f"  ✅ Created: {scene}")
            else:
                print(f"  ℹ️  Already exists: {scene}")
        
        # Add text overlays to key scenes
        print("\n📝 Adding Text Overlays...")
        
        overlays = [
            {
                "scene": "📺 Starting Soon",
                "text": "🚀 Stream Starting Soon!\n📚 Today: Live Coding Session",
                "name": "Starting Text"
            },
            {
                "scene": "☕ Break", 
                "text": "☕ Quick Break - BRB!\n🎵 Enjoy the music",
                "name": "Break Text"
            },
            {
                "scene": "🎉 Ending",
                "text": "Thanks for Watching! 🎉\n👋 See you next time!",
                "name": "Thanks Text"
            }
        ]
        
        for overlay in overlays:
            ws.call(requests.SetCurrentProgramScene(sceneName=overlay["scene"]))
            
            try:
                ws.call(requests.CreateInput(
                    sceneName=overlay["scene"],
                    inputName=overlay["name"],
                    inputKind="text_ft2_source_v2",
                    inputSettings={
                        "text": overlay["text"],
                        "font": {
                            "face": "Arial",
                            "size": 60,
                            "style": "Bold"
                        }
                    }
                ))
                print(f"  ✅ Added text to {overlay['scene']}")
            except:
                print(f"  ℹ️  Text might already exist in {overlay['scene']}")
        
        # Scene tour demo
        print("\n🎬 Scene Tour Demo...")
        print("Watch OBS as I switch through your new programming scenes!")
        
        tour_scenes = [
            ("📺 Starting Soon", "Get ready for coding!", 3),
            ("💻 Code Editor", "Main coding workspace", 4),
            ("🖥️ Terminal", "Running commands", 3),
            ("🔀 Split View", "Code + Terminal together", 3),
            ("🎯 Focus Mode", "Zoomed debugging view", 3),
            ("💭 Explaining", "Teaching concepts", 3),
            ("☕ Break", "Quick break", 2),
            ("🎉 Ending", "Thanks for watching!", 3)
        ]
        
        for scene, description, duration in tour_scenes:
            print(f"  ➡️  {scene}: {description}")
            ws.call(requests.SetCurrentProgramScene(sceneName=scene))
            await asyncio.sleep(duration)
        
        # Final setup
        ws.call(requests.SetCurrentProgramScene(sceneName="💻 Code Editor"))
        
        print("\n✅ Programming Stream Setup Complete!")
        print("\n💡 Your Scenes:")
        print("  💻 Code Editor    - Main coding view")
        print("  🖥️ Terminal       - Terminal/console focus")
        print("  📄 Documentation  - Showing references")
        print("  🔀 Split View     - Code + Terminal together")
        print("  🎯 Focus Mode     - Debugging zoom")
        print("  💭 Explaining     - Webcam focus for teaching")
        print("  🚀 Running Code   - Output and results")
        print("  ☕ Break          - Break screen")
        print("  📺 Starting Soon  - Pre-stream")
        print("  🎉 Ending         - End stream")
        
        print("\n🎮 Pro Tips:")
        print("  - Set up hotkeys in OBS Settings → Hotkeys")
        print("  - Use Code Editor for main development")
        print("  - Switch to Terminal when running code")
        print("  - Use Explaining scene for teaching moments")
        print("  - Focus Mode is great for debugging")
        
        print("\n🎬 Ready to stream! Happy coding! 🚀")
        
        ws.disconnect()
        
    except ConnectionRefusedError:
        print("❌ Cannot connect to OBS!")
        print("\nPlease check:")
        print("1. OBS Studio is running")
        print("2. WebSocket is enabled (Tools → WebSocket Server Settings)")
        print("3. Password matches .env file")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    print("🎯 Quick Programming Stream Setup")
    print("=" * 50)
    
    language = sys.argv[1] if len(sys.argv) > 1 else "python"
    print(f"Setting up for: {language}")
    
    await setup_programming_stream()


if __name__ == "__main__":
    asyncio.run(main())