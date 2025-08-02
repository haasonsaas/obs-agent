"""
CrewAI Tools for Chat Intelligence.

This module provides specialized tools for CrewAI agents to interact with
the chat intelligence system and extract actionable insights.
"""

import logging
from typing import Any, Dict, List, Optional, Type

from crewai_tools import BaseTool
from pydantic import BaseModel, Field

from ..obs_agent.chat_intelligence import ChatIntelligenceService, ChatAnalysis, ChatMessage


logger = logging.getLogger(__name__)


class ChatAnalysisInput(BaseModel):
    """Input for chat analysis tool."""
    
    time_window_minutes: int = Field(
        default=5,
        description="Time window in minutes to analyze chat (1-30)"
    )
    min_engagement_threshold: float = Field(
        default=0.5,
        description="Minimum engagement threshold to filter messages (0.0-1.0)"
    )


class ChatSentimentInput(BaseModel):
    """Input for chat sentiment analysis tool."""
    
    message_count: int = Field(
        default=20,
        description="Number of recent messages to analyze (5-100)"
    )


class EngagementTrendInput(BaseModel):
    """Input for engagement trend analysis tool."""
    
    analysis_period_minutes: int = Field(
        default=10,
        description="Period in minutes to analyze for trends (5-60)"
    )


class ChatModerationInput(BaseModel):
    """Input for chat moderation recommendations."""
    
    toxicity_threshold: float = Field(
        default=0.3,
        description="Toxicity threshold for flagging messages (0.0-1.0)"
    )
    check_recent_count: int = Field(
        default=50,
        description="Number of recent messages to check (10-200)"
    )


class ChatAnalysisTool(BaseTool):
    """Tool for analyzing chat messages and extracting insights."""
    
    name: str = "Chat Analysis Tool"
    description: str = """
    Analyzes recent chat messages to extract sentiment, engagement patterns,
    and actionable insights for stream optimization.
    
    Use this tool to:
    - Understand current audience mood and sentiment
    - Identify engagement peaks and drops
    - Extract trending topics and themes
    - Get recommendations for content adjustments
    """
    args_schema: Type[BaseModel] = ChatAnalysisInput
    
    def __init__(self, chat_service: ChatIntelligenceService):
        super().__init__()
        self.chat_service = chat_service
    
    def _run(self, time_window_minutes: int = 5, min_engagement_threshold: float = 0.5) -> str:
        """Analyze recent chat messages for insights."""
        
        try:
            # Get recent analysis
            recent_analyses = self.chat_service.get_recent_analysis(count=100)
            
            if not recent_analyses:
                return "No recent chat activity to analyze. Chat intelligence system may not be active."
            
            # Filter by engagement threshold
            high_engagement_messages = [
                analysis for analysis in recent_analyses 
                if analysis.engagement_value >= min_engagement_threshold
            ]
            
            # Calculate metrics
            total_messages = len(recent_analyses)
            avg_sentiment = sum(a.sentiment_score for a in recent_analyses) / len(recent_analyses)
            avg_engagement = sum(a.engagement_value for a in recent_analyses) / len(recent_analyses)
            avg_toxicity = sum(a.toxicity_score for a in recent_analyses) / len(recent_analyses)
            
            # Extract emotions
            emotions = [a.emotion for a in recent_analyses]
            emotion_counts = {}
            for emotion in emotions:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutral"
            
            # Extract topics
            all_topics = []
            for analysis in recent_analyses:
                all_topics.extend(analysis.topics)
            
            topic_counts = {}
            for topic in all_topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            trending_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Generate insights
            insights = []
            
            if avg_sentiment > 0.3:
                insights.append("Audience is in a positive mood - great time for engaging content!")
            elif avg_sentiment < -0.3:
                insights.append("Audience sentiment is negative - consider switching topics or adding humor.")
            
            if avg_engagement > 0.7:
                insights.append("High engagement detected - audience is very active and interested!")
            elif avg_engagement < 0.3:
                insights.append("Low engagement - consider interactive content or Q&A to boost participation.")
            
            if avg_toxicity > 0.5:
                insights.append("Elevated toxicity levels detected - moderation attention recommended.")
            
            if len(high_engagement_messages) > total_messages * 0.6:
                insights.append("Strong engagement across most messages - audience is highly invested.")
            
            # Content recommendations
            recommendations = []
            
            if "question" in [analysis.intent for analysis in recent_analyses]:
                recommendations.append("Audience has questions - consider dedicating time to Q&A.")
            
            if "gaming" in dict(trending_topics):
                recommendations.append("Gaming discussion is trending - lean into game-related content.")
            
            if avg_engagement < 0.4:
                recommendations.append("Consider switching scenes, adding interaction, or changing topics.")
            
            return f"""Chat Analysis Results ({time_window_minutes} min window):

📊 METRICS:
- Total Messages: {total_messages}
- Average Sentiment: {avg_sentiment:.2f} (-1 to 1)
- Average Engagement: {avg_engagement:.2f} (0 to 1)  
- Toxicity Level: {avg_toxicity:.2f} (0 to 1)
- Dominant Emotion: {dominant_emotion}

🔥 TRENDING TOPICS:
{chr(10).join([f"- {topic}: {count} mentions" for topic, count in trending_topics[:3]])}

💡 INSIGHTS:
{chr(10).join([f"- {insight}" for insight in insights])}

🎯 RECOMMENDATIONS:
{chr(10).join([f"- {rec}" for rec in recommendations])}

High Engagement Messages: {len(high_engagement_messages)}/{total_messages} ({len(high_engagement_messages)/total_messages*100:.1f}%)"""
            
        except Exception as e:
            logger.error(f"Error in chat analysis tool: {e}")
            return f"Error analyzing chat: {str(e)}"


