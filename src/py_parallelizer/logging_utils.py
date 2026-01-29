"""Logging utilities for parallel execution with tqdm progress bars."""

import logging

from tqdm import tqdm


class TqdmLoggingHandler(logging.Handler):
    """
    Logging handler that works with tqdm progress bars.

    This handler ensures that log messages are written using tqdm.write()
    so they don't interfere with progress bar display.
    """

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
    """
    Set up a logger with the TqdmLoggingHandler.

    Parameters
    ----------
    name : str
        The name of the logger (typically __name__).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    # Only add handler if not already present
    if not any(isinstance(h, TqdmLoggingHandler) for h in logger.handlers):
        logger.addHandler(TqdmLoggingHandler())
    return logger
