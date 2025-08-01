#!/usr/bin/env python3
"""
Real-World Streaming Setup Automation

This example shows a complete streaming setup with practical automations
that streamers actually use. It demonstrates professional-grade automation
patterns for live streaming.

Features:
- Stream startup/shutdown sequences
- Automatic scene management
- Audio ducking and normalization
- Viewer engagement automations
- Recording management
- Alert systems
- Performance monitoring

Perfect for: Content creators, streamers, podcasters, and anyone doing live content.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.obs_agent import OBSAgent
from src.obs_agent.events import (
    CurrentProgramSceneChanged,
    InputMuteStateChanged,
    StreamStateChanged,
    RecordStateChanged,
)


class StreamingAutomationSetup:
    """Professional streaming automation setup."""

    def __init__(self, streamer_config=None):
        self.agent = OBSAgent()
        
        # Configuration (customize for your setup)
        self.config = streamer_config or {
            'scenes': {
                'starting_soon': 'Starting Soon',
                'main': 'Main Stream',
                'brb': 'Be Right Back', 
                'ending': 'Stream Ending',
                'intermission': 'Intermission',
                'chat_only': 'Just Chatting'
            },
            'sources': {
                'microphone': 'Microphone',
                'desktop_audio': 'Desktop Audio',
                'music': 'Background Music',
                'alert_sound': 'Alert Sound',
                'countdown_timer': 'Countdown Timer',
                'follower_count': 'Follower Count',
                'stream_title': 'Stream Title',
                'current_time': 'Current Time'
            },
            'audio_levels': {
                'mic_normal': -12.0,
                'mic_ducked': -20.0,
                'music_normal': -18.0,
                'music_ducked': -30.0,
                'alert_volume': -8.0
            },
            'timings': {
                'brb_delay': 10.0,        # Seconds before switching to BRB
                'return_delay': 2.0,      # Seconds before switching back
                'stream_start_delay': 30.0,  # Starting Soon duration
                'ending_delay': 60.0      # Stream ending duration
            }
        }
        
        self.stream_start_time = None
        self.last_activity = datetime.now()

    async def setup_streaming_automation(self):
        """Set up complete streaming automation system."""
        print("🎥 Setting up Professional Streaming Automation")
        print("=" * 55)
        
        try:
            # Connect and start automation
            await self.agent.connect()
            self.agent.start_automation()
            print("✅ Connected to OBS and started automation engine")
            
            # Set up all automation rules
            await self.setup_stream_lifecycle_automation()
            self.setup_audio_management()
            self.setup_scene_management()
            self.setup_engagement_features()
            self.setup_safety_features()
            self.setup_monitoring()
            
            print("\n🚀 Streaming automation is now active!")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False

    async def setup_stream_lifecycle_automation(self):
        """Automate stream start/stop sequences."""
        print("\n📺 Setting up stream lifecycle automation...")
        
        # Stream startup sequence
        @self.agent.automation.when(StreamStateChanged, lambda e: e.output_active)
        @self.agent.automation.description("Professional stream startup sequence")
        async def stream_startup_sequence(context):
            """Execute professional stream startup."""
            self.stream_start_time = datetime.now()
            print("🎬 Stream started - executing startup sequence...")
            
            # Multi-step startup workflow
            startup_workflow = await (
                self.agent.actions
                .scene(self.config['scenes']['starting_soon'])  # Show "Starting Soon"
                .text(self.config['sources']['stream_title'], f"Stream Starting - {datetime.now().strftime('%B %d, %Y')}")
                .volume(self.config['sources']['music'], volume_db=self.config['audio_levels']['music_normal'])
                .wait(3.0)
                .start_recording()  # Auto-start recording
                .wait(self.config['timings']['stream_start_delay'])  # Wait for "Starting Soon" period
                .scene(self.config['scenes']['main'])  # Switch to main content
                .text(self.config['sources']['current_time'], datetime.now().strftime('%H:%M'))
                .custom(self._log_stream_start)
                .build()
            )
            
            await startup_workflow(context)

        # Stream shutdown sequence  
        @self.agent.automation.when(StreamStateChanged, lambda e: not e.output_active)
        @self.agent.automation.description("Professional stream shutdown sequence")
        async def stream_shutdown_sequence(context):
            """Execute professional stream shutdown."""
            print("🎬 Stream ended - executing shutdown sequence...")
            
            # Calculate stream duration
            if self.stream_start_time:
                duration = datetime.now() - self.stream_start_time
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                duration_text = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            else:
                duration_text = "Unknown"
            
            # Shutdown workflow
            shutdown_workflow = await (
                self.agent.actions
                .scene(self.config['scenes']['ending'])
                .text(self.config['sources']['stream_title'], f"Thanks for watching! Stream duration: {duration_text}")
                .wait(self.config['timings']['ending_delay'])
                .if_recording(True)
                .stop_recording()
                .custom(self._log_stream_end)
                .build()
            )
            
            await shutdown_workflow(context)

        print("✅ Stream lifecycle automation configured")

    def setup_audio_management(self):
        """Set up intelligent audio management."""
        print("🎵 Setting up audio management...")
        
        # Intelligent audio ducking
        @self.agent.automation.when(InputMuteStateChanged, 
                                   lambda e: self.config['sources']['microphone'] in e.input_name)
        @self.agent.automation.description("Smart audio ducking system")
        async def smart_audio_ducking(context):
            """Manage audio levels based on microphone activity."""
            is_muted = context.trigger_event.input_muted
            
            if is_muted:
                # Mic muted - bring up background music
                await self.agent.set_source_volume(
                    self.config['sources']['music'], 
                    volume_db=self.config['audio_levels']['music_normal']
                )
                print("🎵 Mic muted - music volume restored")
            else:
                # Mic active - duck background music  
                await self.agent.set_source_volume(
                    self.config['sources']['music'],
                    volume_db=self.config['audio_levels']['music_ducked']
                )
                print("🎤 Mic active - music ducked")

        # Audio normalization on scene changes
        @self.agent.automation.when(CurrentProgramSceneChanged)
        @self.agent.automation.description("Normalize audio levels per scene")
        async def normalize_audio_per_scene(context):
            """Adjust audio levels for different scenes."""
            scene_name = context.trigger_event.scene_name
            
            # Different audio profiles for different scenes
            if scene_name == self.config['scenes']['chat_only']:
                # Chat scene - higher music, normal mic
                await self.agent.set_source_volume(self.config['sources']['music'], volume_db=-15.0)
                await self.agent.set_source_volume(self.config['sources']['microphone'], volume_db=-10.0)
            elif scene_name == self.config['scenes']['main']:
                # Main scene - normal levels
                await self.agent.set_source_volume(self.config['sources']['music'], volume_db=-18.0)
                await self.agent.set_source_volume(self.config['sources']['microphone'], volume_db=-12.0)
            elif scene_name == self.config['scenes']['brb']:
                # BRB scene - higher music, muted mic
                await self.agent.set_source_volume(self.config['sources']['music'], volume_db=-12.0)

        print("✅ Audio management configured")

    def setup_scene_management(self):
        """Set up intelligent scene management."""
        print("🎬 Setting up scene management...")
        
        # Smart BRB system with return detection
        @self.agent.automation.when(InputMuteStateChanged,
                                   lambda e: self.config['sources']['microphone'] in e.input_name and e.input_muted)
        @self.agent.automation.after_delay(self.config['timings']['brb_delay'])
        @self.agent.automation.description("Intelligent BRB system")
        async def intelligent_brb_system(context):
            """Switch to BRB after mic has been muted for a while."""
            # Double-check mic is still muted
            current_mute = await self.agent.get_source_mute(self.config['sources']['microphone'])
            if current_mute:
                current_scene = await self.agent.get_current_scene()
                if current_scene != self.config['scenes']['brb']:
                    await self.agent.set_scene(self.config['scenes']['brb'])
                    print("🚶 Switched to BRB - streamer seems to be away")

        # Return from BRB
        @self.agent.automation.when(InputMuteStateChanged,
                                   lambda e: self.config['sources']['microphone'] in e.input_name and not e.input_muted)
        @self.agent.automation.after_delay(self.config['timings']['return_delay'])
        @self.agent.automation.description("Return from BRB system")
        async def return_from_brb(context):
            """Return from BRB when streamer is back."""
            current_scene = await self.agent.get_current_scene()
            if current_scene == self.config['scenes']['brb']:
                await self.agent.set_scene(self.config['scenes']['main'])
                print("👋 Welcome back! Returned to main scene")

        # Scene-based timer updates
        @self.agent.automation.when(CurrentProgramSceneChanged)
        @self.agent.automation.description("Update scene timers")
        async def update_scene_timers(context):
            """Update various timers and info when scenes change."""
            scene_name = context.trigger_event.scene_name
            current_time = datetime.now().strftime('%H:%M')
            
            # Update current time display
            try:
                await self.agent.set_source_settings(
                    self.config['sources']['current_time'],
                    {"text": current_time}
                )
            except:
                pass  # Source might not exist
            
            # Log scene activity
            self.last_activity = datetime.now()
            print(f"📍 Scene changed to '{scene_name}' at {current_time}")

        print("✅ Scene management configured")

    def setup_engagement_features(self):
        """Set up viewer engagement features."""
        print("👥 Setting up engagement features...")
        
        # Hourly stream update
        @self.agent.automation.every(3600.0)  # Every hour
        @self.agent.automation.description("Hourly stream updates")
        async def hourly_stream_update(context):
            """Provide hourly updates during stream."""
            if self.stream_start_time:
                duration = datetime.now() - self.stream_start_time
                hours = int(duration.total_seconds() // 3600)
                
                if hours > 0:
                    current_scene = await self.agent.get_current_scene()
                    print(f"⏰ Stream update: {hours} hour(s) of streaming!")
                    
                    # Could trigger overlay updates, announcements, etc.
                    try:
                        await self.agent.set_source_settings(
                            self.config['sources']['stream_title'],
                            {"text": f"Live for {hours}+ hours!"}
                        )
                    except:
                        pass

        # Stream milestone celebrations (could be integrated with Twitch API)
        @self.agent.automation.when(CurrentProgramSceneChanged)
        @self.agent.automation.description("Milestone celebration system")
        async def milestone_celebration(context):
            """Celebrate stream milestones."""
            # This is a placeholder for integration with streaming platforms
            # In a real setup, you'd integrate with Twitch/YouTube APIs
            pass

        print("✅ Engagement features configured")

    def setup_safety_features(self):
        """Set up safety and backup features."""
        print("🛡️ Setting up safety features...")
        
        # Emergency privacy mode
        @self.agent.automation.when(CurrentProgramSceneChanged)
        @self.agent.automation.description("Emergency privacy mode")
        async def emergency_privacy_mode(context):
            """Quick privacy protection."""
            scene_name = context.trigger_event.scene_name
            
            # If switching to a privacy scene, mute mic and duck game audio
            if "privacy" in scene_name.lower() or "emergency" in scene_name.lower():
                await self.agent.set_source_mute(self.config['sources']['microphone'], True)
                await self.agent.set_source_volume(self.config['sources']['desktop_audio'], volume_db=-40.0)
                print("🔒 Emergency privacy mode activated!")

        # Automatic recording backup
        @self.agent.automation.when(RecordStateChanged, lambda e: not e.output_active)
        @self.agent.automation.description("Recording safety check")
        async def recording_safety_check(context):
            """Ensure recordings are properly saved."""
            if context.trigger_event.output_path:
                file_path = Path(context.trigger_event.output_path)
                if file_path.exists():
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    print(f"💾 Recording saved: {file_path.name} ({size_mb:.1f} MB)")
                else:
                    print("⚠️ Warning: Recording file not found!")

        print("✅ Safety features configured")

    def setup_monitoring(self):
        """Set up performance and health monitoring."""
        print("📊 Setting up monitoring...")
        
        # Performance monitoring
        @self.agent.automation.every(300.0)  # Every 5 minutes
        @self.agent.automation.description("Performance monitoring")
        async def performance_monitor(context):
            """Monitor stream and system performance."""
            try:
                # Get OBS stats
                obs_stats = await self.agent.get_stats()
                
                # Check for performance issues
                if 'outputSkippedFrames' in obs_stats and obs_stats['outputSkippedFrames'] > 100:
                    print("⚠️ Performance warning: High frame drops detected!")
                
                # Log basic stats
                if self.stream_start_time:
                    uptime = datetime.now() - self.stream_start_time
                    print(f"📈 Stream health check - Uptime: {uptime}")
                
            except Exception as e:
                print(f"📊 Monitoring error: {e}")

        # Automation health check
        @self.agent.automation.every(600.0)  # Every 10 minutes  
        @self.agent.automation.description("Automation system health check")
        async def automation_health_check(context):
            """Check automation system health."""
            stats = self.agent.get_automation_stats()
            
            success_rate = 0
            if stats.get('total_executions', 0) > 0:
                success_rate = (stats.get('successful_executions', 0) / 
                              stats.get('total_executions', 1)) * 100
            
            print(f"🤖 Automation health: {success_rate:.1f}% success rate, "
                  f"{stats.get('active_rules', 0)} active rules")

        print("✅ Monitoring configured")

    async def _log_stream_start(self, context):
        """Log stream start details."""
        scenes = await self.agent.get_scenes()
        print(f"🎬 Stream started at {self.stream_start_time.strftime('%H:%M:%S')}")
        print(f"📺 Available scenes: {', '.join(scenes[:5])}{'...' if len(scenes) > 5 else ''}")

    async def _log_stream_end(self, context):
        """Log stream end details."""
        if self.stream_start_time:
            duration = datetime.now() - self.stream_start_time
            print(f"🏁 Stream ended after {duration}")
        
        stats = self.agent.get_automation_stats()
        print(f"🤖 Automation stats: {stats.get('total_executions', 0)} total executions")

    async def run_streaming_session(self):
        """Run a complete streaming session with automation."""
        print("🎥 Starting Streaming Session with Full Automation")
        print("=" * 55)
        
        if not await self.setup_streaming_automation():
            return
        
        print("\n🎯 Streaming automation is active!")
        print("-" * 40)
        print("Your streaming setup includes:")
        print("• Automatic stream startup/shutdown sequences")
        print("• Intelligent BRB system (10s delay)")
        print("• Smart audio ducking and normalization")
        print("• Scene-based audio profiles")
        print("• Hourly stream updates")
        print("• Emergency privacy protection")
        print("• Performance monitoring")
        print("• Recording safety checks")
        
        print(f"\nConfiguration:")
        print(f"• Main scene: {self.config['scenes']['main']}")
        print(f"• BRB scene: {self.config['scenes']['brb']}")
        print(f"• Microphone: {self.config['sources']['microphone']}")
        print(f"• Music source: {self.config['sources']['music']}")
        
        print("\n🎮 Ready to stream! Try these actions:")
        print("• Start/stop streaming in OBS")
        print("• Switch between scenes")
        print("• Mute/unmute your microphone")
        print("• Let the automation work its magic!")
        
        print("\nPress Ctrl+C to stop automation and view statistics...")
        
        try:
            # Run for up to 8 hours (typical streaming session)
            await asyncio.sleep(28800)
        except KeyboardInterrupt:
            print("\n⏹️ Stopping streaming automation...")
        
        # Show final statistics
        print("\n📊 Streaming Session Statistics:")
        print("-" * 35)
        stats = self.agent.get_automation_stats()
        for key, value in stats.items():
            print(f"• {key.replace('_', ' ').title()}: {value}")
        
        if self.stream_start_time:
            session_duration = datetime.now() - self.stream_start_time
            print(f"• Session Duration: {session_duration}")
        
        # Cleanup
        self.agent.stop_automation()
        await self.agent.disconnect()
        print("\n✅ Streaming automation stopped. Thanks for streaming!")


async def main():
    """Main entry point."""
    # You can customize this configuration for your setup
    custom_config = {
        'scenes': {
            'starting_soon': 'Starting Soon',
            'main': 'Gaming',           # Adjust to your scene names
            'brb': 'BRB',
            'ending': 'Thanks for Watching',
            'intermission': 'Intermission',
            'chat_only': 'Just Chatting'
        },
        'sources': {
            'microphone': 'Mic/Aux',    # Adjust to your source names
            'desktop_audio': 'Desktop Audio',
            'music': 'Spotify',         # Adjust to your music source
            'stream_title': 'Stream Title Text',
            'current_time': 'Clock'
        },
        # ... other config options
    }
    
    streaming_setup = StreamingAutomationSetup(custom_config)
    await streaming_setup.run_streaming_session()


if __name__ == "__main__":
    asyncio.run(main())