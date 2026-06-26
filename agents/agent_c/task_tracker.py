import os
import json
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from shared.logger import setup_logger

logger = setup_logger("task-tracker")

class TaskTracker:
    def __init__(self, state_file_path: Optional[str] = None):
        self.state_file_path = state_file_path or os.getenv("STATE_FILE_PATH", "tasks.json")
        self.lock = threading.Lock()
        self.tasks: Dict[str, Any] = {}
        self._load()

    def _load(self):
        with self.lock:
            if os.path.exists(self.state_file_path):
                try:
                    with open(self.state_file_path, "r") as f:
                        self.tasks = json.load(f)
                    logger.debug(f"Loaded {len(self.tasks)} tasks from state file.")
                except Exception as e:
                    logger.error(f"Failed to load state file: {e}. Starting with empty task registry.")
                    self.tasks = {}
            else:
                self.tasks = {}

    def _save(self):
        with self.lock:
            try:
                # Ensure directory exists
                dir_name = os.path.dirname(self.state_file_path)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)
                with open(self.state_file_path, "w") as f:
                    json.dump(self.tasks, f, indent=2)
                logger.debug(f"Saved state file to {self.state_file_path}")
            except Exception as e:
                logger.error(f"Failed to write state file: {e}")

    def update_task(self, task_id: str, status: str, progress_pct: int, current_sub_task: str, **kwargs):
        # Read/reload to ensure sync across multi-process volume mounts
        self._load()
        with self.lock:
            task = self.tasks.get(task_id, {})
            task.update({
                "task_id": task_id,
                "status": status,
                "progress_pct": progress_pct,
                "current_sub_task": current_sub_task,
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
            # Add extra key-value pairs (like result summary or execution time)
            for k, v in kwargs.items():
                task[k] = v
            self.tasks[task_id] = task
        self._save()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        self._load()
        with self.lock:
            return self.tasks.get(task_id)
