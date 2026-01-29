"""Logging utilities for parallel execution with tqdm progress bars."""

import logging

from tqdm import tqdm


class TqdmLoggingHandler(logging.Handler):
    """Logging handler that writes messages via tqdm.write() to avoid progress bar interference."""

    def __init__(self, level: int = logging.NOTSET):
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with TqdmLoggingHandler."""
    logger = logging.getLogger(name)
    if not any(isinstance(h, TqdmLoggingHandler) for h in logger.handlers):
        logger.addHandler(TqdmLoggingHandler())
    return logger
