import uuid
import time
import os
import random
import threading
from datetime import datetime, timezone
from typing import Dict, Any
from loguru import logger
from rabbitmq_client import RabbitMQBaseClient
from message_schema import (
    MessageEnvelope, MessageType, TaskProgressPayload,
    TaskCompletedPayload, Metadata
)
from ml_utils import generate_patient_vitals, AnomalyDetector, build_report

# Routing keys from architecture design
ROUTING_KEY_REPORT = "report.task-status"
ROUTING_KEY_FEEDBACK = "feedback.agent-a"
ROUTING_KEY_HEARTBEAT = "heartbeat.agent"
ROUTING_KEY_TASK_AGENT_B = "task.agent-b"

class HeartbeatThread(threading.Thread):
    def __init__(self, agent_id: str):
        super().__init__()
        self.agent_id = agent_id
        self.client = RabbitMQBaseClient(f"heartbeat-{agent_id}")
        self.daemon = True
        self.running = True
        self.interval = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "30"))

    def run(self):
        logger.info(f"Starting heartbeat thread for {self.agent_id} (interval: {self.interval}s)")
        try:
            self.client.connect()
        except Exception as e:
            logger.error(f"Heartbeat client failed to connect for {self.agent_id}: {e}")
            return

        while self.running:
            try:
                cpu_pct = round(random.uniform(1.0, 15.0), 2)
                mem_mb = round(random.uniform(50.0, 200.0), 2)
                
                payload = {
                    "agent_id": self.agent_id,
                    "status": "HEALTHY",
                    "cpu_pct": cpu_pct,
                    "mem_mb": mem_mb
                }
                
                envelope = MessageEnvelope(
                    message_id=str(uuid.uuid4()),
                    sender_id=self.agent_id,
                    receiver_id="broadcast",
                    message_type=MessageType.HEARTBEAT,
                    timestamp=datetime.now(timezone.utc),
                    correlation_id="heartbeat-corr",
                    priority=3,
                    routing_key=ROUTING_KEY_HEARTBEAT,
                    payload=payload
                )
                
                self.client.publish(ROUTING_KEY_HEARTBEAT, envelope)
                logger.debug(f"Published heartbeat for {self.agent_id}")
            except Exception as e:
                logger.error(f"Error publishing heartbeat for {self.agent_id}: {e}")
                
            time.sleep(self.interval)

    def stop(self):
        self.running = False
        self.client.disconnect()


