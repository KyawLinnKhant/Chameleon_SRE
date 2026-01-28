"""
Utility functions for logging, error handling, and common operations.
"""

import sys
from datetime import datetime
from pathlib import Path

from loguru import logger

from src.config import settings


def setup_logging(verbose: bool = True) -> None:
    """
    Configure Loguru logging with appropriate levels and formatting.
    
    Args:
        verbose: If True, use DEBUG level; otherwise INFO
    """
    # Remove default handler
    logger.remove()
    
    # Determine log level
    level = "DEBUG" if verbose or settings.verbose else "INFO"
    
    # Console handler with colors
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    
    # File handler for persistent logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "chameleon-sre_{time}.log",
        rotation="100 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
    )
    
    logger.info(f"Logging initialized at {level} level")


def format_kubectl_output(output: str, max_lines: int = 50) -> str:
    """
    Format kubectl output for better readability.
    
    Args:
        output: Raw kubectl output
        max_lines: Maximum lines to display
        
    Returns:
        str: Formatted output
    """
    lines = output.strip().split("\n")
    
    if len(lines) <= max_lines:
        return output
    
    # Truncate and add summary
    truncated = "\n".join(lines[:max_lines])
    remaining = len(lines) - max_lines
    
    return f"{truncated}\n\n... ({remaining} more lines truncated)"


def sanitize_command(command: str) -> str:
    """
    Sanitize a kubectl command by removing dangerous patterns.
    
    Args:
        command: Raw command string
        
    Returns:
        str: Sanitized command (or raises ValueError if dangerous)
    """
    dangerous_patterns = [
        "rm -rf",
        "delete",
        "drain",
        "cordon",
        "taint",
    ]
    
    command_lower = command.lower()
    
    for pattern in dangerous_patterns:
        if pattern in command_lower and not settings.allow_destructive_commands:
            raise ValueError(
                f"Dangerous command detected: '{pattern}'. "
                f"Set ALLOW_DESTRUCTIVE_COMMANDS=true to enable."
            )
    
    return command


def create_timestamp() -> str:
    """
    Create an ISO 8601 timestamp string.
    
    Returns:
        str: Timestamp in format YYYY-MM-DD HH:MM:SS
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Truncate text to a maximum length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum allowed length
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."


def extract_error_message(error: Exception) -> str:
    """
    Extract a clean error message from an exception.
    
    Args:
        error: Exception object
        
    Returns:
        str: Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    return f"{error_type}: {error_msg}"


if __name__ == "__main__":
    # Test logging
    setup_logging(verbose=True)
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test sanitization
    try:
        sanitize_command("kubectl get pods")
        logger.info("✅ Safe command passed")
    except ValueError as e:
        logger.error(f"❌ {e}")
    
    try:
        sanitize_command("kubectl delete pod dangerous")
        logger.error("❌ Dangerous command should have been blocked!")
    except ValueError as e:
        logger.info(f"✅ Dangerous command blocked: {e}")
