"""
CrewAI Agents for Chat Intelligence System.

This module defines specialized AI agents that collaborate to provide
intelligent chat analysis and streaming optimization.
"""

import logging
from typing import List, Optional

from crewai import Agent, Crew, Process, Task
from langchain.llms.base import BaseLLM

from .chat_intelligence_tools import (
    ChatAnalysisTool,
    ChatModerationTool,
    ChatSentimentTool,
    EngagementTrendTool,
    TopicExtractionTool,
)
from ..obs_agent.chat_intelligence import ChatIntelligenceService

logger = logging.getLogger(__name__)


class ChatIntelligenceAgents:
    """
    Factory for creating and managing chat intelligence agents.
    
    This class provides the core agents that collaborate to analyze
    chat streams and provide actionable insights for streamers.
    """
    
    def __init__(self, chat_service: ChatIntelligenceService, llm: Optional[BaseLLM] = None):
        self.chat_service = chat_service
        self.llm = llm
        
        # Initialize tools
        self.chat_analysis_tool = ChatAnalysisTool(chat_service)
        self.sentiment_tool = ChatSentimentTool(chat_service)
        self.engagement_tool = EngagementTrendTool(chat_service)
        self.moderation_tool = ChatModerationTool(chat_service)
        self.topic_tool = TopicExtractionTool(chat_service)
    
    def create_chat_intelligence_agent(self) -> Agent:
        """
        Create the Chat Intelligence Analyst agent.
        
        This agent specializes in extracting actionable insights from
        real-time chat streams and understanding community dynamics.
        """
        return Agent(
            role="Chat Intelligence Analyst",
            goal="Extract actionable insights from real-time chat streams to optimize streaming content and engagement",
            backstory="""You are an expert at understanding online communities and extracting 
            meaningful patterns from chat interactions. You have deep knowledge of streaming 
            culture, viewer psychology, and engagement patterns. You excel at identifying 
            trends, sentiment shifts, and community dynamics that can help streamers 
            improve their content and build stronger relationships with their audience.""",
            
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            
            tools=[
                self.chat_analysis_tool,
                self.sentiment_tool,
                self.topic_tool,
            ]
        )
    
    def create_engagement_oracle_agent(self) -> Agent:
        """
        Create the Engagement Prediction Specialist agent.
        
        This agent predicts and optimizes viewer engagement in real-time,
        suggesting proactive interventions to maintain audience interest.
        """
        return Agent(
            role="Engagement Prediction Specialist",
            goal="Predict and optimize viewer engagement in real-time to prevent attention drops and maximize audience retention",
            backstory="""You are a master of viewer psychology and engagement patterns. 
            You understand the subtle signals that indicate when audience attention is 
            waning and can predict engagement drops before they happen. Your expertise 
            lies in suggesting proactive content adjustments, timing interactions perfectly, 
            and maintaining the delicate balance of entertainment that keeps viewers 
            engaged throughout a stream.""",
            
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            
            tools=[
                self.engagement_tool,
                self.chat_analysis_tool,
                self.sentiment_tool,
            ]
        )
    
    def create_community_manager_agent(self) -> Agent:
        """
        Create the Intelligent Community Manager agent.
        
        This agent builds and nurtures healthy streaming communities
        while managing disruptive behavior and fostering positive interactions.
        """
        return Agent(
            role="Intelligent Community Manager",
            goal="Build and nurture healthy streaming communities while maintaining positive chat environment and managing conflicts",
            backstory="""You are an experienced community manager who excels at identifying 
            community dynamics and fostering positive interactions. You have a keen eye 
            for spotting potential troublemakers before they disrupt the community, and 
            you know how to guide conversations in positive directions. Your approach 
            combines empathy with firm moderation, always working to build inclusive 
            and welcoming spaces for all viewers.""",
            
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            
            tools=[
                self.moderation_tool,
                self.sentiment_tool,
                self.topic_tool,
                self.chat_analysis_tool,
            ]
        )


