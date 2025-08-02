"""
Comprehensive test suite for the Event Sourcing system.

Tests domain events, event store, CQRS, projections, and time-travel debugging.
"""

import asyncio
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from uuid import UUID, uuid4

import pytest

from obs_agent.events.cqrs import (
    Command,
    CommandBus,
    GetCurrentScene,
    GetEventHistory,
    Query,
    QueryBus,
    ReadModel,
    StartStream,
    SwitchScene,
)
from obs_agent.events.domain import (
    AutomationRuleExecuted,
    AutomationRuleTriggered,
    DomainEvent,
    EventMetadata,
    EventType,
    SceneCreated,
    SceneSwitched,
    SourceCreated,
    StreamStarted,
    StreamStopped,
)
from obs_agent.events.projections import (
    AutomationProjection,
    PerformanceProjection,
    ProjectionBuilder,
    SceneProjection,
    StreamingProjection,
)
from obs_agent.events.store import EventStore, EventStream, Snapshot
from obs_agent.events.time_travel import TimePoint, TimeTravelDebugger


class TestDomainEvents:
    """Test domain event functionality."""

    def test_event_metadata_creation(self):
        """Test creating event metadata."""
        metadata = EventMetadata()
        assert isinstance(metadata.event_id, UUID)
        assert isinstance(metadata.timestamp, datetime)
        assert metadata.version == 1
        assert metadata.source == "obs_agent"

    def test_event_metadata_with_correlation(self):
        """Test metadata with correlation and causation."""
        correlation_id = uuid4()
        causation_id = uuid4()
        metadata = EventMetadata(correlation_id=correlation_id, causation_id=causation_id, user_id="test_user")
        assert metadata.correlation_id == correlation_id
        assert metadata.causation_id == causation_id
        assert metadata.user_id == "test_user"

    def test_scene_created_event(self):
        """Test SceneCreated event."""
        event = SceneCreated(
            aggregate_id="scene:main", scene_name="Main Scene", scene_settings={"width": 1920, "height": 1080}
        )
        assert event.aggregate_id == "scene:main"
        assert event.scene_name == "Main Scene"
        assert event.scene_settings["width"] == 1920
        assert event.event_type == EventType.SCENE_CREATED

    def test_scene_switched_event(self):
        """Test SceneSwitched event."""
        event = SceneSwitched(
            aggregate_id="obs_system",
            from_scene="Scene1",
            to_scene="Scene2",
            transition_type="fade",
            transition_duration=500,
        )
        assert event.from_scene == "Scene1"
        assert event.to_scene == "Scene2"
        assert event.transition_type == "fade"
        assert event.transition_duration == 500

    def test_event_serialization(self):
        """Test event serialization to JSON."""
        event = StreamStarted(aggregate_id="stream", stream_settings={"bitrate": 5000}, service="twitch")
        json_str = event.to_json()
        data = json.loads(json_str)

        assert data["event_type"] == "stream.started"
        assert data["aggregate_id"] == "stream"
        assert data["data"]["service"] == "twitch"
        assert "metadata" in data

    def test_event_deserialization(self):
        """Test event deserialization from dict."""
        original = SceneCreated(aggregate_id="scene:test", scene_name="Test Scene")
        dict_data = original.to_dict()

        reconstructed = DomainEvent.from_dict(dict_data)
        assert isinstance(reconstructed, SceneCreated)
        assert reconstructed.aggregate_id == "scene:test"
        assert reconstructed.scene_name == "Test Scene"


