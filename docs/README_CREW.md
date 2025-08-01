# OBS CrewAI Agent System

A sophisticated multi-agent system for managing OBS Studio using CrewAI. This system employs specialized AI agents that work together as a production crew to autonomously manage streaming, recording, and content creation.

## 🤖 What Makes This Agentic?

Unlike simple automation scripts, this CrewAI implementation features:

### 1. **Autonomous Agents with Specialized Roles**
- **Stream Director**: Makes high-level decisions about content flow and scene transitions
- **Audio Engineer**: Continuously monitors and adjusts audio levels across all sources
- **Technical Producer**: Manages streaming/recording operations and technical quality
- **Quality Controller**: Proactively monitors system health and prevents issues
- **Creative Producer**: Applies visual enhancements and manages effects

### 2. **Collaborative Decision Making**
- Agents work together, sharing information and coordinating actions
- Hierarchical and sequential task execution
- Context passing between agents for informed decisions
- Delegation capabilities for complex tasks

### 3. **Goal-Oriented Behavior**
- Each agent has specific goals and backstories that guide their actions
- Agents understand their role in the larger production
- Decision-making based on professional expertise encoded in prompts

### 4. **Intelligent Task Management**
- Tasks are executed based on context and dependencies
- Agents can adapt their behavior based on findings from other agents
- Real-time problem-solving and optimization

## 📁 Project Structure

```
obs_agent/
├── obs_crew_tools.py      # CrewAI tools for OBS control
├── obs_crew_agents.py     # Agent definitions and crews
├── obs_crew_examples.py   # Example implementations
├── requirements_crew.txt  # CrewAI dependencies
└── README_CREW.md        # This file
```

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements_crew.txt
```

### Basic Usage

```python
from obs_crew_agents import OBSStreamCrew

# Create and run a streaming crew
crew = OBSStreamCrew()
result = crew.streaming_crew().kickoff(inputs={
    "stream_goal": "maintain quality and engagement",
    "duration": "2 hours"
})
```

## 🎭 Available Crews

### 1. **OBSStreamCrew**
Full production crew for live streaming with 5 specialized agents working together.

```python
crew = OBSStreamCrew()
result = crew.streaming_crew().kickoff()
```

### 2. **PodcastCrew**
Specialized crew for podcast recording with audio focus.

```python
crew = PodcastCrew()
result = crew.podcast_crew().kickoff(inputs={
    "podcast_name": "My Podcast",
    "hosts": ["Host Mic", "Guest Mic"]
})
```

### 3. **TutorialCrew**
Crew optimized for creating educational content.

```python
crew = TutorialCrew()
result = crew.tutorial_crew().kickoff(inputs={
    "tutorial_topic": "Python Basics",
    "include_webcam": True
})
```

## 🛠️ CrewAI Tools

### Scene Management Tool
```python
scene_tool = OBSSceneTool()
# List scenes: scene_tool.run("list")
# Switch scene: scene_tool.run("Gaming Scene")
```

### Audio Control Tool
```python
audio_tool = OBSAudioTool()
# List audio: audio_tool.run("list", None, None)
# Adjust volume: audio_tool.run("Microphone", -20.0, False)
```

### Recording Control Tool
```python
recording_tool = OBSRecordingTool()
# Start: recording_tool.run("start")
# Stop: recording_tool.run("stop")
# Status: recording_tool.run("status")
```

### Filter Management Tool
```python
filter_tool = OBSFilterTool()
# Add chroma key: filter_tool.run("Webcam", "chroma_key")
# Add noise suppression: filter_tool.run("Mic", "noise_suppression")
```

## 🎬 Example Scenarios

### Autonomous Streaming Session
```python
async def autonomous_stream():
    crew = OBSStreamCrew()
    
    # The crew will:
    # - Monitor stream health continuously
    # - Balance audio automatically
    # - Switch scenes based on engagement
    # - Handle technical issues proactively
    # - Coordinate all aspects seamlessly
    
    result = crew.streaming_crew().kickoff()
```

### Emergency Response Crew
```python
# Custom crew for handling streaming emergencies
emergency_agent = Agent(
    role="Emergency Response Specialist",
    goal="Quickly resolve streaming emergencies",
    tools=[OBSStatsTool(), OBSAudioTool()],
)

