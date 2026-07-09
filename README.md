# Multi-Agent Anomaly Detection System
### Clinical Vitals Telemetry Analysis & Asynchronous Message Routing Architecture

Welcome to the **Multi-Agent Anomaly Detection System** repository. This project implements a production-grade clinical monitoring solution designed to ingest synthetic patient vital signs, train multivariate Isolation Forest models to establish baseline behaviors, and coordinate immediate alerts using a distributed multi-agent architecture.

This document describes the system design, message structures, communication routing protocols, and setup instructions.

---

## 1. System Architecture & Components

Decoupling is managed through a central `supervisord` process coordinator running inside a single container, utilizing a CloudAMQP RabbitMQ message broker for external state routing:

*   **FastAPI REST Gateway**: Serves the lightweight, light-themed clinical dashboard and exposes endpoints to trigger analyses (`POST /tasks/analyze`), fetch status (`GET /tasks/{id}/status`), and list historical runs (`GET /tasks`).
*   **Planner (Agent A)**: Validates REST calls, creates execution parameters, publishes task messages, and tracks feedback metrics.
*   **Executor (Agent B)**: Performs compute-intensive operations. Simulates multi-dimensional vital signs ($SpO_2$, heart rate, blood pressure, temperature, respiratory rate, glucose), trains a multivariate Isolation Forest algorithm, maps anomalous records, and structures detailed JSON telemetry files.
*   **Monitor (Agent C)**: Tracks execution progress percentages, records heartbeats from all online agents, and routes severity-based warning alerts.
*   **Clinical Light Dashboard**: Served at the root URL. Provides responsive control inputs, progress steppers, Chart.js scatter plots, and patient-specific medical advice.

### Architecture Layout Diagram
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

---

## 2. Message Contract & JSON Schema

The system relies on a rigid envelope structure to guarantee reliable deserialization. All RabbitMQ payloads are encapsulated within a `MessageEnvelope` containing transaction tracing (Correlation ID), priority levels, and routing metadata:

```json
{
  "message_id": "8e32ea70-e67c-473d-8182-d249f7e8a931",
  "sender_id": "agent-a",
  "receiver_id": "agent-b",
  "message_type": "TASK_ASSIGNMENT",
  "timestamp": "2026-07-09T07:18:40.125Z",
  "correlation_id": "session-42b781",
  "priority": 2,
  "routing_key": "task.agent-b",
  "payload": {
    "task_id": "task-df38190",
    "parameters": {
      "total_records": 7000,
      "contamination": 0.05,
      "random_seed": 42
    }
  },
  "metadata": {
    "retry_count": 0,
    "max_retries": 3,
    "routing_path": ["agent-a"]
  }
}
```

---

## 3. Communication Flow & Routing Keys

The messaging lifecycle utilizes the direct exchange `anomaly_exchange`. By binding queues to specific routing keys, we coordinate steps asynchronously:

| Step | Source | Recipient | Routing Key / Channel | Message Type | Description |
|---|---|---|---|---|---|
| 1 | Web UI | FastAPI | HTTP POST `/tasks/analyze` | - | User enters label, launches scan. |
| 2 | Agent A | Broker | `task.agent-b` | TASK_ASSIGNMENT | Planner allocates configuration. |
| 3 | Agent B | Agent A | `feedback` | TASK_ACCEPTED | Executor logs task consumption. |
| 4 | Agent B | Agent C | `report` | TASK_PROGRESS (25% - 75%) | Sends simulation and training states. |
| 5 | Agent B | Agent C | `report` | TASK_PROGRESS (100%) | Compiles anomaly report variables. |
| 6 | Agent B | Agent C & A | `report` & `feedback` | TASK_COMPLETED | Pushes finished report details. |
| 7 | Agent C | Agent A | `feedback` | MONITOR_ALERT | Verifies severity alarms (normal/critical). |

### Resilience Features:
*   **Heartbeats**: Agents publish tick messages to the broker every 30s. Agent C monitors timestamps and escalates offline alerts if any node is silent for > 90s.
*   **Dead-Letter Queue (DLQ)**: If Agent B fails to process a task due to code errors, the Pika envelope increments `retry_count`. After 3 retries, the message is routed to the dead-letter exchange (DLX) for diagnostic capture.

---

## 4. Setup and Run Instructions

### Prerequisites
*   Python 3.11 or later.
*   Access to a running RabbitMQ broker (local or CloudAMQP instance).

### Local Installation
1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/Abhishektiwari050/multi-agent-anomaly-system.git
    cd multi-agent-anomaly-system
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
5.  **Run the Server**:
    Start the FastAPI server and agents using supervisord locally:
    ```bash
    supervisord -c supervisord.conf
    ```
    Or run FastAPI directly:
    ```bash
    python -m uvicorn api.main:app --reload
    ```
    Open `http://localhost:8000` to view the clinical dashboard.

---

## 5. Standalone Execution Agent
A self-contained, isolated packaging of **Agent B (Execution Agent)** is provided under the [/execution-agent](file:///C:/Users/abhis/.gemini/antigravity/scratch/multi-agent-anomaly-system/execution-agent/) directory, complete with its own requirements, Dockerfile, unit test suite, and README.

---

## 6. AI Assistance Disclosure Statement

A clear boundary was maintained between ideation and coding phases:
*   **Ideation Phase (Claude)**: Claude was consulted for initial tech choices. It provided architecture comparisons that led to selecting RabbitMQ (TLS direct routing) and supervisord container management, framing the master plan.
*   **Development Phase (Gemini / Antigravity)**: Gemini performed all coding and debugging. This included overriding Pika's SSL verification settings for CloudAMQP compatibility, separating heartbeat channels to prevent socket corruption, building the light-themed CSS clinical dashboard, and solving test harness flakiness using isolated temporary queues.

---
**Developer**: Abhishek Tiwari
