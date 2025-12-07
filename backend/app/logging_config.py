"""Structured logging configuration using structlog"""
import logging
import sys
from typing import Any
import structlog
from app.config import settings


def setup_logging() -> None:
    """Configure structured logging for the application"""
    
    # Determine log level
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Configure structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add JSON renderer for production, console renderer for development
    if settings.ENVIRONMENT == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """
    Get a structured logger instance
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Structured logger instance
    
    Usage:
        logger = get_logger(__name__)
        logger.info("processing_event", event_id=event.id, contract=event.contract)
    """
    return structlog.get_logger(name)
