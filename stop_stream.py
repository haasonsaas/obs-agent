#!/usr/bin/env python3
"""
Emergency Stream Stopper - Stop streaming immediately
"""

from obswebsocket import obsws, requests
from dotenv import load_dotenv
import os

load_dotenv()

def stop_stream_now():
    """Stop streaming immediately"""
    print("⏹️  STOPPING STREAM")
    print("=" * 30)
    
    password = os.getenv("OBS_WEBSOCKET_PASSWORD", "")
    
    try:
        # Connect
        ws = obsws("localhost", 4455, password)
        ws.connect()
        print("✅ Connected to OBS")
        
        # Check if streaming
        stream_status = ws.call(requests.GetStreamStatus())
        is_streaming = stream_status.datain.get("outputActive", False)
        
        if is_streaming:
            duration = stream_status.datain.get("outputDuration", 0)
            mins = duration // 60
            secs = duration % 60
            print(f"🔴 Stream was live for {mins}:{secs:02d}")
            
            # Switch to ending scene
            ws.call(requests.SetCurrentProgramScene(sceneName="🎉 Ending"))
            print("📺 → Ending scene")
            
            # Stop stream
            ws.call(requests.StopStream())
            print("⏹️  STREAM STOPPED!")
            
            # Check if recording
            record_status = ws.call(requests.GetRecordStatus())
            if record_status.datain.get("outputActive", False):
                output_path = ws.call(requests.StopRecord()).datain.get("outputPath", "")
                print(f"⏹️  Recording stopped: {output_path}")
            
        else:
            print("ℹ️  Stream was not active")
        
        ws.disconnect()
        print("✅ All stopped!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    stop_stream_now()