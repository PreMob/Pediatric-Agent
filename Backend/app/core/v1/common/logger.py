import asyncio
import functools
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

LOG_LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

DEFAULT_LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"


def get_logger(
    name: str,
    save_log_file: bool = True,
    level: str = os.getenv("LOG_LEVEL", "info").lower(),
    rich_console: bool = True,
    format: str = "%(message)s",
    rich_format: str = "%(message)s",
    date_format: str = "[%Y-%m-%d %H:%M:%S]",
) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Name of the logger
        log_file: Optional path to log file
        level: Logging level (default: INFO)
        rich_console: Whether to use rich console logging (default: True)
        format: Format for file logging
        rich_format: Format for rich console logging
        date_format: Date format for logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    log_level = LOG_LEVEL_MAP.get(level.lower(), logging.INFO)
    logger.setLevel(log_level)

    # Remove existing handlers
    logger.handlers = []

    # Console handler with rich formatting
    if rich_console:
        console_handler = RichHandler(
            console=Console(force_terminal=False),
            show_time=True,
            show_path=False,
            markup=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )
        console_handler.setFormatter(
            logging.Formatter(rich_format, datefmt=date_format)
        )
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(format, datefmt=date_format))

    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    # File handler if log_file is specified
    if save_log_file:
        log_path = DEFAULT_LOG_DIR / f"{name}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(logging.Formatter(format, datefmt=date_format))
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

    return logger


def log_execution(logger: Optional[logging.Logger] = None):
    """
    Decorator to log function execution with timing.

    Args:
        logger: Logger instance to use. If None, creates a new logger.
    """

    def decorator(func):
        # Create logger if not provided
        actual_logger = logger if logger is not None else get_logger(func.__module__)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now()
            actual_logger.info(f"Starting {func.__name__}")
            try:
                result = await func(*args, **kwargs)
                execution_time = datetime.now() - start_time
                actual_logger.info(f"Completed {func.__name__} in {execution_time}")
                return result
            except Exception as e:
                execution_time = datetime.now() - start_time
                actual_logger.error(
                    f"Error in {func.__name__} after {execution_time}: {str(e)}",
                    exc_info=True,
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now()
            actual_logger.info(f"Starting {func.__name__}")
            try:
                result = func(*args, **kwargs)
                execution_time = datetime.now() - start_time
                actual_logger.info(f"Completed {func.__name__} in {execution_time}")
                return result
            except Exception as e:
                execution_time = datetime.now() - start_time
                actual_logger.error(
                    f"Error in {func.__name__} after {execution_time}: {str(e)}",
                    exc_info=True,
                )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator