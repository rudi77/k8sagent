"""
Logging configuration for the K8s monitoring agent.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from src.config.settings import settings


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: str = "INFO",
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Set up a logger with console and file handlers.
    
    Args:
        name: Name of the logger
        log_file: Path to the log file
        level: Logging level
        format_string: Custom format string for log messages
        
    Returns:
        logging.Logger: Configured logger instance
    """
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create formatters and handlers
    formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file is provided)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_file))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Create default logger instance
logger = setup_logger(
    name="k8s_monitor",
    log_file=settings.log_file,
    level=settings.log_level,
) 