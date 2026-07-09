import os
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from agents.agent_c.task_tracker import TaskTracker
from shared.logger import setup_logger
from shared.message_schema import MessageEnvelope, MessageType, MonitorAlertPayload
from shared.queue_config import QUEUE_AGENT_C_REPORTS, ROUTING_KEY_FEEDBACK
from shared.rabbitmq_client import RabbitMQBaseClient

logger = setup_logger("agent-c")


class Monitor(RabbitMQBaseClient):
    def __init__(self, tracker: Optional[TaskTracker] = None):
        super().__init__("agent-c")
        self.tracker = tracker or TaskTracker()
        self.heartbeat_registry: Dict[str, datetime] = {}
        self.heartbeat_timeout = int(os.getenv("HEARTBEAT_TIMEOUT_SECONDS", "90"))

        # Start background heartbeat supervisor
        self.watchdog_thread = threading.Thread(target=self._watch_heartbeats, daemon=True)
        self.watchdog_thread.start()

    def handle_message(self, channel, method, properties, body):
        try:
            envelope = MessageEnvelope.model_validate_json(body)
            msg_type = envelope.message_type

            logger.debug(f"Received event {msg_type} from {envelope.sender_id}")

            if msg_type == MessageType.HEARTBEAT:
                self._handle_heartbeat(envelope)
            elif msg_type == MessageType.TASK_PROGRESS:
                self._handle_progress(envelope)
            elif msg_type == MessageType.TASK_COMPLETED:
                self._handle_completion(envelope)
            elif msg_type == MessageType.TASK_FAILED:
                self._handle_failure(envelope)

            channel.basic_ack(method.delivery_tag)
        except Exception as e:
            logger.exception(f"Error processing report message: {e}")
            channel.basic_nack(method.delivery_tag, requeue=False)

    def _handle_heartbeat(self, envelope: MessageEnvelope):
        agent_id = str(envelope.payload.get("agent_id") or "")
        if agent_id:
            self.heartbeat_registry[agent_id] = datetime.now(timezone.utc)
            logger.debug(f"Heartbeat registered for agent: {agent_id}")

    def _handle_progress(self, envelope: MessageEnvelope):
        payload = envelope.payload
        task_id = str(payload.get("task_id") or "")
        status = str(payload.get("status") or "IN_PROGRESS")
        pct = int(payload.get("progress_pct") or 0)
        sub_task = str(payload.get("current_sub_task") or "")

        logger.info(f"Task {task_id} progress update: {pct}% ({sub_task})")
        self.tracker.update_task(
            task_id=task_id,
            status=status,
            progress_pct=pct,
            current_sub_task=sub_task,
            records_processed=int(payload.get("records_processed") or 0),
            total_records=int(payload.get("total_records") or 0),
            anomalies_so_far=int(payload.get("anomalies_so_far") or 0),
        )

    def _handle_completion(self, envelope: MessageEnvelope):
        payload = envelope.payload
        task_id = str(payload.get("task_id") or "")
        summary = dict(payload.get("result_summary") or {})
        execution_time = int(payload.get("execution_time_ms") or 0)

        logger.info(f"Task {task_id} completed in {execution_time}ms.")
        self.tracker.update_task(
            task_id=task_id,
            status="COMPLETED",
            progress_pct=100,
            current_sub_task="report",
            result_summary=summary,
            execution_time_ms=execution_time,
        )

        # Analyze severity levels
        high_severity_count = int(summary.get("high_severity") or 0)
        logger.info(f"Analyzing anomalies for Task {task_id}. High severity count: {high_severity_count}")

        if high_severity_count >= 5:
            self._publish_alert(
                task_id=task_id,
                alert_type="HIGH_SEVERITY_ANOMALIES",
                severity="HIGH",
                message=f"Critically high count of severe clinical anomalies ({high_severity_count}) detected in task run.",
                action_required="ESCALATE_TO_CLINICAL_TEAM",
            )
        elif high_severity_count >= 2:
            self._publish_alert(
                task_id=task_id,
                alert_type="HIGH_SEVERITY_ANOMALIES",
                severity="MEDIUM",
                message=f"Moderate count of severe clinical anomalies ({high_severity_count}) detected.",
                action_required="FLAG_FOR_REVIEW",
            )
        else:
            self._publish_alert(
                task_id=task_id,
                alert_type="HIGH_SEVERITY_ANOMALIES",
                severity="LOW",
                message="Anomaly scan complete. Results are within acceptable ranges.",
                action_required="LOG_AND_ARCHIVE",
            )

    def _handle_failure(self, envelope: MessageEnvelope):
        payload = envelope.payload
        task_id = str(payload.get("task_id") or "")
        error_msg = str(payload.get("error") or "Unknown error")

        logger.error(f"Task {task_id} failed: {error_msg}")
        self.tracker.update_task(
            task_id=task_id, status="FAILED", progress_pct=0, current_sub_task="failed", error=error_msg
        )

    def _publish_alert(self, task_id: str, alert_type: str, severity: str, message: str, action_required: str):
        payload = MonitorAlertPayload(
            task_id=task_id, alert_type=alert_type, severity=severity, message=message, action_required=action_required
        )

        envelope = MessageEnvelope(
            message_id=str(uuid.uuid4()),
            sender_id="agent-c",
            receiver_id="agent-a",
            message_type=MessageType.MONITOR_ALERT,
            timestamp=datetime.now(timezone.utc),
            correlation_id=f"alert-{uuid.uuid4()}",
            priority=1 if severity == "HIGH" else 2,
            routing_key=ROUTING_KEY_FEEDBACK,
            payload=payload.model_dump(),
        )

        self.publish(ROUTING_KEY_FEEDBACK, envelope)
        logger.info(f"Published alert of severity {severity} for Task {task_id} to Planner feedback.")

    def _watch_heartbeats(self):
        logger.info("Heartbeat watchdog thread started.")
        while True:
            try:
                now = datetime.now(timezone.utc)
                for agent_id, last_seen in list(self.heartbeat_registry.items()):
                    silence = (now - last_seen).total_seconds()
                    if silence > self.heartbeat_timeout:
                        logger.critical(
                            f"Agent offline detected: {agent_id}! Silence duration: {silence:.0f}s (Threshold: {self.heartbeat_timeout}s)"
                        )
                        self._publish_alert(
                            task_id="system",
                            alert_type="AGENT_OFFLINE",
                            severity="HIGH",
                            message=f"Agent '{agent_id}' has missed heartbeats and is offline.",
                            action_required="CHECK_AGENT_HEALTH",
                        )
                        # Remove from registry so we don't alert repeatedly
                        self.heartbeat_registry.pop(agent_id, None)
            except Exception as e:
                logger.error(f"Error checking heartbeat registry: {e}")

            time.sleep(15)

    def run_consumer(self):
        self.connect()
        self.start_consuming(QUEUE_AGENT_C_REPORTS)
