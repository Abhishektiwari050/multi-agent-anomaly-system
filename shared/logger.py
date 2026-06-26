import sys
import os
from loguru import logger

def setup_logger(agent_name: str):
    logger.remove()
    
    # Console layout
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
               "<cyan>{extra[agent]}</cyan> | {message}",
        colorize=True,
        level="INFO"
    )
    
    # File logging directory setup
    log_dir = os.getenv("LOG_DIR", "./logs")
    os.makedirs(log_dir, exist_ok=True)
    
    logger.add(
        os.path.join(log_dir, f"{agent_name}.log"),
        rotation="10 MB",
        retention="7 days",
        level="DEBUG"
    )
    
    return logger.bind(agent=agent_name)
