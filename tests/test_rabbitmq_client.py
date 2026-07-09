import os
import time
from datetime import datetime, timezone

import pika
import pytest
from dotenv import load_dotenv

from shared.message_schema import MessageEnvelope, MessageType, Metadata
from shared.queue_config import EXCHANGE_NAME, ROUTING_KEY_TASK_AGENT_B
from shared.rabbitmq_client import RabbitMQBaseClient

load_dotenv()


# Skip integration tests if RabbitMQ is not running
def is_rabbitmq_available():
    url = os.getenv("RABBITMQ_URL")
    if url:
        params = pika.URLParameters(url)
    else:
        host = os.getenv("RABBITMQ_HOST", "localhost")
        port = int(os.getenv("RABBITMQ_PORT", 5672))
        user = os.getenv("RABBITMQ_USER", "guest")
        password = os.getenv("RABBITMQ_PASS", "guest")
        credentials = pika.PlainCredentials(user, password)
        params = pika.ConnectionParameters(
            host=host, port=port, credentials=credentials, connection_attempts=1, retry_delay=1
        )
    try:
        connection = pika.BlockingConnection(params)
        connection.close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not is_rabbitmq_available(), reason="RabbitMQ broker is not running or not reachable.")


class RabbitMQIntegrationClient(RabbitMQBaseClient):
    def __init__(self):
        super().__init__("test-client")
        self.received_messages = []

    def handle_message(self, channel, method, properties, body):
        self.received_messages.append(body)
        channel.basic_ack(method.delivery_tag)


def test_publish_and_consume():
    client = RabbitMQIntegrationClient()
    client.connect()

    # Setup a temporary test queue to capture the routed message without interference from active live consumers
    test_queue = f"test-queue-{int(time.time())}"
    client.channel.queue_declare(queue=test_queue, durable=False, auto_delete=True)
    client.channel.queue_bind(exchange=EXCHANGE_NAME, queue=test_queue, routing_key=ROUTING_KEY_TASK_AGENT_B)

    envelope = MessageEnvelope(
        message_id="msg-test",
        sender_id="test-client",
        receiver_id="agent-b",
        message_type=MessageType.TASK_ASSIGNMENT,
        timestamp=datetime.now(timezone.utc),
        correlation_id="corr-test",
        priority=2,
        routing_key=ROUTING_KEY_TASK_AGENT_B,
        payload={
            "task_id": "task-test",
            "task_type": "ANOMALY_DETECTION",
            "description": "Integration Test",
            "parameters": {},
            "deadline": datetime.now(timezone.utc).isoformat(),
            "sub_tasks": [],
        },
        metadata=Metadata(),
    )

    # Publish message
    client.publish(ROUTING_KEY_TASK_AGENT_B, envelope)
    time.sleep(0.5)

    # Let's get the message using basic_get to avoid blocking forever
    method_frame, header_frame, body = client.channel.basic_get(queue=test_queue, auto_ack=False)
    assert method_frame is not None

    # Parse and verify
    received_env = MessageEnvelope.model_validate_json(body)
    assert received_env.message_id == "msg-test"
    assert received_env.correlation_id == "corr-test"

    # Clean up by acknowledging the retrieved message and closing
    client.channel.basic_ack(method_frame.delivery_tag)
    client.channel.queue_unbind(exchange=EXCHANGE_NAME, queue=test_queue, routing_key=ROUTING_KEY_TASK_AGENT_B)
    client.channel.queue_delete(queue=test_queue)
    client.disconnect()
