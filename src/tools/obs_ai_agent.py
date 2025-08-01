import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from advanced_features import AdvancedOBSAgent, AdvancedOBSController



class StreamGoal(Enum):
    MAINTAIN_QUALITY = "maintain_quality"
    MAXIMIZE_ENGAGEMENT = "maximize_engagement"
    MINIMIZE_RESOURCES = "minimize_resources"
    RECORDING_QUALITY = "recording_quality"
    TUTORIAL_CLARITY = "tutorial_clarity"


class StreamEvent(Enum):
    LOW_AUDIO = "low_audio"
    HIGH_AUDIO = "high_audio"
    DROPPED_FRAMES = "dropped_frames"
    SCENE_STALE = "scene_stale"
    CPU_HIGH = "cpu_high"
    NETWORK_ISSUES = "network_issues"
    AUDIO_CLIPPING = "audio_clipping"
    NO_AUDIO = "no_audio"
    BLACK_SCREEN = "black_screen"


@dataclass
class StreamState:
    current_scene: str = ""
    is_streaming: bool = False
    is_recording: bool = False
    stream_duration: int = 0
    dropped_frames_percent: float = 0.0
    cpu_usage: float = 0.0
    audio_levels: Dict[str, float] = field(default_factory=dict)
    scene_duration: int = 0
    last_scene_change: datetime = field(default_factory=datetime.now)
    viewer_count: int = 0
    chat_activity: float = 0.0
    events_history: List[Tuple[datetime, StreamEvent]] = field(default_factory=list)


@dataclass
class AgentConfig:
    goals: List[StreamGoal] = field(default_factory=list)
    scene_min_duration: int = 30  # seconds
    scene_max_duration: int = 300  # seconds
    audio_target_db: float = -20.0
    audio_tolerance_db: float = 5.0
    max_dropped_frames_percent: float = 5.0
    max_cpu_percent: float = 80.0
    auto_scene_switching: bool = True
    auto_audio_adjustment: bool = True
    auto_quality_adjustment: bool = True
    engagement_scenes: List[str] = field(default_factory=list)


