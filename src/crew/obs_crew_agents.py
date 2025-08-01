from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
from typing import List, Dict, Any, Optional
from obs_crew_tools import (
    OBSSceneTool,
    OBSAudioTool,
    OBSRecordingTool,
    OBSStreamingTool,
    OBSStatsTool,
    OBSFilterTool,
    OBSSnapshotTool,
)
import os
from dotenv import load_dotenv

load_dotenv()


class OBSStreamCrew(CrewBase):
    """OBS Stream Management Crew"""

    def __init__(self):
        super().__init__()
        # Initialize all tools
        self.scene_tool = OBSSceneTool()
        self.audio_tool = OBSAudioTool()
        self.recording_tool = OBSRecordingTool()
        self.streaming_tool = OBSStreamingTool()
        self.stats_tool = OBSStatsTool()
        self.filter_tool = OBSFilterTool()
        self.snapshot_tool = OBSSnapshotTool()

    @agent
    def stream_director(self) -> Agent:
        """Director agent that manages scenes and overall stream flow"""
        return Agent(
            role="Stream Director",
            goal="Manage scene transitions and ensure smooth stream flow",
            backstory="""You are an experienced stream director who knows when to switch 
            scenes for maximum engagement. You understand pacing, viewer retention, and 
            how to create dynamic content. You monitor scene durations and make decisions 
            about when to transition.""",
            tools=[self.scene_tool, self.snapshot_tool],
            verbose=True,
            allow_delegation=True,
        )

    @agent
    def audio_engineer(self) -> Agent:
        """Audio engineer agent that manages all audio sources"""
        return Agent(
            role="Audio Engineer",
            goal="Maintain optimal audio levels and quality across all sources",
            backstory="""You are a professional audio engineer with years of experience 
            in live production. You ensure all audio sources are balanced, clear, and 
            free from issues like clipping or background noise. You know the ideal levels 
            for different types of content.""",
            tools=[self.audio_tool, self.filter_tool],
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def technical_producer(self) -> Agent:
        """Technical producer that handles recording/streaming and monitors performance"""
        return Agent(
            role="Technical Producer",
            goal="Manage recording/streaming operations and ensure technical quality",
            backstory="""You are a technical producer who ensures broadcasts run smoothly. 
            You monitor system performance, manage recordings, handle streaming settings, 
            and quickly respond to technical issues. You prioritize stream stability and quality.""",
            tools=[self.recording_tool, self.streaming_tool, self.stats_tool],
            verbose=True,
            allow_delegation=True,
        )

    @agent
    def quality_controller(self) -> Agent:
        """Quality control agent that monitors and maintains stream quality"""
        return Agent(
            role="Quality Controller",
            goal="Monitor stream health and proactively prevent quality issues",
            backstory="""You are a quality control specialist who constantly monitors 
            stream metrics. You detect issues like dropped frames, high CPU usage, or 
            network problems before they impact viewers. You recommend adjustments to 
            maintain optimal quality.""",
            tools=[self.stats_tool, self.snapshot_tool],
            verbose=True,
            allow_delegation=True,
        )

    @agent
    def creative_producer(self) -> Agent:
        """Creative producer that manages visual effects and filters"""
        return Agent(
            role="Creative Producer",
            goal="Enhance visual quality with appropriate filters and effects",
            backstory="""You are a creative producer who understands visual storytelling. 
            You apply filters and effects to enhance the viewing experience, such as 
            chroma key for green screens, color correction, and other visual improvements. 
            You balance creativity with performance.""",
            tools=[self.filter_tool, self.scene_tool],
            verbose=True,
            allow_delegation=False,
        )

    @task
    def monitor_stream_health_task(self) -> Task:
        """Continuously monitor stream health and report issues"""
        return Task(
            description="""Monitor the current stream health including:
            1. Check CPU usage and system performance
            2. Monitor dropped frames and rendering issues
            3. Verify audio levels are within acceptable range
            4. Check if recording/streaming is active as expected
            5. Report any issues that need attention
            
            Provide a comprehensive health report and any recommended actions.""",
            expected_output="Stream health report with metrics and recommendations",
            agent=self.quality_controller(),
        )

    @task
    def balance_audio_task(self) -> Task:
        """Balance all audio sources for optimal sound"""
        return Task(
            description="""Analyze and balance all audio sources:
            1. List all audio sources
            2. Check current levels for each source
            3. Adjust levels to optimal range (-20dB to -15dB for most sources)
            4. Apply noise suppression to microphone sources if needed
            5. Ensure no sources are muted unintentionally
            
            Target: Clear, balanced audio without clipping or being too quiet.""",
            expected_output="Audio balance report with adjustments made",
            agent=self.audio_engineer(),
        )

    @task
    def optimize_scene_task(self) -> Task:
        """Optimize current scene for performance and quality"""
        return Task(
            description="""Optimize the current scene:
            1. Identify the current scene and its purpose
            2. Check which filters are applied and their impact
            3. Recommend or apply visual enhancements (if needed)
            4. Ensure scene is appropriate for current content
            5. Switch scenes if current one has been active too long
            
            Balance visual quality with system performance.""",
            expected_output="Scene optimization report with actions taken",
            agent=self.creative_producer(),
        )

    @task
    def manage_recording_task(self) -> Task:
        """Manage recording based on current needs"""
        return Task(
            description="""Manage recording operations:
            1. Check current recording status
            2. Start recording if not already active and needed
            3. Monitor recording health (file size, duration)
            4. Ensure recording settings are optimal
            5. Report recording status and any issues
            
            Ensure high-quality recording without interruptions.""",
            expected_output="Recording management report",
            agent=self.technical_producer(),
        )

    @task
    def coordinate_stream_task(self) -> Task:
        """Coordinate all aspects of the stream"""
        return Task(
            description="""As the stream director, coordinate all aspects:
            1. Review reports from all team members
            2. Make decisions about scene transitions
            3. Ensure content flow is engaging
            4. Coordinate timing of any changes
            5. Provide overall stream status summary
            
            Create a cohesive streaming experience.""",
            expected_output="Stream coordination summary and action plan",
            agent=self.stream_director(),
            context=[self.monitor_stream_health_task(), self.balance_audio_task(), self.optimize_scene_task()],
        )

    @crew
    def streaming_crew(self) -> Crew:
        """Create the streaming management crew"""
        return Crew(
            agents=[
                self.stream_director(),
                self.audio_engineer(),
                self.technical_producer(),
                self.quality_controller(),
                self.creative_producer(),
            ],
            tasks=[
                self.monitor_stream_health_task(),
                self.balance_audio_task(),
                self.optimize_scene_task(),
                self.manage_recording_task(),
                self.coordinate_stream_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )


class PodcastCrew(CrewBase):
    """Specialized crew for podcast recording"""

    def __init__(self):
        super().__init__()
        self.audio_tool = OBSAudioTool()
        self.recording_tool = OBSRecordingTool()
        self.scene_tool = OBSSceneTool()
        self.filter_tool = OBSFilterTool()

    @agent
    def podcast_producer(self) -> Agent:
        """Podcast producer that manages the recording session"""
        return Agent(
            role="Podcast Producer",
            goal="Produce high-quality podcast recordings with perfect audio",
            backstory="""You are an experienced podcast producer who has worked on 
            hundreds of episodes. You know how to set up audio for clarity, manage 
            multiple microphones, and ensure consistent quality throughout the recording.""",
            tools=[self.audio_tool, self.recording_tool, self.scene_tool],
            verbose=True,
        )

    @agent
    def podcast_audio_specialist(self) -> Agent:
        """Specialist focused on podcast audio quality"""
        return Agent(
            role="Podcast Audio Specialist",
            goal="Ensure broadcast-quality audio for podcast recording",
            backstory="""You specialize in podcast audio engineering. You understand 
            the importance of noise suppression, proper compression, and maintaining 
            consistent levels between hosts and guests. You apply professional audio 
            processing to achieve radio-quality sound.""",
            tools=[self.audio_tool, self.filter_tool],
            verbose=True,
        )

    @task
    def setup_podcast_audio_task(self) -> Task:
        """Set up optimal audio for podcast recording"""
        return Task(
            description="""Prepare audio for podcast recording:
            1. Identify all microphone sources
            2. Apply noise suppression to each microphone
            3. Add compression (ratio 6:1, threshold -24dB) to all mics
            4. Balance levels between hosts and guests
            5. Set all microphones to -20dB baseline
            6. Verify no background noise or echo
            
            Goal: Broadcast-quality audio ready for recording.""",
            expected_output="Audio setup report with all optimizations applied",
            agent=self.podcast_audio_specialist(),
        )

    @task
    def manage_podcast_recording_task(self) -> Task:
        """Manage the podcast recording session"""
        return Task(
            description="""Manage podcast recording:
            1. Ensure audio setup is complete
            2. Switch to appropriate scene (Podcast/Interview scene)
            3. Start recording with confirmation
            4. Monitor audio levels during recording
            5. Prepare status report
            
            Deliver professional podcast recording.""",
            expected_output="Podcast recording status and quality report",
            agent=self.podcast_producer(),
            context=[self.setup_podcast_audio_task()],
        )

    @crew
    def podcast_crew(self) -> Crew:
        """Create the podcast recording crew"""
        return Crew(
            agents=[self.podcast_producer(), self.podcast_audio_specialist()],
            tasks=[self.setup_podcast_audio_task(), self.manage_podcast_recording_task()],
            process=Process.sequential,
            verbose=True,
        )


class TutorialCrew(CrewBase):
    """Specialized crew for tutorial/screencast recording"""

    def __init__(self):
        super().__init__()
        self.scene_tool = OBSSceneTool()
        self.recording_tool = OBSRecordingTool()
        self.filter_tool = OBSFilterTool()
        self.audio_tool = OBSAudioTool()

    @agent
    def tutorial_director(self) -> Agent:
        """Director specialized in tutorial content"""
        return Agent(
            role="Tutorial Director",
            goal="Create clear, engaging tutorial recordings",
            backstory="""You are an expert in creating educational content. You understand 
            how to structure tutorials for maximum clarity, when to switch between screen 
            and camera views, and how to maintain viewer engagement while teaching.""",
            tools=[self.scene_tool, self.recording_tool],
            verbose=True,
        )

    @agent
    def tutorial_technician(self) -> Agent:
        """Technical specialist for tutorial setup"""
        return Agent(
            role="Tutorial Technician",
            goal="Ensure technical quality for tutorial recordings",
            backstory="""You specialize in the technical aspects of tutorial creation. 
            You ensure screen recordings are crisp, audio is clear, and any webcam 
            footage is properly set up with good lighting and framing.""",
            tools=[self.filter_tool, self.audio_tool],
            verbose=True,
        )

    @task
    def setup_tutorial_environment_task(self) -> Task:
        """Set up optimal environment for tutorial recording"""
        return Task(
            description="""Prepare for tutorial recording:
            1. Switch to screen recording scene
            2. Ensure microphone audio is clear (-20dB to -18dB)
            3. Apply noise suppression to microphone
            4. If webcam is present, check for proper lighting
            5. Verify screen capture is working properly
            6. Set up any overlay elements (if needed)
            
            Create professional tutorial recording environment.""",
            expected_output="Tutorial environment setup report",
            agent=self.tutorial_technician(),
        )

    @task
    def record_tutorial_task(self) -> Task:
        """Manage tutorial recording session"""
        return Task(
            description="""Execute tutorial recording:
            1. Confirm environment setup is complete
            2. Start recording
            3. Manage scene transitions if needed (screen/camera/both)
            4. Monitor recording quality
            5. Provide recording status updates
            
            Deliver high-quality educational content.""",
            expected_output="Tutorial recording report with file location",
            agent=self.tutorial_director(),
            context=[self.setup_tutorial_environment_task()],
        )

    @crew
    def tutorial_crew(self) -> Crew:
        """Create the tutorial recording crew"""
        return Crew(
            agents=[self.tutorial_director(), self.tutorial_technician()],
            tasks=[self.setup_tutorial_environment_task(), self.record_tutorial_task()],
            process=Process.sequential,
            verbose=True,
        )


# Utility function to run crews
async def run_obs_crew(crew_type: str = "streaming", **kwargs):
    """Run a specific OBS crew"""

    if crew_type == "streaming":
        crew = OBSStreamCrew()
        result = crew.streaming_crew().kickoff(inputs=kwargs)
    elif crew_type == "podcast":
        crew = PodcastCrew()
        result = crew.podcast_crew().kickoff(inputs=kwargs)
    elif crew_type == "tutorial":
        crew = TutorialCrew()
        result = crew.tutorial_crew().kickoff(inputs=kwargs)
    else:
        raise ValueError(f"Unknown crew type: {crew_type}")

    return result


# Example usage
if __name__ == "__main__":
    import asyncio

    # Example: Run streaming crew
    result = asyncio.run(run_obs_crew("streaming"))
    print(result)
