import sys
import os
from dotenv import load_dotenv

# Ensure the root project path is in the sys.path for importing shared package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

load_dotenv()

from shared.logger import setup_logger
from agents.agent_a.planner import Planner
from agents.agent_a.heartbeat import HeartbeatThread

logger = setup_logger("agent-a-main")

def main():
    logger.info("Initializing Agent A (Planner)...")
    planner = Planner()
    
    # Start heartbeat thread
    heartbeat = HeartbeatThread(agent_id="agent-a")
    heartbeat.start()
    
    # Run consumer loops
    try:
        planner.run_consumer()
    except Exception as e:
        logger.critical(f"Agent A consumer failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
