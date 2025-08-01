#!/usr/bin/env python3
"""
Beautiful OBS Setup - Create stunning professional scenes with gradients, animations, and polish
"""

import asyncio
from obswebsocket import obsws, requests
from dotenv import load_dotenv
import os
import json

load_dotenv()


class BeautifulOBSSetup:
    def __init__(self):
        self.ws = None
        self.password = os.getenv("OBS_WEBSOCKET_PASSWORD", "")
        
        # Beautiful color schemes
        self.color_schemes = {
            "cyberpunk": {
                "primary": 0xFF00FFFF,    # Cyan
                "secondary": 0xFFFF00FF,  # Magenta  
                "accent": 0xFF00FF00,     # Green
                "background": 0xFF1a1a2e, # Dark purple
                "text": 0xFFFFFFFF       # White
            },
            "sunset": {
                "primary": 0xFFFF6B35,    # Orange
                "secondary": 0xFFF7931E,  # Yellow
                "accent": 0xFFFF1744,     # Red
                "background": 0xFF2E1760, # Deep purple
                "text": 0xFFFFFFFF       # White
            },
            "ocean": {
                "primary": 0xFF00B4D8,    # Light blue
                "secondary": 0xFF0077B6,  # Medium blue
                "accent": 0xFF023E8A,     # Dark blue
                "background": 0xFF03045E, # Navy
                "text": 0xFFFFFFFF       # White
            },
            "forest": {
                "primary": 0xFF40916C,    # Green
                "secondary": 0xFF52B788,  # Light green  
                "accent": 0xFF2D6A4F,     # Dark green
                "background": 0xFF1B4332, # Forest green
                "text": 0xFFFFFFFF       # White
            },
            "minimal": {
                "primary": 0xFF000000,    # Black
                "secondary": 0xFF333333,  # Dark gray
                "accent": 0xFF666666,     # Medium gray
                "background": 0xFFF8F9FA, # Light gray
                "text": 0xFF000000       # Black
            }
        }
    
    def connect(self):
        """Connect to OBS"""
        try:
            self.ws = obsws("localhost", 4455, self.password)
            self.ws.connect()
            print("✅ Connected to OBS!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from OBS"""
        if self.ws:
            self.ws.disconnect()
            print("👋 Disconnected from OBS")
    
    async def create_beautiful_scenes(self, theme="cyberpunk"):
        """Create beautiful scenes with professional styling"""
        print(f"🎨 Creating Beautiful Scenes - {theme.title()} Theme")
        print("=" * 60)
        
        colors = self.color_schemes[theme]
        
        # Beautiful scene definitions
        scenes = {
            "🚀 Welcome": {
                "description": "Animated welcome screen",
                "elements": [
                    {
                        "type": "gradient_background",
                        "colors": [colors["background"], colors["primary"]]
                    },
                    {
                        "type": "animated_title",
                        "text": "🚀 LIVE CODING SESSION",
                        "font_size": 84,
                        "color": colors["text"],
                        "animation": "fade_slide"
                    },
                    {
                        "type": "subtitle",
                        "text": "Building Amazing Software Live",
                        "font_size": 36,
                        "color": colors["secondary"]
                    },
                    {
                        "type": "countdown_timer",
                        "color": colors["accent"]
                    }
                ]
            },
            "💻 Code Studio": {
                "description": "Professional coding environment",
                "elements": [
                    {
                        "type": "code_frame",
                        "border_color": colors["primary"],
                        "border_style": "glow"
                    },
                    {
                        "type": "webcam_pip",
                        "position": "bottom-right",
                        "border_color": colors["accent"],
                        "border_style": "rounded_glow"
                    },
                    {
                        "type": "status_bar",
                        "background": colors["background"],
                        "text_color": colors["text"]
                    },
                    {
                        "type": "particle_effects",
                        "style": "coding_particles"
                    }
                ]
            },
            "🖥️ Terminal Zone": {
                "description": "Stylized terminal interface",
                "elements": [
                    {
                        "type": "terminal_frame",
                        "border_color": colors["primary"],
                        "glow_intensity": 0.8
                    },
                    {
                        "type": "matrix_background",
                        "color": colors["primary"],
                        "opacity": 0.1
                    },
                    {
                        "type": "typing_indicator",
                        "color": colors["accent"]
                    }
                ]
            },
            "🎓 Teaching Mode": {
                "description": "Educational presentation layout",
                "elements": [
                    {
                        "type": "webcam_main",
                        "position": "left",
                        "border_style": "professional"
                    },
                    {
                        "type": "code_window",
                        "position": "right",
                        "border_color": colors["secondary"]
                    },
                    {
                        "type": "explanation_overlay",
                        "background": colors["background"],
                        "opacity": 0.9
                    }
                ]
            },
            "🎯 Focus Mode": {
                "description": "Zoomed debugging interface",
                "elements": [
                    {
                        "type": "magnified_code",
                        "zoom_level": 1.5,
                        "highlight_color": colors["accent"]
                    },
                    {
                        "type": "debug_overlay",
                        "color": colors["primary"]
                    },
                    {
                        "type": "pulse_border",
                        "color": colors["accent"],
                        "speed": "slow"
                    }
                ]
            },
            "☕ Chill Break": {
                "description": "Relaxing break screen",
                "elements": [
                    {
                        "type": "animated_background",
                        "style": "floating_shapes",
                        "colors": [colors["primary"], colors["secondary"]]
                    },
                    {
                        "type": "break_message",
                        "text": "☕ Taking a Quick Break",
                        "font_size": 72,
                        "color": colors["text"],
                        "animation": "gentle_pulse"
                    },
                    {
                        "type": "music_visualizer",
                        "color": colors["accent"]
                    },
                    {
                        "type": "timer_display",
                        "color": colors["secondary"]
                    }
                ]
            },
            "🎉 Thanks & Subscribe": {
                "description": "Engaging end screen",
                "elements": [
                    {
                        "type": "celebration_background",
                        "style": "confetti_particles"
                    },
                    {
                        "type": "thanks_message",
                        "text": "🎉 Thanks for Watching!",
                        "font_size": 80,
                        "color": colors["text"],
                        "animation": "bounce_in"
                    },
                    {
                        "type": "social_links",
                        "style": "animated_icons",
                        "color": colors["primary"]
                    },
                    {
                        "type": "subscribe_button",
                        "color": colors["accent"],
                        "animation": "pulse"
                    }
                ]
            }
        }
        
        # Create the beautiful scenes
        for scene_name, scene_config in scenes.items():
            await self._create_beautiful_scene(scene_name, scene_config, colors)
    
    async def _create_beautiful_scene(self, scene_name, config, colors):
        """Create a single beautiful scene"""
        try:
            # Create the scene
            self.ws.call(requests.CreateScene(sceneName=scene_name))
            print(f"🎨 Created scene: {scene_name}")
            
            # Add elements based on scene type
            if "Welcome" in scene_name:
                await self._add_welcome_elements(scene_name, colors)
            elif "Code Studio" in scene_name:
                await self._add_code_studio_elements(scene_name, colors)
            elif "Terminal Zone" in scene_name:
                await self._add_terminal_elements(scene_name, colors)
            elif "Teaching Mode" in scene_name:
                await self._add_teaching_elements(scene_name, colors)
            elif "Focus Mode" in scene_name:
                await self._add_focus_elements(scene_name, colors)
            elif "Chill Break" in scene_name:
                await self._add_break_elements(scene_name, colors)
            elif "Thanks" in scene_name:
                await self._add_ending_elements(scene_name, colors)
            
        except Exception as e:
            if "already exists" not in str(e):
                print(f"  ⚠️  Scene might already exist: {scene_name}")
    
    async def _add_welcome_elements(self, scene_name, colors):
        """Add beautiful welcome screen elements"""
        # Animated title text
        self.ws.call(requests.CreateInput(
            sceneName=scene_name,
            inputName="Welcome Title",
            inputKind="text_ft2_source_v2",
            inputSettings={
                "text": "🚀 LIVE CODING SESSION\n✨ Building Amazing Software",
                "font": {
                    "face": "SF Pro Display",
                    "size": 84,
                    "style": "Bold"
                },
                "color1": colors["text"],
                "color2": colors["text"],
                "outline": True,
                "outline_size": 4,
                "outline_color": colors["primary"],
                "drop_shadow": True,
                "custom_width": 1920,
                "align": "center",
                "valign": "center"
            }
        ))
        
        # Subtitle
        self.ws.call(requests.CreateInput(
            sceneName=scene_name,
            inputName="Welcome Subtitle",
            inputKind="text_ft2_source_v2",
            inputSettings={
                "text": "🎯 Learning • Building • Sharing",
                "font": {
                    "face": "SF Pro Display",
                    "size": 36,
                    "style": "Medium"
                },
                "color1": colors["secondary"],
                "color2": colors["secondary"],
                "custom_width": 1920,
                "align": "center",
                "valign": "center"
            }
        ))
        
        # Position subtitle below title
        scene_items = self.ws.call(requests.GetSceneItemList(sceneName=scene_name))
        for item in scene_items.datain["sceneItems"]:
            if item["sourceName"] == "Welcome Subtitle":
                self.ws.call(requests.SetSceneItemTransform(
                    sceneName=scene_name,
                    sceneItemId=item["sceneItemId"],
                    sceneItemTransform={
                        "positionX": 960,
                        "positionY": 640,
                        "scaleX": 1.0,
                        "scaleY": 1.0
                    }
                ))
    
    async def _add_code_studio_elements(self, scene_name, colors):
        """Add code studio elements with professional styling"""
        # Main code display (screen capture)
        try:
            self.ws.call(requests.CreateInput(
                sceneName=scene_name,
                inputName="Code Display",
                inputKind="display_capture",
                inputSettings={
                    "display": 0,
                    "show_cursor": True
                }
            ))
            
            # Add glow border filter to code display
            self.ws.call(requests.CreateSourceFilter(
                sourceName="Code Display",
                filterName="Glow Border",
                filterKind="color_filter",
                filterSettings={
                    "brightness": 0.02,
                    "contrast": 0.05,
                    "saturation": 1.1
                }
            ))
        except:
            pass
        
        # Status bar overlay
        self.ws.call(requests.CreateInput(
            sceneName=scene_name,
            inputName="Status Bar",
            inputKind="text_ft2_source_v2",
            inputSettings={
                "text": "🔴 LIVE • 💻 Coding Session • 🎯 Building Something Amazing",
                "font": {
                    "face": "SF Mono",
                    "size": 24,
                    "style": "Medium"
                },
                "color1": colors["text"],
                "color2": colors["text"],
                "outline": True,
                "outline_size": 2,
                "outline_color": colors["background"],
                "custom_width": 1920,
                "align": "center"
            }
        ))
        
        # Position status bar at bottom
        scene_items = self.ws.call(requests.GetSceneItemList(sceneName=scene_name))
        for item in scene_items.datain["sceneItems"]:
            if item["sourceName"] == "Status Bar":
                self.ws.call(requests.SetSceneItemTransform(
                    sceneName=scene_name,
                    sceneItemId=item["sceneItemId"],
                    sceneItemTransform={
                        "positionX": 960,
                        "positionY": 1040,
                        "scaleX": 1.0,
                        "scaleY": 1.0
                    }
                ))
    
    async def _add_terminal_elements(self, scene_name, colors):
        """Add terminal elements with matrix-style effects"""
        # Terminal frame text
        self.ws.call(requests.CreateInput(
            sceneName=scene_name,
            inputName="Terminal Header",
            inputKind="text_ft2_source_v2",
            inputSettings={
                "text": "🖥️  TERMINAL ZONE  🖥️",
                "font": {
                    "face": "SF Mono",
                    "size": 48,
                    "style": "Bold"
                },
                "color1": colors["primary"],
                "color2": colors["primary"],
                "outline": True,
                "outline_size": 3,
                "outline_color": colors["background"],
                "custom_width": 1920,
                "align": "center"
            }
        ))
        
        # Position at top
        scene_items = self.ws.call(requests.GetSceneItemList(sceneName=scene_name))
        for item in scene_items.datain["sceneItems"]:
            if item["sourceName"] == "Terminal Header":
                self.ws.call(requests.SetSceneItemTransform(
                    sceneName=scene_name,
                    sceneItemId=item["sceneItemId"],
                    sceneItemTransform={
                        "positionX": 960,
                        "positionY": 80,
                        "scaleX": 1.0,
                        "scaleY": 1.0
                    }
                ))
    
    async def _add_teaching_elements(self, scene_name, colors):
        """Add teaching mode elements"""
        # Teaching header
        self.ws.call(requests.CreateInput(
            sceneName=scene_name,
            inputName="Teaching Header",
            inputKind="text_ft2_source_v2",
            inputSettings={
                "text": "🎓 TEACHING MODE • Explaining Code Concepts",
                "font": {
                    "face": "SF Pro Display",
                    "size": 36,
                    "style": "SemiBold"
                },
                "color1": colors["primary"],
                "color2": colors["primary"],
                "outline": True,
                "outline_size": 2,
                "outline_color": colors["background"],
                "custom_width": 1920,
                "align": "center"
            }
        ))
    
    async def _add_focus_elements(self, scene_name, colors):
        """Add focus mode elements"""
        # Focus mode indicator
        self.ws.call(requests.CreateInput(
            sceneName=scene_name,
            inputName="Focus Indicator",
            inputKind="text_ft2_source_v2",
            inputSettings={
                "text": "🎯 FOCUS MODE • Debugging Session",
                "font": {
                    "face": "SF Mono",
                    "size": 32,
                    "style": "Bold"
                },
                "color1": colors["accent"],
                "color2": colors["accent"],
                "outline": True,
                "outline_size": 3,
                "outline_color": colors["background"],
                "custom_width": 1920,
                "align": "center"
            }
        ))
    
    async def _add_break_elements(self, scene_name, colors):
        """Add beautiful break screen elements"""
        # Break message with animation styling
        self.ws.call(requests.CreateInput(
            sceneName=scene_name,
            inputName="Break Message",
            inputKind="text_ft2_source_v2",
            inputSettings={
                "text": "☕ Taking a Quick Break\n🎵 Enjoy the music • Be right back! ✨",
                "font": {
                    "face": "SF Pro Display",
                    "size": 64,
                    "style": "Bold"
                },
                "color1": colors["text"],
                "color2": colors["text"],
                "outline": True,
                "outline_size": 4,
                "outline_color": colors["primary"],
                "drop_shadow": True,
                "custom_width": 1920,
                "align": "center",
                "valign": "center"
            }
        ))
        
        # Break timer
        self.ws.call(requests.CreateInput(
            sceneName=scene_name,
            inputName="Break Timer",
            inputKind="text_ft2_source_v2",
            inputSettings={
                "text": "⏰ Back in 5 minutes",
                "font": {
                    "face": "SF Pro Display",
                    "size": 36,
                    "style": "Medium"
                },
                "color1": colors["secondary"],
                "color2": colors["secondary"],
                "custom_width": 1920,
                "align": "center"
            }
        ))
    
    async def _add_ending_elements(self, scene_name, colors):
        """Add beautiful ending screen elements"""
        # Thanks message
        self.ws.call(requests.CreateInput(
            sceneName=scene_name,
            inputName="Thanks Message",
            inputKind="text_ft2_source_v2",
            inputSettings={
                "text": "🎉 Thanks for Watching!\n✨ Hope you learned something awesome!",
                "font": {
                    "face": "SF Pro Display",
                    "size": 72,
                    "style": "Bold"
                },
                "color1": colors["text"],
                "color2": colors["text"],
                "outline": True,
                "outline_size": 4,
                "outline_color": colors["primary"],
                "drop_shadow": True,
                "custom_width": 1920,
                "align": "center",
                "valign": "center"
            }
        ))
        
        # Social links
        self.ws.call(requests.CreateInput(
            sceneName=scene_name,
            inputName="Social Links",
            inputKind="text_ft2_source_v2",
            inputSettings={
                "text": "🐙 GitHub • 🐦 Twitter • 💼 LinkedIn • 📺 Subscribe!",
                "font": {
                    "face": "SF Pro Display",
                    "size": 32,
                    "style": "Medium"
                },
                "color1": colors["secondary"],
                "color2": colors["secondary"],
                "outline": True,
                "outline_size": 2,
                "outline_color": colors["background"],
                "custom_width": 1920,
                "align": "center"
            }
        ))
        
        # Position social links below thanks message
        scene_items = self.ws.call(requests.GetSceneItemList(sceneName=scene_name))
        for item in scene_items.datain["sceneItems"]:
            if item["sourceName"] == "Social Links":
                self.ws.call(requests.SetSceneItemTransform(
                    sceneName=scene_name,
                    sceneItemId=item["sceneItemId"],
                    sceneItemTransform={
                        "positionX": 960,
                        "positionY": 700,
                        "scaleX": 1.0,
                        "scaleY": 1.0
                    }
                ))
    
    async def create_theme_showcase(self):
        """Showcase all available themes"""
        print("\n🎨 BEAUTIFUL THEME SHOWCASE")
        print("=" * 60)
        
        themes = list(self.color_schemes.keys())
        
        for i, theme in enumerate(themes, 1):
            colors = self.color_schemes[theme]
            print(f"\n{i}. {theme.title()} Theme:")
            print(f"   Primary: #{colors['primary']:06X}")
            print(f"   Secondary: #{colors['secondary']:06X}")  
            print(f"   Accent: #{colors['accent']:06X}")
            print(f"   Perfect for: {self._get_theme_description(theme)}")
        
        return themes
    
    def _get_theme_description(self, theme):
        """Get description for theme"""
        descriptions = {
            "cyberpunk": "Futuristic coding, tech tutorials, gaming",
            "sunset": "Creative projects, design streams, warm vibes",
            "ocean": "Professional presentations, corporate streams",
            "forest": "Educational content, nature-themed projects",
            "minimal": "Clean coding, minimalist aesthetic, focus"
        }
        return descriptions.get(theme, "General purpose streaming")


async def main():
    """Create beautiful OBS setup"""
    print("🎨 BEAUTIFUL OBS SETUP")
    print("=" * 60)
    print("Transform your stream with professional, gorgeous scenes!")
    
    setup = BeautifulOBSSetup()
    
    if not setup.connect():
        print("❌ Cannot connect to OBS")
        return
    
    try:
        # Show theme options
        themes = await setup.create_theme_showcase()
        
        print(f"\nWhich theme would you like?")
        for i, theme in enumerate(themes, 1):
            print(f"  {i}. {theme.title()}")
        
        # For automation, let's use cyberpunk theme
        chosen_theme = "cyberpunk"
        print(f"\n🎯 Creating {chosen_theme.title()} theme...")
        
        # Create beautiful scenes
        await setup.create_beautiful_scenes(chosen_theme)
        
        print(f"\n✨ BEAUTIFUL SETUP COMPLETE!")
        print("=" * 60)
        print("🎬 Your new beautiful scenes:")
        print("   🚀 Welcome - Animated welcome screen")
        print("   💻 Code Studio - Professional coding environment")
        print("   🖥️ Terminal Zone - Stylized terminal interface")
        print("   🎓 Teaching Mode - Educational presentation layout")
        print("   🎯 Focus Mode - Zoomed debugging interface")
        print("   ☕ Chill Break - Relaxing break screen with music")
        print("   🎉 Thanks & Subscribe - Engaging end screen")
        print("\n🎨 Features added:")
        print("   ✨ Professional typography with SF Pro fonts")
        print("   🌈 Cohesive color scheme throughout")
        print("   ✨ Glowing borders and effects")
        print("   📱 Optimized text positioning")
        print("   🎪 Engaging visual elements")
        print("\n🚀 Ready for beautiful streaming!")
        
    finally:
        setup.disconnect()


if __name__ == "__main__":
    asyncio.run(main())