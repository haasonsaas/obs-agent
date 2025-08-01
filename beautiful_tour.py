#!/usr/bin/env python3
"""
Beautiful Scene Tour - Showcase the gorgeous new scenes
"""

import asyncio
from obswebsocket import obsws, requests
from dotenv import load_dotenv
import os

load_dotenv()


async def beautiful_scene_tour():
    """Tour through all the beautiful new scenes"""
    print("🎨 BEAUTIFUL SCENE TOUR")
    print("=" * 60)
    print("Showcasing your gorgeous new streaming scenes!")
    
    password = os.getenv("OBS_WEBSOCKET_PASSWORD", "")
    
    try:
        # Connect
        ws = obsws("localhost", 4455, password)
        ws.connect()
        print("✅ Connected to OBS!")
        
        # Beautiful scene tour sequence
        tour_scenes = [
            {
                "scene": "🚀 Welcome",
                "title": "Welcome Screen",
                "description": "Animated welcome with cyberpunk styling",
                "duration": 5,
                "features": ["Glowing text effects", "Professional typography", "Animated elements"]
            },
            {
                "scene": "💻 Code Studio", 
                "title": "Code Studio",
                "description": "Professional coding environment",
                "duration": 6,
                "features": ["Code display frame", "Status bar overlay", "Professional layout"]
            },
            {
                "scene": "🖥️ Terminal Zone",
                "title": "Terminal Zone", 
                "description": "Matrix-style terminal interface",
                "duration": 4,
                "features": ["Cyberpunk header", "Terminal styling", "Futuristic theme"]
            },
            {
                "scene": "🎓 Teaching Mode",
                "title": "Teaching Mode",
                "description": "Educational presentation layout",
                "duration": 5,
                "features": ["Teaching header", "Clean layout", "Educational focus"]
            },
            {
                "scene": "🎯 Focus Mode",
                "title": "Focus Mode",
                "description": "Debugging and focus interface",
                "duration": 4,
                "features": ["Focus indicator", "Debugging theme", "Concentrated view"]
            },
            {
                "scene": "☕ Chill Break",
                "title": "Chill Break",
                "description": "Relaxing break screen",
                "duration": 6,
                "features": ["Break message", "Timer display", "Relaxing vibes"]
            },
            {
                "scene": "🎉 Thanks & Subscribe",
                "title": "Thanks & Subscribe",
                "description": "Engaging end screen",
                "duration": 5,
                "features": ["Thanks message", "Social links", "Subscribe call-to-action"]
            }
        ]
        
        print("\n🎬 Starting beautiful scene tour...")
        print("Watch OBS as we showcase each gorgeous scene!\n")
        
        total_duration = sum(scene["duration"] for scene in tour_scenes)
        print(f"⏰ Total tour time: {total_duration} seconds\n")
        
        # Tour through each scene
        for i, scene_info in enumerate(tour_scenes, 1):
            scene_name = scene_info["scene"]
            title = scene_info["title"]
            description = scene_info["description"]
            duration = scene_info["duration"]
            features = scene_info["features"]
            
            print(f"🎨 Scene {i}/{len(tour_scenes)}: {title}")
            print(f"   📝 {description}")
            print(f"   ✨ Features: {', '.join(features)}")
            print(f"   ⏱️  Displaying for {duration} seconds...")
            
            # Switch to the scene
            ws.call(requests.SetCurrentProgramScene(sceneName=scene_name))
            
            # Show a countdown for this scene
            for remaining in range(duration, 0, -1):
                print(f"      {remaining}...", end=" ", flush=True)
                await asyncio.sleep(1)
            print("✅")
            print()
        
        # Tour complete
        print("🎉 BEAUTIFUL SCENE TOUR COMPLETE!")
        print("=" * 60)
        print("✨ Your stream now has:")
        print("   🎨 Professional cyberpunk theme")
        print("   ✨ Glowing text effects and borders")
        print("   🌈 Cohesive color scheme")
        print("   📱 Optimized layouts for streaming")
        print("   🎪 Engaging visual elements")
        print("   💫 Beautiful typography")
        
        print("\n🚀 Ready to go live with style!")
        print("Your stream will look absolutely stunning! 🎬✨")
        
        # Return to welcome scene
        ws.call(requests.SetCurrentProgramScene(sceneName="🚀 Welcome"))
        print("\n📺 Set to Welcome scene - ready to go live!")
        
        ws.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def quick_style_demo():
    """Quick demo of the styling improvements"""
    print("\n🎨 BEFORE vs AFTER")
    print("=" * 60)
    print("🔸 BEFORE (Plain):")
    print("   - Basic text without styling")
    print("   - No visual effects")
    print("   - Generic layouts")
    print("   - Boring appearance")
    
    print("\n✨ AFTER (Beautiful):")
    print("   - Professional typography (SF Pro fonts)")
    print("   - Glowing borders and effects")
    print("   - Cyberpunk color scheme")
    print("   - Animated elements")
    print("   - Status bars and overlays")
    print("   - Optimized positioning")
    print("   - Cohesive branding")
    
    print("\n🎯 The difference:")
    print("   📈 Professional appearance")
    print("   👀 Better viewer engagement")
    print("   🎨 Memorable visual identity")
    print("   🏆 Stand out from other streams")


async def main():
    print("🎨 Welcome to your Beautiful OBS Setup!")
    print("=" * 60)
    
    await quick_style_demo()
    
    print(f"\n🎬 Ready for the scene tour?")
    # Auto-start tour for demo
    print("Starting tour...")
    await beautiful_scene_tour()


if __name__ == "__main__":
    asyncio.run(main())