class ChatSentimentTool(BaseTool):
    """Tool for real-time sentiment analysis of chat."""
    
    name: str = "Chat Sentiment Analysis Tool"
    description: str = """
    Analyzes sentiment and emotional tone of recent chat messages.
    
    Use this tool to:
    - Get current audience mood and emotional state
    - Track sentiment changes over time
    - Identify when to adjust content tone
    - Detect audience reactions to content
    """
    args_schema: Type[BaseModel] = ChatSentimentInput
    
    def __init__(self, chat_service: ChatIntelligenceService):
        super().__init__()
        self.chat_service = chat_service
    
    def _run(self, message_count: int = 20) -> str:
        """Analyze sentiment of recent messages."""
        
        try:
            recent_analyses = self.chat_service.get_recent_analysis(count=message_count)
            
            if not recent_analyses:
                return "No recent messages to analyze for sentiment."
            
            # Calculate sentiment distribution
            sentiments = [a.sentiment_score for a in recent_analyses]
            emotions = [a.emotion for a in recent_analyses]
            
            positive_count = len([s for s in sentiments if s > 0.1])
            negative_count = len([s for s in sentiments if s < -0.1])
            neutral_count = len(sentiments) - positive_count - negative_count
            
            avg_sentiment = sum(sentiments) / len(sentiments)
            
            # Emotion breakdown
            emotion_counts = {}
            for emotion in emotions:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            # Sentiment trend (compare recent vs older)
            if len(recent_analyses) >= 10:
                recent_sentiment = sum(sentiments[-5:]) / 5
                older_sentiment = sum(sentiments[-10:-5]) / 5
                trend = "improving" if recent_sentiment > older_sentiment + 0.1 else "declining" if recent_sentiment < older_sentiment - 0.1 else "stable"
            else:
                trend = "stable"
            
            return f"""Sentiment Analysis ({message_count} messages):

📈 OVERALL SENTIMENT: {avg_sentiment:.2f}
- Positive: {positive_count} messages ({positive_count/len(sentiments)*100:.1f}%)
- Neutral: {neutral_count} messages ({neutral_count/len(sentiments)*100:.1f}%)
- Negative: {negative_count} messages ({negative_count/len(sentiments)*100:.1f}%)

😊 EMOTION BREAKDOWN:
{chr(10).join([f"- {emotion.title()}: {count}" for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)])}

📊 TREND: {trend.title()}

💭 INTERPRETATION:
{self._interpret_sentiment(avg_sentiment, trend, emotion_counts)}"""
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis tool: {e}")
            return f"Error analyzing sentiment: {str(e)}"
    
    def _interpret_sentiment(self, avg_sentiment: float, trend: str, emotions: Dict[str, int]) -> str:
        """Interpret sentiment results."""
        
        if avg_sentiment > 0.5:
            base = "Audience is very positive and engaged!"
        elif avg_sentiment > 0.1:
            base = "Audience mood is generally positive."
        elif avg_sentiment > -0.1:
            base = "Audience sentiment is neutral."
        elif avg_sentiment > -0.5:
            base = "Audience sentiment is somewhat negative."
        else:
            base = "Audience sentiment is very negative - immediate attention needed."
        
        if trend == "improving":
            trend_text = " Sentiment is improving - keep up current approach!"
        elif trend == "declining":
            trend_text = " Sentiment is declining - consider content adjustment."
        else:
            trend_text = " Sentiment is stable."
        
        return base + trend_text


