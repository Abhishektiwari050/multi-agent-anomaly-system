import pytest
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from message_schema import MessageEnvelope, MessageType, Metadata
from ml_utils import generate_patient_vitals, AnomalyDetector, build_report
from executor import Executor

def test_generate_patient_vitals():
    N = 100
    df, anomaly_indices = generate_patient_vitals(N=N, contamination=0.10, seed=42)
    
    assert len(df) == N
    assert len(anomaly_indices) == 10  # 10% of 100
    assert "heart_rate" in df.columns
    assert "oxygen_saturation" in df.columns
    assert "temperature" in df.columns

def test_anomaly_detector_training():
    N = 200
    df, _ = generate_patient_vitals(N=N, contamination=0.05, seed=42)
    
    detector = AnomalyDetector(contamination=0.05, seed=42)
    predictions, scores = detector.train_and_predict(df)
    
    assert len(predictions) == N
    assert len(scores) == N
    # Anomalies labeled as -1, normal as 1
    anomalies_count = sum(1 for p in predictions if p == -1)
    assert anomalies_count == 10  # 5% of 200

def test_classify_severity():
    detector = AnomalyDetector()
    # High threshold = -0.15, Medium = -0.08
    assert detector.classify_severity(-0.20) == "HIGH"
    assert detector.classify_severity(-0.10) == "MEDIUM"
    assert detector.classify_severity(0.05) == "LOW"

def test_build_report():
    N = 100
    df, _ = generate_patient_vitals(N=N, contamination=0.05, seed=42)
    detector = AnomalyDetector(contamination=0.05, seed=42)
    predictions, scores = detector.train_and_predict(df)
    
    report = build_report("task-123", df, predictions, scores, detector)
    
    assert report["task_id"] == "task-123"
    assert report["total_records"] == N
    assert report["anomalies_detected"] == 5
    assert "high_severity" in report
    assert "medium_severity" in report
    assert "low_severity" in report
    assert len(report["top_anomalous_records"]) <= 5

@patch('pika.BlockingConnection')
def test_executor_task_handling(mock_conn):
    # Mock connection and channel
    mock_channel = MagicMock()
    mock_conn.return_value.channel.return_value = mock_channel
    
    executor = Executor()
    executor.connect()
    
    # Verify connect setup
    assert executor.connection is not None
    assert executor.channel is not None
    
    # Setup mock envelope input body
    envelope = MessageEnvelope(
        message_id="msg-test-123",
        sender_id="agent-a",
        receiver_id="agent-b",
        message_type=MessageType.TASK_ASSIGNMENT,
        timestamp=datetime.now(timezone.utc),
        correlation_id="corr-test-123",
        priority=2,
        routing_key="task.agent-b",
        payload={
            "task_id": "task-test-123",
            "parameters": {
                "total_records": 100,
                "contamination": 0.05,
                "random_seed": 42
            }
        },
        metadata=Metadata()
    )
    body = envelope.model_dump_json()
    
    # Mock publish to collect sent status messages
    published_keys = []
    def mock_publish(routing_key, envelope_out):
        published_keys.append((routing_key, envelope_out.message_type))
        
    with patch.object(executor, 'publish', side_effect=mock_publish):
        mock_method = MagicMock()
        mock_method.delivery_tag = 1
        
        executor.handle_message(mock_channel, mock_method, None, body)
        
        # Verify message acknowledged
        mock_channel.basic_ack.assert_called_once_with(1)
        
        # Verify published status updates sequence:
        # 1. TASK_ACCEPTED (feedback)
        # 2. TASK_PROGRESS 25% (report)
        # 3. TASK_PROGRESS 50% (report)
        # 4. TASK_PROGRESS 75% (report)
        # 5. TASK_PROGRESS 100% (report)
        # 6. TASK_COMPLETED (report)
        # 7. TASK_COMPLETED (feedback)
        assert len(published_keys) == 7
        assert published_keys[0] == ("feedback.agent-a", MessageType.TASK_ACCEPTED)
        assert published_keys[1] == ("report.task-status", MessageType.TASK_PROGRESS)
        assert published_keys[5] == ("report.task-status", MessageType.TASK_COMPLETED)
        assert published_keys[6] == ("feedback.agent-a", MessageType.TASK_COMPLETED)
