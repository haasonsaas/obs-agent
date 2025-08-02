# Installation Guide

## Quick Install

### Core Installation
```bash
pip install -e .
```

### With Chat Intelligence (Recommended)
```bash
pip install -e ".[full]"
```

### Development Installation
```bash
pip install -e ".[dev,full]"
```

## Targeted Installations

### Basic OBS Control Only
```bash
pip install -e .
```

### With CrewAI Support
```bash
pip install -e ".[crew]"
```

### With Chat Intelligence (No AI)
```bash
pip install -e ".[chat]"
```

### With AI Features
```bash
pip install -e ".[ai]"
```

## Dependencies Breakdown

### Core Dependencies (Always Required)
- `obs-websocket-py>=1.0.0` - OBS WebSocket communication
- `asyncio` - Asynchronous programming support
- `typing-extensions>=4.0.0` - Enhanced type hints
- `python-dotenv>=0.19.0` - Environment variable management
- `pydantic>=2.0.0` - Data validation and settings

### Chat Intelligence Dependencies (`[chat]`)
- `aiohttp>=3.8.0` - HTTP client for API calls
- `websockets>=11.0.0` - WebSocket client for real-time connections
- `twitchio>=2.5.0` - Twitch IRC and API integration
- `google-api-python-client>=2.0.0` - YouTube Live Chat API
- `discord.py>=2.3.0` - Discord API integration

### CrewAI Dependencies (`[crew]`)
- `crewai>=0.22.0` - Multi-agent AI framework
- `crewai-tools>=0.1.0` - Tools for CrewAI agents
- `langchain>=0.1.0` - Language model abstraction
- `langchain-openai>=0.0.5` - OpenAI integration for LangChain

### AI/ML Dependencies (`[ai]`)
- `openai>=1.0.0` - OpenAI API client
- `numpy>=1.24.0` - Numerical computing
- `pandas>=2.0.0` - Data analysis and manipulation

### Development Dependencies (`[dev]`)
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async testing support
- `pytest-cov>=4.1.0` - Test coverage
- `black>=23.7.0` - Code formatting
- `isort>=5.12.0` - Import sorting
- `flake8>=6.1.0` - Code linting
- `mypy>=1.4.0` - Static type checking
- `sphinx>=7.1.0` - Documentation generation

## Platform Requirements

### Python Version
- **Minimum**: Python 3.9
- **Recommended**: Python 3.11 or newer

### Operating System
- Windows 10/11 (with OBS Studio)
- macOS 10.15+ (with OBS Studio)
- Linux (Ubuntu 20.04+, with OBS Studio)

### OBS Studio
- **Minimum**: OBS Studio 28.0
- **Recommended**: OBS Studio 30.0+
- **Required**: WebSocket plugin enabled (built-in since v28)

## Verification

### Test Core Installation
```bash
python -c "import obs_agent; print('OBS Agent installed successfully!')"
```

### Test Chat Intelligence
```bash
python -c "from obs_agent.chat_intelligence import ChatIntelligenceService; print('Chat Intelligence ready!')"
```

### Test CrewAI Integration
```bash
python -c "from crew.chat_intelligence_agents import create_chat_intelligence_crew; print('CrewAI integration ready!')"
```

### Run Demo
```bash
obs-chat-demo
# OR
python examples/chat_intelligence_demo.py
```

## Troubleshooting

### Common Issues

#### Import Errors
```
ModuleNotFoundError: No module named 'crewai'
```
**Solution**: Install with full dependencies: `pip install -e ".[full]"`

#### OBS Connection Failed
```
obs.exceptions.ConnectionFailure: Unable to connect to OBS
```
**Solutions**:
1. Start OBS Studio
2. Enable WebSocket server in OBS Tools → WebSocket Server Settings
3. Check host/port/password configuration

#### Authentication Errors
```
HTTP 401: Unauthorized
```
**Solutions**:
1. Check your API tokens in `config/chat_intelligence.env`
2. Verify token permissions/scopes
3. Ensure tokens haven't expired

### Getting Help

1. **Documentation**: Check `docs/` directory
2. **Examples**: See `examples/` directory
3. **Issues**: Report bugs on [GitHub Issues](https://github.com/haasonsaas/obs-agent/issues)
4. **Discussions**: Join [GitHub Discussions](https://github.com/haasonsaas/obs-agent/discussions)

## Next Steps

1. **Configuration**: Copy and edit `config/chat_intelligence.env.example`
2. **OBS Setup**: Follow `docs/OBS_SETUP_GUIDE.md`
3. **Chat Intelligence**: Read `docs/CHAT_INTELLIGENCE.md`
4. **Examples**: Try demos in `examples/` directory