class EngagementTrendTool(BaseTool):
    """Tool for analyzing engagement trends and patterns."""
    
    name: str = "Engagement Trend Analysis Tool"
    description: str = """
    Analyzes engagement trends and predicts audience behavior.
    
    Use this tool to:
    - Track engagement momentum over time
    - Predict when audience attention may drop
    - Identify optimal times for key content
    - Detect engagement patterns and cycles
    """
    args_schema: Type[BaseModel] = EngagementTrendInput
    
    def __init__(self, chat_service: ChatIntelligenceService):
        super().__init__()
        self.chat_service = chat_service
    
    def _run(self, analysis_period_minutes: int = 10) -> str:
        """Analyze engagement trends."""
        
        try:
            stats = self.chat_service.get_stats()
            recent_analyses = self.chat_service.get_recent_analysis(count=100)
            
            if not recent_analyses:
                return "No engagement data available for trend analysis."
            
            # Calculate engagement metrics
            engagement_values = [a.engagement_value for a in recent_analyses]
            avg_engagement = sum(engagement_values) / len(engagement_values)
            
            # Trend calculation
            if len(engagement_values) >= 20:
                recent_avg = sum(engagement_values[-10:]) / 10
                older_avg = sum(engagement_values[-20:-10]) / 10
                trend_direction = recent_avg - older_avg
            else:
                trend_direction = 0
                recent_avg = avg_engagement
            
            # Engagement level classification
            if avg_engagement > 0.7:
                level = "Very High"
                color = "🔥"
            elif avg_engagement > 0.5:
                level = "High"
                color = "⚡"
            elif avg_engagement > 0.3:
                level = "Moderate"
                color = "📊"
            else:
                level = "Low"
                color = "⚠️"
            
            # Trend description
            if trend_direction > 0.1:
                trend_desc = "Strong Upward Trend 📈"
            elif trend_direction > 0.05:
                trend_desc = "Slight Upward Trend ↗️"
            elif trend_direction < -0.1:
                trend_desc = "Strong Downward Trend 📉"
            elif trend_direction < -0.05:
                trend_desc = "Slight Downward Trend ↘️"
            else:
                trend_desc = "Stable ➡️"
            
            # Predictions and recommendations
            predictions = []
            recommendations = []
            
            if trend_direction < -0.1:
                predictions.append("Engagement may continue declining without intervention")
                recommendations.append("Consider switching content or adding interactive elements")
            elif avg_engagement < 0.3:
                predictions.append("Low engagement suggests audience disinterest")
                recommendations.append("Try Q&A, polls, or more dynamic content")
            elif avg_engagement > 0.7 and trend_direction > 0:
                predictions.append("Excellent engagement momentum - audience is highly invested")
                recommendations.append("Continue current approach, consider extending this segment")
            
            if len(recent_analyses) > 50:
                # Pattern detection
                high_engagement_msgs = [a for a in recent_analyses if a.engagement_value > 0.6]
                if len(high_engagement_msgs) > len(recent_analyses) * 0.3:
                    predictions.append("Sustained high-quality engagement pattern detected")
            
            return f"""Engagement Trend Analysis ({analysis_period_minutes} min):

{color} CURRENT LEVEL: {level} ({avg_engagement:.2f}/1.0)
📊 TREND: {trend_desc}
📈 RECENT AVERAGE: {recent_avg:.2f}

🔮 PREDICTIONS:
{chr(10).join([f"- {pred}" for pred in predictions]) if predictions else "- Engagement pattern is stable"}

🎯 RECOMMENDATIONS:
{chr(10).join([f"- {rec}" for rec in recommendations]) if recommendations else "- Continue current approach"}

📋 STATS:
- Total Messages Analyzed: {len(recent_analyses)}
- Message Rate: {stats.get('message_count', 0)} total messages
- Service Status: {'Active' if stats.get('service_running') else 'Inactive'}"""
            
        except Exception as e:
            logger.error(f"Error in engagement trend tool: {e}")
            return f"Error analyzing engagement trends: {str(e)}"


