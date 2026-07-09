import time
import uuid
from datetime import datetime, timezone

from agents.agent_b.ml.data_generator import generate_patient_vitals
from agents.agent_b.ml.isolation_forest import AnomalyDetector
from agents.agent_b.ml.report_builder import build_report
from shared.logger import setup_logger
from shared.message_schema import MessageEnvelope, MessageType, TaskCompletedPayload, TaskProgressPayload
from shared.queue_config import QUEUE_AGENT_B_TASKS, ROUTING_KEY_FEEDBACK, ROUTING_KEY_REPORT, ROUTING_KEY_TASK_AGENT_B
from shared.rabbitmq_client import RabbitMQBaseClient

logger = setup_logger("agent-b")

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

        # 1. Check max retries
        if envelope.metadata.retry_count >= envelope.metadata.max_retries:
            logger.error(f"Max retries ({envelope.metadata.max_retries}) exceeded for task {envelope.payload.get('task_id')}. Routing to DLQ.")
            self._publish_task_failed(envelope, f"Max retries exceeded: {envelope.metadata.retry_count}")
            channel.basic_nack(method.delivery_tag, requeue=False)
            return

        try:
            # 2. Publish TASK_ACCEPTED
            self._publish_status(envelope, MessageType.TASK_ACCEPTED, ROUTING_KEY_FEEDBACK, "agent-a", {})

            # Start timer
            start_time = time.time()

            # Parse parameters
            task_id = envelope.payload.get("task_id")
            params = envelope.payload.get("parameters", {})
            total_records = params.get("total_records", 1000)
            contamination = params.get("contamination", 0.05)
            seed = params.get("random_seed", 42)

            # 3. Step 1: generate_data (25%)
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

            # 4. Step 2: train (50%)
            logger.info(f"Task {task_id}: Training Isolation Forest model...")
            detector = AnomalyDetector(contamination=contamination, seed=seed)
            predictions, scores = detector.train_and_predict(df)

            progress_payload.progress_pct = 50
            progress_payload.current_sub_task = "train"
            self._publish_status(envelope, MessageType.TASK_PROGRESS, ROUTING_KEY_REPORT, "agent-c", progress_payload.model_dump())

            # 5. Step 3: predict (75%)
            logger.info(f"Task {task_id}: Running anomaly classification...")
            anomalies_detected = sum(1 for p in predictions if p == -1)

            progress_payload.progress_pct = 75
            progress_payload.current_sub_task = "predict"
            progress_payload.anomalies_so_far = anomalies_detected
            self._publish_status(envelope, MessageType.TASK_PROGRESS, ROUTING_KEY_REPORT, "agent-c", progress_payload.model_dump())

            # 6. Step 4: build_report (100%)
            logger.info(f"Task {task_id}: Compiling telemetry report...")
            report_data = build_report(task_id, df, predictions, scores, detector)

            progress_payload.progress_pct = 100
            progress_payload.current_sub_task = "report"
            self._publish_status(envelope, MessageType.TASK_PROGRESS, ROUTING_KEY_REPORT, "agent-c", progress_payload.model_dump())

            # 7. Publish TASK_COMPLETED
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

            # Check if we should retry or fail
            if envelope.metadata.retry_count >= envelope.metadata.max_retries:
                logger.error(f"Max retries exceeded on exception for task {envelope.payload.get('task_id')}. Sending to DLQ.")
                self._publish_task_failed(envelope, str(e))
                channel.basic_nack(method.delivery_tag, requeue=False)
            else:
                logger.warning(f"Re-publishing task for retry attempt {envelope.metadata.retry_count}...")
                # Re-publish message to queue with incremented retry count
                self.publish(ROUTING_KEY_TASK_AGENT_B, envelope)
                # Acknowledge the current failed message copy
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
        # Notify Monitor (Agent C) and Planner (Agent A)
        self._publish_status(original_env, MessageType.TASK_FAILED, ROUTING_KEY_REPORT, "agent-c", failed_payload)
        self._publish_status(original_env, MessageType.TASK_FAILED, ROUTING_KEY_FEEDBACK, "agent-a", failed_payload)

    def run_consumer(self):
        self.connect()
        self.start_consuming(QUEUE_AGENT_B_TASKS)