class OBSAIAgent:
    """
    An autonomous agent that monitors and manages OBS Studio based on goals and rules.
    Makes decisions about scene switching, audio levels, quality settings, and more.
    """

    def __init__(self, obs_agent: AdvancedOBSAgent, config: AgentConfig):
        self.obs = obs_agent
        self.config = config
        self.state = StreamState()
        self.controller = AdvancedOBSController(obs_agent)
        self.logger = logging.getLogger(__name__)
        self.decision_history: List[Dict[str, Any]] = []
        self.monitoring = False
        self.rules_engine = RulesEngine()
        self.learning_data: List[Dict[str, Any]] = []

    async def start(self):
        """Start the autonomous agent"""
        self.monitoring = True
        self.logger.info("OBS AI Agent started")

        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_stream_health()),
            asyncio.create_task(self._monitor_audio_levels()),
            asyncio.create_task(self._monitor_scene_staleness()),
            asyncio.create_task(self._decision_loop()),
        ]

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            self.logger.info("Agent monitoring cancelled")
        finally:
            for task in tasks:
                task.cancel()

    async def stop(self):
        """Stop the autonomous agent"""
        self.monitoring = False
        self.logger.info("OBS AI Agent stopped")
        self._save_learning_data()

    async def _update_state(self):
        """Update current stream state"""
        try:
            # Update basic state
            self.state.current_scene = await self.obs.get_current_scene()

            streaming_status = await self.obs.get_streaming_status()
            self.state.is_streaming = streaming_status["is_streaming"]
            self.state.stream_duration = streaming_status["duration"]

            if streaming_status["total_frames"] > 0:
                self.state.dropped_frames_percent = (
                    streaming_status["skipped_frames"] / streaming_status["total_frames"] * 100
                )

            recording_status = await self.obs.get_recording_status()
            self.state.is_recording = recording_status["is_recording"]

            # Update audio levels
            sources = await self.obs.get_sources()
            for source in sources:
                if "Audio" in source.get("inputKind", ""):
                    volume = await self.obs.get_source_volume(source["inputName"])
                    self.state.audio_levels[source["inputName"]] = volume["volume_db"]

            # Update scene duration
            now = datetime.now()
            self.state.scene_duration = (now - self.state.last_scene_change).seconds

            # Get system stats
            stats = await self.obs.get_stats()
            self.state.cpu_usage = stats.get("cpuUsage", 0)

        except Exception as e:
            self.logger.error(f"Failed to update state: {e}")

    async def _monitor_stream_health(self):
        """Monitor stream health metrics"""
        while self.monitoring:
            await self._update_state()

            # Check for issues
            if self.state.dropped_frames_percent > self.config.max_dropped_frames_percent:
                self._record_event(StreamEvent.DROPPED_FRAMES)

            if self.state.cpu_usage > self.config.max_cpu_percent:
                self._record_event(StreamEvent.CPU_HIGH)

            await asyncio.sleep(5)

    async def _monitor_audio_levels(self):
        """Monitor and detect audio issues"""
        while self.monitoring:
            for source_name, level_db in self.state.audio_levels.items():
                target = self.config.audio_target_db
                tolerance = self.config.audio_tolerance_db

                if level_db < -60:  # Essentially no audio
                    self._record_event(StreamEvent.NO_AUDIO)
                elif level_db < target - tolerance:
                    self._record_event(StreamEvent.LOW_AUDIO)
                elif level_db > target + tolerance:
                    self._record_event(StreamEvent.HIGH_AUDIO)
                elif level_db > -3:  # Clipping threshold
                    self._record_event(StreamEvent.AUDIO_CLIPPING)

            await asyncio.sleep(2)

    async def _monitor_scene_staleness(self):
        """Monitor if scene has been active too long"""
        while self.monitoring:
            if self.config.auto_scene_switching and self.state.scene_duration > self.config.scene_max_duration:
                self._record_event(StreamEvent.SCENE_STALE)

            await asyncio.sleep(10)

    async def _decision_loop(self):
        """Main decision-making loop"""
        while self.monitoring:
            await self._update_state()

            # Get recent events
            recent_events = self._get_recent_events(seconds=30)

            # Make decisions based on state and events
            decisions = await self._make_decisions(recent_events)

            # Execute decisions
            for decision in decisions:
                await self._execute_decision(decision)

            await asyncio.sleep(5)

    def _record_event(self, event: StreamEvent):
        """Record an event in history"""
        self.state.events_history.append((datetime.now(), event))
        # Keep only last 100 events
        if len(self.state.events_history) > 100:
            self.state.events_history.pop(0)

    def _get_recent_events(self, seconds: int) -> List[StreamEvent]:
        """Get events from the last N seconds"""
        cutoff = datetime.now() - timedelta(seconds=seconds)
        return [event for timestamp, event in self.state.events_history if timestamp > cutoff]

    async def _make_decisions(self, recent_events: List[StreamEvent]) -> List[Dict[str, Any]]:
        """Make decisions based on current state and events"""
        decisions = []

        # Audio adjustment decisions
        if StreamEvent.LOW_AUDIO in recent_events and self.config.auto_audio_adjustment:
            for source_name, level in self.state.audio_levels.items():
                if level < self.config.audio_target_db - self.config.audio_tolerance_db:
                    decisions.append(
                        {
                            "type": "adjust_audio",
                            "source": source_name,
                            "target_db": self.config.audio_target_db,
                            "reason": "Audio level too low",
                        }
                    )

        elif StreamEvent.AUDIO_CLIPPING in recent_events and self.config.auto_audio_adjustment:
            for source_name, level in self.state.audio_levels.items():
                if level > -3:
                    decisions.append(
                        {
                            "type": "adjust_audio",
                            "source": source_name,
                            "target_db": self.config.audio_target_db,
                            "reason": "Audio clipping detected",
                        }
                    )

        # Scene switching decisions
        if StreamEvent.SCENE_STALE in recent_events and self.config.auto_scene_switching:
            decisions.append(
                {"type": "switch_scene", "reason": "Scene active too long", "strategy": "next_in_rotation"}
            )

        # Quality adjustment decisions
        if StreamEvent.DROPPED_FRAMES in recent_events and self.config.auto_quality_adjustment:
            if StreamGoal.MAINTAIN_QUALITY in self.config.goals:
                decisions.append(
                    {"type": "reduce_quality", "reason": "Dropped frames detected", "action": "lower_bitrate"}
                )

        # CPU optimization decisions
        if StreamEvent.CPU_HIGH in recent_events:
            decisions.append(
                {
                    "type": "optimize_resources",
                    "reason": "High CPU usage",
                    "actions": ["disable_filters", "reduce_sources"],
                }
            )

        # Apply rules engine
        rule_decisions = self.rules_engine.evaluate(self.state, recent_events)
        decisions.extend(rule_decisions)

        return decisions

    async def _execute_decision(self, decision: Dict[str, Any]):
        """Execute a decision"""
        try:
            decision_type = decision["type"]
            self.logger.info(f"Executing decision: {decision_type} - {decision.get('reason', '')}")

            if decision_type == "adjust_audio":
                await self.obs.set_source_volume(decision["source"], volume_db=decision["target_db"])

            elif decision_type == "switch_scene":
                await self._smart_scene_switch(decision.get("strategy", "next_in_rotation"))

            elif decision_type == "reduce_quality":
                await self._reduce_stream_quality()

            elif decision_type == "optimize_resources":
                await self._optimize_resources(decision.get("actions", []))

            # Record decision
            self.decision_history.append(
                {"timestamp": datetime.now().isoformat(), "decision": decision, "state": self._serialize_state()}
            )

            # Learn from decision
            self._record_learning_data(decision)

        except Exception as e:
            self.logger.error(f"Failed to execute decision: {e}")

    async def _smart_scene_switch(self, strategy: str):
        """Intelligently switch scenes based on strategy"""
        scenes = await self.obs.get_scenes()
        current_scene = self.state.current_scene

        if strategy == "next_in_rotation":
            # Simple rotation
            try:
                current_index = scenes.index(current_scene)
                next_index = (current_index + 1) % len(scenes)
                next_scene = scenes[next_index]
            except ValueError:
                next_scene = scenes[0] if scenes else None

        elif strategy == "maximize_engagement" and self.config.engagement_scenes:
            # Switch to high-engagement scenes
            next_scene = self._select_engagement_scene()

        elif strategy == "least_recently_used":
            # Switch to scene that hasn't been used recently
            next_scene = self._select_lru_scene(scenes)

        if next_scene and next_scene != current_scene:
            await self.obs.set_scene(next_scene)
            self.state.last_scene_change = datetime.now()
            self.state.scene_duration = 0

    async def _reduce_stream_quality(self):
        """Reduce stream quality to improve performance"""
        # This would interact with OBS output settings
        # For now, we'll reduce some source quality settings
        sources = await self.obs.get_sources()

        for source in sources:
            if source.get("inputKind") == "av_capture_input":  # Webcam
                settings = await self.obs.get_source_settings(source["inputName"])
                # Reduce resolution or framerate
                settings["settings"]["resolution"] = "1280x720"
                settings["settings"]["fps"] = 30
                await self.obs.set_source_settings(source["inputName"], settings["settings"])

    async def _optimize_resources(self, actions: List[str]):
        """Optimize OBS resources based on CPU usage"""
        if "disable_filters" in actions:
            # Temporarily disable heavy filters
            sources = await self.obs.get_sources()
            for source in sources:
                filters = await self.obs.get_filters(source["inputName"])
                for filter_item in filters:
                    if filter_item["filterKind"] in ["gpu_delay", "chroma_key_filter"]:
                        await self.obs.set_filter_enabled(source["inputName"], filter_item["filterName"], False)

        if "reduce_sources" in actions:
            # Disable non-essential sources
            scene_items = await self.obs.get_scene_items(self.state.current_scene)
            for item in scene_items:
                if "overlay" in item.get("sourceName", "").lower():
                    await self.obs.set_scene_item_enabled(self.state.current_scene, item["sceneItemId"], False)

    def _select_engagement_scene(self) -> Optional[str]:
        """Select a scene that maximizes engagement"""
        # In a real implementation, this would use analytics data
        if self.config.engagement_scenes:
            return self.config.engagement_scenes[0]
        return None

    def _select_lru_scene(self, scenes: List[str]) -> Optional[str]:
        """Select least recently used scene"""
        # Simple implementation - in reality would track scene history
        return scenes[-1] if scenes else None

    def _serialize_state(self) -> Dict[str, Any]:
        """Serialize current state for logging"""
        return {
            "current_scene": self.state.current_scene,
            "is_streaming": self.state.is_streaming,
            "dropped_frames_percent": self.state.dropped_frames_percent,
            "cpu_usage": self.state.cpu_usage,
            "audio_levels": self.state.audio_levels,
            "scene_duration": self.state.scene_duration,
        }

    def _record_learning_data(self, decision: Dict[str, Any]):
        """Record data for future learning"""
        self.learning_data.append(
            {
                "timestamp": datetime.now().isoformat(),
                "state": self._serialize_state(),
                "decision": decision,
                "events": [e.value for e in self._get_recent_events(30)],
            }
        )

    def _save_learning_data(self):
        """Save learning data to file"""
        if self.learning_data:
            filename = f"obs_agent_learning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w") as f:
                json.dump(self.learning_data, f, indent=2)
            self.logger.info(f"Saved learning data to {filename}")

    async def handle_user_feedback(self, feedback: str, positive: bool):
        """Process user feedback on agent actions"""
        if self.decision_history:
            last_decision = self.decision_history[-1]
            last_decision["user_feedback"] = {
                "feedback": feedback,
                "positive": positive,
                "timestamp": datetime.now().isoformat(),
            }

            # Adjust future behavior based on feedback
            if not positive:
                self.logger.info(f"Negative feedback received: {feedback}")
                # Could adjust weights or rules based on feedback


