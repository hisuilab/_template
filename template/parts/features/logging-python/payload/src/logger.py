"""Logging configuration."""

from __future__ import annotations

import logging
import os


def get_logger(name: str) -> logging.Logger:
    level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_str, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    return logging.getLogger(name)
