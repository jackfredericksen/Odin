"""Logging configuration for Odin trading bot."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Dict

import structlog
from structlog.types import EventDict

from odin.config import get_settings


def add_severity_level(
    logger: Any, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add severity level to log records."""
    if method_name == "info":
        event_dict["severity"] = "INFO"
    elif method_name == "warning":
        event_dict["severity"] = "WARNING"
    elif method_name == "error":
        event_dict["severity"] = "ERROR"
    elif method_name == "debug":
        event_dict["severity"] = "DEBUG"
    elif method_name == "critical":
        event_dict["severity"] = "CRITICAL"
    else:
        event_dict["severity"] = "UNKNOWN"
    return event_dict


def setup_logging() -> None:
    """Setup structured logging for the application."""
    settings = get_settings()

    # Create logs directory
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.handlers.RotatingFileHandler(
                settings.log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10 MB
            ),
        ],
    )

    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="ISO"),
        add_severity_level,
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
    ]

    # Add different processors for console vs file
    if sys.stderr.isatty():
        # Pretty console output in development
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a logger instance."""
    return structlog.get_logger(name)
