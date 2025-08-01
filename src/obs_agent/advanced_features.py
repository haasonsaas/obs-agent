import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from obswebsocket import requests

from .obs_agent import OBSAgent


class AdvancedOBSAgent(OBSAgent):

    async def get_filters(self, source_name: str) -> List[Dict[str, Any]]:
        self._check_connection()
        response = self.ws.call(requests.GetSourceFilterList(sourceName=source_name))
        return response.datain.get("filters", [])

    async def add_filter(
        self, source_name: str, filter_name: str, filter_kind: str, filter_settings: Dict[str, Any]
    ) -> bool:
        self._check_connection()
        try:
            self.ws.call(
                requests.CreateSourceFilter(
                    sourceName=source_name,
                    filterName=filter_name,
                    filterKind=filter_kind,
                    filterSettings=filter_settings,
                )
            )
            self.logger.info(f"Added filter {filter_name} to {source_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add filter: {e}")
            return False

    async def remove_filter(self, source_name: str, filter_name: str) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.RemoveSourceFilter(sourceName=source_name, filterName=filter_name))
            self.logger.info(f"Removed filter {filter_name} from {source_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove filter: {e}")
            return False

    async def set_filter_enabled(self, source_name: str, filter_name: str, enabled: bool) -> bool:
        self._check_connection()
        try:
            self.ws.call(
                requests.SetSourceFilterEnabled(sourceName=source_name, filterName=filter_name, filterEnabled=enabled)
            )
            self.logger.info(f"Set filter {filter_name} enabled to {enabled}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set filter enabled: {e}")
            return False

    async def get_audio_monitor_type(self, source_name: str) -> str:
        self._check_connection()
        response = self.ws.call(requests.GetInputAudioMonitorType(inputName=source_name))
        return response.datain.get("monitorType", "")

    async def set_audio_monitor_type(self, source_name: str, monitor_type: str) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.SetInputAudioMonitorType(inputName=source_name, monitorType=monitor_type))
            self.logger.info(f"Set audio monitor type for {source_name} to {monitor_type}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set audio monitor type: {e}")
            return False

    async def get_audio_balance(self, source_name: str) -> float:
        self._check_connection()
        response = self.ws.call(requests.GetInputAudioBalance(inputName=source_name))
        return response.datain.get("inputAudioBalance", 0.5)

    async def set_audio_balance(self, source_name: str, balance: float) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.SetInputAudioBalance(inputName=source_name, inputAudioBalance=balance))
            self.logger.info(f"Set audio balance for {source_name} to {balance}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set audio balance: {e}")
            return False

    async def get_audio_sync_offset(self, source_name: str) -> int:
        self._check_connection()
        response = self.ws.call(requests.GetInputAudioSyncOffset(inputName=source_name))
        return response.datain.get("inputAudioSyncOffset", 0)

    async def set_audio_sync_offset(self, source_name: str, offset_ms: int) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.SetInputAudioSyncOffset(inputName=source_name, inputAudioSyncOffset=offset_ms))
            self.logger.info(f"Set audio sync offset for {source_name} to {offset_ms}ms")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set audio sync offset: {e}")
            return False

    async def get_audio_tracks(self, source_name: str) -> Dict[str, bool]:
        self._check_connection()
        response = self.ws.call(requests.GetInputAudioTracks(inputName=source_name))
        return response.datain.get("inputAudioTracks", {})

    async def set_audio_tracks(self, source_name: str, tracks: Dict[str, bool]) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.SetInputAudioTracks(inputName=source_name, inputAudioTracks=tracks))
            self.logger.info(f"Set audio tracks for {source_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set audio tracks: {e}")
            return False

    async def get_scene_item_transform(self, scene_name: str, item_id: int) -> Dict[str, Any]:
        self._check_connection()
        response = self.ws.call(requests.GetSceneItemTransform(sceneName=scene_name, sceneItemId=item_id))
        return response.datain.get("sceneItemTransform", {})

    async def set_scene_item_transform(self, scene_name: str, item_id: int, transform: Dict[str, Any]) -> bool:
        self._check_connection()
        try:
            self.ws.call(
                requests.SetSceneItemTransform(sceneName=scene_name, sceneItemId=item_id, sceneItemTransform=transform)
            )
            self.logger.info(f"Set transform for scene item {item_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set scene item transform: {e}")
            return False

    async def get_hotkey_list(self) -> List[str]:
        self._check_connection()
        response = self.ws.call(requests.GetHotkeyList())
        return response.datain.get("hotkeys", [])

    async def trigger_hotkey(self, hotkey_name: str) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.TriggerHotkeyByName(hotkeyName=hotkey_name))
            self.logger.info(f"Triggered hotkey: {hotkey_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to trigger hotkey: {e}")
            return False

    async def get_virtual_cam_status(self) -> bool:
        self._check_connection()
        response = self.ws.call(requests.GetVirtualCamStatus())
        return response.datain.get("outputActive", False)

    async def start_virtual_cam(self) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.StartVirtualCam())
            self.logger.info("Virtual camera started")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start virtual camera: {e}")
            return False

    async def stop_virtual_cam(self) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.StopVirtualCam())
            self.logger.info("Virtual camera stopped")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop virtual camera: {e}")
            return False

    async def toggle_virtual_cam(self) -> bool:
        self._check_connection()
        response = self.ws.call(requests.ToggleVirtualCam())
        return response.datain.get("outputActive", False)

    async def get_stream_service_settings(self) -> Dict[str, Any]:
        self._check_connection()
        response = self.ws.call(requests.GetStreamServiceSettings())
        return response.datain.get("streamServiceSettings", {})

    async def set_stream_service_settings(self, settings: Dict[str, Any]) -> bool:
        self._check_connection()
        try:
            self.ws.call(
                requests.SetStreamServiceSettings(
                    streamServiceType=settings.get("service", "rtmp_common"), streamServiceSettings=settings
                )
            )
            self.logger.info("Updated stream service settings")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set stream service settings: {e}")
            return False

    async def pause_recording(self) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.PauseRecord())
            self.logger.info("Recording paused")
            return True
        except Exception as e:
            self.logger.error(f"Failed to pause recording: {e}")
            return False

    async def resume_recording(self) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.ResumeRecord())
            self.logger.info("Recording resumed")
            return True
        except Exception as e:
            self.logger.error(f"Failed to resume recording: {e}")
            return False

    async def toggle_recording_pause(self) -> bool:
        self._check_connection()
        response = self.ws.call(requests.ToggleRecordPause())
        return response.datain.get("outputPaused", False)

    async def get_replay_buffer_status(self) -> bool:
        self._check_connection()
        response = self.ws.call(requests.GetReplayBufferStatus())
        return response.datain.get("outputActive", False)

    async def start_replay_buffer(self) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.StartReplayBuffer())
            self.logger.info("Replay buffer started")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start replay buffer: {e}")
            return False

    async def stop_replay_buffer(self) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.StopReplayBuffer())
            self.logger.info("Replay buffer stopped")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop replay buffer: {e}")
            return False

    async def save_replay_buffer(self) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.SaveReplayBuffer())
            self.logger.info("Replay buffer saved")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save replay buffer: {e}")
            return False

    async def get_output_settings(self, output_name: str) -> Dict[str, Any]:
        self._check_connection()
        response = self.ws.call(requests.GetOutputSettings(outputName=output_name))
        return response.datain.get("outputSettings", {})

    async def set_output_settings(self, output_name: str, settings: Dict[str, Any]) -> bool:
        self._check_connection()
        try:
            self.ws.call(requests.SetOutputSettings(outputName=output_name, outputSettings=settings))
            self.logger.info(f"Updated output settings for {output_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set output settings: {e}")
            return False


