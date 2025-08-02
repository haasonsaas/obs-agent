"""
Chat Intelligence System for OBS Agent.

This module provides AI-powered chat analysis and intelligence capabilities
for streaming platforms, integrated with the CrewAI multi-agent system.

Platform Support:
- Twitch (IRC + EventSub) - Requires OAuth token with chat:read scope
- YouTube Live Chat (API) - Requires API key or OAuth token  
- Discord (Webhooks + Bot API) - Requires bot token and webhooks
"""

import asyncio
import json
import logging
import re
import ssl
import websockets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import quote

import aiohttp
from pydantic import BaseModel, Field

from .config import Config
from .events.domain import DomainEvent, EventType
from .events.store import EventStore
from .types.base import Timestamp, UUID


logger = logging.getLogger(__name__)


# Chat Message Types
@dataclass
class ChatMessage:
    """Represents a chat message from any platform."""
    
    id: str
    platform: str
    user_id: str
    username: str
    display_name: str
    message: str
    timestamp: datetime
    channel: str
    is_moderator: bool = False
    is_subscriber: bool = False
    is_vip: bool = False
    badges: List[str] = None
    emotes: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.badges is None:
            self.badges = []
        if self.emotes is None:
            self.emotes = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ChatAnalysis:
    """Results of chat message analysis."""
    
    message_id: str
    sentiment_score: float  # -1 to 1 (negative to positive)
    emotion: str  # joy, anger, fear, sadness, surprise, neutral
    confidence: float  # 0 to 1
    toxicity_score: float  # 0 to 1 (clean to toxic)
    topics: List[str]
    intent: str  # question, command, praise, complaint, etc.
    urgency: float  # 0 to 1
    engagement_value: float  # predicted impact on stream engagement
    

