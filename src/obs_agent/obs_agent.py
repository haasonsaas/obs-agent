import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from obswebsocket import obsws, requests, events
import logging
from datetime import datetime
from pathlib import Path


class OBSAgent:
    def __init__(self, host: str = "localhost", port: int = 4455, password: str = ""):
        self.host = host
        self.port = port
        self.password = password
        self.ws = None
        self.connected = False
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    async def connect(self) -> bool:
        try:
            self.ws = obsws(self.host, self.port, self.password)
            self.ws.connect()
            self.connected = True
            self.logger.info(f"Connected to OBS at {self.host}:{self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to OBS: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        if self.ws and self.connected:
            self.ws.disconnect()
            self.connected = False
            self.logger.info("Disconnected from OBS")
    
    def _check_connection(self):
        if not self.connected:
            raise ConnectionError("Not connected to OBS. Call connect() first.")
    
    async def get_version(self) -> Dict[str, Any]:
        self._check_connection()
        response = self.ws.call(requests.GetVersion())
        return {
            "obs_version": response.datain.get("obsVersion"),
            "websocket_version": response.datain.get("obsWebSocketVersion"),
            "platform": response.datain.get("platform"),
            "platform_description": response.datain.get("platformDescription")
        }
    
    async def get_scenes(self) -> List[str]:
        self._check_connection()
        response = self.ws.call(requests.GetSceneList())
        scenes = response.datain.get("scenes", [])
        return [scene["sceneName"] for scene in scenes]
    
    async def get_current_scene(self) -> str:
        self._check_connection()
        response = self.ws.call(requests.GetCurrentProgramScene())
        return response.datain.get("currentProgramSceneName", "")
    
    async def set_scene(self, scene_name: str) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.SetCurrentProgramScene(sceneName=scene_name))
            self.logger.info(f"Switched to scene: {scene_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to switch scene: {e}")
            return False
    
    async def start_recording(self) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.StartRecord())
            self.logger.info("Recording started")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            return False
    
    async def stop_recording(self) -> str:
        self._check_connection()
        try:
            response = self.ws.call(requests.StopRecord())
            output_path = response.datain.get("outputPath", "")
            self.logger.info(f"Recording stopped. File saved to: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            return ""
    
    async def toggle_recording(self) -> Dict[str, Any]:
        self._check_connection()
        response = self.ws.call(requests.ToggleRecord())
        return {
            "output_active": response.datain.get("outputActive", False),
            "output_path": response.datain.get("outputPath", "")
        }
    
    async def get_recording_status(self) -> Dict[str, Any]:
        self._check_connection()
        response = self.ws.call(requests.GetRecordStatus())
        return {
            "is_recording": response.datain.get("outputActive", False),
            "is_paused": response.datain.get("outputPaused", False),
            "duration": response.datain.get("outputDuration", 0),
            "bytes": response.datain.get("outputBytes", 0)
        }
    
    async def start_streaming(self) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.StartStream())
            self.logger.info("Streaming started")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start streaming: {e}")
            return False
    
    async def stop_streaming(self) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.StopStream())
            self.logger.info("Streaming stopped")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop streaming: {e}")
            return False
    
    async def toggle_streaming(self) -> bool:
        self._check_connection()
        response = self.ws.call(requests.ToggleStream())
        return response.datain.get("outputActive", False)
    
    async def get_streaming_status(self) -> Dict[str, Any]:
        self._check_connection()
        response = self.ws.call(requests.GetStreamStatus())
        return {
            "is_streaming": response.datain.get("outputActive", False),
            "duration": response.datain.get("outputDuration", 0),
            "bytes": response.datain.get("outputBytes", 0),
            "skipped_frames": response.datain.get("outputSkippedFrames", 0),
            "total_frames": response.datain.get("outputTotalFrames", 0)
        }
    
    async def get_sources(self) -> List[Dict[str, Any]]:
        self._check_connection()
        response = self.ws.call(requests.GetInputList())
        return response.datain.get("inputs", [])
    
    async def get_source_settings(self, source_name: str) -> Dict[str, Any]:
        self._check_connection()
        response = self.ws.call(requests.GetInputSettings(inputName=source_name))
        return {
            "kind": response.datain.get("inputKind", ""),
            "settings": response.datain.get("inputSettings", {})
        }
    
    async def set_source_settings(self, source_name: str, settings: Dict[str, Any]) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.SetInputSettings(
                inputName=source_name,
                inputSettings=settings
            ))
            self.logger.info(f"Updated settings for source: {source_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update source settings: {e}")
            return False
    
    async def get_source_mute(self, source_name: str) -> bool:
        self._check_connection()
        response = self.ws.call(requests.GetInputMute(inputName=source_name))
        return response.datain.get("inputMuted", False)
    
    async def set_source_mute(self, source_name: str, muted: bool) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.SetInputMute(
                inputName=source_name,
                inputMuted=muted
            ))
            self.logger.info(f"Set mute for {source_name} to {muted}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set source mute: {e}")
            return False
    
    async def toggle_source_mute(self, source_name: str) -> bool:
        self._check_connection()
        response = self.ws.call(requests.ToggleInputMute(inputName=source_name))
        return response.datain.get("inputMuted", False)
    
    async def get_source_volume(self, source_name: str) -> Dict[str, float]:
        self._check_connection()
        response = self.ws.call(requests.GetInputVolume(inputName=source_name))
        return {
            "volume_mul": response.datain.get("inputVolumeMul", 0.0),
            "volume_db": response.datain.get("inputVolumeDb", 0.0)
        }
    
    async def set_source_volume(self, source_name: str, volume_db: Optional[float] = None, 
                              volume_mul: Optional[float] = None) -> bool:
        self._check_connection()
        try:
            params = {"inputName": source_name}
            if volume_db is not None:
                params["inputVolumeDb"] = volume_db
            if volume_mul is not None:
                params["inputVolumeMul"] = volume_mul
            
            self.ws.call(requests.SetInputVolume(**params))
            self.logger.info(f"Set volume for {source_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set source volume: {e}")
            return False
    
    async def create_scene(self, scene_name: str) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.CreateScene(sceneName=scene_name))
            self.logger.info(f"Created scene: {scene_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create scene: {e}")
            return False
    
    async def remove_scene(self, scene_name: str) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.RemoveScene(sceneName=scene_name))
            self.logger.info(f"Removed scene: {scene_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove scene: {e}")
            return False
    
    async def take_screenshot(self, source_name: str, file_path: str, 
                            width: Optional[int] = None, height: Optional[int] = None) -> bool:
        self._check_connection()
        try:
            params = {
                "sourceName": source_name,
                "imageFilePath": file_path,
                "imageFormat": "png"
            }
            if width:
                params["imageWidth"] = width
            if height:
                params["imageHeight"] = height
            
            self.ws.call(requests.SaveSourceScreenshot(**params))
            self.logger.info(f"Screenshot saved to: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        self._check_connection()
        response = self.ws.call(requests.GetStats())
        return response.datain
    
    async def set_transition(self, transition_name: str) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.SetCurrentSceneTransition(transitionName=transition_name))
            self.logger.info(f"Set transition to: {transition_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set transition: {e}")
            return False
    
    async def get_transitions(self) -> List[str]:
        self._check_connection()
        response = self.ws.call(requests.GetSceneTransitionList())
        transitions = response.datain.get("transitions", [])
        return [t["transitionName"] for t in transitions]
    
    async def set_transition_duration(self, duration_ms: int) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.SetCurrentSceneTransitionDuration(transitionDuration=duration_ms))
            self.logger.info(f"Set transition duration to: {duration_ms}ms")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set transition duration: {e}")
            return False
    
    async def get_scene_items(self, scene_name: str) -> List[Dict[str, Any]]:
        self._check_connection()
        response = self.ws.call(requests.GetSceneItemList(sceneName=scene_name))
        return response.datain.get("sceneItems", [])
    
    async def set_scene_item_enabled(self, scene_name: str, item_id: int, enabled: bool) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.SetSceneItemEnabled(
                sceneName=scene_name,
                sceneItemId=item_id,
                sceneItemEnabled=enabled
            ))
            self.logger.info(f"Set scene item {item_id} enabled to {enabled}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set scene item enabled: {e}")
            return False
    
    async def create_source(self, scene_name: str, source_name: str, 
                          source_kind: str, settings: Optional[Dict[str, Any]] = None) -> int:
        self._check_connection()
        try:
            params = {
                "sceneName": scene_name,
                "inputName": source_name,
                "inputKind": source_kind
            }
            if settings:
                params["inputSettings"] = settings
            
            response = self.ws.call(requests.CreateInput(**params))
            item_id = response.datain.get("sceneItemId", -1)
            self.logger.info(f"Created source {source_name} with ID {item_id}")
            return item_id
        except Exception as e:
            self.logger.error(f"Failed to create source: {e}")
            return -1
    
    async def remove_source(self, source_name: str) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.RemoveInput(inputName=source_name))
            self.logger.info(f"Removed source: {source_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove source: {e}")
            return False
    
    def register_event_handler(self, event_type: str, handler: Callable):
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        self.logger.info(f"Registered handler for event: {event_type}")
    
    async def wait_for_event(self, event_type: str, timeout: float = 30.0) -> Optional[Any]:
        self._check_connection()
        event_received = asyncio.Event()
        event_data = None
        
        def handler(event):
            nonlocal event_data
            event_data = event
            event_received.set()
        
        self.register_event_handler(event_type, handler)
        
        try:
            await asyncio.wait_for(event_received.wait(), timeout)
            return event_data
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout waiting for event: {event_type}")
            return None


