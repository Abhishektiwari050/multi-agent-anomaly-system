import os
import sys

from dotenv import load_dotenv

# Ensure the root project path is in the sys.path for importing shared package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

load_dotenv()

from agents.agent_b.executor import Executor
from agents.agent_b.heartbeat import HeartbeatThread
from shared.logger import setup_logger

logger = setup_logger("agent-b-main")


def main():
    logger.info("Initializing Agent B (Executor)...")
    executor = Executor()

    # Start heartbeat thread
    heartbeat = HeartbeatThread(agent_id="agent-b")
    heartbeat.start()

    # Run consumer loops
    try:
        executor.run_consumer()
    except Exception as e:
        logger.critical(f"Agent B consumer failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
