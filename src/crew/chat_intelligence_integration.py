"""
Integration layer for Chat Intelligence with OBS Agent and CrewAI.

This module provides the integration between the chat intelligence system,
OBS automation, and the existing CrewAI infrastructure.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..obs_agent.chat_intelligence import ChatIntelligenceService
from ..obs_agent.events.integration import EventSourcingSystem
from .chat_intelligence_agents import ChatIntelligenceCrew, create_chat_intelligence_crew
# Temporarily commented out for testing
# from .obs_crew_tools import OBSConnection

logger = logging.getLogger(__name__)


class ChatIntelligenceIntegration:
    """
    Main integration class that connects chat intelligence with OBS automation.
    
    This class:
    - Manages the chat intelligence service and CrewAI agents
    - Integrates with the event sourcing system
    - Provides automated responses based on chat analysis
    - Coordinates between chat analysis and OBS actions
    """
    
    def __init__(
        self, 
        obs_agent=None,
        event_system: Optional[EventSourcingSystem] = None,
        llm=None
    ):
        self.obs_agent = obs_agent
        self.event_system = event_system
        self.llm = llm
        
        # Initialize chat intelligence service
        self.chat_service = ChatIntelligenceService()
        
        # Initialize CrewAI crew
        self.crew = create_chat_intelligence_crew(self.chat_service, llm)
        
        # Integration state
        self.is_running = False
        self.auto_response_enabled = True
        self.analysis_interval = 30.0  # seconds
        self.last_analysis_time = None
        
        # Performance thresholds for automated actions
        self.thresholds = {
            'low_engagement': 0.3,
            'high_toxicity': 0.6,
            'sentiment_drop': -0.5,
            'engagement_drop_rate': 0.2  # 20% drop triggers action
        }
        
        # OBS connection for automation (temporarily disabled for testing)
        self.obs_connection = None  # OBSConnection()
    
    async def start(self) -> None:
        """Start the chat intelligence integration system."""
        try:
            logger.info("Starting Chat Intelligence Integration...")
            
            # Start chat intelligence service
            await self.chat_service.start()
            
            # Start automated analysis loop
            self.is_running = True
            asyncio.create_task(self._analysis_loop())
            
            logger.info("Chat Intelligence Integration started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Chat Intelligence Integration: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the chat intelligence integration system."""
        try:
            logger.info("Stopping Chat Intelligence Integration...")
            
            self.is_running = False
            await self.chat_service.stop()
            
            logger.info("Chat Intelligence Integration stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Chat Intelligence Integration: {e}")
    
    async def _analysis_loop(self) -> None:
        """Main analysis loop that runs continuous chat intelligence."""
        while self.is_running:
            try:
                await self._perform_periodic_analysis()
                await asyncio.sleep(self.analysis_interval)
                
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
                await asyncio.sleep(5)  # Short delay before retry
    
    async def _perform_periodic_analysis(self) -> None:
        """Perform periodic chat analysis and trigger actions if needed."""
        try:
            # Get current stats
            stats = self.chat_service.get_stats()
            
            # Skip if no recent activity
            if stats.get('message_count', 0) == 0:
                return
            
            # Perform quick engagement check
            engagement_result = await self.crew.engagement_alert()
            
            # Check if immediate action is needed
            if await self._should_trigger_automation(engagement_result):
                await self._trigger_automated_response(engagement_result)
            
            # Update last analysis time
            self.last_analysis_time = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error in periodic analysis: {e}")
    
    async def _should_trigger_automation(self, analysis_result: str) -> bool:
        """Determine if automated response should be triggered."""
        if not self.auto_response_enabled:
            return False
        
        # Simple keyword-based trigger detection
        # In production, this would use more sophisticated NLP
        trigger_keywords = [
            'immediate action needed',
            'engagement dropping',
            'toxicity alert',
            'low engagement',
            'attention required'
        ]
        
        result_lower = analysis_result.lower()
        return any(keyword in result_lower for keyword in trigger_keywords)
    
    async def _trigger_automated_response(self, analysis_result: str) -> None:
        """Trigger automated OBS responses based on analysis."""
        try:
            logger.info("Triggering automated response based on chat analysis")
            
            # Get detailed analysis for response planning
            full_analysis = await self.crew.analyze_current_stream(
                context="Automated response triggered by engagement alert"
            )
            
            # Extract action recommendations from analysis
            actions = self._extract_actions_from_analysis(full_analysis)
            
            # Execute OBS actions
            for action in actions:
                await self._execute_obs_action(action)
            
            # Log to event system if available
            if self.event_system:
                from ..obs_agent.events.domain import DomainEvent, EventMetadata, EventType
                
                class ChatIntelligenceActionTriggered(DomainEvent):
                    def __init__(self, actions: List[str], analysis_summary: str, **kwargs):
                        super().__init__(**kwargs)
                        self.actions = actions
                        self.analysis_summary = analysis_summary
                    
                    def _get_event_type(self) -> EventType:
                        return EventType.CUSTOM
                    
                    def get_event_data(self) -> Dict[str, Any]:
                        return {
                            'actions': self.actions,
                            'analysis_summary': self.analysis_summary
                        }
                
                event = ChatIntelligenceActionTriggered(
                    aggregate_id="chat_intelligence",
                    metadata=EventMetadata(),
                    actions=[str(action) for action in actions],
                    analysis_summary=analysis_result[:500]  # Truncate for storage
                )
                self.event_system.event_store.append(event)
            
        except Exception as e:
            logger.error(f"Error in automated response: {e}")
    
    def _extract_actions_from_analysis(self, analysis: str) -> List[Dict[str, Any]]:
        """Extract actionable OBS commands from analysis text."""
        actions = []
        analysis_lower = analysis.lower()
        
        # Scene switching recommendations
        if 'switch scene' in analysis_lower or 'change scene' in analysis_lower:
            if 'interactive' in analysis_lower or 'q&a' in analysis_lower:
                actions.append({'type': 'scene', 'action': 'switch', 'target': 'Q&A Scene'})
            elif 'gaming' in analysis_lower:
                actions.append({'type': 'scene', 'action': 'switch', 'target': 'Gaming Scene'})
        
        # Audio adjustments
        if 'lower volume' in analysis_lower or 'reduce audio' in analysis_lower:
            actions.append({'type': 'audio', 'action': 'volume', 'source': 'Desktop Audio', 'value': -5})
        elif 'increase volume' in analysis_lower or 'boost audio' in analysis_lower:
            actions.append({'type': 'audio', 'action': 'volume', 'source': 'Desktop Audio', 'value': 5})
        
        # Engagement boosting actions
        if 'low engagement' in analysis_lower:
            actions.append({'type': 'notification', 'message': 'Consider interactive content or Q&A'})
        
        # Moderation actions
        if 'toxicity' in analysis_lower and 'high' in analysis_lower:
            actions.append({'type': 'notification', 'message': 'Moderation attention needed'})
        
        return actions
    
    async def _execute_obs_action(self, action: Dict[str, Any]) -> None:
        """Execute a specific OBS action."""
        try:
            action_type = action.get('type')
            
            if action_type == 'scene':
                if self.obs_connection:
                    obs = await self.obs_connection.ensure_connected()
                    target_scene = action.get('target', 'Main Scene')
                    await obs.set_scene(target_scene)
                    logger.info(f"Switched to scene: {target_scene}")
                else:
                    logger.info(f"Would switch to scene: {action.get('target', 'Main Scene')}")
            
            elif action_type == 'audio':
                if self.obs_connection:
                    obs = await self.obs_connection.ensure_connected()
                    source = action.get('source', 'Desktop Audio')
                    volume_change = action.get('value', 0)
                    
                    # Get current volume and adjust
                    current = await obs.get_source_volume(source)
                    new_volume = current.get('volume_db', 0) + volume_change
                    await obs.set_source_volume(source, volume_db=new_volume)
                    logger.info(f"Adjusted {source} volume by {volume_change}dB")
                else:
                    logger.info(f"Would adjust {action.get('source', 'Desktop Audio')} volume by {action.get('value', 0)}dB")
            
            elif action_type == 'notification':
                message = action.get('message', 'Chat intelligence alert')
                logger.info(f"Notification: {message}")
                # In a real implementation, this might trigger overlay notifications
            
        except Exception as e:
            logger.error(f"Error executing OBS action {action}: {e}")
    
    # Public API methods
    
    async def analyze_chat(self, context: str = "") -> str:
        """Perform comprehensive chat analysis."""
        return await self.crew.analyze_current_stream(context)
    
    async def quick_sentiment(self) -> str:
        """Get quick sentiment analysis."""
        return await self.crew.quick_sentiment_check()
    
    async def engagement_status(self) -> str:
        """Get current engagement status."""
        return await self.crew.engagement_alert()
    
    async def moderation_status(self) -> str:
        """Get moderation recommendations."""
        return await self.crew.moderation_check()
    
    async def add_chat_channel(self, platform: str, channel: str, **kwargs) -> bool:
        """Add a chat channel to monitor."""
        return await self.chat_service.add_channel(platform, channel, **kwargs)
    
    async def remove_chat_channel(self, platform: str, channel: str) -> bool:
        """Remove a chat channel from monitoring."""
        return await self.chat_service.remove_channel(platform, channel)
    
    def get_chat_stats(self) -> Dict[str, Any]:
        """Get current chat statistics."""
        return self.chat_service.get_stats()
    
    def configure_thresholds(self, **thresholds) -> None:
        """Configure automation thresholds."""
        self.thresholds.update(thresholds)
        logger.info(f"Updated automation thresholds: {self.thresholds}")
    
    def enable_auto_response(self, enabled: bool = True) -> None:
        """Enable or disable automated responses."""
        self.auto_response_enabled = enabled
        logger.info(f"Automated responses {'enabled' if enabled else 'disabled'}")
    
    def set_analysis_interval(self, seconds: float) -> None:
        """Set the interval for automated analysis."""
        self.analysis_interval = max(10.0, seconds)  # Minimum 10 seconds
        logger.info(f"Analysis interval set to {self.analysis_interval} seconds")
    
    async def manual_trigger(self, action_type: str = "comprehensive") -> str:
        """Manually trigger analysis and potential automation."""
        try:
            if action_type == "comprehensive":
                result = await self.analyze_chat("Manual comprehensive analysis requested")
            elif action_type == "sentiment":
                result = await self.quick_sentiment()
            elif action_type == "engagement":
                result = await self.engagement_status()
            elif action_type == "moderation":
                result = await self.moderation_status()
            else:
                return f"Unknown analysis type: {action_type}"
            
            # Check if automated response should be triggered
            if await self._should_trigger_automation(result):
                await self._trigger_automated_response(result)
                return f"Analysis completed and automation triggered:\n\n{result}"
            else:
                return f"Analysis completed (no automation triggered):\n\n{result}"
            
        except Exception as e:
            logger.error(f"Error in manual trigger: {e}")
            return f"Error: {str(e)}"


# Factory function for easy integration setup
async def setup_chat_intelligence(obs_agent=None, event_system=None, llm=None) -> ChatIntelligenceIntegration:
    """
    Set up and start the chat intelligence integration.
    
    Args:
        obs_agent: OBS Agent instance (optional)
        event_system: Event sourcing system (optional)
        llm: Language model for agents (optional)
    
    Returns:
        Started ChatIntelligenceIntegration instance
    """
    integration = ChatIntelligenceIntegration(
        obs_agent=obs_agent,
        event_system=event_system,
        llm=llm
    )
    
    await integration.start()
    return integration