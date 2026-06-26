from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any
from agents.agent_a.planner import Planner
from agents.agent_c.task_tracker import TaskTracker

router = APIRouter(prefix="/tasks", tags=["tasks"])

class AnalyzeRequest(BaseModel):
    total_records: int = Field(default=7000, ge=10, le=100000)
    contamination: float = Field(default=0.05, ge=0.001, le=0.5)
    random_seed: int = Field(default=42)
    deadline_minutes: int = Field(default=10, ge=1, le=1440)
    description: str = Field(default="Patient vitals anomaly detection")

class AnalyzeResponse(BaseModel):
    task_id: str
    correlation_id: str
    status: str
    message: str

# Shared instances to reuse connections where applicable
_planner_instance = None

def get_planner() -> Planner:
    global _planner_instance
    if _planner_instance is None:
        _planner_instance = Planner()
        _planner_instance.connect()
    return _planner_instance

def get_tracker() -> TaskTracker:
    return TaskTracker()

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_vitals(request: AnalyzeRequest, planner: Planner = Depends(get_planner)):
    try:
        task_id, correlation_id = planner.plan_task(
            total_records=request.total_records,
            contamination=request.contamination,
            random_seed=request.random_seed,
            deadline_minutes=request.deadline_minutes,
            description=request.description
        )
        return AnalyzeResponse(
            task_id=task_id,
            correlation_id=correlation_id,
            status="DISPATCHED",
            message="Task enqueued. Monitor progress via /tasks/{id}/status"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {e}")

@router.get("", response_model=Dict[str, Any])
def list_tasks(tracker: TaskTracker = Depends(get_tracker)):
    try:
        return tracker.get_all_tasks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {e}")

@router.get("/{task_id}/status")
def get_task_status(task_id: str, tracker: TaskTracker = Depends(get_tracker)):
    task = tracker.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
    return task

