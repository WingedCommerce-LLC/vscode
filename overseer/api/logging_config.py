"""
Structured logging configuration for Overseer API.

This module provides centralized logging configuration with structured output,
request correlation IDs, and different log levels for different environments.
"""

import logging
import logging.config
import sys
import uuid
from contextvars import ContextVar
from typing import Dict, Any

from config.settings import get_settings

settings = get_settings()

# Context variable for request correlation ID
request_id_var: ContextVar[str] = ContextVar('request_id', default='')


class CorrelationFilter(logging.Filter):
    """
    Logging filter that adds correlation ID to log records.
    """

    def filter(self, record):
        record.correlation_id = request_id_var.get('')
        return True


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs in production
    and human-readable logs in development.
    """

    def format(self, record):
        if settings.is_production:
            # JSON structured logging for production
            import json
            log_entry = {
                'timestamp': self.formatTime(record),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
            }

            # Add correlation ID if available
            if hasattr(record, 'correlation_id') and record.correlation_id:
                log_entry['correlation_id'] = record.correlation_id

            # Add exception info if present
            if record.exc_info:
                log_entry['exception'] = self.formatException(record.exc_info)

            # Add extra fields
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno',
                              'pathname', 'filename', 'module', 'lineno',
                              'funcName', 'created', 'msecs', 'relativeCreated',
                              'thread', 'threadName', 'processName', 'process',
                              'getMessage', 'exc_info', 'exc_text', 'stack_info',
                              'correlation_id']:
                    log_entry[key] = value

            return json.dumps(log_entry)
        else:
            # Human-readable logging for development
            correlation_id = getattr(record, 'correlation_id', '')
            correlation_part = f" [{correlation_id}]" if correlation_id else ""

            formatted = super().format(record)
            return f"{formatted}{correlation_part}"


def setup_logging():
    """
    Configure logging for the application.
    """

    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Configure root logger (don't use basicConfig with custom formatter)
    # We'll set up our own handler instead

    # Get root logger and add correlation filter
    root_logger = logging.getLogger()

    # Clear existing handlers and add our custom handler
    root_logger.handlers.clear()

    # Create handler with structured formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.addFilter(CorrelationFilter())
    handler.setFormatter(StructuredFormatter())

    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Configure specific loggers
    loggers_config = {
        'uvicorn': log_level,
        'uvicorn.access': logging.WARNING if settings.is_production else logging.INFO,
        'sqlalchemy.engine': logging.WARNING if settings.is_production else logging.INFO,
        'sqlalchemy.pool': logging.WARNING,
        'alembic': logging.INFO,
        'overseer': log_level,
    }

    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured - Level: {settings.LOG_LEVEL}, "
        f"Environment: {settings.ENVIRONMENT}, "
        f"Structured: {settings.is_production}"
    )


def get_correlation_id() -> str:
    """
    Get the current request correlation ID.

    Returns:
        str: Current correlation ID or empty string if not set
    """
    return request_id_var.get('')


def set_correlation_id(correlation_id: str = None) -> str:
    """
    Set the correlation ID for the current request.

    Args:
        correlation_id: Optional correlation ID. If not provided, generates a new UUID.

    Returns:
        str: The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    request_id_var.set(correlation_id)
    return correlation_id


def clear_correlation_id():
    """
    Clear the current correlation ID.
    """
    request_id_var.set('')


# Convenience function to get a logger with the module name
def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with optional name.

    Args:
        name: Logger name. If not provided, uses the caller's module name.

    Returns:
        logging.Logger: Configured logger instance
    """
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'overseer')

    return logging.getLogger(name)
