"""Application logging configured for source and packaged Windows builds."""

import logging
import os
from logging.handlers import RotatingFileHandler

from storage import app_data_dir


def configure_logging() -> str | None:
    log_dir = os.path.join(app_data_dir(), "logs")
    try:
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "softcurse.log")
        handler = RotatingFileHandler(
            log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        ))
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)
        return log_path
    except OSError:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger(__name__).exception("Could not initialize file logging")
        return None
