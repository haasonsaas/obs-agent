#!/usr/bin/env python3
"""
Quick launcher for programming livestream setup
"""

import asyncio
import sys
from examples.programming_stream import ProgrammingStreamSetup
from dotenv import load_dotenv

load_dotenv()


async def main():
    print("🚀 OBS Programming Stream Setup")
    print("=" * 50)
    
    # Get language preference
    if len(sys.argv) > 1:
        language = sys.argv[1]
    else:
        print("\nSupported languages:")
        print("- python")
        print("- javascript")
        print("- java")
        print("- go")
        print("- rust")
        language = input("\nChoose language (default: python): ").strip() or "python"
    
    # Quick setup options
    print("\nSetup options:")
    print("1. Quick setup (recommended)")
    print("2. Custom setup")
    print("3. Setup + Start AI streaming")
    
    choice = input("\nSelect option (1-3): ").strip() or "1"
    
    setup = ProgrammingStreamSetup()
    
    if not await setup.connect():
        print("❌ Failed to connect to OBS")
        print("\nPlease ensure:")
        print("1. OBS is running")
        print("2. WebSocket is enabled (Tools → WebSocket Server Settings)")
        print("3. Password in .env matches OBS settings")
        return
    
    try:
        if choice == "1":
            # Quick setup with defaults
            await setup.create_programming_environment(
                language=language,
                theme="dark",
                include_webcam=True,
                terminal_position="bottom"
            )
            
        elif choice == "2":
            # Custom setup
            theme = input("Theme (dark/light): ").strip() or "dark"
            webcam = input("Include webcam? (y/n): ").strip().lower() == "y"
            terminal = input("Terminal position (bottom/right/hidden): ").strip() or "bottom"
            ide = input("IDE name (VS Code/IntelliJ/Vim): ").strip() or "VS Code"
            
            await setup.create_programming_environment(
                language=language,
                theme=theme,
                include_webcam=webcam,
                terminal_position=terminal,
                ide_name=ide
            )
            
        elif choice == "3":
            # Setup + AI streaming
            await setup.create_programming_environment(language=language)
            
            print("\n🤖 Starting AI-assisted streaming...")
            duration = float(input("Stream duration (hours): ") or "2.0")
            await setup.start_intelligent_stream(duration_hours=duration)
        
        # Show quick tips
        print("\n💡 Quick Tips:")
        print("- Scene hotkeys: Set up in OBS Settings → Hotkeys")
        print("- Use '💻 Code Editor' for main coding")
        print("- Switch to '🖥️ Terminal' when running code")
        print("- '💭 Explaining' for teaching moments")
        print("- Take breaks with '☕ Break' scene")
        print("\n🎬 Ready to stream! Good luck with your coding session!")
        
    finally:
        setup.agent.disconnect()


if __name__ == "__main__":
    asyncio.run(main())