class TestEventStore:
    """Test event store functionality."""

    @pytest.fixture
    def event_store(self):
        """Create a temporary event store."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = EventStore(db_path=Path(tmpdir) / "test_events.db")
            yield store
            store.close()  # Close store before cleanup

    def test_append_and_retrieve_events(self, event_store):
        """Test appending and retrieving events."""
        event1 = SceneCreated(aggregate_id="scene:1", scene_name="Scene 1")
        event2 = SceneSwitched(aggregate_id="obs_system", from_scene="Scene 1", to_scene="Scene 2")

        event_store.append(event1)
        event_store.append(event2)

        # Retrieve by aggregate
        scene_events = event_store.get_events("scene:1")
        assert len(scene_events) == 1
        assert scene_events[0].scene_name == "Scene 1"

        system_events = event_store.get_events("obs_system")
        assert len(system_events) == 1
        assert system_events[0].to_scene == "Scene 2"

    def test_get_events_by_type(self, event_store):
        """Test retrieving events by type."""
        for i in range(3):
            event_store.append(SceneCreated(aggregate_id=f"scene:{i}", scene_name=f"Scene {i}"))

        event_store.append(StreamStarted(aggregate_id="stream", service="youtube"))

        scene_events = event_store.get_events_by_type(EventType.SCENE_CREATED)
        assert len(scene_events) == 3

        stream_events = event_store.get_events_by_type(EventType.STREAM_STARTED)
        assert len(stream_events) == 1

    def test_replay_events_with_filters(self, event_store):
        """Test replaying events with various filters."""
        now = datetime.utcnow()
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)

        # Add events with specific timestamps
        event1 = SceneCreated(aggregate_id="scene:1", metadata=EventMetadata(timestamp=past), scene_name="Old Scene")
        event2 = SceneCreated(aggregate_id="scene:2", metadata=EventMetadata(timestamp=now), scene_name="Current Scene")

        event_store.append(event1)
        event_store.append(event2)

        # Replay all
        all_events = event_store.replay_events()
        assert len(all_events) == 2

        # Replay since timestamp
        recent_events = event_store.replay_events(since=now - timedelta(minutes=30))
        assert len(recent_events) == 1
        assert recent_events[0].scene_name == "Current Scene"

    def test_snapshots(self, event_store):
        """Test snapshot functionality."""
        snapshot = Snapshot("test_agg", version=10, timestamp=datetime.utcnow(), state={"counter": 42, "name": "test"})

        event_store.save_snapshot(snapshot)

        retrieved = event_store.get_latest_snapshot("test_agg")
        assert retrieved is not None
        assert retrieved.version == 10
        assert retrieved.state["counter"] == 42

    def test_event_subscription(self, event_store):
        """Test event subscription mechanism."""
        received_events = []

        def handler(event):
            received_events.append(event)

        unsubscribe = event_store.subscribe(handler)

        event = SceneCreated(aggregate_id="scene:test", scene_name="Test Scene")
        event_store.append(event)

        assert len(received_events) == 1
        assert received_events[0].scene_name == "Test Scene"

        # Unsubscribe and verify no more events
        unsubscribe()
        event2 = SceneCreated(aggregate_id="scene:test2", scene_name="Test Scene 2")
        event_store.append(event2)
        assert len(received_events) == 1

    def test_correlation_chain(self, event_store):
        """Test getting correlation chain."""
        correlation_id = uuid4()

        for i in range(3):
            event = SceneCreated(
                aggregate_id=f"scene:{i}",
                metadata=EventMetadata(correlation_id=correlation_id),
                scene_name=f"Scene {i}",
            )
            event_store.append(event)

        # Add unrelated event
        event_store.append(SceneCreated(aggregate_id="scene:other", scene_name="Other Scene"))

        chain = event_store.get_correlation_chain(correlation_id)
        assert len(chain) == 3
        assert all(e.metadata.correlation_id == correlation_id for e in chain)


class TestCQRS:
    """Test CQRS implementation."""

    @pytest.fixture
    def setup_cqrs(self):
        """Set up CQRS components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            event_store = EventStore(db_path=Path(tmpdir) / "test_events.db")
            command_bus = CommandBus(event_store)
            read_model = ReadModel(event_store)
            query_bus = QueryBus(event_store, read_model)
            yield event_store, command_bus, query_bus, read_model
            event_store.close()  # Close store before cleanup

    @pytest.mark.asyncio
    async def test_switch_scene_command(self, setup_cqrs):
        """Test switching scene via command."""
        event_store, command_bus, query_bus, read_model = setup_cqrs

        # Send switch scene command
        command = SwitchScene(to_scene="New Scene", transition_type="cut")
        await command_bus.send(command)

        # Verify event was stored
        events = event_store.get_events("obs_system")
        assert len(events) == 1
        assert events[0].to_scene == "New Scene"

        # Verify read model updated
        assert read_model.get_current_scene() == "New Scene"

    @pytest.mark.asyncio
    async def test_start_stream_command(self, setup_cqrs):
        """Test starting stream via command."""
        event_store, command_bus, query_bus, read_model = setup_cqrs

        command = StartStream(stream_settings={"bitrate": 6000}, service="twitch")
        await command_bus.send(command)

        events = event_store.get_events("stream")
        assert len(events) == 1
        assert events[0].service == "twitch"
        assert read_model.is_streaming()

    @pytest.mark.asyncio
    async def test_get_current_scene_query(self, setup_cqrs):
        """Test querying current scene."""
        event_store, command_bus, query_bus, read_model = setup_cqrs

        # Set up initial state
        await command_bus.send(SwitchScene(to_scene="Test Scene"))

        # Query current scene
        query = GetCurrentScene()
        result = await query_bus.send(query)
        assert result == "Test Scene"

    @pytest.mark.asyncio
    async def test_get_event_history_query(self, setup_cqrs):
        """Test querying event history."""
        event_store, command_bus, query_bus, read_model = setup_cqrs

        # Create some events
        for i in range(3):
            await command_bus.send(SwitchScene(to_scene=f"Scene {i}"))

        # Query history
        query = GetEventHistory(aggregate_id="obs_system", limit=2)
        history = await query_bus.send(query)

        assert len(history) == 2
        assert history[0]["data"]["to_scene"] == "Scene 0"

    @pytest.mark.asyncio
    async def test_command_with_correlation(self, setup_cqrs):
        """Test command with correlation ID."""
        event_store, command_bus, query_bus, read_model = setup_cqrs

        correlation_id = uuid4()
        command = SwitchScene(to_scene="Correlated Scene", correlation_id=correlation_id, user_id="test_user")
        await command_bus.send(command)

        events = event_store.get_events("obs_system")
        assert events[0].metadata.correlation_id == correlation_id
        assert events[0].metadata.user_id == "test_user"


