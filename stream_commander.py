#!/usr/bin/env python3
"""
Stream Commander - Real-time stream control with hotkeys
"""

import asyncio
import keyboard
import sys
from obswebsocket import obsws, requests
from dotenv import load_dotenv
import os
import threading
import time

load_dotenv()


class StreamCommander:
    def __init__(self):
        self.ws = None
        self.password = os.getenv("OBS_WEBSOCKET_PASSWORD", "")
        self.connected = False
        self.current_scene = ""
        self.running = True
        
        # Scene mappings
        self.scenes = {
            'f1': '💻 Code Editor',
            'f2': '🖥️ Terminal', 
            'f3': '📄 Documentation',
            'f4': '🔀 Split View',
            'f5': '🎯 Focus Mode',
            'f6': '💭 Explaining',
            'f7': '☕ Break',
            'f8': '🚀 Running Code'
        }
        
    def connect(self):
        """Connect to OBS"""
        try:
            self.ws = obsws("localhost", 4455, self.password)
            self.ws.connect()
            self.connected = True
            print("✅ Connected to OBS!")
            
            # Get current scene
            response = self.ws.call(requests.GetCurrentProgramScene())
            self.current_scene = response.datain.get('currentProgramSceneName', '')
            print(f"📺 Current scene: {self.current_scene}")
            
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def set_scene(self, scene_name):
        """Switch to scene"""
        if not self.connected:
            return False
        
        try:
            self.ws.call(requests.SetCurrentProgramScene(sceneName=scene_name))
            self.current_scene = scene_name
            print(f"📺 → {scene_name}")
            return True
        except Exception as e:
            print(f"❌ Scene switch failed: {e}")
            return False
    
    def get_status(self):
        """Get stream/record status"""
        if not self.connected:
            return {}
        
        try:
            stream = self.ws.call(requests.GetStreamStatus())
            record = self.ws.call(requests.GetRecordStatus())
            
            return {
                "streaming": stream.datain.get("outputActive", False),
                "recording": record.datain.get("outputActive", False),
                "stream_time": stream.datain.get("outputDuration", 0),
                "record_time": record.datain.get("outputDuration", 0)
            }
        except:
            return {}
    
    def toggle_streaming(self):
        """Toggle streaming on/off"""
        if not self.connected:
            return
        
        try:
            response = self.ws.call(requests.ToggleStream())
            is_active = response.datain.get("outputActive", False)
            
            if is_active:
                print("🔴 STREAMING STARTED!")
            else:
                print("⏹️  STREAMING STOPPED")
        except Exception as e:
            print(f"❌ Stream toggle failed: {e}")
    
    def toggle_recording(self):
        """Toggle recording on/off"""
        if not self.connected:
            return
        
        try:
            response = self.ws.call(requests.ToggleRecord())
            is_active = response.datain.get("outputActive", False)
            
            if is_active:
                print("🔴 RECORDING STARTED!")
            else:
                output_path = response.datain.get("outputPath", "")
                print(f"⏹️  RECORDING STOPPED: {output_path}")
        except Exception as e:
            print(f"❌ Record toggle failed: {e}")
    
    def setup_hotkeys(self):
        """Setup keyboard hotkeys"""
        print("\n⌨️  Setting up hotkeys...")
        
        # Scene switching hotkeys
        for key, scene in self.scenes.items():
            keyboard.add_hotkey(key, lambda s=scene: self.set_scene(s))
            print(f"   {key.upper()} → {scene}")
        
        # Stream controls
        keyboard.add_hotkey('ctrl+shift+s', self.toggle_streaming)
        keyboard.add_hotkey('ctrl+shift+r', self.toggle_recording)
        keyboard.add_hotkey('ctrl+shift+q', self.quit)
        
        print(f"   CTRL+SHIFT+S → Toggle Streaming")
        print(f"   CTRL+SHIFT+R → Toggle Recording")
        print(f"   CTRL+SHIFT+Q → Quit Commander")
        print("\n🎮 Stream Commander Active!")
    
    def quit(self):
        """Quit the commander"""
        self.running = False
        print("\n👋 Stream Commander stopping...")
    
    def status_monitor(self):
        """Monitor and display status"""
        while self.running:
            status = self.get_status()
            
            if status:
                stream_emoji = "🔴" if status["streaming"] else "⚫"
                record_emoji = "🔴" if status["recording"] else "⚫"
                
                stream_time = f"{status['stream_time']//60}:{status['stream_time']%60:02d}"
                record_time = f"{status['record_time']//60}:{status['record_time']%60:02d}"
                
                status_line = f"{stream_emoji} Stream: {stream_time} | {record_emoji} Record: {record_time} | Scene: {self.current_scene}"
                
                # Clear line and print status
                print(f"\r{status_line}", end="", flush=True)
            
            time.sleep(1)
    
    def run(self):
        """Run the stream commander"""
        if not self.connect():
            return
        
        try:
            self.setup_hotkeys()
            
            # Start status monitor in background
            status_thread = threading.Thread(target=self.status_monitor, daemon=True)
            status_thread.start()
            
            # Keep running until quit
            while self.running:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            pass
        finally:
            if self.ws and self.connected:
                self.ws.disconnect()
            print("\n👋 Stream Commander stopped")


def main():
    print("🎮 STREAM COMMANDER")
    print("=" * 50)
    print("Real-time OBS control with hotkeys!")
    print()
    
    # Check if keyboard module is available
    try:
        import keyboard
    except ImportError:
        print("❌ Missing 'keyboard' module")
        print("Install with: pip install keyboard")
        print("Note: May require sudo on some systems")
        return
    
    commander = StreamCommander()
    commander.run()


if __name__ == "__main__":
    main()