emergency_crew = Crew(
    agents=[emergency_agent],
    tasks=[diagnose_task, recovery_task],
    process=Process.sequential
)
```

### Collaborative Production
```python
# Simulates a full TV production crew
production_crew = Crew(
    agents=[director, technical_director, audio_engineer, video_engineer],
    process=Process.hierarchical,
    manager_llm="gpt-4"  # Director leads
)
```

## 🧠 How Agents Make Decisions

### Stream Director Example
```
Role: Stream Director
Goal: Manage scene transitions for maximum engagement

Decision Process:
1. Monitors how long current scene has been active
2. Considers viewer engagement patterns
3. Checks with other agents about system health
4. Decides optimal time for scene transition
5. Coordinates with Technical Producer for smooth switch
```

### Audio Engineer Example
```
Role: Audio Engineer  
Goal: Maintain broadcast-quality audio

Decision Process:
1. Continuously samples audio levels
2. Detects issues (too low, clipping, imbalance)
3. Calculates optimal adjustments
4. Applies corrections gradually
5. Monitors results and fine-tunes
```

## 🔄 Agent Communication Flow

```
Stream Director
    ├── Receives health reports from Quality Controller
    ├── Gets audio status from Audio Engineer
    ├── Coordinates with Technical Producer
    └── Delegates to Creative Producer for effects

Quality Controller
    ├── Monitors all system metrics
    ├── Alerts other agents of issues
    └── Recommends preventive actions

Audio Engineer
    ├── Reports audio status
    └── Executes audio adjustments

Technical Producer
    ├── Manages recording/streaming
    └── Implements technical changes

Creative Producer
    └── Applies visual enhancements
```

## 🎯 Key Differences from Simple Automation

### Traditional Automation:
- Fixed scripts with predefined actions
- No decision-making capability
- Cannot adapt to unexpected situations
- Requires constant human oversight

### CrewAI Agent System:
- Autonomous decision-making based on goals
- Agents collaborate and share context
- Adapts to changing conditions
- Self-monitoring and self-correcting
- Professional expertise encoded in agent personas

## 🔧 Customization

### Creating Custom Agents
```python
custom_agent = Agent(
    role="Your Role",
    goal="Your Goal",
    backstory="Agent's expertise and background",
    tools=[tool1, tool2],
    verbose=True,
    allow_delegation=True
)
```

### Creating Custom Tasks
```python
custom_task = Task(
    description="Detailed task description",
    expected_output="What the task should produce",
    agent=custom_agent,
    context=[dependent_task1, dependent_task2]
)
```

### Creating Custom Crews
```python
custom_crew = Crew(
    agents=[agent1, agent2, agent3],
    tasks=[task1, task2, task3],
    process=Process.sequential,  # or hierarchical
    verbose=True
)
```

## 🚀 Advanced Features

### 1. **Hierarchical Management**
- Director agent can delegate to other agents
- Chain of command for complex productions

### 2. **Context Awareness**
- Agents share findings through task context
- Decisions based on collective intelligence

### 3. **Adaptive Behavior**
- Agents adjust strategies based on content type
- Learn from patterns and optimize over time

### 4. **Emergency Handling**
- Specialized emergency response agents
- Rapid diagnosis and recovery procedures

## 📊 Benefits of CrewAI Approach

1. **Scalability**: Easy to add new agents for new capabilities
2. **Modularity**: Each agent is independent and reusable
3. **Reliability**: Multiple agents provide redundancy
4. **Intelligence**: Collective decision-making improves outcomes
5. **Flexibility**: Crews can be reconfigured for different needs

## 🎮 Use Cases

- **Live Streaming**: Autonomous management of live broadcasts
- **Podcast Production**: Professional audio setup and recording
- **Tutorial Creation**: Optimized settings for educational content
- **Event Coverage**: Multi-camera coordination and switching
- **Emergency Response**: Rapid issue resolution during streams

## 🔗 Integration

The CrewAI OBS system can be integrated with:
- Stream scheduling systems
- Analytics platforms
- Chat monitoring tools
- Social media automation
- Content management systems

This CrewAI implementation transforms OBS Studio into an intelligent, self-managing broadcast system powered by collaborative AI agents.