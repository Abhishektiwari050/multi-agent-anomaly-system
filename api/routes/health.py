import os
import pika
from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
def health_check():
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", 5672))
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASS", "guest")
    
    credentials = pika.PlainCredentials(user, password)
    params = pika.ConnectionParameters(
        host=host,
        port=port,
        credentials=credentials,
        connection_attempts=1,
        retry_delay=1
    )
    
    rabbitmq_status = "disconnected"
    try:
        connection = pika.BlockingConnection(params)
        if connection.is_open:
            rabbitmq_status = "connected"
            connection.close()
    except Exception:
        pass
        
    return {
        "status": "ok" if rabbitmq_status == "connected" else "degraded",
        "rabbitmq": rabbitmq_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
