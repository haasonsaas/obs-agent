import asyncio
from crewai import Agent, Task, Crew, Process
from obs_crew_agents import OBSStreamCrew, PodcastCrew, TutorialCrew
from obs_crew_tools import OBSConnection
import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()


async def autonomous_streaming_session():
    """Run a fully autonomous streaming session with the crew"""
    print("🎬 Starting Autonomous Streaming Session")
    print("=" * 50)
    
    # Initialize OBS connection
    conn = OBSConnection()
    obs = await conn.ensure_connected()
    
    # Create streaming crew
    crew = OBSStreamCrew()
    
    # The crew will autonomously:
    # 1. Monitor stream health
    # 2. Balance audio levels
    # 3. Optimize scenes
    # 4. Manage recordings
    # 5. Coordinate all aspects
    
    print("\n🤖 Crew is taking control of your stream...\n")
    
    # Run the crew
    result = crew.streaming_crew().kickoff(inputs={
        "stream_goal": "maintain quality and engagement",
        "duration": "2 hours",
        "content_type": "gaming"
    })
    
    print("\n📊 Streaming Session Results:")
    print(result)
    
    return result


async def automated_podcast_recording():
    """Run an automated podcast recording session"""
    print("🎙️ Starting Automated Podcast Recording")
    print("=" * 50)
    
    # Initialize connection
    conn = OBSConnection()
    obs = await conn.ensure_connected()
    
    # Create podcast crew
    crew = PodcastCrew()
    
    print("\n🤖 Podcast crew is preparing your recording setup...\n")
    
    # Run the crew
    result = crew.podcast_crew().kickoff(inputs={
        "podcast_name": "Tech Talk Weekly",
        "episode_number": "42",
        "hosts": ["Host Microphone", "Guest Microphone"],
        "target_duration": "30 minutes"
    })
    
    print("\n📊 Podcast Recording Results:")
    print(result)
    
    return result


async def automated_tutorial_creation():
    """Create a tutorial with automated setup and recording"""
    print("📚 Starting Automated Tutorial Creation")
    print("=" * 50)
    
    # Initialize connection
    conn = OBSConnection()
    obs = await conn.ensure_connected()
    
    # Create tutorial crew
    crew = TutorialCrew()
    
    print("\n🤖 Tutorial crew is setting up your recording...\n")
    
    # Run the crew
    result = crew.tutorial_crew().kickoff(inputs={
        "tutorial_topic": "Python Programming Basics",
        "include_webcam": True,
        "estimated_duration": "15 minutes"
    })
    
    print("\n📊 Tutorial Recording Results:")
    print(result)
    
    return result


async def emergency_stream_recovery():
    """Demonstrate crew handling stream emergencies"""
    print("🚨 Emergency Stream Recovery Crew")
    print("=" * 50)
    
    # Create a custom emergency crew
    from obs_crew_tools import (
        OBSSceneTool, OBSAudioTool, OBSStreamingTool, 
        OBSStatsTool, OBSFilterTool
    )
    
    # Emergency Response Agent
    emergency_agent = Agent(
        role="Emergency Response Specialist",
        goal="Quickly identify and resolve streaming emergencies",
        backstory="""You are an emergency response specialist for live streams. 
        You can quickly diagnose issues like dropped frames, audio problems, or 
        system overload and take immediate corrective action.""",
        tools=[OBSStatsTool(), OBSAudioTool(), OBSStreamingTool(), OBSSceneTool()],
        verbose=True
    )
    
    # Emergency tasks
    diagnose_task = Task(
        description="""EMERGENCY DIAGNOSTIC:
        1. Check stream health and system stats immediately
        2. Identify all critical issues (dropped frames, CPU usage, audio problems)
        3. List all problems in order of severity
        4. Recommend immediate actions
        
        Time is critical - be concise and action-oriented.""",
        expected_output="Emergency diagnostic report with immediate actions",
        agent=emergency_agent
    )
    
    recovery_task = Task(
        description="""EMERGENCY RECOVERY:
        1. Execute the most critical fixes first
        2. If CPU is high, reduce quality settings
        3. If audio is problematic, fix levels immediately
        4. If frames are dropping, optimize the stream
        5. Switch to a simpler scene if needed
        
        Stabilize the stream as quickly as possible.""",
        expected_output="Recovery actions taken and stream status",
        agent=emergency_agent,
        context=[diagnose_task]
    )
    
    # Create emergency crew
    emergency_crew = Crew(
        agents=[emergency_agent],
        tasks=[diagnose_task, recovery_task],
        process=Process.sequential,
        verbose=True
    )
    
    print("\n🚨 Emergency crew responding to stream issues...\n")
    
    result = emergency_crew.kickoff()
    
    print("\n✅ Emergency Response Complete:")
    print(result)
    
    return result


