from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    TASK_ASSIGNMENT = "TASK_ASSIGNMENT"
    TASK_ACCEPTED = "TASK_ACCEPTED"
    TASK_PROGRESS = "TASK_PROGRESS"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    HEARTBEAT = "HEARTBEAT"
    MONITOR_ALERT = "MONITOR_ALERT"

class Metadata(BaseModel):
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    routing_path: List[str] = Field(default_factory=list)

class MessageEnvelope(BaseModel):
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: MessageType
    timestamp: datetime
    correlation_id: str
    priority: int = Field(default=2, ge=0, le=5)
    routing_key: str
    payload: Dict[str, Any]
    metadata: Metadata = Field(default_factory=Metadata)

class TaskAssignmentPayload(BaseModel):
    task_id: str
    task_type: str = "ANOMALY_DETECTION"
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    deadline: datetime
    sub_tasks: List[str] = Field(default_factory=list)

class TaskProgressPayload(BaseModel):
    task_id: str
    progress_pct: int
    current_sub_task: str
    records_processed: int
    total_records: int
    anomalies_so_far: int
    status: str = "IN_PROGRESS"

class TaskCompletedPayload(BaseModel):
    task_id: str
    result_summary: Dict[str, Any]
    execution_time_ms: int
