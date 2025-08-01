#!/usr/bin/env python3
"""
Consolidated OBS connection and functionality tests
"""

import asyncio
import getpass
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from obswebsocket import obsws, requests

from src.obs_agent import OBSAgent

load_dotenv()


def test_basic_connection(host="localhost", port=4455, password=""):
    """Test basic OBS WebSocket connection"""
    print("🔌 Testing OBS Connection")
    print("=" * 40)

    try:
        ws = obsws(host, port, password)
        ws.connect()
        print("✅ Connected successfully!")

        # Get version info
        version = ws.call(requests.GetVersion())
        print(f"📦 OBS Version: {version.datain.get('obsVersion', 'Unknown')}")
        print(f"🔌 WebSocket Version: {version.datain.get('obsWebSocketVersion', 'Unknown')}")

        # Get current status
        scene_data = ws.call(requests.GetCurrentProgramScene())
        print(f"🎬 Current Scene: {scene_data.datain.get('currentProgramSceneName', 'Unknown')}")

        ws.disconnect()
        return True

    except ConnectionRefusedError:
        print("❌ Connection refused. Please check:")
        print("   1. OBS Studio is running")
        print("   2. WebSocket is enabled (Tools → WebSocket Server Settings)")
        print("   3. Port is correct (default: 4455)")
        return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


import pytest

@pytest.mark.skip(reason="Interactive test - requires user input")
def test_interactive():
    """Interactive connection test with user input"""
    print("🎬 OBS Interactive Connection Test")
    print("=" * 40)

    host = input("Host (default: localhost): ").strip() or "localhost"
    port_str = input("Port (default: 4455): ").strip() or "4455"
    port = int(port_str)

    print("\nPassword options:")
    print("1. No password")
    print("2. Enter password")
    print("3. Use from .env file")

    choice = input("Choose (1-3): ").strip()

    if choice == "2":
        password = getpass.getpass("Password: ")
    elif choice == "3":
        password = os.getenv("OBS_WEBSOCKET_PASSWORD", "")
        print("Using password from .env file")
    else:
        password = ""
        print("Using no password")

    return test_basic_connection(host, port, password)


async def test_agent_functionality():
    """Test OBS Agent functionality"""
    print("\n🤖 Testing OBS Agent")
    print("=" * 40)

    agent = OBSAgent(password=os.getenv("OBS_WEBSOCKET_PASSWORD", ""))

    if not await agent.connect():
        print("❌ Failed to connect")
        return False

    try:
        # Test various functions
        print("\n📋 Running functionality tests...")

        # 1. Get scenes
        scenes = await agent.get_scenes()
        print(f"✅ get_scenes(): {len(scenes)} scenes found")

        # 2. Get current scene
        current = await agent.get_current_scene()
        print(f"✅ get_current_scene(): {current}")

        # 3. Get sources
        sources = await agent.get_sources()
        print(f"✅ get_sources(): {len(sources)} sources found")

        # 4. Get stats
        stats = await agent.get_stats()
        print(f"✅ get_stats(): CPU {stats.get('cpuUsage', 0):.1f}%")

        # 5. Recording status
        rec_status = await agent.get_recording_status()
        print(f"✅ get_recording_status(): {'Recording' if rec_status['is_recording'] else 'Not recording'}")

        # 6. Streaming status
        stream_status = await agent.get_streaming_status()
        print(f"✅ get_streaming_status(): {'Streaming' if stream_status['is_streaming'] else 'Not streaming'}")

        print("\n✅ All tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

    finally:
        agent.disconnect()


async def test_scene_operations():
    """Test scene creation and manipulation"""
    print("\n🎬 Testing Scene Operations")
    print("=" * 40)

    agent = OBSAgent(password=os.getenv("OBS_WEBSOCKET_PASSWORD", ""))

    if not await agent.connect():
        return False

    try:
        test_scene = "Test Scene 123"

        # Create scene
        print(f"Creating scene: {test_scene}")
        await agent.create_scene(test_scene)
        print("✅ Scene created")

        # Switch to scene
        print(f"Switching to scene: {test_scene}")
        await agent.set_scene(test_scene)
        print("✅ Scene switched")

        # Add text source
        print("Adding text source...")
        item_id = await agent.create_source(
            scene_name=test_scene,
            source_name="Test Text",
            source_kind="text_ft2_source_v2",
            settings={"text": "Test Successful! ✅", "font": {"face": "Arial", "size": 48}},
        )
        print(f"✅ Text source added (ID: {item_id})")

        # Wait a bit
        await asyncio.sleep(2)

        # Clean up
        print("Cleaning up...")
        await agent.remove_scene(test_scene)
        print("✅ Test scene removed")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    finally:
        agent.disconnect()


def main():
    """Main test menu"""
    print("🧪 OBS Agent Test Suite")
    print("=" * 40)
    print("1. Basic connection test")
    print("2. Interactive connection test")
    print("3. Agent functionality test")
    print("4. Scene operations test")
    print("5. Run all tests")

    choice = input("\nSelect test (1-5): ").strip()

    if choice == "1":
        password = os.getenv("OBS_WEBSOCKET_PASSWORD", "")
        test_basic_connection(password=password)

    elif choice == "2":
        test_interactive()

    elif choice == "3":
        asyncio.run(test_agent_functionality())

    elif choice == "4":
        asyncio.run(test_scene_operations())

    elif choice == "5":
        print("\n🏃 Running all tests...\n")

        password = os.getenv("OBS_WEBSOCKET_PASSWORD", "")
        if test_basic_connection(password=password):
            asyncio.run(test_agent_functionality())
            asyncio.run(test_scene_operations())

    else:
        print("Invalid choice")


if __name__ == "__main__":
    # If password provided as argument, use it
    if len(sys.argv) > 1:
        password = sys.argv[1]
        test_basic_connection(password=password)
    else:
        main()
