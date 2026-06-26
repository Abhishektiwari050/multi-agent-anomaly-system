from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator

class MessageType(str, Enum):
    TASK_ASSIGNMENT = "TASK_ASSIGNMENT"   # A -> B
    TASK_ACCEPTED   = "TASK_ACCEPTED"     # B -> A
    TASK_PROGRESS   = "TASK_PROGRESS"     # B -> C
    TASK_COMPLETED  = "TASK_COMPLETED"    # B -> C & A
    TASK_FAILED     = "TASK_FAILED"       # B -> C & A
    MONITOR_ALERT   = "MONITOR_ALERT"     # C -> A
    HEARTBEAT       = "HEARTBEAT"         # all -> broadcast

class Metadata(BaseModel):
    version: str = "1.0"
    retry_count: int = 0
    max_retries: int = 3
    ttl_seconds: int = 3600

    @model_validator(mode='after')
    def check_retry_limits(self) -> 'Metadata':
        if self.retry_count > self.max_retries:
            raise ValueError("retry_count cannot exceed max_retries")
        return self

class TaskAssignmentPayload(BaseModel):
    task_id: str
    task_type: str = "ANOMALY_DETECTION"
    description: str
    parameters: Dict[str, Any]
    deadline: datetime
    sub_tasks: List[str]

class TaskProgressPayload(BaseModel):
    task_id: str
    status: str = "IN_PROGRESS"
    progress_pct: int
    current_sub_task: str
    records_processed: int
    total_records: int
    anomalies_so_far: int

class TaskCompletedPayload(BaseModel):
    task_id: str
    status: str = "COMPLETED"
    result_summary: Dict[str, Any]
    execution_time_ms: int

class MonitorAlertPayload(BaseModel):
    task_id: str
    alert_type: str  # e.g., "HIGH_SEVERITY_ANOMALIES", "AGENT_OFFLINE", "DEADLINE_BREACH"
    severity: str    # e.g., "HIGH", "MEDIUM", "LOW"
    message: str
    action_required: str

class HeartbeatPayload(BaseModel):
    agent_id: str
    status: str      # e.g., "HEALTHY", "DEGRADED"
    current_task: Optional[str] = None
    cpu_pct: float
    mem_mb: float

class MessageEnvelope(BaseModel):
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: MessageType
    timestamp: datetime
    correlation_id: str
    priority: int  # 1=Critical, 2=Normal, 3=Low
    routing_key: str
    payload: Dict[str, Any]
    metadata: Metadata = Field(default_factory=Metadata)
