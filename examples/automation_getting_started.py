#!/usr/bin/env python3
"""
Smart Scene Automation - Getting Started Guide

This is a simple introduction to the OBS Agent automation system.
Perfect for beginners who want to get started quickly!

What you'll learn:
1. Basic event-triggered automation
2. Time-based automation
3. Using pre-built smart actions
4. Managing automation rules

Prerequisites:
- OBS Studio running with WebSocket server enabled
- Python 3.9+ with obs-agent installed
"""

import asyncio
import os
import sys

# Add src to path for development
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.obs_agent import OBSAgent
from src.obs_agent.events import InputMuteStateChanged, CurrentProgramSceneChanged


async def getting_started_tutorial():
    """Step-by-step tutorial for automation basics."""
    
    print("🎓 OBS Agent Automation - Getting Started")
    print("=" * 50)
    
    # Step 1: Connect to OBS
    print("\n📡 Step 1: Connecting to OBS...")
    agent = OBSAgent()
    
    try:
        await agent.connect()
        print("✅ Connected successfully!")
        
        # Start the automation engine
        agent.start_automation()
        print("🤖 Automation engine started")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Make sure OBS is running with WebSocket server enabled!")
        print("   Tools → obs-websocket Settings → Enable WebSocket server")
        return
    
    # Step 2: Simple event automation
    print("\n🎬 Step 2: Creating your first automation rule...")
    
    @agent.automation.when(CurrentProgramSceneChanged)
    @agent.automation.description("Welcome message for new users")
    async def welcome_scene_change(context):
        """This function runs whenever you change scenes in OBS!"""
        scene_name = context.trigger_event.scene_name
        print(f"✨ Automation triggered! You switched to: {scene_name}")
    
    print("✅ Created scene change automation")
    print("   💡 Try switching scenes in OBS to see it work!")
    
    # Step 3: Microphone mute automation  
    print("\n🎤 Step 3: Microphone mute automation...")
    
    @agent.automation.when(
        InputMuteStateChanged, 
        lambda event: "Mic" in event.input_name  # Only trigger for microphone
    )
    @agent.automation.description("React to microphone mute changes")
    async def mic_mute_handler(context):
        """This runs when you mute/unmute your microphone!"""
        event = context.trigger_event
        if event.input_muted:
            print("🔇 Microphone muted - you're now silent!")
        else:
            print("🎤 Microphone unmuted - you're back on air!")
    
    print("✅ Created microphone automation")
    print("   💡 Try muting/unmuting your microphone!")
    
    # Step 4: Time-based automation
    print("\n⏰ Step 4: Time-based automation...")
    
    @agent.automation.every(30.0)  # Every 30 seconds
    @agent.automation.description("Periodic greeting")
    async def periodic_greeting(context):
        """This runs every 30 seconds automatically!"""
        current_scene = await agent.get_current_scene()
        print(f"⏰ Periodic check: You're currently on scene '{current_scene}'")
    
    print("✅ Created periodic automation (every 30 seconds)")
    
    # Step 5: Using smart pre-built actions
    print("\n🧠 Step 5: Using smart pre-built automations...")
    
    # This creates a "Be Right Back" system
    brb_action = agent.smart_actions.create_brb_automation(
        brb_scene="BRB",           # Scene to switch to (create this in OBS)
        mic_source="Microphone",   # Your microphone source name
        delay_seconds=5.0          # Wait 5 seconds before switching
    )
    
    @agent.automation.when(
        InputMuteStateChanged,
        lambda e: "Mic" in e.input_name and e.input_muted
    )
    async def activate_brb(context):
        await brb_action(context)
        print("🚶 BRB mode activated - switched to BRB scene!")
    
    print("✅ Created smart BRB automation")
    print("   💡 Mute your mic and wait 5 seconds to see BRB mode!")
    
    # Step 6: Let the automation run
    print("\n🎯 Step 6: Automation is now active!")
    print("-" * 30)
    print("Your automations are running! Try these:")
    print("• Switch between scenes in OBS")
    print("• Mute/unmute your microphone") 
    print("• Wait for periodic messages")
    print("• Create a 'BRB' scene and test BRB mode")
    print("\nPress Ctrl+C when you're done exploring...")
    
    try:
        # Keep running for 5 minutes
        await asyncio.sleep(300)
    except KeyboardInterrupt:
        print("\n⏹️ Stopping automation...")
    
    # Step 7: Show statistics and cleanup
    print("\n📊 Final Statistics:")
    stats = agent.get_automation_stats()
    print(f"• Total rules created: {stats.get('total_rules', 0)}")
    print(f"• Active rules: {stats.get('active_rules', 0)}")
    print(f"• Total executions: {stats.get('total_executions', 0)}")
    print(f"• Successful executions: {stats.get('successful_executions', 0)}")
    
    # Cleanup
    agent.stop_automation()
    await agent.disconnect()
    print("\n🎉 Tutorial completed! You've learned the basics of OBS automation!")


def show_next_steps():
    """Show what users can do next."""
    print("\n🚀 Next Steps:")
    print("-" * 20)
    print("1. 📖 Check out automation_demos.py for advanced examples")
    print("2. 🎨 Create custom scenes (Main, BRB, Gaming, etc.)")
    print("3. 🎤 Set up proper audio sources")
    print("4. 📺 Try the action builder for complex workflows:")
    print("   action = await agent.actions.scene('Main').mute('Mic', True).wait(2.0).build()")
    print("5. ⏰ Experiment with scheduled automations:")
    print("   @agent.automation.at_time(hour=9, minute=0)  # 9 AM daily")
    print("6. 🔧 Build your own custom automation functions!")
    
    print("\n📚 Documentation:")
    print("• Automation Engine: src/obs_agent/automation.py")
    print("• Pre-built Actions: src/obs_agent/actions.py") 
    print("• Event Types: src/obs_agent/events.py")
    
    print("\n💡 Pro Tips:")
    print("• Use descriptive names for your scenes and sources")
    print("• Test automations with simple print statements first")
    print("• Check automation statistics with agent.get_automation_stats()")
    print("• Use agent.get_automation_rule_status('rule_name') to debug")


async def main():
    """Main function."""
    try:
        await getting_started_tutorial()
        show_next_steps()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("\n🆘 Troubleshooting:")
        print("1. Make sure OBS is running")
        print("2. Enable WebSocket server in OBS")
        print("3. Check that port 4455 is not blocked")
        print("4. Verify your Python environment has obs-agent installed")


if __name__ == "__main__":
    asyncio.run(main())