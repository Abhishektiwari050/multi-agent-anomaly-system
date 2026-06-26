import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from shared.message_schema import (
    MessageEnvelope,
    Metadata,
    MessageType,
    TaskAssignmentPayload,
    TaskProgressPayload,
    TaskCompletedPayload,
    MonitorAlertPayload,
    HeartbeatPayload
)

def test_metadata_default_values():
    meta = Metadata()
    assert meta.version == "1.0"
    assert meta.retry_count == 0
    assert meta.max_retries == 3
    assert meta.ttl_seconds == 3600

def test_metadata_validation_retry_count():
    # retry_count should not exceed max_retries
    with pytest.raises(ValidationError):
        Metadata(retry_count=4, max_retries=3)

def test_task_assignment_payload():
    payload_data = {
        "task_id": "task-123",
        "task_type": "ANOMALY_DETECTION",
        "description": "Test Task",
        "parameters": {"total_records": 100},
        "deadline": datetime.now(timezone.utc).isoformat(),
        "sub_tasks": ["generate_data", "train", "predict", "report"]
    }
    payload = TaskAssignmentPayload(**payload_data)
    assert payload.task_id == "task-123"
    assert payload.parameters["total_records"] == 100

def test_message_envelope_validation():
    # Valid envelope
    envelope_data = {
        "message_id": "msg-123",
        "sender_id": "agent-a",
        "receiver_id": "agent-b",
        "message_type": MessageType.TASK_ASSIGNMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": "corr-123",
        "priority": 2,
        "routing_key": "task.agent-b",
        "payload": {
            "task_id": "task-123",
            "task_type": "ANOMALY_DETECTION",
            "description": "Test Task",
            "parameters": {"total_records": 100},
            "deadline": datetime.now(timezone.utc).isoformat(),
            "sub_tasks": ["generate_data"]
        },
        "metadata": Metadata().model_dump()
    }
    envelope = MessageEnvelope(**envelope_data)
    assert envelope.message_id == "msg-123"
    assert envelope.message_type == MessageType.TASK_ASSIGNMENT

def test_message_envelope_invalid_type():
    envelope_data = {
        "message_id": "msg-123",
        "sender_id": "agent-a",
        "receiver_id": "agent-b",
        "message_type": "INVALID_TYPE",  # invalid enum value
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": "corr-123",
        "priority": 2,
        "routing_key": "task.agent-b",
        "payload": {},
        "metadata": Metadata().model_dump()
    }
    with pytest.raises(ValidationError):
        MessageEnvelope(**envelope_data)