class AdvancedOBSController:
    def __init__(self, agent: AdvancedOBSAgent):
        self.agent = agent
        self.logger = logging.getLogger(__name__)

    async def apply_chroma_key(
        self, source_name: str, key_color: int = 0x00FF00, similarity: int = 400, smoothness: int = 80
    ) -> bool:
        filter_settings = {
            "key_color": key_color,
            "similarity": similarity,
            "smoothness": smoothness,
            "key_color_type": "green",
        }

        return await self.agent.add_filter(
            source_name=source_name,
            filter_name="Chroma Key",
            filter_kind="chroma_key_filter",
            filter_settings=filter_settings,
        )

    async def apply_noise_suppression(self, source_name: str, suppression_level: int = -30) -> bool:
        filter_settings = {"suppress_level": suppression_level}

        return await self.agent.add_filter(
            source_name=source_name,
            filter_name="Noise Suppression",
            filter_kind="noise_suppress_filter",
            filter_settings=filter_settings,
        )

    async def apply_compressor(
        self, source_name: str, ratio: float = 10.0, threshold: float = -18.0, attack: float = 6.0
    ) -> bool:
        filter_settings = {
            "ratio": ratio,
            "threshold": threshold,
            "attack_time": attack,
            "release_time": 60.0,
            "output_gain": 0.0,
        }

        return await self.agent.add_filter(
            source_name=source_name,
            filter_name="Compressor",
            filter_kind="compressor_filter",
            filter_settings=filter_settings,
        )

    async def create_pip_layout(
        self, main_source: str, pip_source: str, pip_position: Tuple[float, float] = (0.7, 0.7), pip_scale: float = 0.25
    ) -> bool:
        current_scene = await self.agent.get_current_scene()
        scene_items = await self.agent.get_scene_items(current_scene)

        pip_item_id = None
        for item in scene_items:
            if item.get("sourceName") == pip_source:
                pip_item_id = item.get("sceneItemId")
                break

        if pip_item_id:
            transform = {
                "positionX": pip_position[0] * 1920,
                "positionY": pip_position[1] * 1080,
                "scaleX": pip_scale,
                "scaleY": pip_scale,
                "cropTop": 0,
                "cropBottom": 0,
                "cropLeft": 0,
                "cropRight": 0,
            }

            return await self.agent.set_scene_item_transform(
                scene_name=current_scene, item_id=pip_item_id, transform=transform
            )

        return False

    async def create_animated_transition(
        self, from_scene: str, to_scene: str, transition_type: str = "Slide", duration_ms: int = 500
    ) -> bool:
        await self.agent.set_transition(transition_type)
        await self.agent.set_transition_duration(duration_ms)

        await self.agent.set_scene(from_scene)
        await asyncio.sleep(0.5)
        await self.agent.set_scene(to_scene)

        return True

    async def balance_audio_levels(self, target_db: float = -20.0) -> Dict[str, float]:
        sources = await self.agent.get_sources()
        audio_sources = [s for s in sources if "Audio" in s.get("inputKind", "")]

        adjustments = {}

        for source in audio_sources:
            source_name = source["inputName"]
            current_volume = await self.agent.get_source_volume(source_name)
            current_db = current_volume["volume_db"]

            adjustment = target_db - current_db

            await self.agent.set_source_volume(source_name, volume_db=target_db)
            adjustments[source_name] = adjustment

            self.logger.info(f"Adjusted {source_name} by {adjustment:.1f} dB")

        return adjustments

    async def create_stream_starting_sequence(
        self, countdown_seconds: int = 10, starting_scene: str = "Starting Soon"
    ) -> bool:
        await self.agent.set_scene(starting_scene)

        for i in range(countdown_seconds, 0, -1):
            self.logger.info(f"Starting in {i} seconds...")
            await asyncio.sleep(1)

        await self.agent.start_streaming()
        await self.agent.set_scene("Main Scene")

        return True

    async def monitor_and_auto_adjust_audio(
        self, duration_seconds: int = 60, target_range: Tuple[float, float] = (-25.0, -15.0)
    ):
        end_time = datetime.now() + timedelta(seconds=duration_seconds)

        while datetime.now() < end_time:
            sources = await self.agent.get_sources()
            audio_sources = [s for s in sources if "Audio" in s.get("inputKind", "")]

            for source in audio_sources:
                source_name = source["inputName"]
                volume = await self.agent.get_source_volume(source_name)
                current_db = volume["volume_db"]

                if current_db < target_range[0]:
                    new_db = target_range[0]
                    await self.agent.set_source_volume(source_name, volume_db=new_db)
                    self.logger.info(f"Boosted {source_name} to {new_db} dB")
                elif current_db > target_range[1]:
                    new_db = target_range[1]
                    await self.agent.set_source_volume(source_name, volume_db=new_db)
                    self.logger.info(f"Reduced {source_name} to {new_db} dB")

            await asyncio.sleep(2)

    async def create_highlight_reel(self, clips: List[Dict[str, Any]]) -> str:
        await self.agent.start_recording()

        for clip in clips:
            scene = clip.get("scene")
            duration = clip.get("duration", 5)
            transition = clip.get("transition", "Cut")

            await self.agent.set_transition(transition)
            await self.agent.set_scene(scene)
            await asyncio.sleep(duration)

        output_path = await self.agent.stop_recording()
        return output_path
