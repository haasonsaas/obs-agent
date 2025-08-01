#!/usr/bin/env python3
"""
Programming Livestream Setup - Automated OBS configuration for code streaming
Creates a professional programming/coding livestream environment with AI assistance
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.obs_agent import AdvancedOBSAgent, AdvancedOBSController
from src.tools import OBSAIAgent, OBSAgentOrchestrator, StreamGoal
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class ProgrammingStreamSetup:
    """Complete setup automation for programming livestreams"""
    
    def __init__(self, password: str = None):
        self.agent = AdvancedOBSAgent(
            password=password or os.getenv("OBS_WEBSOCKET_PASSWORD", "")
        )
        self.controller = AdvancedOBSController(self.agent)
        self.scenes_created = []
        
    async def connect(self) -> bool:
        """Connect to OBS"""
        return await self.agent.connect()
    
    async def create_programming_environment(
        self,
        language: str = "python",
        theme: str = "dark",
        include_webcam: bool = True,
        terminal_position: str = "bottom",
        ide_name: str = "VS Code"
    ):
        """Create a complete programming stream environment"""
        
        print("🚀 Programming Stream Setup")
        print("=" * 50)
        print(f"Language: {language}")
        print(f"Theme: {theme}")
        print(f"IDE: {ide_name}")
        print(f"Webcam: {'Yes' if include_webcam else 'No'}")
        print(f"Terminal: {terminal_position}")
        print("=" * 50)
        
        # 1. Create programming-specific scenes
        await self._create_programming_scenes()
        
        # 2. Configure layouts for each scene
        await self._configure_layouts(include_webcam, terminal_position)
        
        # 3. Set up audio for commentary
        await self._setup_audio()
        
        # 4. Apply visual filters for readability
        await self._apply_code_filters(theme)
        
        # 5. Create keyboard shortcuts info
        await self._create_shortcut_overlays()
        
        # 6. Set up automated behaviors
        await self._configure_automation(language)
        
        print("\n✅ Programming stream environment ready!")
        print("📺 You can now start streaming your coding sessions!")
        
    async def _create_programming_scenes(self):
        """Create scenes optimized for programming streams"""
        
        print("\n📋 Creating Programming Scenes...")
        
        scenes = {
            "💻 Code Editor": {
                "description": "Main coding view with editor",
                "sources": ["Screen Capture", "Webcam", "Key Display"]
            },
            "🖥️ Terminal": {
                "description": "Terminal/console focused view",
                "sources": ["Terminal Capture", "Command Display"]
            },
            "📄 Documentation": {
                "description": "Showing docs or references",
                "sources": ["Browser Capture", "Notes"]
            },
            "🔀 Split View": {
                "description": "Code + Terminal side by side",
                "sources": ["Screen Capture", "Terminal Window"]
            },
            "🎯 Focus Mode": {
                "description": "Zoomed code section",
                "sources": ["Cropped Screen", "Line Highlight"]
            },
            "💭 Explaining": {
                "description": "Webcam focused for explanations",
                "sources": ["Webcam Large", "Code Thumbnail"]
            },
            "🚀 Running Code": {
                "description": "Output and results view",
                "sources": ["Output Window", "Status Display"]
            },
            "☕ Break": {
                "description": "Break screen",
                "sources": ["Break Message", "Music Visualizer"]
            },
            "📺 Starting Soon": {
                "description": "Pre-stream screen",
                "sources": ["Starting Text", "Schedule"]
            },
            "🎉 Ending": {
                "description": "End stream screen",
                "sources": ["Thanks Message", "Social Links"]
            }
        }
        
        for scene_name, config in scenes.items():
            if scene_name not in await self.agent.get_scenes():
                await self.agent.create_scene(scene_name)
                self.scenes_created.append(scene_name)
                print(f"  ✅ Created: {scene_name} - {config['description']}")
    
    async def _configure_layouts(self, include_webcam: bool, terminal_position: str):
        """Configure layouts for programming scenes"""
        
        print("\n🎨 Configuring Layouts...")
        
        # Main coding layout
        await self.agent.set_scene("💻 Code Editor")
        
        # Add display capture for code editor
        try:
            await self.agent.create_source(
                scene_name="💻 Code Editor",
                source_name="Code Display",
                source_kind="display_capture",
                settings={
                    "display": 0,
                    "show_cursor": True
                }
            )
            print("  ✅ Added screen capture for code")
        except:
            print("  ℹ️  Screen capture might already exist")
        
        # Add webcam if requested
        if include_webcam:
            try:
                await self.agent.create_source(
                    scene_name="💻 Code Editor",
                    source_name="Webcam",
                    source_kind="av_capture_input",
                    settings={
                        "device": 0,
                        "preset": "1280x720"
                    }
                )
                
                # Position webcam as PiP
                scene_items = await self.agent.get_scene_items("💻 Code Editor")
                for item in scene_items:
                    if item.get("sourceName") == "Webcam":
                        # Bottom right corner, 20% size
                        transform = {
                            "positionX": 1920 * 0.75,
                            "positionY": 1080 * 0.75,
                            "scaleX": 0.2,
                            "scaleY": 0.2,
                            "cropTop": 0,
                            "cropBottom": 0,
                            "cropLeft": 0,
                            "cropRight": 0
                        }
                        await self.agent.set_scene_item_transform(
                            "💻 Code Editor",
                            item["sceneItemId"],
                            transform
                        )
                        print("  ✅ Positioned webcam as PiP")
            except Exception as e:
                print(f"  ℹ️  Webcam setup: {e}")
        
        # Add overlay text elements
        overlays = [
            {
                "scene": "📺 Starting Soon",
                "name": "Starting Text",
                "text": "🚀 Stream Starting Soon!\n📚 Today: Live Coding Session",
                "size": 72,
                "color": 0xFF00FFFF
            },
            {
                "scene": "☕ Break",
                "name": "Break Text", 
                "text": "☕ Quick Break - BRB!\n🎵 Enjoy the music",
                "size": 64,
                "color": 0xFFFF00FF
            },
            {
                "scene": "🎉 Ending",
                "name": "Thanks Text",
                "text": "Thanks for Watching! 🎉\n👋 See you next time!",
                "size": 60,
                "color": 0xFF00FF00
            }
        ]
        
        for overlay in overlays:
            await self.agent.set_scene(overlay["scene"])
            try:
                await self.agent.create_source(
                    scene_name=overlay["scene"],
                    source_name=overlay["name"],
                    source_kind="text_ft2_source_v2",
                    settings={
                        "text": overlay["text"],
                        "font": {
                            "face": "Arial",
                            "size": overlay["size"],
                            "style": "Bold"
                        },
                        "color1": overlay["color"],
                        "color2": overlay["color"],
                        "align": "center",
                        "valign": "center"
                    }
                )
                print(f"  ✅ Added overlay to {overlay['scene']}")
            except:
                pass
    
    async def _setup_audio(self):
        """Configure audio for programming streams"""
        
        print("\n🎤 Setting Up Audio...")
        
        # Get audio sources
        sources = await self.agent.get_sources()
        audio_sources = [s for s in sources if "Audio" in s.get("inputKind", "")]
        
        for source in audio_sources:
            source_name = source["inputName"]
            
            # Set optimal levels for commentary
            await self.agent.set_source_volume(source_name, volume_db=-15.0)
            
            # Apply noise suppression to microphones
            if "mic" in source_name.lower() or "input" in source_name.lower():
                try:
                    await self.agent.add_filter(
                        source_name=source_name,
                        filter_name="Noise Suppression",
                        filter_kind="noise_suppress_filter",
                        filter_settings={"suppress_level": -30}
                    )
                    print(f"  ✅ Applied noise suppression to {source_name}")
                    
                    # Add compressor for consistent levels
                    await self.agent.add_filter(
                        source_name=source_name,
                        filter_name="Compressor",
                        filter_kind="compressor_filter",
                        filter_settings={
                            "ratio": 4.0,
                            "threshold": -24.0,
                            "attack_time": 1.0,
                            "release_time": 50.0,
                            "output_gain": 2.0
                        }
                    )
                    print(f"  ✅ Applied compressor to {source_name}")
                except:
                    pass
    
    async def _apply_code_filters(self, theme: str):
        """Apply filters to improve code readability"""
        
        print("\n🎨 Applying Visual Filters...")
        
        # Get screen capture sources
        sources = await self.agent.get_sources()
        screen_sources = [s for s in sources if "capture" in s.get("inputKind", "").lower()]
        
        for source in screen_sources:
            source_name = source["inputName"]
            
            if theme == "dark":
                # Slight brightness boost for dark themes
                try:
                    await self.agent.add_filter(
                        source_name=source_name,
                        filter_name="Brightness Boost",
                        filter_kind="color_filter",
                        filter_settings={
                            "brightness": 0.05,
                            "contrast": 0.02,
                            "saturation": 1.1
                        }
                    )
                    print(f"  ✅ Enhanced visibility for dark theme on {source_name}")
                except:
                    pass
            
            # Sharpen filter for text clarity
            try:
                await self.agent.add_filter(
                    source_name=source_name,
                    filter_name="Sharpen",
                    filter_kind="sharpness_filter",
                    filter_settings={"sharpness": 0.08}
                )
                print(f"  ✅ Applied sharpening to {source_name}")
            except:
                pass
    
    async def _create_shortcut_overlays(self):
        """Create keyboard shortcut display overlays"""
        
        print("\n⌨️  Creating Shortcut Overlays...")
        
        # Common shortcuts to display
        shortcuts = {
            "VS Code": "Ctrl+P: Quick Open | Ctrl+Shift+P: Command Palette | Ctrl+`: Terminal",
            "General": "Ctrl+S: Save | Ctrl+Z: Undo | Ctrl+Shift+Z: Redo",
            "Terminal": "Ctrl+C: Cancel | Ctrl+L: Clear | Tab: Autocomplete"
        }
        
        await self.agent.set_scene("💻 Code Editor")
        
        try:
            await self.agent.create_source(
                scene_name="💻 Code Editor",
                source_name="Shortcuts Display",
                source_kind="text_ft2_source_v2",
                settings={
                    "text": shortcuts["VS Code"],
                    "font": {
                        "face": "Consolas",
                        "size": 18,
                        "style": "Regular"
                    },
                    "color1": 0xFFFFFFFF,
                    "color2": 0xFFFFFFFF,
                    "align": "left",
                    "valign": "bottom",
                    "outline": True,
                    "outline_size": 2,
                    "outline_color": 0xFF000000
                }
            )
            
            # Position at bottom of screen
            scene_items = await self.agent.get_scene_items("💻 Code Editor")
            for item in scene_items:
                if item.get("sourceName") == "Shortcuts Display":
                    transform = {
                        "positionX": 10,
                        "positionY": 1080 - 50,
                        "scaleX": 1.0,
                        "scaleY": 1.0
                    }
                    await self.agent.set_scene_item_transform(
                        "💻 Code Editor",
                        item["sceneItemId"],
                        transform
                    )
            
            print("  ✅ Added keyboard shortcuts display")
        except:
            pass
    
    async def _configure_automation(self, language: str):
        """Set up automated behaviors for programming streams"""
        
        print("\n🤖 Configuring Automation...")
        
        # Create automation rules based on language
        automation_config = {
            "python": {
                "run_command": "python",
                "error_patterns": ["Traceback", "Error:", "Exception"],
                "success_patterns": ["Process finished", "Successfully"]
            },
            "javascript": {
                "run_command": "node",
                "error_patterns": ["Error:", "TypeError", "ReferenceError"],
                "success_patterns": ["Done", "Completed"]
            },
            "java": {
                "run_command": "java",
                "error_patterns": ["Exception", "Error:"],
                "success_patterns": ["BUILD SUCCESSFUL"]
            }
        }
        
        config = automation_config.get(language, automation_config["python"])
        
        # Save automation config
        with open("programming_automation.json", "w") as f:
            json.dump({
                "language": language,
                "config": config,
                "scene_rules": {
                    "on_run": "🖥️ Terminal",
                    "on_error": "🎯 Focus Mode",
                    "on_explain": "💭 Explaining",
                    "on_success": "💻 Code Editor"
                }
            }, f, indent=2)
        
        print(f"  ✅ Configured automation for {language}")
        print("  ✅ Scene switching rules saved")
    
    async def start_intelligent_stream(self, duration_hours: float = 2.0):
        """Start streaming with AI assistance"""
        
        print("\n🤖 Starting Intelligent Programming Stream...")
        
        # Create AI agent configuration
        from src.tools import AgentConfig, StreamGoal
        
        config = AgentConfig(
            goals=[StreamGoal.TUTORIAL_CLARITY, StreamGoal.MAXIMIZE_ENGAGEMENT],
            scene_min_duration=45,  # Longer for coding
            scene_max_duration=600,  # Up to 10 minutes per scene
            audio_target_db=-15.0,  # Louder for commentary
            auto_scene_switching=True,
            engagement_scenes=["💭 Explaining", "🎯 Focus Mode"]
        )
        
        # Create AI agent
        ai_agent = OBSAIAgent(self.agent, config)
        
        # Start streaming
        await self.agent.start_streaming()
        print("🔴 Streaming started!")
        
        # Run AI monitoring
        agent_task = asyncio.create_task(ai_agent.start())
        
        # Simulate programming activities
        print("\n📊 AI is now managing your stream:")
        print("  - Monitoring audio levels")
        print("  - Switching scenes based on activity")
        print("  - Optimizing for viewer engagement")
        print("  - Preventing technical issues")
        
        # Stream for specified duration
        await asyncio.sleep(duration_hours * 3600)
        
        # Stop everything
        await ai_agent.stop()
        agent_task.cancel()
        await self.agent.stop_streaming()
        
        print("\n✅ Intelligent streaming session complete!")
    
    async def quick_setup_and_test(self):
        """Quick setup and test for programming stream"""
        
        if not await self.connect():
            print("❌ Failed to connect to OBS")
            return
        
        try:
            # Create basic programming environment
            await self.create_programming_environment(
                language="python",
                theme="dark",
                include_webcam=True,
                terminal_position="bottom"
            )
            
            # Quick scene tour
            print("\n🎬 Testing Scene Transitions...")
            
            test_sequence = [
                ("📺 Starting Soon", 3),
                ("💻 Code Editor", 5),
                ("🖥️ Terminal", 3),
                ("🔀 Split View", 3),
                ("💭 Explaining", 3),
                ("☕ Break", 2),
                ("💻 Code Editor", 2)
            ]
            
            for scene, duration in test_sequence:
                print(f"  ➡️  {scene}")
                await self.agent.set_scene(scene)
                await asyncio.sleep(duration)
            
            print("\n✅ Programming stream setup complete!")
            print("\n💡 Tips for your stream:")
            print("  - Use '💻 Code Editor' for main coding")
            print("  - Switch to '🖥️ Terminal' when running code")
            print("  - Use '💭 Explaining' when teaching concepts")
            print("  - '🎯 Focus Mode' for debugging")
            print("  - Take breaks with '☕ Break' scene")
            
        finally:
            self.agent.disconnect()


# Standalone functions for quick use
async def setup_programming_stream(language: str = "python"):
    """Quick function to set up programming stream"""
    setup = ProgrammingStreamSetup()
    await setup.quick_setup_and_test()


async def main():
    """Demo the programming stream setup"""
    print("🚀 Programming Stream Setup Demo")
    print("=" * 50)
    
    setup = ProgrammingStreamSetup()
    await setup.quick_setup_and_test()


if __name__ == "__main__":
    asyncio.run(main())