# Event Types for Chat Intelligence
class ChatMessageReceived(DomainEvent):
    """Event fired when a chat message is received."""
    
    def __init__(self, message: ChatMessage, **kwargs):
        super().__init__(
            aggregate_id=f"chat:{message.platform}:{message.channel}",
            **kwargs
        )
        self.message = message
    
    def _get_event_type(self) -> EventType:
        return EventType.CHAT_MESSAGE_RECEIVED
        
    def get_event_data(self) -> Dict[str, Any]:
        return {
            "message_id": self.message.id,
            "platform": self.message.platform,
            "user_id": self.message.user_id,
            "username": self.message.username,
            "message": self.message.message,
            "timestamp": self.message.timestamp.isoformat(),
            "channel": self.message.channel,
            "is_moderator": self.message.is_moderator,
            "is_subscriber": self.message.is_subscriber,
            "badges": self.message.badges,
        }
    
    @classmethod
    def from_event_data(cls, aggregate_id: str, metadata, data: Dict[str, Any]):
        """Reconstruct event from stored data."""
        from datetime import datetime
        message = ChatMessage(
            id=data["message_id"],
            platform=data["platform"],
            user_id=data["user_id"],
            username=data["username"],
            display_name=data["username"],  # Simplified
            message=data["message"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            channel=data["channel"],
            is_moderator=data["is_moderator"],
            is_subscriber=data["is_subscriber"],
            badges=data["badges"]
        )
        return cls(message=message, aggregate_id=aggregate_id, metadata=metadata)


class ChatAnalysisCompleted(DomainEvent):
    """Event fired when chat analysis is completed."""
    
    def __init__(self, analysis: ChatAnalysis, **kwargs):
        super().__init__(
            aggregate_id=f"chat:analysis:{analysis.message_id}",
            **kwargs
        )
        self.analysis = analysis
    
    def _get_event_type(self) -> EventType:
        return EventType.CHAT_ANALYSIS_COMPLETED
        
    def get_event_data(self) -> Dict[str, Any]:
        return {
            "message_id": self.analysis.message_id,
            "sentiment_score": self.analysis.sentiment_score,
            "emotion": self.analysis.emotion,
            "confidence": self.analysis.confidence,
            "toxicity_score": self.analysis.toxicity_score,
            "topics": self.analysis.topics,
            "intent": self.analysis.intent,
            "urgency": self.analysis.urgency,
            "engagement_value": self.analysis.engagement_value,
        }
    
    @classmethod
    def from_event_data(cls, aggregate_id: str, metadata, data: Dict[str, Any]):
        """Reconstruct event from stored data."""
        # This is a simplified reconstruction - in production you'd want
        # to properly reconstruct the ChatAnalysis object
        analysis = ChatAnalysis(
            message_id=data["message_id"],
            sentiment_score=data["sentiment_score"],
            emotion=data["emotion"],
            confidence=data["confidence"],
            toxicity_score=data["toxicity_score"],
            topics=data["topics"],
            intent=data["intent"],
            urgency=data["urgency"],
            engagement_value=data["engagement_value"]
        )
        return cls(analysis=analysis, aggregate_id=aggregate_id, metadata=metadata)


class EngagementMomentDetected(DomainEvent):
    """Event fired when a significant engagement moment is detected."""
    
    def __init__(self, moment_type: str, intensity: float, context: Dict[str, Any], **kwargs):
        super().__init__(
            aggregate_id="chat:engagement",
            **kwargs
        )
        self.moment_type = moment_type
        self.intensity = intensity
        self.context = context
    
    def _get_event_type(self) -> EventType:
        return EventType.CHAT_ENGAGEMENT_MOMENT
        
    def get_event_data(self) -> Dict[str, Any]:
        return {
            "moment_type": self.moment_type,
            "intensity": self.intensity,
            "context": self.context,
        }
    
    @classmethod
    def from_event_data(cls, aggregate_id: str, metadata, data: Dict[str, Any]):
        """Reconstruct event from stored data."""
        return cls(
            moment_type=data["moment_type"],
            intensity=data["intensity"],
            context=data["context"],
            aggregate_id=aggregate_id,
            metadata=metadata
        )


# Chat Intelligence Engine
class ChatIntelligenceEngine:
    """Core engine for chat analysis and intelligence."""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.message_buffer: List[ChatMessage] = []
        self.analysis_cache: Dict[str, ChatAnalysis] = {}
        self.engagement_history: List[float] = []
        self.running = False
        
        # Simple sentiment keywords (will be replaced with proper NLP)
        self.positive_keywords = {
            'love', 'awesome', 'great', 'amazing', 'fantastic', 'perfect',
            'wonderful', 'brilliant', 'excellent', 'good', 'nice', 'cool',
            'epic', 'poggers', 'pog', 'kappa', 'lol', 'haha', 'funny',
            'thanks', 'thank you', 'appreciate'
        }
        
        self.negative_keywords = {
            'hate', 'terrible', 'awful', 'bad', 'worst', 'stupid', 'dumb',
            'boring', 'sucks', 'crap', 'trash', 'garbage', 'cringe',
            'annoying', 'frustrating', 'disappointed'
        }
        
        self.toxic_keywords = {
            'toxic', 'idiot', 'moron', 'loser', 'noob', 'scrub', 'trash',
            'ez', 'rekt', 'owned', 'destroyed'  # Gaming toxicity
        }
        
        self.question_indicators = {
            'what', 'how', 'why', 'when', 'where', 'who', 'which', 'can you',
            'could you', 'would you', 'do you', 'did you', 'will you', '?'
        }
    
    async def analyze_message(self, message: ChatMessage) -> ChatAnalysis:
        """Analyze a single chat message for sentiment, toxicity, and intent."""
        
        # Simple rule-based analysis (MVP version)
        text = message.message.lower()
        words = set(re.findall(r'\w+', text))
        
        # Sentiment analysis
        positive_count = len(words.intersection(self.positive_keywords))
        negative_count = len(words.intersection(self.negative_keywords))
        
        if positive_count > negative_count:
            sentiment_score = min(1.0, positive_count * 0.3)
            emotion = "joy"
        elif negative_count > positive_count:
            sentiment_score = max(-1.0, -negative_count * 0.3)
            emotion = "anger" if negative_count > 2 else "sadness"
        else:
            sentiment_score = 0.0
            emotion = "neutral"
        
        # Toxicity detection
        toxic_count = len(words.intersection(self.toxic_keywords))
        toxicity_score = min(1.0, toxic_count * 0.4)
        
        # Intent detection
        has_question = any(indicator in text for indicator in self.question_indicators)
        intent = "question" if has_question else "comment"
        
        # Urgency (simple heuristic)
        urgency = 0.8 if message.is_moderator else 0.3
        if '!' in message.message:
            urgency += 0.2
        if message.message.isupper() and len(message.message) > 5:
            urgency += 0.3
        urgency = min(1.0, urgency)
        
        # Engagement value
        engagement_value = 0.5
        if message.is_subscriber:
            engagement_value += 0.2
        if message.is_vip:
            engagement_value += 0.1
        if len(message.message) > 50:  # Longer messages often more engaging
            engagement_value += 0.1
        if has_question:
            engagement_value += 0.2
        engagement_value = min(1.0, engagement_value)
        
        # Simple topic extraction (keywords)
        topics = []
        gaming_terms = {'game', 'play', 'level', 'boss', 'win', 'lose', 'score'}
        streaming_terms = {'stream', 'chat', 'follow', 'subscribe', 'donate'}
        
        if words.intersection(gaming_terms):
            topics.append("gaming")
        if words.intersection(streaming_terms):
            topics.append("streaming")
        if has_question:
            topics.append("question")
        
        analysis = ChatAnalysis(
            message_id=message.id,
            sentiment_score=sentiment_score,
            emotion=emotion,
            confidence=0.7,  # Rule-based confidence
            toxicity_score=toxicity_score,
            topics=topics,
            intent=intent,
            urgency=urgency,
            engagement_value=engagement_value
        )
        
        # Cache analysis
        self.analysis_cache[message.id] = analysis
        
        # Store event
        event = ChatAnalysisCompleted(analysis)
        self.event_store.append(event)
        
        return analysis
    
    async def process_message(self, message: ChatMessage) -> None:
        """Process a new chat message."""
        
        # Store message event
        event = ChatMessageReceived(message)
        self.event_store.append(event)
        
        # Add to buffer
        self.message_buffer.append(message)
        
        # Keep buffer size manageable
        if len(self.message_buffer) > 1000:
            self.message_buffer = self.message_buffer[-500:]
        
        # Analyze message
        analysis = await self.analyze_message(message)
        
        # Update engagement tracking
        self.engagement_history.append(analysis.engagement_value)
        if len(self.engagement_history) > 100:
            self.engagement_history = self.engagement_history[-50:]
        
        # Check for engagement moments
        await self._check_engagement_moments()
        
        logger.info(
            f"Processed message from {message.username}: "
            f"sentiment={analysis.sentiment_score:.2f}, "
            f"engagement={analysis.engagement_value:.2f}"
        )
    
    async def _check_engagement_moments(self) -> None:
        """Check if current chat activity indicates significant engagement moments."""
        
        if len(self.engagement_history) < 10:
            return
        
        recent_engagement = self.engagement_history[-10:]
        avg_engagement = sum(recent_engagement) / len(recent_engagement)
        
        # Detect engagement spike
        if avg_engagement > 0.7:
            event = EngagementMomentDetected(
                moment_type="high_engagement",
                intensity=avg_engagement,
                context={
                    "recent_messages": len(recent_engagement),
                    "average_engagement": avg_engagement,
                    "timestamp": datetime.now().isoformat()
                }
            )
            self.event_store.append(event)
            logger.info(f"High engagement moment detected: {avg_engagement:.2f}")
        
        # Detect engagement drop
        elif avg_engagement < 0.3 and len(self.engagement_history) > 20:
            older_engagement = self.engagement_history[-20:-10]
            old_avg = sum(older_engagement) / len(older_engagement)
            
            if old_avg > 0.5:  # Significant drop
                event = EngagementMomentDetected(
                    moment_type="engagement_drop",
                    intensity=old_avg - avg_engagement,
                    context={
                        "previous_engagement": old_avg,
                        "current_engagement": avg_engagement,
                        "drop_magnitude": old_avg - avg_engagement,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                self.event_store.append(event)
                logger.warning(f"Engagement drop detected: {old_avg:.2f} -> {avg_engagement:.2f}")
    
    def get_engagement_stats(self) -> Dict[str, Any]:
        """Get current engagement statistics."""
        
        if not self.engagement_history:
            return {"average_engagement": 0.0, "message_count": 0}
        
        recent_messages = self.engagement_history[-20:] if len(self.engagement_history) >= 20 else self.engagement_history
        
        return {
            "average_engagement": sum(recent_messages) / len(recent_messages),
            "message_count": len(self.message_buffer),
            "total_analyzed": len(self.analysis_cache),
            "engagement_trend": "increasing" if len(recent_messages) > 10 and 
                              recent_messages[-5:] > recent_messages[-10:-5] else "stable"
        }
    
    def get_recent_analysis(self, count: int = 10) -> List[ChatAnalysis]:
        """Get recent chat analysis results."""
        
        recent_messages = self.message_buffer[-count:]
        analyses = []
        
        for message in recent_messages:
            if message.id in self.analysis_cache:
                analyses.append(self.analysis_cache[message.id])
        
        return analyses


# Platform Configuration
@dataclass
class ChatPlatformConfig:
    """Configuration for chat platform connections."""
    
    # Twitch Config
    twitch_oauth_token: Optional[str] = None  # OAuth token with chat:read scope
    twitch_client_id: Optional[str] = None
    twitch_username: Optional[str] = None
    
    # YouTube Config  
    youtube_api_key: Optional[str] = None
    youtube_oauth_token: Optional[str] = None
    
    # Discord Config
    discord_bot_token: Optional[str] = None
    discord_webhook_urls: List[str] = None
    
    def __post_init__(self):
        if self.discord_webhook_urls is None:
            self.discord_webhook_urls = []


# Twitch Chat Connector (Updated with proper authentication)
class TwitchChatConnector:
    """
    Connects to Twitch chat using IRC with OAuth authentication.
    
    Supports both anonymous and authenticated connections.
    For authenticated access, requires OAuth token with chat:read scope.
    
    Authentication Guide:
    1. Register app at https://dev.twitch.tv/console
    2. Get OAuth token with chat:read scope
    3. Use token in format: oauth:your_token_here
    """
    
    def __init__(self, channel: str, intelligence_engine: ChatIntelligenceEngine, 
                 config: Optional[ChatPlatformConfig] = None):
        self.channel = channel.lower().lstrip('#')
        self.intelligence_engine = intelligence_engine
        self.config = config or ChatPlatformConfig()
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.message_handlers: List[Callable[[ChatMessage], None]] = []
        self.use_ssl = True  # Prefer SSL connection
    
    async def connect(self) -> None:
        """Connect to Twitch IRC with proper authentication."""
        
        try:
            # Choose connection type based on SSL preference
            if self.use_ssl:
                ssl_context = ssl.create_default_context()
                self.reader, self.writer = await asyncio.open_connection(
                    'irc.chat.twitch.tv', 6697, ssl=ssl_context
                )
            else:
                self.reader, self.writer = await asyncio.open_connection(
                    'irc.chat.twitch.tv', 6667
                )
            
            # Authentication
            if self.config.twitch_oauth_token and self.config.twitch_username:
                # Authenticated connection
                oauth_token = self.config.twitch_oauth_token
                if not oauth_token.startswith('oauth:'):
                    oauth_token = f'oauth:{oauth_token}'
                
                self.writer.write(f'PASS {oauth_token}\r\n'.encode())
                self.writer.write(f'NICK {self.config.twitch_username}\r\n'.encode())
                logger.info(f"Connecting to Twitch as authenticated user: {self.config.twitch_username}")
            else:
                # Anonymous connection (read-only)
                self.writer.write(b'PASS SCHMOOPIIE\r\n')
                self.writer.write(b'NICK justinfan12345\r\n')
                logger.info("Connecting to Twitch as anonymous user (read-only)")
            
            await self.writer.drain()
            
            # Request capabilities for better message parsing
            self.writer.write(b'CAP REQ :twitch.tv/tags twitch.tv/commands\r\n')
            await self.writer.drain()
            
            # Join channel
            self.writer.write(f'JOIN #{self.channel}\r\n'.encode())
            await self.writer.drain()
            
            self.connected = True
            logger.info(f"Connected to Twitch chat: #{self.channel}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Twitch: {e}")
            logger.info("Connection troubleshooting:")
            logger.info("1. Check your OAuth token is valid (get from https://twitchapps.com/tmi/)")
            logger.info("2. Ensure token has 'chat:read' scope")
            logger.info("3. Verify username matches the token's account")
            logger.info("4. Check if channel name is correct (without #)")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Twitch IRC."""
        
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        
        self.connected = False
        logger.info("Disconnected from Twitch chat")
    
    def add_message_handler(self, handler: Callable[[ChatMessage], None]) -> None:
        """Add a message handler callback."""
        self.message_handlers.append(handler)
    
    async def listen(self) -> None:
        """Listen for chat messages."""
        
        if not self.connected:
            await self.connect()
        
        try:
            while self.connected and self.reader:
                line = await self.reader.readline()
                if not line:
                    break
                
                await self._process_irc_message(line.decode('utf-8').strip())
                
        except Exception as e:
            logger.error(f"Error in chat listener: {e}")
            self.connected = False
    
    async def _process_irc_message(self, raw_message: str) -> None:
        """Process raw IRC message from Twitch."""
        
        # Handle PING
        if raw_message.startswith('PING'):
            pong = raw_message.replace('PING', 'PONG')
            self.writer.write(f'{pong}\r\n'.encode())
            await self.writer.drain()
            return
        
        # Parse PRIVMSG (chat message)
        if 'PRIVMSG' in raw_message:
            try:
                message = self._parse_twitch_message(raw_message)
                if message:
                    # Process with intelligence engine
                    await self.intelligence_engine.process_message(message)
                    
                    # Call additional handlers
                    for handler in self.message_handlers:
                        try:
                            handler(message)
                        except Exception as e:
                            logger.error(f"Error in message handler: {e}")
                            
            except Exception as e:
                logger.error(f"Error parsing Twitch message: {e}")
    
    def _parse_twitch_message(self, raw_message: str) -> Optional[ChatMessage]:
        """Parse raw Twitch IRC message into ChatMessage."""
        
        # Basic IRC message parsing
        # Format: @badges=... :user!user@user.tmi.twitch.tv PRIVMSG #channel :message
        
        try:
            parts = raw_message.split(' ')
            
            # Extract tags (badges, subscriber info, etc.)
            tags = {}
            if raw_message.startswith('@'):
                tag_part = parts[0][1:]  # Remove @
                for tag in tag_part.split(';'):
                    if '=' in tag:
                        key, value = tag.split('=', 1)
                        tags[key] = value
            
            # Find username
            user_part = None
            for i, part in enumerate(parts):
                if part.startswith(':') and '!' in part:
                    user_part = part[1:]  # Remove :
                    break
            
            if not user_part:
                return None
            
            username = user_part.split('!')[0]
            
            # Find message content
            message_start = raw_message.find(' :', raw_message.find('PRIVMSG'))
            if message_start == -1:
                return None
            
            message_text = raw_message[message_start + 2:]  # Remove ' :'
            
            # Extract user info from tags
            display_name = tags.get('display-name', username)
            user_id = tags.get('user-id', username)
            is_mod = tags.get('mod', '0') == '1'
            is_subscriber = tags.get('subscriber', '0') == '1'
            is_vip = 'vip' in tags.get('badges', '')
            
            badges = []
            if tags.get('badges'):
                badges = [badge.split('/')[0] for badge in tags['badges'].split(',')]
            
            return ChatMessage(
                id=f"twitch_{datetime.now().timestamp()}_{username}",
                platform="twitch",
                user_id=user_id,
                username=username,
                display_name=display_name,
                message=message_text,
                timestamp=datetime.now(),
                channel=self.channel,
                is_moderator=is_mod,
                is_subscriber=is_subscriber,
                is_vip=is_vip,
                badges=badges,
                metadata=tags
            )
            
        except Exception as e:
            logger.error(f"Error parsing Twitch message: {e}")
            return None


# YouTube Live Chat Connector
class YouTubeLiveChatConnector:
    """
    Connects to YouTube Live Chat using the YouTube Data API v3.
    
    Requires API key or OAuth token with appropriate scopes.
    
    Authentication Guide:
    1. Create project at https://console.developers.google.com/
    2. Enable YouTube Data API v3
    3. Get API key or OAuth credentials
    4. Find live chat ID from video ID using videos.list API
    """
    
    def __init__(self, video_id: str, intelligence_engine: ChatIntelligenceEngine,
                 config: Optional[ChatPlatformConfig] = None):
        self.video_id = video_id
        self.intelligence_engine = intelligence_engine
        self.config = config or ChatPlatformConfig()
        self.live_chat_id: Optional[str] = None
        self.connected = False
        self.next_page_token: Optional[str] = None
        self.polling_interval = 5  # seconds
        self.message_handlers: List[Callable[[ChatMessage], None]] = []
    
    async def connect(self) -> None:
        """Connect to YouTube Live Chat."""
        
        if not (self.config.youtube_api_key or self.config.youtube_oauth_token):
            raise ValueError("YouTube API key or OAuth token required")
        
        try:
            # Get live chat ID from video ID
            self.live_chat_id = await self._get_live_chat_id()
            if not self.live_chat_id:
                raise ValueError(f"No active live chat found for video: {self.video_id}")
            
            self.connected = True
            logger.info(f"Connected to YouTube live chat: {self.live_chat_id}")
            
        except Exception as e:
            logger.error(f"Failed to connect to YouTube: {e}")
            logger.info("Connection troubleshooting:")
            logger.info("1. Verify API key or OAuth token is valid")
            logger.info("2. Ensure YouTube Data API v3 is enabled")
            logger.info("3. Check video ID is correct and stream is live")
            logger.info("4. Verify live chat is enabled for the stream")
            raise
    
    async def _get_live_chat_id(self) -> Optional[str]:
        """Get live chat ID from video ID."""
        
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "liveStreamingDetails",
            "id": self.video_id,
        }
        
        if self.config.youtube_api_key:
            params["key"] = self.config.youtube_api_key
        
        headers = {}
        if self.config.youtube_oauth_token:
            headers["Authorization"] = f"Bearer {self.config.youtube_oauth_token}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    if items:
                        live_details = items[0].get("liveStreamingDetails", {})
                        return live_details.get("activeLiveChatId")
                else:
                    logger.error(f"YouTube API error: {response.status}")
                    return None
    
    async def listen(self) -> None:
        """Listen for chat messages by polling."""
        
        if not self.connected:
            await self.connect()
        
        while self.connected:
            try:
                await self._fetch_messages()
                await asyncio.sleep(self.polling_interval)
            except Exception as e:
                logger.error(f"Error in YouTube chat listener: {e}")
                await asyncio.sleep(self.polling_interval * 2)  # Back off on error
    
    async def _fetch_messages(self) -> None:
        """Fetch new chat messages from YouTube API."""
        
        url = "https://www.googleapis.com/youtube/v3/liveChat/messages"
        params = {
            "liveChatId": self.live_chat_id,
            "part": "snippet,authorDetails",
        }
        
        if self.next_page_token:
            params["pageToken"] = self.next_page_token
        
        if self.config.youtube_api_key:
            params["key"] = self.config.youtube_api_key
        
        headers = {}
        if self.config.youtube_oauth_token:
            headers["Authorization"] = f"Bearer {self.config.youtube_oauth_token}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Update polling interval from API
                    self.polling_interval = data.get("pollingIntervalMillis", 5000) / 1000
                    self.next_page_token = data.get("nextPageToken")
                    
                    # Process messages
                    for item in data.get("items", []):
                        message = self._parse_youtube_message(item)
                        if message:
                            await self.intelligence_engine.process_message(message)
                            
                            for handler in self.message_handlers:
                                try:
                                    handler(message)
                                except Exception as e:
                                    logger.error(f"Error in message handler: {e}")
                else:
                    logger.error(f"YouTube API error: {response.status}")
    
    def _parse_youtube_message(self, item: Dict[str, Any]) -> Optional[ChatMessage]:
        """Parse YouTube API message into ChatMessage."""
        
        try:
            snippet = item.get("snippet", {})
            author = item.get("authorDetails", {})
            
            return ChatMessage(
                id=f"youtube_{item.get('id', '')}",
                platform="youtube",
                user_id=author.get("channelId", ""),
                username=author.get("displayName", "Unknown"),
                display_name=author.get("displayName", "Unknown"),
                message=snippet.get("displayMessage", ""),
                timestamp=datetime.fromisoformat(snippet.get("publishedAt", "").replace("Z", "+00:00")),
                channel=self.video_id,
                is_moderator=author.get("isChatModerator", False),
                is_subscriber=author.get("isChatSponsor", False),
                is_vip=author.get("isChatOwner", False),
                badges=[],
                metadata={
                    "messageType": snippet.get("type", "textMessageEvent"),
                    "authorChannelId": author.get("channelId"),
                    "profileImageUrl": author.get("profileImageUrl"),
                }
            )
        except Exception as e:
            logger.error(f"Error parsing YouTube message: {e}")
            return None
    
    async def disconnect(self) -> None:
        """Disconnect from YouTube Live Chat."""
        self.connected = False
        logger.info("Disconnected from YouTube live chat")
    
    def add_message_handler(self, handler: Callable[[ChatMessage], None]) -> None:
        """Add a message handler callback."""
        self.message_handlers.append(handler)


# Discord Chat Connector
class DiscordChatConnector:
    """
    Connects to Discord using bot API for real-time chat monitoring.
    
    Requires Discord bot token with appropriate permissions.
    
    Setup Guide:
    1. Create application at https://discord.com/developers/applications
    2. Create bot and get token
    3. Invite bot to server with Read Messages permission
    4. Use guild/channel IDs to monitor specific channels
    """
    
    def __init__(self, guild_id: str, channel_ids: List[str], 
                 intelligence_engine: ChatIntelligenceEngine,
                 config: Optional[ChatPlatformConfig] = None):
        self.guild_id = guild_id
        self.channel_ids = set(channel_ids)
        self.intelligence_engine = intelligence_engine
        self.config = config or ChatPlatformConfig()
        self.connected = False
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.session_id: Optional[str] = None
        self.sequence: Optional[int] = None
        self.heartbeat_interval: Optional[float] = None
        self.message_handlers: List[Callable[[ChatMessage], None]] = []
    
    async def connect(self) -> None:
        """Connect to Discord Gateway."""
        
        if not self.config.discord_bot_token:
            raise ValueError("Discord bot token required")
        
        try:
            # Connect to Discord Gateway
            gateway_url = await self._get_gateway_url()
            self.websocket = await websockets.connect(f"{gateway_url}?v=10&encoding=json")
            
            self.connected = True
            logger.info(f"Connected to Discord gateway")
            
        except Exception as e:
            logger.error(f"Failed to connect to Discord: {e}")
            logger.info("Connection troubleshooting:")
            logger.info("1. Verify bot token is valid")
            logger.info("2. Ensure bot has Read Messages permission")
            logger.info("3. Check guild and channel IDs are correct")
            logger.info("4. Verify bot is invited to the server")
            raise
    
    async def _get_gateway_url(self) -> str:
        """Get Discord gateway URL."""
        
        headers = {"Authorization": f"Bot {self.config.discord_bot_token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get("https://discord.com/api/v10/gateway/bot", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["url"]
                else:
                    raise Exception(f"Failed to get gateway URL: {response.status}")
    
    async def listen(self) -> None:
        """Listen for Discord messages via Gateway."""
        
        if not self.connected:
            await self.connect()
        
        try:
            await self._authenticate()
            
            async for message in self.websocket:
                await self._handle_gateway_message(json.loads(message))
                
        except Exception as e:
            logger.error(f"Error in Discord listener: {e}")
            self.connected = False
    
    async def _authenticate(self) -> None:
        """Authenticate with Discord Gateway."""
        
        identify_payload = {
            "op": 2,
            "d": {
                "token": self.config.discord_bot_token,
                "intents": 512,  # GUILD_MESSAGES intent
                "properties": {
                    "os": "linux",
                    "browser": "obs-agent",
                    "device": "obs-agent"
                }
            }
        }
        
        await self.websocket.send(json.dumps(identify_payload))
    
    async def _handle_gateway_message(self, payload: Dict[str, Any]) -> None:
        """Handle Discord Gateway message."""
        
        op = payload.get("op")
        data = payload.get("d")
        
        if op == 10:  # Hello
            self.heartbeat_interval = data["heartbeat_interval"] / 1000
            asyncio.create_task(self._heartbeat())
            
        elif op == 0:  # Dispatch
            event_type = payload.get("t")
            self.sequence = payload.get("s")
            
            if event_type == "READY":
                self.session_id = data["session_id"]
                logger.info("Discord bot ready")
                
            elif event_type == "MESSAGE_CREATE":
                await self._process_discord_message(data)
    
    async def _heartbeat(self) -> None:
        """Send heartbeat to Discord Gateway."""
        
        while self.connected and self.websocket:
            await asyncio.sleep(self.heartbeat_interval)
            
            heartbeat_payload = {
                "op": 1,
                "d": self.sequence
            }
            
            try:
                await self.websocket.send(json.dumps(heartbeat_payload))
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break
    
    async def _process_discord_message(self, data: Dict[str, Any]) -> None:
        """Process Discord message."""
        
        # Check if message is from monitored channel
        if data.get("channel_id") not in self.channel_ids:
            return
        
        # Skip bot messages
        if data.get("author", {}).get("bot", False):
            return
        
        message = self._parse_discord_message(data)
        if message:
            await self.intelligence_engine.process_message(message)
            
            for handler in self.message_handlers:
                try:
                    handler(message)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")
    
    def _parse_discord_message(self, data: Dict[str, Any]) -> Optional[ChatMessage]:
        """Parse Discord API message into ChatMessage."""
        
        try:
            author = data.get("author", {})
            member = data.get("member", {})
            
            return ChatMessage(
                id=f"discord_{data.get('id', '')}",
                platform="discord",
                user_id=author.get("id", ""),
                username=author.get("username", "Unknown"),
                display_name=member.get("nick") or author.get("display_name") or author.get("username", "Unknown"),
                message=data.get("content", ""),
                timestamp=datetime.fromisoformat(data.get("timestamp", "").replace("Z", "+00:00")),
                channel=data.get("channel_id", ""),
                is_moderator=False,  # Would need to check permissions
                is_subscriber=False,  # Discord doesn't have direct equivalent
                is_vip=False,  # Would need to check roles
                badges=[],
                metadata={
                    "messageType": data.get("type", 0),
                    "guildId": data.get("guild_id"),
                    "channelId": data.get("channel_id"),
                    "authorId": author.get("id"),
                }
            )
        except Exception as e:
            logger.error(f"Error parsing Discord message: {e}")
            return None
    
    async def disconnect(self) -> None:
        """Disconnect from Discord."""
        
        self.connected = False
        if self.websocket:
            await self.websocket.close()
        
        logger.info("Disconnected from Discord")
    
    def add_message_handler(self, handler: Callable[[ChatMessage], None]) -> None:
        """Add a message handler callback."""
        self.message_handlers.append(handler)


# Main Chat Intelligence Service
class ChatIntelligenceService:
    """Main service for managing chat intelligence across platforms."""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.intelligence_engine = ChatIntelligenceEngine(event_store)
        self.connectors: Dict[str, Any] = {}
        self.running = False
    
    async def add_twitch_channel(self, channel: str, config: Optional[ChatPlatformConfig] = None) -> None:
        """Add a Twitch channel for monitoring."""
        
        connector = TwitchChatConnector(channel, self.intelligence_engine, config)
        self.connectors[f"twitch:{channel}"] = connector
        
        logger.info(f"Added Twitch channel: {channel}")
    
    async def add_youtube_stream(self, video_id: str, config: Optional[ChatPlatformConfig] = None) -> None:
        """Add a YouTube live stream for monitoring."""
        
        connector = YouTubeLiveChatConnector(video_id, self.intelligence_engine, config)
        self.connectors[f"youtube:{video_id}"] = connector
        
        logger.info(f"Added YouTube stream: {video_id}")
    
    async def add_discord_channels(self, guild_id: str, channel_ids: List[str], 
                                  config: Optional[ChatPlatformConfig] = None) -> None:
        """Add Discord channels for monitoring."""
        
        connector = DiscordChatConnector(guild_id, channel_ids, self.intelligence_engine, config)
        self.connectors[f"discord:{guild_id}"] = connector
        
        logger.info(f"Added Discord guild {guild_id} with {len(channel_ids)} channels")
    
    async def start(self) -> None:
        """Start the chat intelligence service."""
        
        self.running = True
        tasks = []
        
        # Start all connectors
        for connector_id, connector in self.connectors.items():
            if hasattr(connector, 'listen'):
                task = asyncio.create_task(connector.listen())
                tasks.append(task)
                logger.info(f"Started connector: {connector_id}")
        
        # Wait for all connectors
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self) -> None:
        """Stop the chat intelligence service."""
        
        self.running = False
        
        # Disconnect all connectors
        for connector in self.connectors.values():
            if hasattr(connector, 'disconnect'):
                await connector.disconnect()
        
        logger.info("Chat intelligence service stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        
        stats = self.intelligence_engine.get_engagement_stats()
        stats.update({
            "active_connectors": len(self.connectors),
            "service_running": self.running,
        })
        
        return stats
    
    def get_recent_analysis(self, count: int = 10) -> List[ChatAnalysis]:
        """Get recent chat analysis results."""
        return self.intelligence_engine.get_recent_analysis(count)