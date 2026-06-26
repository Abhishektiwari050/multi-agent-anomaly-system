import os

# Exchange names
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "agent.events")
DLX_NAME = os.getenv("DLX_NAME", "agent.dlx")

# Routing Keys
ROUTING_KEY_TASK_AGENT_B = "task.agent-b"
ROUTING_KEY_REPORT = "report.task-status"
ROUTING_KEY_HEARTBEAT = "heartbeat.agent"
ROUTING_KEY_FEEDBACK = "feedback.agent-a"
ROUTING_KEY_DLQ = "dead.letter"

# Queue names
QUEUE_AGENT_B_TASKS = "agent.b.tasks"
QUEUE_AGENT_C_REPORTS = "agent.c.reports"
QUEUE_AGENT_A_FEEDBACK = "agent.a.feedback"
QUEUE_DLQ = "agent.dlq"

# Queue bindings map: Queue -> list of (Routing Key Pattern)
QUEUE_BINDINGS = {
    QUEUE_AGENT_B_TASKS: ["task.#"],
    QUEUE_AGENT_C_REPORTS: ["report.#", "heartbeat.#"],
    QUEUE_AGENT_A_FEEDBACK: ["feedback.#"],
}
