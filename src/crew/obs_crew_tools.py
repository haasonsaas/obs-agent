from crewai_tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional, Dict, List, Any
import asyncio
from obs_agent import OBSAgent
from advanced_features import AdvancedOBSAgent
import json


class OBSConnection:
    """Singleton OBS connection manager"""
    _instance = None
    _obs_agent = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OBSConnection, cls).__new__(cls)
        return cls._instance
    
    def get_agent(self) -> AdvancedOBSAgent:
        if self._obs_agent is None:
            self._obs_agent = AdvancedOBSAgent(
                host="localhost",
                port=4455,
                password=""  # Will be set from env
            )
        return self._obs_agent
    
    async def ensure_connected(self):
        agent = self.get_agent()
        if not agent.connected:
            await agent.connect()
        return agent


# Tool Input Schemas
class SceneInput(BaseModel):
    """Input for scene operations"""
    scene_name: str = Field(..., description="Name of the scene")


class AudioInput(BaseModel):
    """Input for audio operations"""
    source_name: str = Field(..., description="Name of the audio source")
    volume_db: Optional[float] = Field(None, description="Volume in decibels")
    muted: Optional[bool] = Field(None, description="Mute state")


class RecordingInput(BaseModel):
    """Input for recording operations"""
    action: str = Field(..., description="Action to perform: start, stop, pause, resume")


class StreamingInput(BaseModel):
    """Input for streaming operations"""
    action: str = Field(..., description="Action to perform: start, stop, toggle")


class FilterInput(BaseModel):
    """Input for filter operations"""
    source_name: str = Field(..., description="Name of the source")
    filter_name: str = Field(..., description="Name of the filter")
    filter_type: Optional[str] = Field(None, description="Type of filter")
    settings: Optional[Dict[str, Any]] = Field(None, description="Filter settings")


# OBS Tools for CrewAI
class OBSSceneTool(BaseTool):
    name: str = "OBS Scene Manager"
    description: str = "Manage OBS scenes - list, switch, create, or remove scenes"
    args_schema: Type[BaseModel] = SceneInput
    
    def _run(self, scene_name: str) -> str:
        """Synchronous wrapper for scene operations"""
        return asyncio.run(self._arun(scene_name))
    
    async def _arun(self, scene_name: str) -> str:
        """Switch to a specific scene"""
        try:
            conn = OBSConnection()
            obs = await conn.ensure_connected()
            
            # If scene_name is "list", return all scenes
            if scene_name.lower() == "list":
                scenes = await obs.get_scenes()
                current = await obs.get_current_scene()
                return f"Available scenes: {', '.join(scenes)}. Current scene: {current}"
            
            # Otherwise switch to the scene
            success = await obs.set_scene(scene_name)
            if success:
                return f"Successfully switched to scene: {scene_name}"
            else:
                return f"Failed to switch to scene: {scene_name}"
                
        except Exception as e:
            return f"Error managing scene: {str(e)}"


class OBSAudioTool(BaseTool):
    name: str = "OBS Audio Controller"
    description: str = "Control audio sources - adjust volume, mute/unmute, check levels"
    args_schema: Type[BaseModel] = AudioInput
    
    def _run(self, source_name: str, volume_db: Optional[float] = None, 
             muted: Optional[bool] = None) -> str:
        """Synchronous wrapper for audio operations"""
        return asyncio.run(self._arun(source_name, volume_db, muted))
    
    async def _arun(self, source_name: str, volume_db: Optional[float] = None,
                   muted: Optional[bool] = None) -> str:
        """Control audio settings"""
        try:
            conn = OBSConnection()
            obs = await conn.ensure_connected()
            
            results = []
            
            # Get current audio status
            if source_name.lower() == "list":
                sources = await obs.get_sources()
                audio_sources = [s for s in sources if "Audio" in s.get("inputKind", "")]
                audio_info = []
                for source in audio_sources:
                    name = source["inputName"]
                    volume = await obs.get_source_volume(name)
                    is_muted = await obs.get_source_mute(name)
                    audio_info.append(f"{name}: {volume['volume_db']:.1f}dB, {'muted' if is_muted else 'active'}")
                return "Audio sources: " + "; ".join(audio_info)
            
            # Adjust volume if specified
            if volume_db is not None:
                success = await obs.set_source_volume(source_name, volume_db=volume_db)
                results.append(f"Set volume to {volume_db}dB" if success else "Failed to set volume")
            
            # Adjust mute if specified
            if muted is not None:
                success = await obs.set_source_mute(source_name, muted)
                results.append(f"{'Muted' if muted else 'Unmuted'} {source_name}" if success else "Failed to set mute")
            
            # Get current status
            volume = await obs.get_source_volume(source_name)
            is_muted = await obs.get_source_mute(source_name)
            results.append(f"Current: {volume['volume_db']:.1f}dB, {'muted' if is_muted else 'active'}")
            
            return "; ".join(results)
            
        except Exception as e:
            return f"Error controlling audio: {str(e)}"


