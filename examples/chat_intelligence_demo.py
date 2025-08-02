"""
Chat Intelligence System Demo

This example demonstrates how to use the Chat Intelligence system
with OBS Agent for automated streaming optimization.
"""

import asyncio
import logging
import os
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the src directory to Python path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from crew.chat_intelligence_integration import setup_chat_intelligence
    from obs_agent.chat_intelligence import ChatIntelligenceService
    from obs_agent.advanced_features import AdvancedOBSAgent
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Make sure you're running from the correct directory and all dependencies are installed")
    sys.exit(1)


class ChatIntelligenceDemo:
    """Demonstration of the Chat Intelligence system."""
    
    def __init__(self):
        self.obs_agent = None
        self.chat_integration = None
    
    async def setup_obs_connection(self):
        """Set up OBS connection (optional for demo)."""
        try:
            # Try to connect to OBS (will fail gracefully if OBS not running)
            self.obs_agent = AdvancedOBSAgent(
                host=os.getenv('OBS_HOST', 'localhost'),
                port=int(os.getenv('OBS_PORT', '4455')),
                password=os.getenv('OBS_PASSWORD', '')
            )
            
            await self.obs_agent.connect()
            logger.info("✅ Connected to OBS Studio")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Could not connect to OBS: {e}")
            logger.info("Demo will continue without OBS integration")
            self.obs_agent = None
            return False
    
    async def setup_chat_intelligence(self):
        """Set up the chat intelligence system."""
        try:
            # Initialize chat intelligence integration
            self.chat_integration = await setup_chat_intelligence(
                obs_agent=self.obs_agent,
                event_system=None,  # Could integrate with event sourcing here
                llm=None  # Could use custom LLM here
            )
            
            logger.info("✅ Chat Intelligence system initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup chat intelligence: {e}")
            return False
    
    async def demonstrate_chat_analysis(self):
        """Demonstrate chat analysis capabilities."""
        logger.info("\n🔍 Demonstrating Chat Analysis...")
        
        # Add some mock chat channels (in real usage, these would be real channels)
        demo_channels = [
            ('twitch', 'demo_channel'),
            ('youtube', 'demo_stream_id'),
            ('discord', 'demo_guild_id/demo_channel_id')
        ]
        
        for platform, channel in demo_channels:
            try:
                success = await self.chat_integration.add_chat_channel(platform, channel)
                logger.info(f"{'✅' if success else '❌'} Added {platform} channel: {channel}")
            except Exception as e:
                logger.warning(f"⚠️ Could not add {platform} channel: {e}")
        
        # Simulate some analysis
        await asyncio.sleep(2)
        
        # Get chat statistics
        stats = self.chat_integration.get_chat_stats()
        logger.info(f"📊 Chat Stats: {stats}")
    
    async def demonstrate_sentiment_analysis(self):
        """Demonstrate sentiment analysis."""
        logger.info("\n😊 Demonstrating Sentiment Analysis...")
        
        try:
            sentiment_result = await self.chat_integration.quick_sentiment()
            logger.info(f"Sentiment Analysis Result:\n{sentiment_result}")
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
    
    async def demonstrate_engagement_monitoring(self):
        """Demonstrate engagement monitoring."""
        logger.info("\n⚡ Demonstrating Engagement Monitoring...")
        
        try:
            engagement_result = await self.chat_integration.engagement_status()
            logger.info(f"Engagement Status:\n{engagement_result}")
        except Exception as e:
            logger.error(f"Error in engagement monitoring: {e}")
    
    async def demonstrate_moderation_features(self):
        """Demonstrate moderation capabilities."""
        logger.info("\n🛡️ Demonstrating Moderation Features...")
        
        try:
            moderation_result = await self.chat_integration.moderation_status()
            logger.info(f"Moderation Status:\n{moderation_result}")
        except Exception as e:
            logger.error(f"Error in moderation check: {e}")
    
    async def demonstrate_comprehensive_analysis(self):
        """Demonstrate comprehensive chat analysis."""
        logger.info("\n🧠 Demonstrating Comprehensive Analysis...")
        
        try:
            context = "Live streaming demo with multiple chat platforms"
            analysis_result = await self.chat_integration.analyze_chat(context)
            logger.info(f"Comprehensive Analysis:\n{analysis_result}")
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
    
    async def demonstrate_automation_features(self):
        """Demonstrate automation capabilities."""
        logger.info("\n🤖 Demonstrating Automation Features...")
        
        # Configure thresholds
        self.chat_integration.configure_thresholds(
            low_engagement=0.3,
            high_toxicity=0.6,
            sentiment_drop=-0.5
        )
        logger.info("✅ Configured automation thresholds")
        
        # Enable auto-response
        self.chat_integration.enable_auto_response(True)
        logger.info("✅ Enabled automated responses")
        
        # Set analysis interval
        self.chat_integration.set_analysis_interval(15.0)  # 15 seconds for demo
        logger.info("✅ Set analysis interval to 15 seconds")
        
        # Demonstrate manual trigger
        try:
            trigger_result = await self.chat_integration.manual_trigger("comprehensive")
            logger.info(f"Manual Trigger Result:\n{trigger_result}")
        except Exception as e:
            logger.error(f"Error in manual trigger: {e}")
    
    async def run_demo(self):
        """Run the complete demonstration."""
        logger.info("🚀 Starting Chat Intelligence Demo")
        logger.info("=" * 50)
        
        # Setup
        obs_connected = await self.setup_obs_connection()
        chat_setup = await self.setup_chat_intelligence()
        
        if not chat_setup:
            logger.error("❌ Failed to setup chat intelligence system")
            return
        
        try:
            # Run demonstrations
            await self.demonstrate_chat_analysis()
            await self.demonstrate_sentiment_analysis()
            await self.demonstrate_engagement_monitoring()
            await self.demonstrate_moderation_features()
            await self.demonstrate_comprehensive_analysis()
            await self.demonstrate_automation_features()
            
            # Run for a short period to show continuous monitoring
            logger.info("\n⏰ Running continuous monitoring for 30 seconds...")
            logger.info("(In real usage, this would run continuously during streaming)")
            
            await asyncio.sleep(30)
            
        finally:
            # Cleanup
            logger.info("\n🧹 Cleaning up...")
            if self.chat_integration:
                await self.chat_integration.stop()
            
            if self.obs_agent:
                await self.obs_agent.disconnect()
        
        logger.info("✅ Demo completed successfully!")
        logger.info("=" * 50)


async def main():
    """Main entry point for the demo."""
    demo = ChatIntelligenceDemo()
    await demo.run_demo()


if __name__ == "__main__":
    # Print banner
    print("""
╔════════════════════════════════════════════════════════════════╗
║                    OBS Agent Chat Intelligence                 ║
║                         Demo System                           ║
╠════════════════════════════════════════════════════════════════╣
║  This demo showcases the AI-powered chat intelligence system  ║
║  that analyzes streaming chat in real-time and provides       ║
║  automated optimization recommendations.                       ║
║                                                                ║
║  Features demonstrated:                                        ║
║  • Multi-platform chat analysis (Twitch, YouTube, Discord)   ║
║  • Real-time sentiment analysis                              ║
║  • Engagement prediction and optimization                     ║
║  • Community moderation recommendations                       ║
║  • Automated OBS control based on chat intelligence          ║
║  • CrewAI multi-agent collaboration                          ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Demo interrupted by user")
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()