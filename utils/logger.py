
import logging
import sys
from config import Config


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger configured with the project's format and level.
    Call once per module:  log = get_logger(__name__)
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers when the function is called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, Config.LOG_LEVEL, logging.INFO))

    fmt = logging.Formatter(Config.LOG_FORMAT)

    # Console handler
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # Optional file handler
    if Config.LOG_FILE:
        try:
            fh = logging.FileHandler(Config.LOG_FILE)
            fh.setFormatter(fmt)
            logger.addHandler(fh)
        except OSError:
            logger.warning("Could not open log file '%s' — logging to console only.", Config.LOG_FILE)

    return logger