class OBSRecordingTool(BaseTool):
    name: str = "OBS Recording Controller"
    description: str = "Control OBS recording - start, stop, pause, resume, or check status"
    args_schema: Type[BaseModel] = RecordingInput
    
    def _run(self, action: str) -> str:
        """Synchronous wrapper for recording operations"""
        return asyncio.run(self._arun(action))
    
    async def _arun(self, action: str) -> str:
        """Control recording"""
        try:
            conn = OBSConnection()
            obs = await conn.ensure_connected()
            
            if action.lower() == "start":
                success = await obs.start_recording()
                return "Recording started" if success else "Failed to start recording"
            
            elif action.lower() == "stop":
                output_path = await obs.stop_recording()
                return f"Recording stopped. File saved to: {output_path}" if output_path else "Failed to stop recording"
            
            elif action.lower() == "pause":
                success = await obs.pause_recording()
                return "Recording paused" if success else "Failed to pause recording"
            
            elif action.lower() == "resume":
                success = await obs.resume_recording()
                return "Recording resumed" if success else "Failed to resume recording"
            
            elif action.lower() == "status":
                status = await obs.get_recording_status()
                if status["is_recording"]:
                    duration = status["duration"]
                    paused = "paused" if status["is_paused"] else "active"
                    return f"Recording {paused} for {duration}s, {status['bytes']/1024/1024:.1f}MB"
                else:
                    return "Not recording"
            
            else:
                return f"Unknown action: {action}. Use start, stop, pause, resume, or status"
                
        except Exception as e:
            return f"Error controlling recording: {str(e)}"


class OBSStreamingTool(BaseTool):
    name: str = "OBS Streaming Controller"
    description: str = "Control OBS streaming - start, stop, or check status with health metrics"
    args_schema: Type[BaseModel] = StreamingInput
    
    def _run(self, action: str) -> str:
        """Synchronous wrapper for streaming operations"""
        return asyncio.run(self._arun(action))
    
    async def _arun(self, action: str) -> str:
        """Control streaming"""
        try:
            conn = OBSConnection()
            obs = await conn.ensure_connected()
            
            if action.lower() == "start":
                success = await obs.start_streaming()
                return "Streaming started" if success else "Failed to start streaming"
            
            elif action.lower() == "stop":
                success = await obs.stop_streaming()
                return "Streaming stopped" if success else "Failed to stop streaming"
            
            elif action.lower() == "status":
                status = await obs.get_streaming_status()
                if status["is_streaming"]:
                    duration = status["duration"]
                    dropped_percent = 0
                    if status["total_frames"] > 0:
                        dropped_percent = (status["skipped_frames"] / status["total_frames"]) * 100
                    return (f"Streaming for {duration}s, "
                           f"{status['bytes']/1024/1024:.1f}MB sent, "
                           f"{dropped_percent:.1f}% frames dropped")
                else:
                    return "Not streaming"
            
            else:
                return f"Unknown action: {action}. Use start, stop, or status"
                
        except Exception as e:
            return f"Error controlling streaming: {str(e)}"


class OBSStatsTool(BaseTool):
    name: str = "OBS Stats Monitor"
    description: str = "Get OBS performance statistics and system health"
    
    def _run(self) -> str:
        """Synchronous wrapper for stats operations"""
        return asyncio.run(self._arun())
    
    async def _arun(self) -> str:
        """Get OBS statistics"""
        try:
            conn = OBSConnection()
            obs = await conn.ensure_connected()
            
            stats = await obs.get_stats()
            
            # Extract key metrics
            cpu = stats.get("cpuUsage", 0)
            memory = stats.get("memoryUsage", 0)
            fps = stats.get("activeFps", 0)
            render_missed = stats.get("renderMissedFrames", 0)
            render_total = stats.get("renderTotalFrames", 0)
            output_missed = stats.get("outputSkippedFrames", 0)
            output_total = stats.get("outputTotalFrames", 0)
            
            # Calculate percentages
            render_missed_percent = (render_missed / render_total * 100) if render_total > 0 else 0
            output_missed_percent = (output_missed / output_total * 100) if output_total > 0 else 0
            
            return (f"CPU: {cpu:.1f}%, Memory: {memory/1024/1024:.0f}MB, "
                   f"FPS: {fps:.1f}, "
                   f"Render missed: {render_missed_percent:.1f}%, "
                   f"Output missed: {output_missed_percent:.1f}%")
            
        except Exception as e:
            return f"Error getting stats: {str(e)}"


