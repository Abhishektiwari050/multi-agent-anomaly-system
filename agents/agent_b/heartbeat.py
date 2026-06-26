import time
import random
import threading
import uuid
import os
from datetime import datetime, timezone
from shared.rabbitmq_client import RabbitMQBaseClient
from shared.message_schema import MessageEnvelope, HeartbeatPayload, MessageType
from shared.queue_config import ROUTING_KEY_HEARTBEAT
from shared.logger import setup_logger

logger = setup_logger("agent-b-heartbeat")

class HeartbeatThread(threading.Thread):
    def __init__(self, agent_id: str, client: RabbitMQBaseClient):
        super().__init__()
        self.agent_id = agent_id
        self.client = client
        self.daemon = True
        self.running = True
        self.interval = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "30"))

    def run(self):
        logger.info(f"Starting heartbeat thread for {self.agent_id} (interval: {self.interval}s)")
        while self.running:
            try:
                # Mock CPU/memory
                cpu_pct = round(random.uniform(1.0, 15.0), 2)
                mem_mb = round(random.uniform(50.0, 200.0), 2)
                
                payload = HeartbeatPayload(
                    agent_id=self.agent_id,
                    status="HEALTHY",
                    current_task=None,
                    cpu_pct=cpu_pct,
                    mem_mb=mem_mb
                )
                
                envelope = MessageEnvelope(
                    message_id=str(uuid.uuid4()),
                    sender_id=self.agent_id,
                    receiver_id="broadcast",
                    message_type=MessageType.HEARTBEAT,
                    timestamp=datetime.now(timezone.utc),
                    correlation_id="heartbeat-corr",
                    priority=3,
                    routing_key=ROUTING_KEY_HEARTBEAT,
                    payload=payload.model_dump()
                )
                
                self.client.publish(ROUTING_KEY_HEARTBEAT, envelope)
                logger.debug(f"Published heartbeat for {self.agent_id}")
            except Exception as e:
                logger.error(f"Error publishing heartbeat for {self.agent_id}: {e}")
                
            time.sleep(self.interval)

    def stop(self):
        self.running = False
