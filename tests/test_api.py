import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from agents.agent_c.task_tracker import TaskTracker
from api.main import app
from api.routes.tasks import get_planner


@pytest.fixture
def mock_planner():
    planner = MagicMock()
    return planner


@pytest.fixture(autouse=True)
def override_dependencies(mock_planner):
    app.dependency_overrides[get_planner] = lambda: mock_planner
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_create_task(mock_planner, client):
    # Setup mock return values for plan_task
    mock_planner.plan_task.return_value = ("task-api-test-id", "session-api-test-id")

    # Test POST /tasks/analyze
    payload = {
        "total_records": 1000,
        "contamination": 0.05,
        "random_seed": 42,
        "deadline_minutes": 10,
        "description": "API Test Run",
    }
    response = client.post("/tasks/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "DISPATCHED"
    assert data["task_id"] == "task-api-test-id"
    assert data["correlation_id"] == "session-api-test-id"

    mock_planner.plan_task.assert_called_once_with(
        total_records=1000, contamination=0.05, random_seed=42, deadline_minutes=10, description="API Test Run"
    )


def test_get_task_status(client):
    # Setup test file in state tracker
    test_file = "./test_tasks_api.json"
    tracker = TaskTracker(state_file_path=test_file)
    tracker.update_task(task_id="task-api-test", status="IN_PROGRESS", progress_pct=50, current_sub_task="train")

    # Force the API to use the test file
    with patch.dict(os.environ, {"STATE_FILE_PATH": test_file}):
        response = client.get("/tasks/task-api-test/status")
        assert response.status_code == 200

        data = response.json()
        assert data["task_id"] == "task-api-test"
        assert data["status"] == "IN_PROGRESS"
        assert data["progress_pct"] == 50

        # Test non-existent task
        response_404 = client.get("/tasks/non-existent/status")
        assert response_404.status_code == 404

    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)


@patch("pika.BlockingConnection")
def test_health_endpoint(mock_conn, client):
    # Mock successful connection
    mock_instance = MagicMock()
    mock_instance.is_open = True
    mock_conn.return_value = mock_instance

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["rabbitmq"] == "connected"


def test_list_tasks(client):
    test_file = "./test_tasks_list.json"
    tracker = TaskTracker(state_file_path=test_file)
    tracker.update_task(task_id="task-api-test-1", status="IN_PROGRESS", progress_pct=50, current_sub_task="train")
    tracker.update_task(task_id="task-api-test-2", status="COMPLETED", progress_pct=100, current_sub_task="report")

    with patch.dict(os.environ, {"STATE_FILE_PATH": test_file}):
        response = client.get("/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "task-api-test-1" in data
        assert "task-api-test-2" in data
        assert data["task-api-test-1"]["status"] == "IN_PROGRESS"
        assert data["task-api-test-2"]["status"] == "COMPLETED"

    if os.path.exists(test_file):
        os.remove(test_file)