class ChatIntelligenceCrew:
    """
    Coordinated crew of agents working together for chat intelligence.
    
    This crew orchestrates the collaboration between agents to provide
    comprehensive chat analysis and streaming optimization.
    """
    
    def __init__(self, chat_service: ChatIntelligenceService, llm: Optional[BaseLLM] = None):
        self.chat_service = chat_service
        self.agents_factory = ChatIntelligenceAgents(chat_service, llm)
        
        # Create agents
        self.chat_analyst = self.agents_factory.create_chat_intelligence_agent()
        self.engagement_oracle = self.agents_factory.create_engagement_oracle_agent()
        self.community_manager = self.agents_factory.create_community_manager_agent()
    
    def create_analysis_task(self, context: str = "") -> Task:
        """Create a task for comprehensive chat analysis."""
        return Task(
            description=f"""
            Analyze the current chat environment and provide comprehensive insights.
            
            Context: {context}
            
            Your analysis should include:
            1. Current sentiment and emotional tone of the chat
            2. Engagement levels and trends
            3. Key topics and themes being discussed
            4. Notable patterns or changes in community behavior
            5. Specific recommendations for content optimization
            
            Focus on actionable insights that can help improve the streaming experience.
            """,
            agent=self.chat_analyst,
            expected_output="Detailed chat analysis with sentiment metrics, engagement insights, and actionable recommendations"
        )
    
    def create_engagement_optimization_task(self, context: str = "") -> Task:
        """Create a task for engagement prediction and optimization."""
        return Task(
            description=f"""
            Analyze engagement patterns and predict potential attention drops.
            
            Context: {context}
            
            Your analysis should focus on:
            1. Current engagement momentum and trends
            2. Prediction of potential engagement drops
            3. Optimal timing for interactive content
            4. Recommendations for maintaining audience interest
            5. Suggestions for content transitions and scene changes
            
            Provide proactive recommendations to prevent engagement decline.
            """,
            agent=self.engagement_oracle,
            expected_output="Engagement analysis with trend predictions and proactive optimization recommendations"
        )
    
    def create_community_health_task(self, context: str = "") -> Task:
        """Create a task for community health monitoring and moderation."""
        return Task(
            description=f"""
            Monitor community health and provide moderation recommendations.
            
            Context: {context}
            
            Your assessment should cover:
            1. Overall chat environment health and safety
            2. Detection of toxic or problematic behavior
            3. Community sentiment and mood assessment
            4. Moderation action recommendations
            5. Strategies for fostering positive interactions
            
            Focus on maintaining a welcoming and inclusive community environment.
            """,
            agent=self.community_manager,
            expected_output="Community health assessment with moderation recommendations and positive engagement strategies"
        )
    
    def create_comprehensive_crew(self, context: str = "") -> Crew:
        """
        Create a crew for comprehensive chat intelligence analysis.
        
        This crew coordinates all three agents to provide complete
        chat analysis, engagement optimization, and community management.
        """
        
        # Create tasks
        analysis_task = self.create_analysis_task(context)
        engagement_task = self.create_engagement_optimization_task(context)
        community_task = self.create_community_health_task(context)
        
        # Create synthesis task that combines all insights
        synthesis_task = Task(
            description="""
            Synthesize insights from chat analysis, engagement optimization, and community management
            to provide comprehensive streaming optimization recommendations.
            
            Create a unified report that includes:
            1. Executive summary of current stream state
            2. Priority recommendations ranked by impact
            3. Immediate actions that should be taken
            4. Medium-term strategies for improvement
            5. Key metrics to monitor going forward
            
            The output should be actionable and prioritized for maximum streaming success.
            """,
            agent=self.chat_analyst,  # Lead analyst synthesizes the findings
            expected_output="Comprehensive streaming optimization report with prioritized recommendations and action items",
            context=[analysis_task, engagement_task, community_task]
        )
        
        return Crew(
            agents=[self.chat_analyst, self.engagement_oracle, self.community_manager],
            tasks=[analysis_task, engagement_task, community_task, synthesis_task],
            process=Process.sequential,
            verbose=True
        )
    
    async def analyze_current_stream(self, context: str = "") -> str:
        """
        Perform comprehensive analysis of current stream state.
        
        This is the main entry point for getting chat intelligence insights.
        """
        try:
            # Create and execute crew
            crew = self.create_comprehensive_crew(context)
            result = crew.kickoff()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in chat intelligence analysis: {e}")
            return f"Error performing chat analysis: {str(e)}"
    
    async def quick_sentiment_check(self) -> str:
        """Perform a quick sentiment analysis of current chat."""
        try:
            task = Task(
                description="Provide a quick sentiment analysis of the current chat environment",
                agent=self.chat_analyst,
                expected_output="Brief sentiment summary with key insights"
            )
            
            crew = Crew(
                agents=[self.chat_analyst],
                tasks=[task],
                process=Process.sequential,
                verbose=False
            )
            
            return crew.kickoff()
            
        except Exception as e:
            logger.error(f"Error in quick sentiment check: {e}")
            return f"Error: {str(e)}"
    
    async def engagement_alert(self) -> str:
        """Get immediate engagement status and alerts."""
        try:
            task = Task(
                description="Assess current engagement levels and provide immediate alerts if action is needed",
                agent=self.engagement_oracle,
                expected_output="Engagement status with immediate action recommendations if needed"
            )
            
            crew = Crew(
                agents=[self.engagement_oracle],
                tasks=[task],
                process=Process.sequential,
                verbose=False
            )
            
            return crew.kickoff()
            
        except Exception as e:
            logger.error(f"Error in engagement alert: {e}")
            return f"Error: {str(e)}"
    
    async def moderation_check(self) -> str:
        """Perform community health and moderation check."""
        try:
            task = Task(
                description="Check community health and provide moderation recommendations",
                agent=self.community_manager,
                expected_output="Community health status with moderation actions if needed"
            )
            
            crew = Crew(
                agents=[self.community_manager],
                tasks=[task],
                process=Process.sequential,
                verbose=False
            )
            
            return crew.kickoff()
            
        except Exception as e:
            logger.error(f"Error in moderation check: {e}")
            return f"Error: {str(e)}"


# Factory function for easy instantiation
def create_chat_intelligence_crew(chat_service: ChatIntelligenceService, llm: Optional[BaseLLM] = None) -> ChatIntelligenceCrew:
    """
    Factory function to create a chat intelligence crew.
    
    Args:
        chat_service: The chat intelligence service to use
        llm: Optional language model to use for agents
        
    Returns:
        Configured ChatIntelligenceCrew ready for use
    """
    return ChatIntelligenceCrew(chat_service, llm)