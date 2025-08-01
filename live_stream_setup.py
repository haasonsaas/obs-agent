#!/usr/bin/env python3
"""
Live Programming Stream Setup - Complete setup and streaming assistance
"""

import asyncio
import sys
import os
from obswebsocket import obsws, requests
from dotenv import load_dotenv
import time
from datetime import datetime

load_dotenv()


class LiveStreamManager:
    def __init__(self):
        self.ws = None
        self.password = os.getenv("OBS_WEBSOCKET_PASSWORD", "")
        self.connected = False
        
    def connect(self):
        """Connect to OBS"""
        try:
            print("🔌 Connecting to OBS...")
            self.ws = obsws("localhost", 4455, self.password)
            self.ws.connect()
            self.connected = True
            print("✅ Connected to OBS!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from OBS"""
        if self.ws and self.connected:
            self.ws.disconnect()
            self.connected = False
            print("👋 Disconnected from OBS")
    
    def get_streaming_status(self):
        """Get current streaming status"""
        try:
            response = self.ws.call(requests.GetStreamStatus())
            return {
                "is_streaming": response.datain.get("outputActive", False),
                "duration": response.datain.get("outputDuration", 0),
                "bytes": response.datain.get("outputBytes", 0),
                "dropped_frames": response.datain.get("outputSkippedFrames", 0),
                "total_frames": response.datain.get("outputTotalFrames", 0)
            }
        except:
            return {"is_streaming": False}
    
    def get_recording_status(self):
        """Get current recording status"""
        try:
            response = self.ws.call(requests.GetRecordStatus())
            return {
                "is_recording": response.datain.get("outputActive", False),
                "duration": response.datain.get("outputDuration", 0),
                "bytes": response.datain.get("outputBytes", 0)
            }
        except:
            return {"is_recording": False}
    
    def set_scene(self, scene_name):
        """Switch to a scene"""
        try:
            self.ws.call(requests.SetCurrentProgramScene(sceneName=scene_name))
            return True
        except:
            return False
    
    def start_streaming(self):
        """Start streaming"""
        try:
            self.ws.call(requests.StartStream())
            return True
        except Exception as e:
            print(f"❌ Failed to start stream: {e}")
            return False
    
    def stop_streaming(self):
        """Stop streaming"""
        try:
            self.ws.call(requests.StopStream())
            return True
        except:
            return False
    
    def start_recording(self):
        """Start recording"""
        try:
            self.ws.call(requests.StartRecord())
            return True
        except:
            return False
    
    def stop_recording(self):
        """Stop recording"""
        try:
            response = self.ws.call(requests.StopRecord())
            return response.datain.get("outputPath", "")
        except:
            return ""


async def setup_hotkeys_guide():
    """Show hotkeys setup guide"""
    print("\n⌨️  HOTKEY SETUP GUIDE")
    print("=" * 50)
    print("To set up hotkeys in OBS:")
    print("1. Open OBS Settings (Cmd+, on Mac)")
    print("2. Go to 'Hotkeys' section")
    print("3. Set these recommended hotkeys:")
    print()
    
    hotkeys = {
        "💻 Code Editor": "F1",
        "🖥️ Terminal": "F2", 
        "📄 Documentation": "F3",
        "🔀 Split View": "F4",
        "🎯 Focus Mode": "F5",
        "💭 Explaining": "F6",
        "☕ Break": "F7",
        "Start Streaming": "Cmd+Shift+S",
        "Stop Streaming": "Cmd+Shift+X",
        "Start Recording": "Cmd+Shift+R",
        "Stop Recording": "Cmd+Shift+E"
    }
    
    for scene, key in hotkeys.items():
        print(f"   {scene:<20} → {key}")
    
    print("\n4. Click 'Apply' and 'OK'")
    input("\nPress Enter when hotkeys are set up...")


async def pre_stream_checklist():
    """Run through pre-stream checklist"""
    print("\n📋 PRE-STREAM CHECKLIST")
    print("=" * 50)
    
    checklist = [
        "🎤 Microphone levels good (-20dB to -15dB)",
        "🎥 Webcam positioned and focused",
        "💡 Lighting looks good",
        "🖥️ Screen resolution appropriate for stream",
        "📱 Phone on silent/do not disturb",
        "☕ Water/coffee nearby",
        "📝 Code project ready to work on",
        "💬 Chat/social media ready",
        "🔋 Laptop plugged in (if applicable)",
        "🌐 Internet connection stable"
    ]
    
    for item in checklist:
        print(f"   {item}")
        response = input("   ✅ Ready? (y/n): ").strip().lower()
        if response != 'y':
            print("   ⏸️  Take your time to get this ready...")
            input("   Press Enter when ready...")
    
    print("\n🎉 All set! Ready to stream!")


async def stream_countdown(manager):
    """Countdown before going live"""
    print("\n⏰ STREAM COUNTDOWN")
    print("=" * 50)
    
    # Switch to Starting Soon scene
    manager.set_scene("📺 Starting Soon")
    print("📺 Switched to 'Starting Soon' scene")
    
    # Countdown
    for i in range(10, 0, -1):
        print(f"   Going live in {i}...")
        await asyncio.sleep(1)
    
    print("🔴 GOING LIVE!")


async def live_stream_assistant(manager):
    """Assist during live streaming"""
    print("\n🤖 LIVE STREAM ASSISTANT ACTIVE")
    print("=" * 50)
    print("Commands:")
    print("  'scenes' - Show scene switching menu")
    print("  'status' - Show stream health")
    print("  'record' - Start/stop recording")
    print("  'break' - Quick break mode")
    print("  'end' - End stream")
    print("  'help' - Show commands")
    print()
    
    # Start with main coding scene
    manager.set_scene("💻 Code Editor")
    print("📺 Switched to main coding scene")
    
    while True:
        try:
            command = input("\n🎮 Command (or 'end' to stop): ").strip().lower()
            
            if command == 'scenes':
                print("\n📺 Scene Menu:")
                scenes = [
                    ("1", "💻 Code Editor", "Main coding"),
                    ("2", "🖥️ Terminal", "Terminal focus"),
                    ("3", "📄 Documentation", "Show docs"),
                    ("4", "🔀 Split View", "Code + Terminal"),
                    ("5", "🎯 Focus Mode", "Debug zoom"),
                    ("6", "💭 Explaining", "Teaching mode"),
                    ("7", "🚀 Running Code", "Show output"),
                    ("8", "☕ Break", "Break screen")
                ]
                
                for num, scene, desc in scenes:
                    print(f"   {num}. {scene} - {desc}")
                
                scene_choice = input("\nSelect scene (1-8): ").strip()
                scene_map = {s[0]: s[1] for s in scenes}
                
                if scene_choice in scene_map:
                    scene_name = scene_map[scene_choice]
                    if manager.set_scene(scene_name):
                        print(f"✅ Switched to {scene_name}")
                    else:
                        print("❌ Failed to switch scene")
            
            elif command == 'status':
                stream_status = manager.get_streaming_status()
                record_status = manager.get_recording_status()
                
                print(f"\n📊 Stream Status:")
                print(f"   🔴 Streaming: {'Yes' if stream_status['is_streaming'] else 'No'}")
                if stream_status['is_streaming']:
                    duration_min = stream_status['duration'] // 60
                    dropped_pct = 0
                    if stream_status['total_frames'] > 0:
                        dropped_pct = (stream_status['dropped_frames'] / stream_status['total_frames']) * 100
                    print(f"   ⏱️  Duration: {duration_min} minutes")
                    print(f"   📦 MB Sent: {stream_status['bytes']/1024/1024:.1f}")
                    print(f"   📉 Dropped: {dropped_pct:.1f}%")
                
                print(f"   🔴 Recording: {'Yes' if record_status['is_recording'] else 'No'}")
                if record_status['is_recording']:
                    rec_duration_min = record_status['duration'] // 60
                    print(f"   ⏱️  Rec Duration: {rec_duration_min} minutes")
                    print(f"   💾 MB Recorded: {record_status['bytes']/1024/1024:.1f}")
            
            elif command == 'record':
                record_status = manager.get_recording_status()
                if record_status['is_recording']:
                    output_path = manager.stop_recording()
                    print(f"⏹️  Recording stopped: {output_path}")
                else:
                    if manager.start_recording():
                        print("🔴 Recording started!")
                    else:
                        print("❌ Failed to start recording")
            
            elif command == 'break':
                print("☕ Taking a break...")
                manager.set_scene("☕ Break")
                
                duration = input("Break duration (minutes, default 5): ").strip() or "5"
                try:
                    break_minutes = int(duration)
                    print(f"⏰ Break timer: {break_minutes} minutes")
                    
                    for i in range(break_minutes * 60, 0, -60):
                        print(f"   Break time remaining: {i//60} minutes")
                        await asyncio.sleep(60)
                    
                    print("🔔 Break time over!")
                    manager.set_scene("💻 Code Editor")
                    
                except ValueError:
                    print("❌ Invalid time")
            
            elif command == 'help':
                print("\n🎮 Available Commands:")
                print("   scenes  - Switch between scenes")
                print("   status  - Check stream health")
                print("   record  - Toggle recording")
                print("   break   - Take a timed break")
                print("   end     - End the stream")
            
            elif command == 'end':
                break
            
            else:
                print("❓ Unknown command. Type 'help' for commands.")
                
        except KeyboardInterrupt:
            break
    
    print("\n🎬 Stream assistant stopped")


async def end_stream_sequence(manager):
    """End stream with proper sequence"""
    print("\n🎬 ENDING STREAM")
    print("=" * 50)
    
    # Switch to ending scene
    manager.set_scene("🎉 Ending")
    print("📺 Switched to ending scene")
    
    # Countdown to end
    print("Ending stream in:")
    for i in range(10, 0, -1):
        print(f"   {i}...")
        await asyncio.sleep(1)
    
    # Stop recording if active
    record_status = manager.get_recording_status()
    if record_status['is_recording']:
        output_path = manager.stop_recording()
        print(f"⏹️  Recording stopped: {output_path}")
    
    # Stop streaming if active
    stream_status = manager.get_streaming_status()
    if stream_status['is_streaming']:
        manager.stop_streaming()
        print("⏹️  Stream stopped")
    
    print("✅ Stream ended successfully!")


async def main():
    """Main streaming workflow"""
    print("🎬 LIVE PROGRAMMING STREAM MANAGER")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    manager = LiveStreamManager()
    
    if not manager.connect():
        print("❌ Cannot connect to OBS. Please check setup.")
        return
    
    try:
        # Pre-stream setup
        await setup_hotkeys_guide()
        await pre_stream_checklist()
        
        # Ask about streaming platform
        print("\n📡 Streaming Platform:")
        platform = input("Where are you streaming? (Twitch/YouTube/etc): ").strip()
        print(f"Great! Setting up for {platform}")
        
        # Start streaming
        start_stream = input("\n🔴 Start streaming now? (y/n): ").strip().lower()
        
        if start_stream == 'y':
            await stream_countdown(manager)
            
            if manager.start_streaming():
                print("🔴 STREAM IS LIVE!")
                
                # Ask about recording
                record = input("Start recording? (y/n): ").strip().lower()
                if record == 'y':
                    manager.start_recording()
                    print("🔴 Recording started!")
                
                # Launch live assistant
                await live_stream_assistant(manager)
                
                # End stream
                await end_stream_sequence(manager)
            else:
                print("❌ Failed to start stream")
        else:
            print("👍 Stream setup complete. Use hotkeys to go live when ready!")
    
    finally:
        manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())