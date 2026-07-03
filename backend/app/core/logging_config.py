#Logging Configuration.

import logging
import sys
from typing import Any

import structlog
from structlog.processors import JSONNRenderer

from app.config import settings

def configure_logging() -> None:
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contectvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
    ]

    if settings.is_development:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else: 
        # JSON formatting for production
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            JSONRenderer(),
        ]    

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )    

    # Configure standard library logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.getLevelName(settings.stdlib.BoundLogger),
    )    

def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)


# TODO: Add correlation ID processor for distributed tracing
# TODO: Add PII masking processor for GDPR compliance
# TODO: Add log sampling processor for high-traffic endpoints
# TODO: Add metrics extraction from logs

# Future Enhancements:
    # - Add log aggregation (ELK Stack, Splunk, Datadog)
    # - Add distributed tracing correlation IDs
    # - Add log sampling for high-volume endpoints
    # - Add PII masking in logs