import os
import sys
import signal
from dotenv import load_dotenv
from loguru import logger
from executor import Executor, HeartbeatThread

# Load environment configuration
load_dotenv()

# Setup log format
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <7}</level> | <cyan>execution-agent</cyan> | {message}",
    level="INFO"
)

active_executor = None
active_heartbeat = None

def handle_shutdown(signum, frame):
    logger.info("Shutdown signal received. Cleansing connections...")
    
    if active_heartbeat:
        active_heartbeat.stop()
        
    if active_executor:
        active_executor.disconnect()
        
    logger.info("Standalone Execution Agent terminated cleanly.")
    sys.exit(0)

# Register shutdown signals
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

def main():
    global active_executor, active_heartbeat
    
    logger.info("Initializing Standalone Clinical Execution Agent (Agent B)...")
    
    # 1. Start Heartbeat Thread
    active_heartbeat = HeartbeatThread("agent-b")
    active_heartbeat.start()
    
    # 2. Start Message Consumer
    active_executor = Executor()
    try:
        active_executor.run_consumer()
    except Exception as e:
        logger.critical(f"Standalone agent failed with critical error: {e}")
        handle_shutdown(None, None)

if __name__ == "__main__":
    main()
