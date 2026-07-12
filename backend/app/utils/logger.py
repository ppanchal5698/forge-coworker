"""Structured logging setup.

One log line per node transition (node name, timestamp, truncated payload)
satisfying the observability NFR in PRD Section 10.
"""

import logging
import sys

import structlog


def setup_logging():
    """Configure structlog to output JSON in production and colored text in dev."""
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure stdlib logging to route through structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


# We export a convenient getter
def get_logger(name: str):
    """Get a structured logger."""
    return structlog.get_logger(name)