async def collaborative_production_crew():
    """Advanced crew that simulates a full production team"""
    print("🎭 Collaborative Production Crew")
    print("=" * 50)
    
    from obs_crew_tools import (
        OBSSceneTool, OBSAudioTool, OBSStreamingTool,
        OBSRecordingTool, OBSStatsTool, OBSFilterTool,
        OBSSnapshotTool
    )
    
    # Create specialized agents for a production
    director = Agent(
        role="Live Director",
        goal="Direct the live production for maximum impact",
        backstory="""You are an Emmy-winning live TV director. You make split-second 
        decisions about camera angles, timing, and pacing. You communicate clearly 
        with your team and keep the show running smoothly.""",
        tools=[OBSSceneTool(), OBSSnapshotTool()],
        verbose=True,
        allow_delegation=True
    )
    
    td = Agent(
        role="Technical Director", 
        goal="Execute the director's vision flawlessly",
        backstory="""You are the technical director who makes the director's vision 
        reality. You handle scene transitions, manage the technical flow, and ensure 
        everything happens on cue.""",
        tools=[OBSSceneTool(), OBSStreamingTool(), OBSRecordingTool()],
        verbose=True
    )
    
    audio_a1 = Agent(
        role="A1 Audio Engineer",
        goal="Deliver broadcast-quality audio mix",
        backstory="""You are the A1 (primary audio engineer) responsible for the 
        final audio mix. You balance all sources, apply processing, and ensure 
        viewers hear perfect audio.""",
        tools=[OBSAudioTool(), OBSFilterTool()],
        verbose=True
    )
    
    shader = Agent(
        role="Shader/Video Engineer",
        goal="Ensure optimal video quality and color",
        backstory="""You are the shader who ensures all video sources look their 
        best. You adjust filters, color correction, and visual effects to create 
        a cohesive look.""",
        tools=[OBSFilterTool(), OBSStatsTool()],
        verbose=True
    )
    
    # Production tasks
    pre_show_task = Task(
        description="""PRE-SHOW SETUP:
        1. Director: Review all available scenes and create show rundown
        2. TD: Test all scene transitions
        3. A1: Check and balance all audio sources
        4. Shader: Verify video quality and apply necessary filters
        5. Everyone: Report readiness for show
        
        We go live in 5 minutes!""",
        expected_output="Pre-show checklist completed with all systems go",
        agent=director
    )
    
    live_show_task = Task(
        description="""LIVE SHOW EXECUTION:
        1. Director: Call the shots and manage pacing
        2. TD: Execute scene changes on director's cues
        3. A1: Continuously monitor and adjust audio
        4. Shader: Monitor video quality and make adjustments
        5. Team: Work together to deliver flawless production
        
        It's showtime!""",
        expected_output="Live show execution report",
        agent=director,
        context=[pre_show_task]
    )
    
    # Create production crew
    production_crew = Crew(
        agents=[director, td, audio_a1, shader],
        tasks=[pre_show_task, live_show_task],
        process=Process.hierarchical,
        manager_llm="gpt-4",  # Director leads the crew
        verbose=True
    )
    
    print("\n🎬 Production crew is taking positions...\n")
    
    result = production_crew.kickoff(inputs={
        "show_name": "Tech Conference Keynote",
        "duration": "45 minutes",
        "style": "professional corporate event"
    })
    
    print("\n🎭 Production Complete:")
    print(result)
    
    return result


async def adaptive_content_crew():
    """Crew that adapts to different content types automatically"""
    print("🔄 Adaptive Content Crew")
    print("=" * 50)
    
    # This crew detects content type and adapts its behavior
    crew = OBSStreamCrew()
    
    # Create a content analyzer agent
    analyzer = Agent(
        role="Content Analyzer",
        goal="Identify content type and optimize settings accordingly",
        backstory="""You are an AI that can analyze streaming content and determine 
        the best settings. You recognize gaming, talking head, presentation, and 
        other content types and know how to optimize for each.""",
        tools=[crew.snapshot_tool, crew.stats_tool],
        verbose=True
    )
    
    # Add analyzer to the crew
    analysis_task = Task(
        description="""Analyze current content:
        1. Take a snapshot of current state
        2. Identify content type (gaming, podcast, tutorial, etc.)
        3. Recommend optimal settings for this content
        4. Suggest scene and audio configurations
        
        Be specific about what changes would improve the stream.""",
        expected_output="Content analysis with optimization recommendations",
        agent=analyzer
    )
    
    # Run adaptive analysis
    print("\n🤖 Adaptive crew analyzing your content...\n")
    
    result = await crew.streaming_crew().kickoff(inputs={
        "adaptive_mode": True,
        "auto_optimize": True
    })
    
    print("\n🔄 Adaptive Optimization Complete:")
    print(result)
    
    return result


async def main():
    """Main example runner"""
    print("🎥 OBS CrewAI Examples")
    print("=" * 50)
    print("1. Autonomous Streaming Session")
    print("2. Automated Podcast Recording") 
    print("3. Automated Tutorial Creation")
    print("4. Emergency Stream Recovery")
    print("5. Collaborative Production Crew")
    print("6. Adaptive Content Crew")
    print("=" * 50)
    
    choice = input("\nSelect an example (1-6): ")
    
    examples = {
        "1": autonomous_streaming_session,
        "2": automated_podcast_recording,
        "3": automated_tutorial_creation,
        "4": emergency_stream_recovery,
        "5": collaborative_production_crew,
        "6": adaptive_content_crew
    }
    
    if choice in examples:
        await examples[choice]()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())