import asyncio
from obs_agent import OBSAgent, OBSController
import os
from dotenv import load_dotenv

load_dotenv()


async def basic_usage_example():
    agent = OBSAgent(
        host="localhost",
        port=4455,
        password=os.getenv("OBS_WEBSOCKET_PASSWORD", "")
    )
    
    if await agent.connect():
        version = await agent.get_version()
        print(f"OBS Version: {version['obs_version']}")
        print(f"WebSocket Version: {version['websocket_version']}")
        
        scenes = await agent.get_scenes()
        print(f"\nAvailable scenes: {scenes}")
        
        current_scene = await agent.get_current_scene()
        print(f"Current scene: {current_scene}")
        
        sources = await agent.get_sources()
        print(f"\nAvailable sources: {[s['inputName'] for s in sources]}")
        
        agent.disconnect()


async def recording_example():
    agent = OBSAgent(password=os.getenv("OBS_WEBSOCKET_PASSWORD", ""))
    
    if await agent.connect():
        print("Starting recording...")
        await agent.start_recording()
        
        await asyncio.sleep(5)
        
        status = await agent.get_recording_status()
        print(f"Recording status: {status}")
        
        output_path = await agent.stop_recording()
        print(f"Recording saved to: {output_path}")
        
        agent.disconnect()


async def scene_switching_example():
    agent = OBSAgent(password=os.getenv("OBS_WEBSOCKET_PASSWORD", ""))
    
    if await agent.connect():
        scenes = await agent.get_scenes()
        print(f"Available scenes: {scenes}")
        
        for scene in scenes[:3]:
            print(f"Switching to scene: {scene}")
            await agent.set_scene(scene)
            await asyncio.sleep(3)
        
        agent.disconnect()


async def audio_control_example():
    agent = OBSAgent(password=os.getenv("OBS_WEBSOCKET_PASSWORD", ""))
    
    if await agent.connect():
        sources = await agent.get_sources()
        audio_sources = [s for s in sources if "Audio" in s.get("inputKind", "")]
        
        for source in audio_sources:
            source_name = source["inputName"]
            print(f"\nAudio source: {source_name}")
            
            volume = await agent.get_source_volume(source_name)
            print(f"Current volume: {volume['volume_db']:.1f} dB")
            
            is_muted = await agent.get_source_mute(source_name)
            print(f"Muted: {is_muted}")
            
            await agent.set_source_volume(source_name, volume_db=-10.0)
            print("Set volume to -10 dB")
            
            await agent.toggle_source_mute(source_name)
            print("Toggled mute state")
        
        agent.disconnect()


async def streaming_example():
    agent = OBSAgent(password=os.getenv("OBS_WEBSOCKET_PASSWORD", ""))
    controller = OBSController(agent)
    
    if await agent.connect():
        def alert_callback(message):
            print(f"ALERT: {message}")
        
        print("Starting stream...")
        await agent.start_streaming()
        
        monitor_task = asyncio.create_task(
            controller.monitor_stream_health(alert_callback)
        )
        
        await asyncio.sleep(30)
        
        status = await agent.get_streaming_status()
        print(f"Stream status: {status}")
        
        await agent.stop_streaming()
        print("Stream stopped")
        
        monitor_task.cancel()
        agent.disconnect()


async def automated_recording_session():
    agent = OBSAgent(password=os.getenv("OBS_WEBSOCKET_PASSWORD", ""))
    controller = OBSController(agent)
    
    if await agent.connect():
        scenes = await agent.get_scenes()
        
        print("Starting automated recording session...")
        output_path = await controller.create_recording_session(
            scenes=scenes[:3],
            duration_per_scene=5
        )
        print(f"Recording saved to: {output_path}")
        
        agent.disconnect()


async def create_source_example():
    agent = OBSAgent(password=os.getenv("OBS_WEBSOCKET_PASSWORD", ""))
    
    if await agent.connect():
        current_scene = await agent.get_current_scene()
        
        text_settings = {
            "text": "Hello from OBS Agent!",
            "font": {"face": "Arial", "size": 72},
            "color": 0xFFFFFF
        }
        
        item_id = await agent.create_source(
            scene_name=current_scene,
            source_name="Test Text Source",
            source_kind="text_gdiplus_v2",
            settings=text_settings
        )
        
        if item_id > 0:
            print(f"Created text source with ID: {item_id}")
            await asyncio.sleep(5)
            await agent.remove_source("Test Text Source")
            print("Removed text source")
        
        agent.disconnect()


async def backup_restore_example():
    agent = OBSAgent(password=os.getenv("OBS_WEBSOCKET_PASSWORD", ""))
    controller = OBSController(agent)
    
    if await agent.connect():
        print("Backing up OBS scenes...")
        backup_path = await controller.backup_scenes("obs_backup.json")
        print(f"Backup saved to: {backup_path}")
        
        agent.disconnect()


async def transition_example():
    agent = OBSAgent(password=os.getenv("OBS_WEBSOCKET_PASSWORD", ""))
    
    if await agent.connect():
        transitions = await agent.get_transitions()
        print(f"Available transitions: {transitions}")
        
        scenes = await agent.get_scenes()
        if len(scenes) >= 2:
            await agent.set_transition("Fade")
            await agent.set_transition_duration(1000)
            
            print(f"Switching from {scenes[0]} to {scenes[1]} with fade transition")
            await agent.set_scene(scenes[0])
            await asyncio.sleep(2)
            await agent.set_scene(scenes[1])
        
        agent.disconnect()


async def screenshot_example():
    agent = OBSAgent(password=os.getenv("OBS_WEBSOCKET_PASSWORD", ""))
    
    if await agent.connect():
        sources = await agent.get_sources()
        if sources:
            source_name = sources[0]["inputName"]
            screenshot_path = f"screenshot_{source_name}.png"
            
            success = await agent.take_screenshot(
                source_name=source_name,
                file_path=screenshot_path,
                width=1920,
                height=1080
            )
            
            if success:
                print(f"Screenshot saved: {screenshot_path}")
        
        agent.disconnect()


async def main():
    print("OBS Agent Examples")
    print("==================")
    print("1. Basic Usage")
    print("2. Recording")
    print("3. Scene Switching")
    print("4. Audio Control")
    print("5. Streaming")
    print("6. Automated Recording Session")
    print("7. Create Source")
    print("8. Backup Scenes")
    print("9. Transitions")
    print("10. Screenshot")
    
    choice = input("\nSelect an example (1-10): ")
    
    examples = {
        "1": basic_usage_example,
        "2": recording_example,
        "3": scene_switching_example,
        "4": audio_control_example,
        "5": streaming_example,
        "6": automated_recording_session,
        "7": create_source_example,
        "8": backup_restore_example,
        "9": transition_example,
        "10": screenshot_example
    }
    
    if choice in examples:
        await examples[choice]()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())