class ChatModerationTool(BaseTool):
    """Tool for chat moderation insights and recommendations."""
    
    name: str = "Chat Moderation Tool"
    description: str = """
    Analyzes chat for moderation needs and provides recommendations.
    
    Use this tool to:
    - Detect toxic or inappropriate messages
    - Identify users who may need attention
    - Get moderation action recommendations
    - Monitor chat health and safety
    """
    args_schema: Type[BaseModel] = ChatModerationInput
    
    def __init__(self, chat_service: ChatIntelligenceService):
        super().__init__()
        self.chat_service = chat_service
    
    def _run(self, toxicity_threshold: float = 0.3, check_recent_count: int = 50) -> str:
        """Analyze chat for moderation needs."""
        
        try:
            recent_analyses = self.chat_service.get_recent_analysis(count=check_recent_count)
            
            if not recent_analyses:
                return "No recent messages to analyze for moderation."
            
            # Toxicity analysis
            toxic_messages = [a for a in recent_analyses if a.toxicity_score >= toxicity_threshold]
            avg_toxicity = sum(a.toxicity_score for a in recent_analyses) / len(recent_analyses)
            
            # High urgency messages
            urgent_messages = [a for a in recent_analyses if a.urgency > 0.7]
            
            # Generate moderation status
            if avg_toxicity > 0.5:
                status = "⚠️ HIGH RISK"
                status_desc = "Elevated toxicity levels - active moderation recommended"
            elif avg_toxicity > 0.3:
                status = "⚡ MODERATE RISK"
                status_desc = "Some toxic content detected - monitor closely"
            elif len(toxic_messages) > 0:
                status = "👀 LOW RISK"
                status_desc = "Minimal toxic content - standard monitoring"
            else:
                status = "✅ HEALTHY"
                status_desc = "Clean chat environment"
            
            # Recommendations
            recommendations = []
            
            if len(toxic_messages) > check_recent_count * 0.1:
                recommendations.append("Consider enabling stricter moderation filters")
                
            if len(urgent_messages) > 5:
                recommendations.append("Multiple urgent messages detected - review for important issues")
            
            if avg_toxicity > 0.4:
                recommendations.append("Consider timeout or warnings for repeat offenders")
                recommendations.append("Review chat rules and community guidelines")
            
            # Action items
            actions = []
            if len(toxic_messages) > 0:
                actions.append(f"Review {len(toxic_messages)} flagged messages")
            
            if len(urgent_messages) > 0:
                actions.append(f"Address {len(urgent_messages)} urgent messages")
            
            return f"""Chat Moderation Analysis ({check_recent_count} messages):

🛡️ STATUS: {status}
{status_desc}

📊 METRICS:
- Average Toxicity: {avg_toxicity:.2f}/1.0
- Flagged Messages: {len(toxic_messages)} ({len(toxic_messages)/len(recent_analyses)*100:.1f}%)
- Urgent Messages: {len(urgent_messages)}
- Threshold Used: {toxicity_threshold}

⚡ IMMEDIATE ACTIONS:
{chr(10).join([f"- {action}" for action in actions]) if actions else "- No immediate actions required"}

🎯 RECOMMENDATIONS:
{chr(10).join([f"- {rec}" for rec in recommendations]) if recommendations else "- Continue current moderation approach"}

💡 INSIGHTS:
{self._get_moderation_insights(avg_toxicity, len(toxic_messages), len(recent_analyses))}"""
            
        except Exception as e:
            logger.error(f"Error in moderation tool: {e}")
            return f"Error analyzing moderation needs: {str(e)}"
    
    def _get_moderation_insights(self, avg_toxicity: float, toxic_count: int, total_count: int) -> str:
        """Generate insights for moderation."""
        
        toxic_percentage = (toxic_count / total_count) * 100 if total_count > 0 else 0
        
        if toxic_percentage > 20:
            return "High percentage of toxic messages suggests need for stronger community guidelines"
        elif toxic_percentage > 10:
            return "Moderate toxicity levels - consider reviewing moderation settings"
        elif toxic_percentage > 5:
            return "Low but present toxicity - maintain current vigilance"
        else:
            return "Excellent chat health - community guidelines are effective"


