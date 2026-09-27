"""Opt-in JSON event logging; payload-bearing snapshots are never logged."""

import logging
import os

from app.core.models import Event

logger = logging.getLogger("agent_runtime.events")


def configure_logging() -> None:
    """Enable metadata-only logging with RUNTIME_LOG_LEVEL=INFO."""
    logger.setLevel(os.getenv("RUNTIME_LOG_LEVEL", "WARNING"))
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    logger.propagate = False


def log_event(event: Event) -> None:
    logger.info(event.model_dump_json())
