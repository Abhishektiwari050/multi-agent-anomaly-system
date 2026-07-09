# Standalone Clinical Execution Agent (Agent B)

This project contains a standalone, fully-functional implementation of the **Execution Agent (Agent B)** from the Multi-Agent Anomaly Detection System architecture.

---

## 1. Purpose and Responsibilities

The Execution Agent is the compute core of the diagnostics system. Its primary responsibilities are:
1.  **Queue Listening**: Subscribes to the `agent.b.tasks` queue using a RabbitMQ consumer connection and consumes `TASK_ASSIGNMENT` packets.
2.  **Dataset Simulation**: Generates high-fidelity clinical vital signs telemetry (Heart Rate, Blood Oxygen saturation $SpO_2$, Blood Pressure, Temperature, Respiratory Rate, Glucose) programmatically based on configuration parameters.
3.  **Machine Learning Training**: Fits a multivariate **Isolation Forest** model to establish a patient vitals baseline.
4.  **Anomaly Detection**: Predicts multivariate deviations, isolates records indicating medical emergency patterns (e.g. hypoxic distress paired with elevated heart rate), and classifies them into High, Medium, and Low severity indices.
5.  **Telemetry Reporting**: Compiles a diagnostic report detailing total counts, average anomaly scores, and vital signs profiles of the top 5 most anomalous patients.
6.  **Progress Updates**: Publishes periodic `TASK_PROGRESS` updates to notify the system Monitor (Agent C) as it completes simulation, training, and predicting steps.
7.  **Task Finalization**: Dispatches `TASK_COMPLETED` (or `TASK_FAILED`) messages to both Agent C (Monitor) and Agent A (Planner) upon run completion.
8.  **Process Heartbeats**: Spawns a dedicated background thread that publishes telemetry heartbeats to notify Agent C that it remains online and healthy.

---

## 2. Architecture & Communication Protocol

The agent is decoupled from the REST API gateway and other agents. It coordinates with them asynchronously via AMQP routing keys:

```
                          +------------------------+
                          |   FastAPI Web Server   |
                          +-----------+------------+
                                      |
                                  HTTP POST
                                      v
+------------------+    task.agent-b  +------------------------+
| Agent A (Planner)+----------------->|   CloudAMQP Broker     |
+--------^---------+                  +-----------+------------+
         |                                        |
      feedback.#                               task.#
         |                                        v
         |  feedback.agent-a          +-----------+------------+
         +----------------------------+ Agent B (Executor)     |
                                      +-----------+------------+
                                                  |
                                               report.#
                                                  v
+------------------+                  +-----------+------------+
| Agent C (Monitor)|<-----------------+  agent.c.reports Queue |
+------------------+                  +------------------------+
```

### Routing Keys Used:
*   **Consume**: Listen to `agent.b.tasks` queue (bound to pattern `task.#`).
*   **Publish Status**: Dispatch updates (`TASK_PROGRESS`, `TASK_COMPLETED`, `TASK_FAILED`, `HEARTBEAT`) to `report.task-status` routing key (routed to `agent.c.reports` queue).
*   **Publish Feedback**: Dispatch coordination signals (`TASK_ACCEPTED`, `TASK_COMPLETED`, `TASK_FAILED`) to `feedback.agent-a` routing key (routed to `agent.a.feedback` queue).

---

## 3. Setup and Run Instructions

### Prerequisites
*   Python 3.11 or later.
*   Access to a running RabbitMQ broker (local or CloudAMQP instance).

### Local Installation
1.  **Navigate to the directory**:
    ```bash
    cd C:/Users/abhis/.gemini/antigravity/scratch/execution-agent
    ```
2.  **Create a Virtual Environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure environment variables**:
    Copy `.env.example` to `.env` and fill in your connection credentials:
    ```bash
    cp .env.example .env
    ```

### Running the Agent
Start the consumer execution loops:
```bash
python main.py
```

### Running the Test Suite
Verify that all unit and mock integration tests pass successfully:
```bash
pytest test_executor.py
```

---

## 4. Docker Deployment

To build and run the standalone agent container:

1.  **Build the Docker Image**:
    ```bash
    docker build -t clinical-execution-agent .
    ```
2.  **Run the Container**:
    ```bash
    docker run --env-file .env clinical-execution-agent
    ```

---

## 5. Assumptions and Limitations

*   **RabbitMQ Topology**: Assumes the `agent.events` topic exchange and binding patterns are correctly initialized. The base client handles auto-declaration of these components on startup, but requires appropriate queue setup privileges.
*   **Synthetic Telemetry**: The vitals data processed is programmatically generated for demonstration and safety. It should not be used as a diagnostics tool for actual human vital records without adjusting baseline scales and model tuning.
*   **State Management**: The agent is designed to be stateless. It processes incoming messages, builds report dictionaries, and publishes results, but does not store run histories locally on disk. Long-term storage of tasks is delegated to Agent C (Monitor).
*   **SSL Handshake**: If connecting to CloudAMQP, a default TLS context with bypassed certificate verification (`verify_mode = CERT_NONE`) is implemented. This is necessary for running inside locked container platforms like Render, but should be adjusted in highly secure corporate network topologies.
