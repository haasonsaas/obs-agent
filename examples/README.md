# OBS Agent Automation Examples

This directory contains comprehensive examples showcasing the powerful **Smart Scene Automation Engine** of OBS Agent. These examples demonstrate real-world automation patterns for streamers, content creators, and anyone using OBS Studio.

## 🚀 Quick Start

### Prerequisites

1. **OBS Studio** with WebSocket server enabled:
   - Open OBS → Tools → obs-websocket Settings
   - Check "Enable WebSocket server"
   - Note the port (default: 4455)

2. **Python 3.9+** with OBS Agent:
   ```bash
   pip install obs-agent
   ```

3. **Basic OBS Setup**:
   - Create scenes: "Main", "BRB", "Starting Soon"
   - Set up audio sources: "Microphone", "Desktop Audio"
   - Optional: Add text sources for dynamic updates

### Run Your First Automation

```bash
# Start with the beginner-friendly tutorial
python examples/automation_getting_started.py

# Try the comprehensive demo
python examples/automation_demos.py

# Set up professional streaming automation
python examples/streaming_setup_automation.py
```

## 📚 Example Files

### 1. `automation_getting_started.py` 
**Perfect for beginners!** 

A step-by-step tutorial that teaches automation basics:
- ✅ Simple event-triggered automation
- ✅ Time-based automation  
- ✅ Using pre-built smart actions
- ✅ Managing automation rules

**What you'll learn:**
- How to react to scene changes
- Microphone mute/unmute automation
- Periodic status updates
- Smart "Be Right Back" system

### 2. `automation_demos.py`
**Comprehensive feature showcase**

Demonstrates all automation engine capabilities:
- 🎯 Event-based triggers (`@when`)
- ⏰ Time-based automation (`@after_delay`, `@every`, `@at_time`)
- 🔧 Action builder patterns
- 🧠 Smart pre-built automations
- ⚙️ Rule management and monitoring

**Advanced features:**
- Complex multi-step workflows
- Audio ducking systems
- Scheduled automations
- Stream/recording management
- Performance monitoring

### 3. `streaming_setup_automation.py`
**Professional streaming automation**

A complete real-world streaming setup:
- 🎬 Stream startup/shutdown sequences
- 🎵 Intelligent audio management
- 📺 Smart scene transitions
- 👥 Viewer engagement features
- 🛡️ Safety and backup systems
- 📊 Performance monitoring

**Professional features:**
- Automatic "Starting Soon" → "Main Stream" → "Stream Ending" flow
- Audio ducking when microphone is active
- Emergency privacy mode
- Recording safety checks
- Hourly stream updates

## 🎯 Automation Patterns

### Event-Based Automation
React to OBS events in real-time:

```python
@agent.automation.when(CurrentProgramSceneChanged)
async def on_scene_change(context):
    scene = context.trigger_event.scene_name
    print(f"Switched to: {scene}")

@agent.automation.when(InputMuteStateChanged, 
                      lambda e: "Mic" in e.input_name)
async def on_mic_toggle(context):
    if context.trigger_event.input_muted:
        print("Microphone muted!")
```

### Time-Based Automation
Automate based on time:

```python
@agent.automation.after_delay(5.0)  # 5 seconds after trigger
async def delayed_action(context):
    await agent.set_scene("BRB")

@agent.automation.every(30.0)  # Every 30 seconds
async def periodic_check(context):
    current_scene = await agent.get_current_scene()
    print(f"Current scene: {current_scene}")

@agent.automation.at_time(hour=9, minute=0)  # Daily at 9 AM
async def morning_setup(context):
    await agent.set_scene("Morning Show")
```

### Action Builder Pattern
Create complex multi-step workflows:

```python
# Build a complex workflow
workflow = await (
    agent.actions
    .scene("Main Stream")           # Switch scene
    .wait(2.0)                      # Wait 2 seconds
    .mute("Microphone", False)      # Unmute mic
    .volume("Music", volume_db=-20) # Lower music
    .text("Status", "🔴 LIVE")     # Update text
    .start_recording()              # Start recording
    .if_streaming(False)            # Only if not streaming
    .start_streaming()              # Start stream
    .build()
)

@agent.automation.when(SomeEvent)
async def complex_automation(context):
    await workflow(context)
```

### Smart Pre-Built Actions
Use intelligent automation patterns:

```python
# Smart BRB system
brb_action = agent.smart_actions.create_brb_automation(
    brb_scene="BRB",
    mic_source="Microphone", 
    delay_seconds=10.0
)

# Audio ducking
ducking_action = agent.smart_actions.create_audio_ducking(
    music_source="Background Music",
    mic_source="Microphone",
    ducked_volume_db=-25.0
)

# Auto-recording with streaming
record_action = agent.smart_actions.create_auto_record_stream()
```

## 🔧 Customization Guide

### Configure for Your Setup

1. **Update Scene Names** in examples:
   ```python
   config = {
       'scenes': {
           'main': 'Your Main Scene Name',
           'brb': 'Your BRB Scene Name',
           # ... adjust to match your OBS scenes
       }
   }
   ```

