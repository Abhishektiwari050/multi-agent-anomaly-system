import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple

from shared.logger import setup_logger
from shared.message_schema import MessageEnvelope, MessageType, TaskAssignmentPayload
from shared.queue_config import QUEUE_AGENT_A_FEEDBACK, ROUTING_KEY_TASK_AGENT_B
from shared.rabbitmq_client import RabbitMQBaseClient

logger = setup_logger("agent-a")

class Planner(RabbitMQBaseClient):
    def __init__(self):
        super().__init__("agent-a")

    def plan_task(
        self,
        total_records: int,
        contamination: float,
        random_seed: int,
        deadline_minutes: int,
        description: str
    ) -> Tuple[str, str]:
        task_id = f"task-{uuid.uuid4()}"
        correlation_id = f"session-{uuid.uuid4()}"
        deadline = datetime.now(timezone.utc) + timedelta(minutes=deadline_minutes)

        payload = TaskAssignmentPayload(
            task_id=task_id,
            task_type="ANOMALY_DETECTION",
            description=description,
            parameters={
                "total_records": total_records,
                "contamination": contamination,
                "random_seed": random_seed
            },
            deadline=deadline,
            sub_tasks=["generate_data", "train", "predict", "report"]
        )

        envelope = MessageEnvelope(
            message_id=str(uuid.uuid4()),
            sender_id="agent-a",
            receiver_id="agent-b",
            message_type=MessageType.TASK_ASSIGNMENT,
            timestamp=datetime.now(timezone.utc),
            correlation_id=correlation_id,
            priority=2,
            routing_key=ROUTING_KEY_TASK_AGENT_B,
            payload=payload.model_dump()
        )

        self.publish(ROUTING_KEY_TASK_AGENT_B, envelope)
        logger.info(f"Task enqueued. Task ID: {task_id} (correlation: {correlation_id})")
        return task_id, correlation_id

    def handle_message(self, channel, method, properties, body):
        try:
            envelope = MessageEnvelope.model_validate_json(body)
            msg_type = envelope.message_type

            logger.info(f"Received feedback message type: {msg_type} from {envelope.sender_id}")

            if msg_type == MessageType.TASK_ACCEPTED:
                logger.info(f"Task accepted by {envelope.sender_id}. Correlation ID: {envelope.correlation_id}")

            elif msg_type == MessageType.TASK_COMPLETED:
                summary = envelope.payload.get("result_summary", {})
                logger.info(
                    f"Task {envelope.payload.get('task_id')} COMPLETED! "
                    f"Processed: {summary.get('total_records')}, "
                    f"Detected Anomalies: {summary.get('anomalies_detected')} "
                    f"(High: {summary.get('high_severity')}, Med: {summary.get('medium_severity')}, Low: {summary.get('low_severity')})"
                )

            elif msg_type == MessageType.TASK_FAILED:
                logger.error(f"Task {envelope.payload.get('task_id')} FAILED on {envelope.sender_id}!")

            elif msg_type == MessageType.MONITOR_ALERT:
                alert_type = envelope.payload.get("alert_type")
                severity = envelope.payload.get("severity")
                msg = envelope.payload.get("message")
                action = envelope.payload.get("action_required")

                log_msg = f"MONITOR ALERT: [{alert_type}] Severity: {severity}. Msg: {msg}. Action required: {action}"
                if severity == "HIGH":
                    logger.critical(log_msg)
                else:
                    logger.warning(log_msg)

            channel.basic_ack(method.delivery_tag)
        except Exception as e:
            logger.exception(f"Error handling feedback message: {e}")
            channel.basic_nack(method.delivery_tag, requeue=False)

    def run_consumer(self):
        self.connect()
        self.start_consuming(QUEUE_AGENT_A_FEEDBACK)