class TestProjections:
    """Test event projections."""

    @pytest.fixture
    def projection_setup(self):
        """Set up projections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            event_store = EventStore(db_path=Path(tmpdir) / "test_events.db")
            builder = ProjectionBuilder(event_store)
            yield event_store, builder
            event_store.close()  # Close store before cleanup

    def test_scene_projection(self, projection_setup):
        """Test scene projection."""
        event_store, builder = projection_setup

        # Add scene events
        event_store.append(SceneCreated(aggregate_id="scene:1", scene_name="Scene 1"))
        event_store.append(SceneSwitched(aggregate_id="obs_system", from_scene="Unknown", to_scene="Scene 1"))
        event_store.append(SceneCreated(aggregate_id="scene:2", scene_name="Scene 2"))
        event_store.append(SceneSwitched(aggregate_id="obs_system", from_scene="Scene 1", to_scene="Scene 2"))

        # Get scene projection
        projection = builder.get_projection("scenes")
        assert projection is not None

        state = projection.get_state()
        assert state.data["current_scene"] == "Scene 2"
        assert state.data["previous_scene"] == "Scene 1"
        assert "Scene 1" in state.data["scenes"]
        assert "Scene 2" in state.data["scenes"]
        assert state.data["scene_switch_count"] == 2

    def test_streaming_projection(self, projection_setup):
        """Test streaming projection."""
        event_store, builder = projection_setup

        # Add streaming events
        event_store.append(StreamStarted(aggregate_id="stream", service="twitch"))
        event_store.append(
            StreamStopped(
                "stream",
                duration_seconds=3600,
                total_frames=216000,
                dropped_frames=10,
                bytes_sent=1000000000,
            )
        )

        projection = builder.get_projection("streaming")
        state = projection.get_state()

        assert not state.data["is_streaming"]
        assert state.data["stream_count"] == 1
        assert state.data["total_stream_time"] == 3600
        assert state.data["total_frames"] == 216000
        assert state.data["dropped_frames"] == 10

    def test_automation_projection(self, projection_setup):
        """Test automation projection."""
        event_store, builder = projection_setup

        # Add automation events
        event_store.append(
            AutomationRuleTriggered(
                "rule:1",
                rule_id="rule1",
                rule_name="Test Rule",
                trigger_type="scene_change",
                trigger_data={"scene": "Scene1"},
            )
        )
        event_store.append(
            AutomationRuleExecuted(
                "rule:1",
                rule_id="rule1",
                rule_name="Test Rule",
                actions_executed=["switch_scene", "mute_source"],
                execution_time_ms=50.5,
                result={"success": True},
            )
        )

        projection = builder.get_projection("automation")
        state = projection.get_state()

        assert state.data["total_executions"] == 1
        assert len(state.data["recent_executions"]) == 1
        assert state.data["recent_executions"][0]["rule_id"] == "rule1"

    def test_projection_query(self, projection_setup):
        """Test querying projections."""
        event_store, builder = projection_setup

        # Add events
        event_store.append(SceneCreated(aggregate_id="scene:main", scene_name="Main Scene"))
        event_store.append(SceneSwitched(aggregate_id="obs_system", from_scene="Unknown", to_scene="Main Scene"))

        # Query projection
        current_scene = builder.query("scenes", lambda s: s["current_scene"])
        assert current_scene == "Main Scene"

        scene_list = builder.query("scenes", lambda s: s["scenes"])
        assert "Main Scene" in scene_list


class TestTimeTravelDebugger:
    """Test time-travel debugging functionality."""

    @pytest.fixture
    def debugger_setup(self):
        """Set up time-travel debugger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            event_store = EventStore(db_path=Path(tmpdir) / "test_events.db")
            debugger = TimeTravelDebugger(event_store)
            yield event_store, debugger
            event_store.close()  # Close store before cleanup

    def test_start_debug_session(self, debugger_setup):
        """Test starting a debug session."""
        event_store, debugger = debugger_setup

        # Add some events
        for i in range(5):
            event_store.append(SceneCreated(aggregate_id=f"scene:{i}", scene_name=f"Scene {i}"))

        session = debugger.start_session()
        assert session is not None
        assert len(session.events_in_range) == 5

    def test_goto_timestamp(self, debugger_setup):
        """Test jumping to specific timestamp."""
        event_store, debugger = debugger_setup

        now = datetime.utcnow()
        past = now - timedelta(hours=1)

        # Add events at different times
        event1 = SceneCreated(aggregate_id="scene:1", metadata=EventMetadata(timestamp=past), scene_name="Past Scene")
        event2 = SceneSwitched(
            "obs_system",
            metadata=EventMetadata(timestamp=now),
            from_scene="Past Scene",
            to_scene="Current Scene",
        )

        event_store.append(event1)
        event_store.append(event2)

        session = debugger.start_session(start_time=past - timedelta(minutes=10), end_time=now + timedelta(minutes=10))

        # Go to past
        state = debugger.goto(past + timedelta(seconds=1))
        assert len(state["scenes"]) == 1
        assert state["current_scene"] == "Unknown"

        # Go to present
        state = debugger.goto(now + timedelta(seconds=1))
        assert state["current_scene"] == "Current Scene"

    def test_step_forward_backward(self, debugger_setup):
        """Test stepping through events."""
        import time

        event_store, debugger = debugger_setup

        # Add events with small delays to ensure unique timestamps
        for i in range(3):
            event_store.append(SceneCreated(aggregate_id=f"scene:{i}", scene_name=f"Scene {i}"))
            time.sleep(0.001)  # 1ms delay to ensure unique timestamps on all platforms

        session = debugger.start_session()

        # Step forward
        events, state = debugger.step_forward(2)
        assert len(events) == 2
        assert state["event_count"] == 2

        # Step backward
        undone, state = debugger.step_backward(1)
        assert len(undone) == 1
        assert state["event_count"] == 1

    def test_set_breakpoint(self, debugger_setup):
        """Test setting breakpoints."""
        event_store, debugger = debugger_setup

        # Add events
        for i in range(5):
            event_store.append(SceneCreated(aggregate_id=f"scene:{i}", scene_name=f"Scene {i}"))

        event_store.append(StreamStarted(aggregate_id="stream", service="youtube"))

        session = debugger.start_session()

        # Set breakpoint on stream start
        breakpoint = debugger.set_breakpoint(lambda e: e.event_type == EventType.STREAM_STARTED)

        assert breakpoint is not None
        assert breakpoint.event_count == 6

    def test_what_if_scenario(self, debugger_setup):
        """Test what-if scenarios."""
        event_store, debugger = debugger_setup

        # Add events
        event_store.append(SceneCreated(aggregate_id="scene:1", scene_name="Scene 1"))
        event_store.append(SceneSwitched(aggregate_id="obs_system", from_scene="Unknown", to_scene="Scene 1"))

        session = debugger.start_session()

        # Move debugger position to the end to include all events
        import datetime

        debugger.goto(datetime.datetime.utcnow() + datetime.timedelta(seconds=1))

        # What if we switched to a different scene?
        def modify_events(events):
            modified = []
            for event in events:
                if isinstance(event, SceneSwitched):
                    # Replace with alternative scene switch
                    modified.append(
                        SceneSwitched(
                            aggregate_id="obs_system",
                            from_scene="Unknown",
                            to_scene="Alternative Scene",
                            metadata=event.metadata,
                        )
                    )
                else:
                    modified.append(event)
            return modified

        state = debugger.what_if(modify_events)
        # Debug: Check if events were modified correctly
        modified = modify_events(session.events_in_range)
        assert any(
            isinstance(e, SceneSwitched) and e.to_scene == "Alternative Scene" for e in modified
        ), f"No modified SceneSwitched event found. Events: {[type(e).__name__ for e in modified]}"
        assert state["current_scene"] == "Alternative Scene"

    def test_find_event_pattern(self, debugger_setup):
        """Test finding event patterns."""
        event_store, debugger = debugger_setup

        # Create a pattern: scene create -> scene switch
        event_store.append(SceneCreated(aggregate_id="scene:1", scene_name="Scene 1"))
        event_store.append(SceneSwitched(aggregate_id="obs_system", from_scene="Unknown", to_scene="Scene 1"))
        event_store.append(SceneCreated(aggregate_id="scene:2", scene_name="Scene 2"))
        event_store.append(SceneSwitched(aggregate_id="obs_system", from_scene="Scene 1", to_scene="Scene 2"))

        session = debugger.start_session()

        # Find pattern
        pattern = [EventType.SCENE_CREATED, EventType.SCENE_SWITCHED]
        matches = debugger.find_event_pattern(pattern)

        assert len(matches) == 2
        assert matches[0][0].scene_name == "Scene 1"
        assert matches[1][0].scene_name == "Scene 2"

    def test_get_statistics(self, debugger_setup):
        """Test getting debug session statistics."""
        event_store, debugger = debugger_setup

        # Add various events
        for i in range(3):
            event_store.append(SceneCreated(aggregate_id=f"scene:{i}", scene_name=f"Scene {i}"))

        event_store.append(StreamStarted(aggregate_id="stream", service="twitch"))

        session = debugger.start_session()
        stats = debugger.get_statistics()

        assert stats["total_events"] == 4
        assert stats["event_types"]["scene.created"] == 3
        assert stats["event_types"]["stream.started"] == 1
        assert len(stats["most_active_aggregates"]) > 0

    def test_export_session(self, debugger_setup):
        """Test exporting debug session."""
        event_store, debugger = debugger_setup

        # Add events
        event_store.append(SceneCreated(aggregate_id="scene:1", scene_name="Test Scene"))

        session = debugger.start_session()

        # Export as JSON
        export = debugger.export_session("json")
        data = json.loads(export)

        assert "session_id" in data
        assert data["event_count"] == 1
        assert "statistics" in data


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test async operations in the event system."""

    async def test_async_event_streaming(self):
        """Test async event streaming."""
        with tempfile.TemporaryDirectory() as tmpdir:
            event_store = EventStore(db_path=Path(tmpdir) / "test_events.db")
            try:
                # Add events
                for i in range(10):
                    event_store.append(SceneCreated(aggregate_id=f"scene:{i}", scene_name=f"Scene {i}"))

                # Stream events
                batches = []
                async for batch in event_store.stream_events(batch_size=3):
                    batches.append(batch)

                assert len(batches) == 4  # 10 events / 3 per batch = 4 batches
                assert len(batches[0]) == 3
                assert len(batches[-1]) == 1  # Last batch has remainder
            finally:
                event_store.close()  # Close store before cleanup

    async def test_continuous_projection_updates(self):
        """Test continuous projection updates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            event_store = EventStore(db_path=Path(tmpdir) / "test_events.db")
            builder = ProjectionBuilder(event_store)
            try:
                # Start continuous updates
                await builder.start_continuous_update(interval=0.1)

                # Add events
                event_store.append(SceneCreated(aggregate_id="scene:1", scene_name="Dynamic Scene"))

                # Wait for update
                await asyncio.sleep(0.2)

                # Check projection updated
                projection = builder.get_projection("scenes")
                assert "Dynamic Scene" in projection.state["scenes"]

                # Stop updates
                await builder.stop_continuous_update()
            finally:
                event_store.close()  # Close store before cleanup


class TestEventStoreCompaction:
    """Test event store compaction and optimization."""

    def test_compaction_with_snapshots(self):
        """Test compacting old events while keeping snapshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            event_store = EventStore(db_path=Path(tmpdir) / "test_events.db")
            try:
                # Add old events
                old_time = datetime.utcnow() - timedelta(days=7)
                for i in range(10):
                    event = SceneCreated(
                        "scene:old", metadata=EventMetadata(timestamp=old_time), scene_name=f"Old Scene {i}"
                    )
                    event_store.append(event)

                # Create snapshot
                snapshot = Snapshot(
                    "scene:old", version=5, timestamp=old_time + timedelta(hours=1), state={"scene_count": 5}
                )
                event_store.save_snapshot(snapshot)

                # Add recent events
                for i in range(5):
                    event = SceneCreated(aggregate_id="scene:new", scene_name=f"New Scene {i}")
                    event_store.append(event)

                # Compact old events
                cutoff = datetime.utcnow() - timedelta(days=1)
                removed = event_store.compact(before=cutoff, keep_snapshots=True)

                assert removed > 0

                # Verify recent events still exist
                recent_events = event_store.get_events("scene:new")
                assert len(recent_events) == 5
            finally:
                event_store.close()  # Close store before cleanup