2. **Update Source Names**:
   ```python
   config = {
       'sources': {
           'microphone': 'Your Mic Source Name',
           'music': 'Your Music Source Name',
           # ... adjust to match your OBS sources
       }
   }
   ```

3. **Adjust Timings**:
   ```python
   config = {
       'timings': {
           'brb_delay': 15.0,  # Wait 15s before BRB
           'return_delay': 3.0,  # Wait 3s before returning
       }
   }
   ```

### Create Custom Automations

```python
@agent.automation.when(YourEvent, your_filter_function)
@agent.automation.description("Your automation description")
@agent.automation.cooldown(5.0)  # Prevent rapid re-triggering
async def your_custom_automation(context):
    # Your automation logic here
    await agent.set_scene("Custom Scene")
    print("Custom automation triggered!")
```

## 📊 Monitoring and Debugging

### View Automation Statistics
```python
stats = agent.get_automation_stats()
print(f"Active rules: {stats['active_rules']}")
print(f"Total executions: {stats['total_executions']}")
print(f"Success rate: {stats['successful_executions'] / stats['total_executions'] * 100:.1f}%")
```

### Check Individual Rules
```python
status = agent.get_automation_rule_status("rule_name")
print(f"Rule state: {status['state']}")
print(f"Execution count: {status['execution_count']}")
print(f"Last execution: {status['last_execution']}")
```

### Enable/Disable Rules
```python
agent.disable_automation_rule("rule_name")  # Temporarily disable
agent.enable_automation_rule("rule_name")   # Re-enable
```

## 🎨 Scene and Source Setup Tips

### Recommended Scene Structure
```
📺 Scenes:
├── Starting Soon       # Pre-stream countdown
├── Main Stream        # Primary content
├── Just Chatting      # Chat-focused scenes  
├── BRB               # Be Right Back
├── Intermission      # Break time
├── Stream Ending     # Post-stream outro
└── Emergency Privacy # Quick privacy mode
```

### Essential Sources
```
🎤 Audio Sources:
├── Microphone        # Your microphone
├── Desktop Audio     # System/game audio
├── Background Music  # Music/ambiance
└── Alert Sounds     # Notification sounds

📝 Text Sources:
├── Stream Title      # Dynamic stream info
├── Current Time      # Live clock
├── Scene Timer       # Time in current scene
├── Follower Count    # Live follower count
└── Stream Status     # "LIVE", "BRB", etc.
```

## 🚀 Advanced Use Cases

### Multi-Platform Streaming
- Automate different scenes for different platforms
- Platform-specific audio settings
- Cross-platform chat integration

### Gaming Automation
- Game-specific scene switching
- Performance-based audio adjustments  
- Automatic highlight recording

### Podcast/Talk Show Automation
- Guest introduction sequences
- Commercial break automation
- Audio level management per speaker

### Educational Content
- Slide advancement automation
- Break reminders
- Student engagement features

## 🔧 Troubleshooting

### Common Issues

1. **"Connection failed"**
   - ✅ Check OBS is running
   - ✅ Enable WebSocket server in OBS
   - ✅ Verify port 4455 is not blocked

2. **"Scene not found"**
   - ✅ Check scene names match exactly (case-sensitive)
   - ✅ Create missing scenes in OBS

3. **"Source not found"** 
   - ✅ Check source names match exactly
   - ✅ Verify sources exist and are active

4. **Automation not triggering**
   - ✅ Check event filters (lambda functions)
   - ✅ Verify automation engine is started
   - ✅ Check rule status with `get_automation_rule_status()`

### Debug Mode
Add debug prints to your automations:

```python
@agent.automation.when(YourEvent)
async def debug_automation(context):
    print(f"🔍 Debug - Event: {context.trigger_event}")
    print(f"🔍 Debug - Time: {context.trigger_time}")
    print(f"🔍 Debug - Variables: {context.variables}")
    # Your automation logic...
```

## 📖 Next Steps

1. **Start Simple**: Begin with `automation_getting_started.py`
2. **Explore Features**: Try `automation_demos.py` for all capabilities  
3. **Go Professional**: Use `streaming_setup_automation.py` as a template
4. **Customize**: Modify examples for your specific setup
5. **Create**: Build your own automation patterns
6. **Share**: Contribute your automations back to the community!

## 🤝 Contributing

Have a cool automation pattern? Found a useful optimization? We'd love to see your contributions!

1. Fork the repository
2. Create your automation example
3. Test thoroughly with different scenarios
4. Submit a pull request with clear documentation

## 📚 Further Reading

- **Core Documentation**: `src/obs_agent/automation.py`
- **Action Patterns**: `src/obs_agent/actions.py`
- **Event Types**: `src/obs_agent/events.py`
- **OBS Agent Guide**: Main README.md

---

**Happy Streaming!** 🎥✨

*The OBS Agent Automation Engine makes professional streaming automation accessible to everyone. From simple scene changes to complex multi-step workflows, automate your stream like a pro!*