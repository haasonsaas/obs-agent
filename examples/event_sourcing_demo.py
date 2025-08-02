#!/usr/bin/env python3
"""
Event Sourcing and Time-Travel Debugging Demo for OBS Agent.

This example demonstrates:
- Event sourcing with complete audit trail
- CQRS command/query separation  
- Time-travel debugging
- Event projections and read models
- What-if scenario analysis
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from obs_agent import OBSAgent, Config
from obs_agent.events import (
    EventSourcingSystem,
    EventSourcingConfig,
    SwitchScene,
    GetCurrentScene,
    GetEventHistory,
)


async def demo_event_sourcing():
    """Demonstrate event sourcing capabilities."""
    
    print("=" * 60)
    print("OBS Agent Event Sourcing & Time-Travel Debugging Demo")
    print("=" * 60)
    
    # Initialize OBS Agent
    config = Config.load()
    agent = OBSAgent(config)
    
    # Initialize event sourcing system
    es_config = EventSourcingConfig(
        db_path=Path.home() / ".obs_agent" / "demo_events.db",
        enable_snapshots=True,
        enable_projections=True,
        enable_time_travel=True
    )
    
    event_system = EventSourcingSystem(agent, es_config)
    await event_system.start()
    
    try:
        # Connect to OBS
        print("\n📡 Connecting to OBS...")
        await agent.connect()
        print("✅ Connected!")
        
        # ========================================
        # 1. Basic Event Sourcing
        # ========================================
        print("\n" + "=" * 40)
        print("1. BASIC EVENT SOURCING")
        print("=" * 40)
        
        # Start a correlation for user interaction
        correlation_id = event_system.start_correlation()
        print(f"\n🔗 Started correlation: {correlation_id}")
        
        # Perform some operations
        scenes = await agent.scenes.get_scene_list()
        print(f"\n📋 Available scenes: {scenes}")
        
        if len(scenes) >= 2:
            # Switch between scenes
            for scene in scenes[:2]:
                print(f"\n🎬 Switching to scene: {scene}")
                await agent.scenes.switch_scene(scene)
                await asyncio.sleep(1)
        
        event_system.end_correlation()
        
        # ========================================
        # 2. Query Event History
        # ========================================
        print("\n" + "=" * 40)
        print("2. QUERY EVENT HISTORY")
        print("=" * 40)
        
        # Query recent events
        history_query = GetEventHistory(
            since=datetime.utcnow() - timedelta(minutes=5),
            limit=10
        )
        recent_events = await event_system.query_bus.send(history_query)
        
        print(f"\n📜 Recent events ({len(recent_events)} total):")
        for event in recent_events:
            print(f"  - {event['event_type']}: {event['aggregate_id']}")
            print(f"    Time: {event['metadata']['timestamp']}")
        
        # ========================================
        # 3. Projections and Read Models
        # ========================================
        print("\n" + "=" * 40)
        print("3. PROJECTIONS & READ MODELS")
        print("=" * 40)
        
        if event_system.projection_builder:
            # Query scene projection
            current_scene = event_system.query_projection("scenes", "current_scene")
            switch_count = event_system.query_projection("scenes", "scene_switch_count")
            most_used = event_system.query_projection("scenes", "most_used_scene")
            
            print(f"\n📊 Scene Statistics:")
            print(f"  Current scene: {current_scene}")
            print(f"  Total switches: {switch_count}")
            print(f"  Most used scene: {most_used}")
            
            # Query performance projection
            event_counts = event_system.query_projection("performance", "event_counts_by_type")
            if event_counts:
                print(f"\n📈 Event Type Distribution:")
                for event_type, count in list(event_counts.items())[:5]:
                    print(f"  {event_type}: {count}")
        
        # ========================================
        # 4. Time-Travel Debugging
        # ========================================
        print("\n" + "=" * 40)
        print("4. TIME-TRAVEL DEBUGGING")
        print("=" * 40)
        
        if event_system.debugger:
            # Start debugging session
            session = event_system.start_debugging(hours_back=1)
            print(f"\n🔍 Started debugging session: {session.session_id}")
            print(f"   Events in range: {len(session.events_in_range)}")
            
            # Step through events
            print("\n⏭️  Stepping forward through events:")
            for _ in range(min(3, len(session.events_in_range))):
                events, state = event_system.debugger.step_forward()
                if events:
                    event = events[0]
                    print(f"  Event: {event.event_type.value}")
                    print(f"  State: Scene={state['current_scene']}, Streaming={state['is_streaming']}")
            
            # Step backward
            print("\n⏮️  Stepping backward:")
            events, state = event_system.debugger.step_backward(2)
            print(f"  Undid {len(events)} events")
            print(f"  State: Scene={state['current_scene']}")
            
            # Set a breakpoint
            def scene_switch_condition(event):
                return event.event_type.value == "scene.switched"
            
            try:
                breakpoint = event_system.debugger.set_breakpoint(scene_switch_condition)
                print(f"\n🔴 Set breakpoint at: {breakpoint}")
            except ValueError:
                print("\n⚠️  No scene switches found for breakpoint")
            
            # Get debugging statistics
            stats = event_system.debugger.get_statistics()
            print(f"\n📊 Debug Session Statistics:")
            print(f"  Total events: {stats['total_events']}")
            print(f"  Event rate: {stats['event_rate_per_second']:.2f} events/sec")
            print(f"  Time span: {stats['time_span']}")
        
        # ========================================
        # 5. What-If Scenarios
        # ========================================
        print("\n" + "=" * 40)
        print("5. WHAT-IF SCENARIO ANALYSIS")
        print("=" * 40)
        
        if event_system.debugger:
            # Run a what-if scenario
            def modify_events(events):
                """What if we had switched to a different scene?"""
                modified = events.copy()
                
                # Find scene switch events and modify them
                for i, event in enumerate(modified):
                    if event.event_type.value == "scene.switched":
                        # Create a modified event
                        from obs_agent.events.domain import SceneSwitched
                        new_event = SceneSwitched(
                            aggregate_id=event.aggregate_id,
                            metadata=event.metadata,
                            from_scene=event.get_event_data()["from_scene"],
                            to_scene="What-If Scene"  # Different scene
                        )
                        modified[i] = new_event
                        break
                
                return modified
            
            what_if_state = event_system.debugger.what_if(modify_events)
            print(f"\n🤔 What-If Analysis:")
            print(f"  Original scene: {event_system.query_projection('scenes', 'current_scene')}")
            print(f"  What-if scene: {what_if_state['current_scene']}")
        
        # ========================================
        # 6. Automation Event Tracking
        # ========================================
        print("\n" + "=" * 40)
        print("6. AUTOMATION EVENT TRACKING")
        print("=" * 40)
        
        # Create and trigger an automation rule
        @agent.automation.when("scene_switched")
        async def track_scene_switch(data):
            """Example automation rule for tracking."""
            print(f"  🤖 Automation triggered: Scene switched to {data.get('scene_name')}")
        
        # Trigger the automation
        if len(scenes) >= 1:
            print(f"\n🎬 Triggering automation by switching scene...")
            await agent.scenes.switch_scene(scenes[0])
            await asyncio.sleep(1)
            
            # Query automation projection
            if event_system.projection_builder:
                total_executions = event_system.query_projection(
                    "automation", "total_executions"
                )
                print(f"\n📊 Automation Statistics:")
                print(f"  Total rule executions: {total_executions}")
        
        # ========================================
        # 7. Event Export
        # ========================================
        print("\n" + "=" * 40)
        print("7. EVENT EXPORT")
        print("=" * 40)
        
        # Export recent events
        export_json = event_system.export_events(
            format="json",
            since=datetime.utcnow() - timedelta(minutes=5)
        )
        
        import json
        export_data = json.loads(export_json)
        print(f"\n💾 Exported {export_data['event_count']} events")
        print(f"   Export size: {len(export_json)} bytes")
        
        # Save to file
        export_path = Path.home() / ".obs_agent" / "event_export.json"
        export_path.write_text(export_json)
        print(f"   Saved to: {export_path}")
        
        # ========================================
        # 8. System Statistics
        # ========================================
        print("\n" + "=" * 40)
        print("8. SYSTEM STATISTICS")
        print("=" * 40)
        
        stats = event_system.get_statistics()
        print(f"\n📊 Event Sourcing Statistics:")
        print(f"  Total events: {stats['total_events']}")
        print(f"  Aggregates: {stats['aggregates']}")
        print(f"  Event types: {stats['event_types']}")
        
        if 'projections' in stats:
            print(f"\n  Projections:")
            for name, version in stats['projections'].items():
                print(f"    {name}: v{version}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        await event_system.stop()
        await agent.disconnect()
        print("\n✅ Demo completed!")


async def demo_advanced_debugging():
    """Demonstrate advanced debugging capabilities."""
    
    print("\n" + "=" * 60)
    print("ADVANCED TIME-TRAVEL DEBUGGING")
    print("=" * 60)
    
    # This would connect to an existing event store with history
    config = Config.load()
    agent = OBSAgent(config)
    
    es_config = EventSourcingConfig(
        db_path=Path.home() / ".obs_agent" / "events.db"  # Use existing DB
    )
    
    event_system = EventSourcingSystem(agent, es_config)
    await event_system.start()
    
    try:
        if event_system.debugger:
            # Start session for last 24 hours
            session = event_system.start_debugging(hours_back=24)
            
            print(f"\n🔍 Analyzing last 24 hours:")
            print(f"   Total events: {len(session.events_in_range)}")
            
            # Find patterns
            from obs_agent.events.domain import EventType
            
            pattern = [
                EventType.SCENE_SWITCHED,
                EventType.STREAM_STARTED
            ]
            
            matches = event_system.debugger.find_event_pattern(
                pattern,
                within=timedelta(seconds=10)
            )
            
            print(f"\n🔎 Found {len(matches)} instances of pattern:")
            print(f"   Scene Switch → Stream Start (within 10 seconds)")
            
            for match in matches[:3]:  # Show first 3
                print(f"\n   Match at {match[0].metadata.timestamp}:")
                for event in match:
                    print(f"     - {event.event_type.value}")
            
            # Analyze causation chains
            if session.events_in_range:
                # Find an automation trigger event
                for event in session.events_in_range:
                    if event.event_type == EventType.AUTOMATION_RULE_TRIGGERED:
                        print(f"\n🔗 Analyzing causation chain for rule trigger:")
                        chain = event_system.debugger.analyze_causation_chain(
                            event.metadata.event_id
                        )
                        print(f"   Caused {len(chain)} downstream events:")
                        for caused_event in chain[:5]:
                            print(f"     → {caused_event.event_type.value}")
                        break
            
            # Export debugging session
            session_export = event_system.debugger.export_session()
            print(f"\n💾 Exported debug session ({len(session_export)} bytes)")
    
    finally:
        await event_system.stop()
        print("\n✅ Advanced debugging completed!")


if __name__ == "__main__":
    print("\n🚀 Starting Event Sourcing Demo...")
    print("\nMake sure OBS is running and WebSocket is enabled!")
    print("WebSocket password should be set in ~/.obs_agent/config.json")
    
    # Run the main demo
    asyncio.run(demo_event_sourcing())
    
    # Optionally run advanced debugging
    # asyncio.run(demo_advanced_debugging())