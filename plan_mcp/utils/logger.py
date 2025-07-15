"""Logging configuration for Plan-MCP."""

import sys

from loguru import logger

from ..config import get_config


def setup_logger() -> None:
    """Set up the logger with the configured level and format."""
    config = get_config()

    # Remove default logger
    logger.remove()

    # Add custom logger with our format
    logger.add(
        sys.stderr,
        level=config.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # Optionally add file logging
    if config.log_level == "DEBUG":
        logger.add(
            "logs/plan_mcp_{time}.log",
            level="DEBUG",
            rotation="1 day",
            retention="7 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        )


# Set up logger when module is imported
setup_logger()
