from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from agents.agent_a.planner import Planner
from agents.agent_b.executor import Executor
from agents.agent_c.monitor import Monitor
from agents.agent_c.task_tracker import TaskTracker
from shared.message_schema import MessageEnvelope, MessageType


@pytest.fixture
def mock_rabbitmq_client():
    with patch("shared.rabbitmq_client.RabbitMQBaseClient") as mock_base:
        mock_instance = MagicMock()
        mock_base.return_value = mock_instance
        yield mock_instance


def test_planner_creates_task(mock_rabbitmq_client):
    planner = Planner()
    # Mock routing/publish
    planner.publish = MagicMock()

    task_id, correlation_id = planner.plan_task(
        total_records=1000, contamination=0.05, random_seed=42, deadline_minutes=10, description="Test vitals run"
    )

    assert task_id is not None
    assert correlation_id is not None
    assert planner.publish.call_count == 1

    # Check that it published TASK_ASSIGNMENT
    args, kwargs = planner.publish.call_args
    routing_key, envelope = args
    assert routing_key == "task.agent-b"
    assert envelope.message_type == MessageType.TASK_ASSIGNMENT
    assert envelope.payload["parameters"]["total_records"] == 1000


def test_executor_handles_task(mock_rabbitmq_client):
    executor = Executor()
    executor.publish = MagicMock()

    # Create a task assignment envelope
    assignment = MessageEnvelope(
        message_id="msg-1",
        sender_id="agent-a",
        receiver_id="agent-b",
        message_type=MessageType.TASK_ASSIGNMENT,
        timestamp=datetime.now(timezone.utc),
        correlation_id="corr-1",
        priority=2,
        routing_key="task.agent-b",
        payload={
            "task_id": "task-1",
            "task_type": "ANOMALY_DETECTION",
            "description": "Test Executor Run",
            "parameters": {"total_records": 100, "contamination": 0.05, "random_seed": 42},
            "deadline": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            "sub_tasks": ["generate_data", "train", "predict", "report"],
        },
    )

    mock_channel = MagicMock()
    mock_method = MagicMock(delivery_tag=1)
    mock_properties = MagicMock()

    # Execute
    executor.handle_message(mock_channel, mock_method, mock_properties, assignment.model_dump_json())

    # Check that channel.basic_ack was called
    mock_channel.basic_ack.assert_called_once_with(1)

    # Verify publications: ACCEPTED, PROGRESS (25, 50, 75, 100), COMPLETED
    # Should have published at least:
    # 1. ACCEPTED
    # 2. PROGRESS x 4 (25%, 50%, 75%, 100%)
    # 3. COMPLETED
    published_types = [call[0][1].message_type for call in executor.publish.call_args_list]
    assert MessageType.TASK_ACCEPTED in published_types
    assert MessageType.TASK_PROGRESS in published_types
    assert MessageType.TASK_COMPLETED in published_types


def test_monitor_tracks_task(mock_rabbitmq_client):
    # Setup temporary file path for state tracker to avoid docker volumes locally
    tracker = TaskTracker(state_file_path="./test_tasks.json")
    monitor = Monitor(tracker=tracker)
    monitor.publish = MagicMock()

    # Send Progress message
    progress_env = MessageEnvelope(
        message_id="msg-p",
        sender_id="agent-b",
        receiver_id="agent-c",
        message_type=MessageType.TASK_PROGRESS,
        timestamp=datetime.now(timezone.utc),
        correlation_id="corr-1",
        priority=2,
        routing_key="report.task-status",
        payload={
            "task_id": "task-1",
            "status": "IN_PROGRESS",
            "progress_pct": 50,
            "current_sub_task": "train",
            "records_processed": 50,
            "total_records": 100,
            "anomalies_so_far": 2,
        },
    )

    mock_channel = MagicMock()
    monitor.handle_message(mock_channel, MagicMock(delivery_tag=1), MagicMock(), progress_env.model_dump_json())

    task_state = tracker.get_task("task-1")
    assert task_state is not None
    assert task_state["status"] == "IN_PROGRESS"
    assert task_state["progress_pct"] == 50

    # Send high anomaly completion message to trigger alert
    completed_env = MessageEnvelope(
        message_id="msg-c",
        sender_id="agent-b",
        receiver_id="agent-c",
        message_type=MessageType.TASK_COMPLETED,
        timestamp=datetime.now(timezone.utc),
        correlation_id="corr-1",
        priority=2,
        routing_key="report.task-status",
        payload={
            "task_id": "task-1",
            "status": "COMPLETED",
            "result_summary": {
                "total_records": 100,
                "anomalies_detected": 10,
                "high_severity": 6,  # triggers alert (>= 5)
                "medium_severity": 3,
                "low_severity": 1,
                "avg_anomaly_score": -0.18,
                "top_anomalous_records": [],
            },
            "execution_time_ms": 120,
        },
    )

    monitor.handle_message(mock_channel, MagicMock(delivery_tag=2), MagicMock(), completed_env.model_dump_json())

    # Task tracker should show COMPLETED
    task_state = tracker.get_task("task-1")
    assert task_state["status"] == "COMPLETED"

    # Verify C published a MONITOR_ALERT because high_severity >= 5
    published_types = [call[0][1].message_type for call in monitor.publish.call_args_list]
    assert MessageType.MONITOR_ALERT in published_types

    # Clean up test tracker file
    import os

    if os.path.exists("./test_tasks.json"):
        os.remove("./test_tasks.json")
