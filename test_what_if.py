#!/usr/bin/env python3
"""Standalone test for what_if scenario."""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

# Import only the event modules, not the main obs_agent
import importlib

# Direct import without going through obs_agent.__init__
domain_module = importlib.import_module('obs_agent.events.domain')
store_module = importlib.import_module('obs_agent.events.store')
time_travel_module = importlib.import_module('obs_agent.events.time_travel')

SceneCreated = domain_module.SceneCreated
SceneSwitched = domain_module.SceneSwitched
EventStore = store_module.EventStore
TimeTravelDebugger = time_travel_module.TimeTravelDebugger

# Set up the test
with tempfile.TemporaryDirectory() as tmpdir:
    event_store = EventStore(db_path=Path(tmpdir) / 'test_events.db')
    debugger = TimeTravelDebugger(event_store)
    
    # Add events
    event_store.append(SceneCreated(aggregate_id='scene:1', scene_name='Scene 1'))
    event_store.append(SceneSwitched(aggregate_id='obs_system', from_scene='Unknown', to_scene='Scene 1'))
    
    session = debugger.start_session()
    
    print(f"Events in session: {len(session.events_in_range)}")
    for i, event in enumerate(session.events_in_range):
        print(f"  Event {i}: {event.__class__.__name__} - {event}")
    
    # What if we switched to a different scene?
    def modify_events(events):
        print(f"\nModifying {len(events)} events:")
        modified = []
        for i, event in enumerate(events):
            print(f"  Event {i}: {event.__class__.__name__}")
            if isinstance(event, SceneSwitched):
                # Replace with alternative scene switch
                new_event = SceneSwitched(
                    aggregate_id='obs_system',
                    from_scene='Unknown',
                    to_scene='Alternative Scene',
                    metadata=event.metadata
                )
                print(f"    Replacing to_scene: '{event.to_scene}' -> '{new_event.to_scene}'")
                modified.append(new_event)
            else:
                modified.append(event)
        print(f"Modified events count: {len(modified)}")
        return modified
    
    state = debugger.what_if(modify_events)
    print(f'\nFinal state:')
    print(f'  Current scene: {state["current_scene"]}')
    print(f'  Expected: Alternative Scene')
    print(f'  Test passes: {state["current_scene"] == "Alternative Scene"}')