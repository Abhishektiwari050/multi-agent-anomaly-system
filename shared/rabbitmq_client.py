import os
import time

import pika
from loguru import logger

from shared.message_schema import MessageEnvelope
from shared.queue_config import DLX_NAME, EXCHANGE_NAME, QUEUE_BINDINGS, QUEUE_DLQ, ROUTING_KEY_DLQ


class RabbitMQBaseClient:
    def __init__(self, client_name: str):
        self.client_name = client_name
        self.host = os.getenv("RABBITMQ_HOST", "localhost")
        self.port = int(os.getenv("RABBITMQ_PORT", 5672))
        self.user = os.getenv("RABBITMQ_USER", "guest")
        self.password = os.getenv("RABBITMQ_PASS", "guest")

        url = os.getenv("RABBITMQ_URL")
        if url:
            logger.info(f"[{self.client_name}] Using RABBITMQ_URL for connection parameters.")
            self.params = pika.URLParameters(url)
            if url.startswith("amqps://"):
                import ssl

                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.params.ssl_options = pika.SSLOptions(context)
        else:
            credentials = pika.PlainCredentials(self.user, self.password)
            self.params = pika.ConnectionParameters(
                host=self.host, port=self.port, credentials=credentials, heartbeat=60, blocked_connection_timeout=300
            )
        self.connection = None
        self.channel = None

    def connect(self, max_attempts: int = 10):
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    f"[{self.client_name}] Connecting to RabbitMQ (attempt {attempt}/{max_attempts}) at {self.params.host}:{self.params.port}"
                )
                self.connection = pika.BlockingConnection(self.params)
                assert self.connection is not None
                self.channel = self.connection.channel()
                self._declare_topology()
                logger.info(f"[{self.client_name}] Connected to RabbitMQ.")
                return
            except pika.exceptions.AMQPConnectionError as e:
                wait = min(2**attempt, 60)
                logger.warning(f"[{self.client_name}] Connection failed. Retrying in {wait}s. Error: {e}")
                time.sleep(wait)
        raise RuntimeError(f"[{self.client_name}] Could not connect to RabbitMQ after {max_attempts} attempts.")

    def _declare_topology(self):
        # 1. Declare Topic Exchange
        self.channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic", durable=True)

        # 2. Declare Dead Letter Exchange (DLX)
        self.channel.exchange_declare(exchange=DLX_NAME, exchange_type="direct", durable=True)

        # 3. Declare Dead Letter Queue (DLQ) and bind to DLX
        self.channel.queue_declare(queue=QUEUE_DLQ, durable=True)
        self.channel.queue_bind(exchange=DLX_NAME, queue=QUEUE_DLQ, routing_key=ROUTING_KEY_DLQ)

        # 4. Declare standard queues with DLQ configuration
        queue_args = {
            "x-dead-letter-exchange": DLX_NAME,
            "x-dead-letter-routing-key": ROUTING_KEY_DLQ,
            "x-message-ttl": 3600000,  # 1 hour
            "x-max-priority": 3,
        }

        for queue, patterns in QUEUE_BINDINGS.items():
            self.channel.queue_declare(queue=queue, durable=True, arguments=queue_args)
            for pattern in patterns:
                self.channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue, routing_key=pattern)

    def publish(self, routing_key: str, envelope: MessageEnvelope):
        if not self.channel or self.channel.is_closed:
            self.connect()
        assert self.channel is not None

        body = envelope.model_dump_json()
        properties = pika.BasicProperties(
            delivery_mode=2,  # make message persistent
            priority=envelope.priority,
            correlation_id=envelope.correlation_id,
            content_type="application/json",
        )
        self.channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=routing_key, body=body, properties=properties)
        logger.debug(f"[{self.client_name}] Published to '{routing_key}': {envelope.message_id}")

    def start_consuming(self, queue_name: str):
        if not self.channel or self.channel.is_closed:
            self.connect()
        assert self.channel is not None

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=queue_name, on_message_callback=self._wrap_handle_message)
        logger.info(f"[{self.client_name}] Started consuming from queue '{queue_name}'")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info(f"[{self.client_name}] Consumer stopped via interrupt.")
            self.disconnect()
        except Exception as e:
            logger.error(f"[{self.client_name}] Consumer encountered error: {e}")
            self.disconnect()

    def _wrap_handle_message(self, channel, method, properties, body):
        try:
            self.handle_message(channel, method, properties, body)
        except Exception as e:
            logger.exception(f"[{self.client_name}] Exception in message handler: {e}")
            # By default, reject and requeue=False to push to DLQ if exception bubbles up
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def handle_message(self, channel, method, properties, body):
        raise NotImplementedError("Subclasses must implement handle_message")

    def disconnect(self):
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info(f"[{self.client_name}] Disconnected from RabbitMQ.")
        except Exception as e:
            logger.error(f"[{self.client_name}] Error while disconnecting: {e}")