class Executor(RabbitMQBaseClient):
    def __init__(self):
        super().__init__("agent-b")

    def handle_message(self, channel, method, properties, body):
        try:
            envelope = MessageEnvelope.model_validate_json(body)
        except Exception as e:
            logger.error(f"Failed to parse incoming message body: {body}. Error: {e}")
            # Reject to DLQ immediately since it is malformed
            channel.basic_nack(method.delivery_tag, requeue=False)
            return

        # Check max retries
        if envelope.metadata.retry_count >= envelope.metadata.max_retries:
            logger.error(f"Max retries ({envelope.metadata.max_retries}) exceeded for task {envelope.payload.get('task_id')}. Routing to DLQ.")
            self._publish_task_failed(envelope, f"Max retries exceeded: {envelope.metadata.retry_count}")
            channel.basic_nack(method.delivery_tag, requeue=False)
            return

        try:
            # Publish TASK_ACCEPTED
            self._publish_status(envelope, MessageType.TASK_ACCEPTED, ROUTING_KEY_FEEDBACK, "agent-a", {})
            logger.info(f"Accepted task: {envelope.payload.get('task_id')}")
            
            # Start timer
            start_time = time.time()
            
            # Parse parameters
            task_id = envelope.payload.get("task_id")
            params = envelope.payload.get("parameters", {})
            total_records = params.get("total_records", 1000)
            contamination = params.get("contamination", 0.05)
            seed = params.get("random_seed", 42)
            
            # Step 1: generate_data (25%)
            logger.info(f"Task {task_id}: Generating synthetic vital data...")
            df, anomaly_indices = generate_patient_vitals(N=total_records, contamination=contamination, seed=seed)
            
            progress_payload = TaskProgressPayload(
                task_id=task_id,
                progress_pct=25,
                current_sub_task="generate_data",
                records_processed=total_records,
                total_records=total_records,
                anomalies_so_far=0
            )
            self._publish_status(envelope, MessageType.TASK_PROGRESS, ROUTING_KEY_REPORT, "agent-c", progress_payload.model_dump())
            
            # Step 2: train (50%)
            logger.info(f"Task {task_id}: Training Isolation Forest model...")
            detector = AnomalyDetector(contamination=contamination, seed=seed)
            predictions, scores = detector.train_and_predict(df)
            
            progress_payload.progress_pct = 50
            progress_payload.current_sub_task = "train"
            self._publish_status(envelope, MessageType.TASK_PROGRESS, ROUTING_KEY_REPORT, "agent-c", progress_payload.model_dump())
            
            # Step 3: predict (75%)
            logger.info(f"Task {task_id}: Running anomaly classification...")
            anomalies_detected = sum(1 for p in predictions if p == -1)
            
            progress_payload.progress_pct = 75
            progress_payload.current_sub_task = "predict"
            progress_payload.anomalies_so_far = anomalies_detected
            self._publish_status(envelope, MessageType.TASK_PROGRESS, ROUTING_KEY_REPORT, "agent-c", progress_payload.model_dump())
            
            # Step 4: build_report (100%)
            logger.info(f"Task {task_id}: Compiling telemetry report...")
            report_data = build_report(task_id, df, predictions, scores, detector)
            
            progress_payload.progress_pct = 100
            progress_payload.current_sub_task = "report"
            self._publish_status(envelope, MessageType.TASK_PROGRESS, ROUTING_KEY_REPORT, "agent-c", progress_payload.model_dump())
            
            # Publish TASK_COMPLETED
            execution_time = int((time.time() - start_time) * 1000)
            completed_payload = TaskCompletedPayload(
                task_id=task_id,
                result_summary=report_data,
                execution_time_ms=execution_time
            )
            
            # Publish completion to both Agent C and Agent A
            self._publish_status(envelope, MessageType.TASK_COMPLETED, ROUTING_KEY_REPORT, "agent-c", completed_payload.model_dump())
            self._publish_status(envelope, MessageType.TASK_COMPLETED, ROUTING_KEY_FEEDBACK, "agent-a", completed_payload.model_dump())
            
            logger.info(f"Task {task_id} successfully completed in {execution_time}ms.")
            channel.basic_ack(method.delivery_tag)
            
        except Exception as e:
            logger.exception(f"Error executing task {envelope.payload.get('task_id')}: {e}")
            # Increment retry count
            envelope.metadata.retry_count += 1
            
            if envelope.metadata.retry_count >= envelope.metadata.max_retries:
                logger.error(f"Max retries exceeded on exception for task {envelope.payload.get('task_id')}. Sending to DLQ.")
                self._publish_task_failed(envelope, str(e))
                channel.basic_nack(method.delivery_tag, requeue=False)
            else:
                logger.warning(f"Re-publishing task for retry attempt {envelope.metadata.retry_count}...")
                self.publish(ROUTING_KEY_TASK_AGENT_B, envelope)
                channel.basic_ack(method.delivery_tag)

    def _publish_status(self, original_env: MessageEnvelope, msg_type: MessageType, routing_key: str, receiver_id: str, payload: dict):
        env = MessageEnvelope(
            message_id=str(uuid.uuid4()),
            sender_id="agent-b",
            receiver_id=receiver_id,
            message_type=msg_type,
            timestamp=datetime.now(timezone.utc),
            correlation_id=original_env.correlation_id,
            priority=original_env.priority,
            routing_key=routing_key,
            payload=payload,
            metadata=original_env.metadata
        )
        self.publish(routing_key, env)

    def _publish_task_failed(self, original_env: MessageEnvelope, error_msg: str):
        failed_payload = {
            "task_id": original_env.payload.get("task_id"),
            "status": "FAILED",
            "error": error_msg
        }
        self._publish_status(original_env, MessageType.TASK_FAILED, ROUTING_KEY_REPORT, "agent-c", failed_payload)
        self._publish_status(original_env, MessageType.TASK_FAILED, ROUTING_KEY_FEEDBACK, "agent-a", failed_payload)

    def run_consumer(self):
        self.connect()
        self.start_consuming("agent.b.tasks")