class RulesEngine:
    """Rule-based decision engine for common scenarios"""

    def __init__(self):
        self.rules = [
            {
                "name": "no_audio_emergency",
                "condition": lambda state, events: StreamEvent.NO_AUDIO in events,
                "action": {
                    "type": "emergency_audio",
                    "reason": "No audio detected",
                    "actions": ["unmute_all", "boost_audio"],
                },
            },
            {
                "name": "black_screen_detection",
                "condition": lambda state, events: StreamEvent.BLACK_SCREEN in events,
                "action": {"type": "switch_scene", "reason": "Black screen detected", "strategy": "fallback_scene"},
            },
            {
                "name": "network_optimization",
                "condition": lambda state, events: (StreamEvent.NETWORK_ISSUES in events and state.is_streaming),
                "action": {"type": "reduce_bitrate", "reason": "Network issues detected", "target_reduction": 0.7},
            },
        ]

    def evaluate(self, state: StreamState, events: List[StreamEvent]) -> List[Dict[str, Any]]:
        """Evaluate rules and return decisions"""
        decisions = []

        for rule in self.rules:
            if rule["condition"](state, events):
                decisions.append(rule["action"])

        return decisions


class OBSAgentOrchestrator:
    """High-level orchestrator for managing the AI agent"""

    def __init__(self, password: str = ""):
        self.obs = AdvancedOBSAgent(password=password)
        self.agent = None
        self.logger = logging.getLogger(__name__)

    async def start_autonomous_stream(self, goals: List[StreamGoal], duration_hours: float = 2.0):
        """Start a fully autonomous streaming session"""
        try:
            # Connect to OBS
            if not await self.obs.connect():
                raise ConnectionError("Failed to connect to OBS")

            # Configure agent
            config = AgentConfig(
                goals=goals, auto_scene_switching=True, auto_audio_adjustment=True, auto_quality_adjustment=True
            )

            # Load engagement scenes if maximizing engagement
            if StreamGoal.MAXIMIZE_ENGAGEMENT in goals:
                scenes = await self.obs.get_scenes()
                config.engagement_scenes = [s for s in scenes if "highlight" in s.lower()]

            # Create and start agent
            self.agent = OBSAIAgent(self.obs, config)

            # Start streaming
            await self.obs.start_streaming()
            self.logger.info("Autonomous streaming started")

            # Run agent for specified duration
            agent_task = asyncio.create_task(self.agent.start())

            await asyncio.sleep(duration_hours * 3600)

            # Stop agent and streaming
            await self.agent.stop()
            agent_task.cancel()
            await self.obs.stop_streaming()

            self.logger.info("Autonomous streaming completed")

        finally:
            self.obs.disconnect()

    async def start_autonomous_recording(self, goals: List[StreamGoal], scenes_sequence: List[Dict[str, Any]]):
        """Start an autonomous recording session with planned scenes"""
        try:
            if not await self.obs.connect():
                raise ConnectionError("Failed to connect to OBS")

            config = AgentConfig(
                goals=goals,
                auto_scene_switching=False,  # We'll handle scene switching
                auto_audio_adjustment=True,
                auto_quality_adjustment=True,
            )

            self.agent = OBSAIAgent(self.obs, config)

            # Start recording
            await self.obs.start_recording()

            # Start agent
            agent_task = asyncio.create_task(self.agent.start())

            # Execute scene sequence
            for scene_config in scenes_sequence:
                scene_name = scene_config["scene"]
                duration = scene_config.get("duration", 60)

                await self.obs.set_scene(scene_name)
                self.logger.info(f"Recording scene: {scene_name} for {duration}s")

                # Let agent handle audio and quality during this time
                await asyncio.sleep(duration)

            # Stop everything
            await self.agent.stop()
            agent_task.cancel()
            output_path = await self.obs.stop_recording()

            self.logger.info(f"Autonomous recording saved to: {output_path}")
            return output_path

        finally:
            self.obs.disconnect()


# Example usage
async def main():
    orchestrator = OBSAgentOrchestrator(password="your_password")

    # Example 1: Autonomous streaming focused on quality
    await orchestrator.start_autonomous_stream(
        goals=[StreamGoal.MAINTAIN_QUALITY, StreamGoal.MAXIMIZE_ENGAGEMENT], duration_hours=2.0
    )

    # Example 2: Autonomous recording focused on tutorial clarity
    await orchestrator.start_autonomous_recording(
        goals=[StreamGoal.TUTORIAL_CLARITY, StreamGoal.RECORDING_QUALITY],
        scenes_sequence=[
            {"scene": "Intro", "duration": 10},
            {"scene": "Main Content", "duration": 300},
            {"scene": "Outro", "duration": 10},
        ],
    )


if __name__ == "__main__":
    asyncio.run(main())