class OBSFilterTool(BaseTool):
    name: str = "OBS Filter Manager"
    description: str = "Manage filters on sources - add, remove, or configure filters like chroma key, noise suppression"
    args_schema: Type[BaseModel] = FilterInput
    
    def _run(self, source_name: str, filter_name: str, 
             filter_type: Optional[str] = None, 
             settings: Optional[Dict[str, Any]] = None) -> str:
        """Synchronous wrapper for filter operations"""
        return asyncio.run(self._arun(source_name, filter_name, filter_type, settings))
    
    async def _arun(self, source_name: str, filter_name: str,
                   filter_type: Optional[str] = None,
                   settings: Optional[Dict[str, Any]] = None) -> str:
        """Manage filters"""
        try:
            conn = OBSConnection()
            obs = await conn.ensure_connected()
            
            # Special commands
            if filter_name.lower() == "list":
                filters = await obs.get_filters(source_name)
                if filters:
                    filter_list = [f"{f['filterName']} ({f['filterKind']})" for f in filters]
                    return f"Filters on {source_name}: " + ", ".join(filter_list)
                else:
                    return f"No filters on {source_name}"
            
            # Add preset filters
            if filter_name.lower() == "chroma_key" and filter_type is None:
                success = await obs.add_filter(
                    source_name=source_name,
                    filter_name="Chroma Key",
                    filter_kind="chroma_key_filter",
                    filter_settings={
                        "key_color": 0x00FF00,
                        "similarity": 400,
                        "smoothness": 80,
                        "key_color_type": "green"
                    }
                )
                return "Added chroma key filter" if success else "Failed to add chroma key"
            
            elif filter_name.lower() == "noise_suppression" and filter_type is None:
                success = await obs.add_filter(
                    source_name=source_name,
                    filter_name="Noise Suppression",
                    filter_kind="noise_suppress_filter",
                    filter_settings={"suppress_level": -30}
                )
                return "Added noise suppression" if success else "Failed to add noise suppression"
            
            # Add custom filter
            elif filter_type and settings:
                success = await obs.add_filter(
                    source_name=source_name,
                    filter_name=filter_name,
                    filter_kind=filter_type,
                    filter_settings=settings
                )
                return f"Added {filter_name}" if success else f"Failed to add {filter_name}"
            
            # Remove filter
            elif filter_name.lower().startswith("remove:"):
                filter_to_remove = filter_name[7:]
                success = await obs.remove_filter(source_name, filter_to_remove)
                return f"Removed {filter_to_remove}" if success else f"Failed to remove {filter_to_remove}"
            
            else:
                return "Please specify filter_type and settings, or use presets: chroma_key, noise_suppression"
                
        except Exception as e:
            return f"Error managing filter: {str(e)}"


class OBSSnapshotTool(BaseTool):
    name: str = "OBS Snapshot"
    description: str = "Take a screenshot of a source or get current state information"
    
    def _run(self) -> str:
        """Synchronous wrapper for snapshot operations"""
        return asyncio.run(self._arun())
    
    async def _arun(self) -> str:
        """Get comprehensive OBS state snapshot"""
        try:
            conn = OBSConnection()
            obs = await conn.ensure_connected()
            
            # Gather all state information
            current_scene = await obs.get_current_scene()
            scenes = await obs.get_scenes()
            sources = await obs.get_sources()
            recording_status = await obs.get_recording_status()
            streaming_status = await obs.get_streaming_status()
            stats = await obs.get_stats()
            
            # Build snapshot
            snapshot = {
                "current_scene": current_scene,
                "available_scenes": len(scenes),
                "total_sources": len(sources),
                "is_recording": recording_status["is_recording"],
                "is_streaming": streaming_status["is_streaming"],
                "cpu_usage": f"{stats.get('cpuUsage', 0):.1f}%",
                "fps": stats.get('activeFps', 0)
            }
            
            # Format as readable string
            return (f"Scene: {snapshot['current_scene']} ({snapshot['available_scenes']} total), "
                   f"Sources: {snapshot['total_sources']}, "
                   f"Recording: {'Yes' if snapshot['is_recording'] else 'No'}, "
                   f"Streaming: {'Yes' if snapshot['is_streaming'] else 'No'}, "
                   f"CPU: {snapshot['cpu_usage']}, FPS: {snapshot['fps']:.1f}")
            
        except Exception as e:
            return f"Error getting snapshot: {str(e)}"