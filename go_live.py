#!/usr/bin/env python3
"""
GO LIVE! - Start your programming stream right now
"""

import asyncio
import sys
from obswebsocket import obsws, requests
from dotenv import load_dotenv
import os
import time

load_dotenv()


async def go_live_now():
    """Start streaming immediately with programming setup"""
    print("🚀 GO LIVE - Programming Stream")
    print("=" * 50)
    
    # Connect to OBS
    password = os.getenv("OBS_WEBSOCKET_PASSWORD", "")
    
    try:
        print("🔌 Connecting to OBS...")
        ws = obsws("localhost", 4455, password)
        ws.connect()
        print("✅ Connected!")
        
        # Quick setup check
        current = ws.call(requests.GetCurrentProgramScene()).datain.get('currentProgramSceneName', '')
        print(f"📺 Current Scene: {current}")
        
        # Check if we have programming scenes
        scenes = ws.call(requests.GetSceneList()).datain["scenes"]
        scene_names = [s["sceneName"] for s in scenes]
        
        if "💻 Code Editor" not in scene_names:
            print("⚠️  Programming scenes not found. Setting up now...")
            await setup_quick_scenes(ws)
        
        # Pre-stream countdown
        print("\n🎬 GOING LIVE IN...")
        for i in range(10, 0, -1):
            print(f"   {i}...")
            await asyncio.sleep(1)
        
        # Switch to starting scene
        ws.call(requests.SetCurrentProgramScene(sceneName="📺 Starting Soon"))
        print("📺 → Starting Soon scene")
        
        # START STREAMING!
        print("\n🔴 STARTING STREAM!")
        ws.call(requests.StartStream())
        print("✅ STREAM IS LIVE!")
        
        # Switch to main coding scene after 5 seconds
        await asyncio.sleep(5)
        ws.call(requests.SetCurrentProgramScene(sceneName="💻 Code Editor"))
        print("📺 → Code Editor scene")
        
        print("\n🎉 YOU ARE LIVE!")
        print("=" * 50)
        print("📺 Scene Shortcuts (set in OBS Settings → Hotkeys):")
        print("   F1 → 💻 Code Editor")
        print("   F2 → 🖥️ Terminal")
        print("   F3 → 📄 Documentation")
        print("   F4 → 🔀 Split View")
        print("   F5 → 🎯 Focus Mode")
        print("   F6 → 💭 Explaining")
        print("   F7 → ☕ Break")
        print()
        print("🎮 Stream Controls:")
        print("   Cmd+Shift+S → Toggle Streaming")
        print("   Cmd+Shift+R → Toggle Recording")
        print()
        print("💡 Tips:")
        print("   - Use Code Editor for main development")
        print("   - Switch to Terminal when running code")
        print("   - Use Explaining for teaching moments")
        print("   - Take breaks with the Break scene")
        print()
        print("🔴 Stream is running! Start coding and have fun!")
        
        # Keep monitoring
        await stream_monitor(ws)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'ws' in locals():
            ws.disconnect()


async def setup_quick_scenes(ws):
    """Quick scene setup"""
    scenes = [
        "💻 Code Editor",
        "🖥️ Terminal", 
        "📄 Documentation",
        "🔀 Split View",
        "🎯 Focus Mode",
        "💭 Explaining",
        "☕ Break",
        "📺 Starting Soon"
    ]
    
    for scene in scenes:
        try:
            ws.call(requests.CreateScene(sceneName=scene))
            print(f"  ✅ Created: {scene}")
        except:
            pass


async def stream_monitor(ws):
    """Monitor stream and provide status"""
    print("\n🤖 Stream Monitor Active")
    print("Type 'help' for commands, 'quit' to stop")
    
    start_time = time.time()
    
    while True:
        try:
            # Get stream status
            try:
                stream_status = ws.call(requests.GetStreamStatus())
                is_streaming = stream_status.datain.get("outputActive", False)
                duration = stream_status.datain.get("outputDuration", 0)
                dropped = stream_status.datain.get("outputSkippedFrames", 0)
                total = stream_status.datain.get("outputTotalFrames", 1)
                dropped_pct = (dropped / total) * 100 if total > 0 else 0
                
                if is_streaming:
                    mins = duration // 60
                    secs = duration % 60
                    status = f"🔴 Live: {mins}:{secs:02d} | Dropped: {dropped_pct:.1f}%"
                else:
                    status = "⚫ Not streaming"
                
                print(f"\r{status}", end="", flush=True)
                
            except:
                print("\r🔴 Stream monitor error", end="", flush=True)
            
            await asyncio.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping stream...")
            try:
                ws.call(requests.StopStream())
                print("✅ Stream stopped")
            except:
                pass
            break


async def main():
    print("🎬 Ready to go live with your programming stream?")
    
    # Get streaming platform info
    if len(sys.argv) > 1:
        platform = sys.argv[1]
    else:
        platform = "your platform"
    
    print(f"📡 Streaming to: {platform}")
    print("🎯 Content: Live Programming/Coding")
    print(f"⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    await go_live_now()


if __name__ == "__main__":
    asyncio.run(main())