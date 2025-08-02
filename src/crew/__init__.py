# Chat Intelligence System
from .chat_intelligence_agents import ChatIntelligenceCrew, create_chat_intelligence_crew
from .chat_intelligence_tools import (
    ChatAnalysisTool,
    ChatModerationTool,
    ChatSentimentTool,
    EngagementTrendTool,
    TopicExtractionTool,
)

# Legacy OBS Crew (may have import issues, importing conditionally)
try:
    from .obs_crew_agents import OBSStreamCrew, PodcastCrew, TutorialCrew
    from .obs_crew_tools import (
        OBSAudioTool,
        OBSFilterTool,
        OBSRecordingTool,
        OBSSceneTool,
        OBSSnapshotTool,
        OBSStatsTool,
        OBSStreamingTool,
    )
    
    _obs_tools_available = True
except ImportError:
    _obs_tools_available = False

__all__ = [
    # Chat Intelligence
    "ChatIntelligenceCrew",
    "create_chat_intelligence_crew",
    "ChatAnalysisTool",
    "ChatModerationTool", 
    "ChatSentimentTool",
    "EngagementTrendTool",
    "TopicExtractionTool",
]

# Add OBS tools if available
if _obs_tools_available:
    __all__.extend([
        "OBSStreamCrew",
        "PodcastCrew", 
        "TutorialCrew",
        "OBSSceneTool",
        "OBSAudioTool",
        "OBSRecordingTool",
        "OBSStreamingTool",
        "OBSStatsTool",
        "OBSFilterTool",
        "OBSSnapshotTool",
    ])