class OBSController:
    def __init__(self, agent: OBSAgent):
        self.agent = agent
    
    async def auto_scene_switcher(self, scene_schedule: List[Dict[str, Any]]):
        for schedule in scene_schedule:
            scene_name = schedule.get("scene")
            duration = schedule.get("duration", 10)
            
            if await self.agent.set_scene(scene_name):
                await asyncio.sleep(duration)
    
    async def monitor_stream_health(self, alert_callback: Optional[Callable] = None):
        while True:
            stats = await self.agent.get_streaming_status()
            
            if stats["is_streaming"]:
                dropped_frames_percent = 0
                if stats["total_frames"] > 0:
                    dropped_frames_percent = (stats["skipped_frames"] / stats["total_frames"]) * 100
                
                if dropped_frames_percent > 5 and alert_callback:
                    alert_callback(f"High dropped frames: {dropped_frames_percent:.1f}%")
            
            await asyncio.sleep(5)
    
    async def backup_scenes(self, backup_path: str = "obs_backup.json"):
        scenes = await self.agent.get_scenes()
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "scenes": []
        }
        
        for scene_name in scenes:
            scene_items = await self.agent.get_scene_items(scene_name)
            backup_data["scenes"].append({
                "name": scene_name,
                "items": scene_items
            })
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        return backup_path
    
    async def create_recording_session(self, scenes: List[str], duration_per_scene: int = 10):
        await self.agent.start_recording()
        
        for scene in scenes:
            await self.agent.set_scene(scene)
            await asyncio.sleep(duration_per_scene)
        
        output_path = await self.agent.stop_recording()
        return output_path