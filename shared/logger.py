import sys
import os
from loguru import logger

def setup_logger(agent_name: str):
    logger.remove()
    
    def console_formatter(record):
        agent = record["extra"].get("agent", agent_name)
        return f"<green>{{time:HH:mm:ss}}</green> | <level>{{level: <8}}</level> | <cyan>{agent}</cyan> | {{message}}\n"
        
    def file_formatter(record):
        agent = record["extra"].get("agent", agent_name)
        return f"{{time:YYYY-MM-DD HH:mm:ss.SSS}} | {{level: <8}} | {agent} | {{message}}\n"
    
    # Console layout
    logger.add(
        sys.stdout,
        format=console_formatter,
        colorize=True,
        level="INFO"
    )
    
    # File logging directory setup
    log_dir = os.getenv("LOG_DIR", "./logs")
    os.makedirs(log_dir, exist_ok=True)
    
    logger.add(
        os.path.join(log_dir, f"{agent_name}.log"),
        format=file_formatter,
        rotation="10 MB",
        retention="7 days",
        level="DEBUG"
    )
    
    return logger.bind(agent=agent_name)