class TopicExtractionTool(BaseTool):
    """Tool for extracting trending topics and themes from chat."""
    
    name: str = "Topic Extraction Tool"
    description: str = """
    Extracts trending topics and conversation themes from chat.
    
    Use this tool to:
    - Identify what audience is discussing
    - Find trending topics and themes
    - Understand audience interests
    - Get content suggestions based on chat topics
    """
    
    def __init__(self, chat_service: ChatIntelligenceService):
        super().__init__()
        self.chat_service = chat_service
        self.args_schema = BaseModel
    
    def _run(self) -> str:
        """Extract trending topics from recent chat."""
        
        try:
            recent_analyses = self.chat_service.get_recent_analysis(count=100)
            
            if not recent_analyses:
                return "No recent messages to analyze for topics."
            
            # Extract all topics
            all_topics = []
            for analysis in recent_analyses:
                all_topics.extend(analysis.topics)
            
            # Count topic frequency
            topic_counts = {}
            for topic in all_topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            # Sort by frequency
            trending_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Extract intents
            intents = [a.intent for a in recent_analyses]
            intent_counts = {}
            for intent in intents:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            # Generate content suggestions
            suggestions = []
            
            if topic_counts.get("question", 0) > 5:
                suggestions.append("High number of questions - consider dedicated Q&A time")
            
            if topic_counts.get("gaming", 0) > topic_counts.get("streaming", 0):
                suggestions.append("Gaming discussion is dominant - focus on game-related content")
            
            if "comment" in intent_counts and intent_counts["comment"] > len(intents) * 0.7:
                suggestions.append("Audience is primarily commenting - good engagement for current content")
            
            return f"""Topic Analysis (100 recent messages):

🔥 TRENDING TOPICS:
{chr(10).join([f"- {topic.title()}: {count} mentions" for topic, count in trending_topics[:8]]) if trending_topics else "- No specific topics identified"}

💬 CONVERSATION TYPES:
{chr(10).join([f"- {intent.title()}: {count} messages" for intent, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)])}

🎯 CONTENT SUGGESTIONS:
{chr(10).join([f"- {suggestion}" for suggestion in suggestions]) if suggestions else "- Continue with current content approach"}

📊 INSIGHTS:
- Total Unique Topics: {len(topic_counts)}
- Most Active Topic: {trending_topics[0][0].title() if trending_topics else 'None'}
- Topic Diversity: {'High' if len(topic_counts) > 5 else 'Moderate' if len(topic_counts) > 2 else 'Low'}"""
            
        except Exception as e:
            logger.error(f"Error in topic extraction tool: {e}")
            return f"Error extracting topics: {str(e)}"