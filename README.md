# OBS Agent 🎬🤖

An AI-powered multi-agent system for controlling OBS Studio programmatically. Automate your streaming, recording, and content creation with intelligent agents that work together like a professional production crew.

## 🚀 Features

- **🤖 AI Agents**: Multiple specialized agents (Director, Audio Engineer, Technical Producer) working together
- **🎮 Full OBS Control**: Scene management, source control, recording, streaming, filters, and more
- **🧠 Intelligent Automation**: AI-driven decision making for optimal stream quality and engagement
- **📡 WebSocket API**: Real-time control via OBS WebSocket protocol
- **🎯 Goal-Oriented**: Agents work towards defined objectives (quality, engagement, resource optimization)

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Project Structure](#-project-structure)
- [Usage Examples](#-usage-examples)
- [Programming Livestream Setup](#-programming-livestream)
- [API Reference](#-api-reference)
- [Advanced Features](#-advanced-features)
- [Contributing](#-contributing)

## 🏃 Quick Start

```bash
# Clone the repository
git clone https://github.com/haasonsaas/obs-agent.git
cd obs-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure OBS
# 1. Open OBS Studio
# 2. Tools → WebSocket Server Settings
# 3. Enable WebSocket server
# 4. Set a password (optional)

# Test connection
python tests/test_obs.py
```

## 📦 Installation

### Requirements

- Python 3.7+
- OBS Studio 28.0+ (includes WebSocket server)
- macOS, Windows, or Linux

### Dependencies

```bash
# Core dependencies
pip install obs-websocket-py python-dotenv

# For AI agents (optional)
pip install crewai crewai-tools langchain
```

## 📁 Project Structure

```
obs_agent/
├── src/
│   ├── obs_agent/          # Core OBS control library
│   │   ├── __init__.py
│   │   ├── obs_agent.py    # Basic OBS control
│   │   └── advanced_features.py  # Advanced features
│   ├── crew/               # CrewAI multi-agent system
│   │   ├── __init__.py
│   │   ├── obs_crew_agents.py   # Agent definitions
│   │   └── obs_crew_tools.py    # CrewAI tools
│   └── tools/              # Additional tools
│       └── obs_ai_agent.py       # Autonomous AI agent
├── examples/               # Example scripts
│   ├── programming_stream.py     # Programming livestream setup
│   ├── automation_scripts.py     # Various automations
│   └── demos/              # Demo scripts
├── tests/                  # Test scripts
├── docs/                   # Documentation
└── requirements.txt        # Dependencies
```

## 🎯 Usage Examples

### Basic Control

```python
import asyncio
from src.obs_agent import OBSAgent

async def basic_control():
    # Connect to OBS
    agent = OBSAgent(password="your_password")
    await agent.connect()
    
    # Get scenes
    scenes = await agent.get_scenes()
    print(f"Available scenes: {scenes}")
    
    # Switch scene
    await agent.set_scene("Gaming")
    
    # Start recording
    await agent.start_recording()
    await asyncio.sleep(10)
    output_path = await agent.stop_recording()
    print(f"Recording saved to: {output_path}")
    
    agent.disconnect()

asyncio.run(basic_control())
```

### Multi-Agent Streaming Crew

```python
from src.crew import OBSStreamCrew

# Create a streaming crew
crew = OBSStreamCrew()

# Run autonomous streaming session
result = crew.streaming_crew().kickoff(inputs={
    "stream_goal": "maintain quality and engagement",
    "duration": "2 hours",
    "content_type": "gaming"
})
```

## 💻 Programming Livestream

Set up a complete programming livestream environment with one command:

```python
from examples.programming_stream import ProgrammingStreamSetup

# Create programming stream setup
setup = ProgrammingStreamSetup()

# Configure for your needs
await setup.create_programming_environment(
    language="python",
    theme="dark",
    include_webcam=True,
    terminal_position="bottom"
)

# Start streaming with AI assistance
await setup.start_intelligent_stream()
```

### Features of Programming Stream Setup:

- **📺 Scenes**: Code editor, Terminal, Documentation, Break, Starting Soon
- **🎨 Layouts**: PiP webcam, split screen terminal, documentation view
- **🔧 Filters**: Noise suppression, color correction for readability
- **🤖 AI Features**: 
  - Auto-switch to terminal when running code
  - Focus on errors when they occur
  - Smart scene transitions based on activity
  - Viewer engagement optimization

## 📚 API Reference

### OBSAgent

The core class for controlling OBS.

```python
agent = OBSAgent(host="localhost", port=4455, password="")
```

#### Key Methods

- `connect()` - Connect to OBS WebSocket
- `disconnect()` - Disconnect from OBS
- `get_scenes()` - Get list of scenes
- `set_scene(scene_name)` - Switch to a scene
- `start_recording()` - Start recording
- `stop_recording()` - Stop recording and return file path
- `start_streaming()` - Start streaming
- `stop_streaming()` - Stop streaming
- `create_source(scene, name, kind, settings)` - Add a source
- `set_source_volume(source, volume_db)` - Adjust audio
- `take_screenshot(source, file_path)` - Capture screenshot

### CrewAI Agents

Specialized agents for different production roles:

- **Stream Director**: Manages scenes and content flow
- **Audio Engineer**: Handles all audio sources and levels
- **Technical Producer**: Manages streaming/recording operations
- **Quality Controller**: Monitors performance and health
- **Creative Producer**: Applies filters and visual effects

## 🚀 Advanced Features

### Intelligent Scene Switching
```python
# AI automatically switches scenes based on:
# - Scene staleness (too long on one scene)
# - Viewer engagement metrics
# - Content type detection
# - Optimal pacing for retention
```

### Audio Management
```python
# Automatic audio optimization:
# - Level balancing across sources
# - Noise suppression application
# - Clipping prevention
# - Compression for consistent volume
```

### Stream Health Monitoring
```python
# Real-time monitoring of:
# - CPU usage and optimization
# - Dropped frames detection
# - Network stability
# - Automatic quality adjustment
```

## 🛠️ Configuration

Create a `.env` file in the project root:

```env
OBS_WEBSOCKET_PASSWORD=your_password_here
OBS_WEBSOCKET_HOST=localhost
OBS_WEBSOCKET_PORT=4455
```

## 📖 Documentation

- [OBS Setup Guide](docs/OBS_SETUP_GUIDE.md) - Detailed OBS configuration
- [CrewAI Integration](docs/README_CREW.md) - Multi-agent system details
- [API Documentation](docs/API.md) - Complete API reference

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- OBS Studio team for the excellent WebSocket API
- CrewAI for the multi-agent framework
- The streaming community for inspiration

---

Built with ❤️ by AI agents who love streaming!