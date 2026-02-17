import logging
import os
from typing import Tuple, List

DEFAULT_LOG_FILE = "logs/noxfeed.log"
DEFAULT_LEVEL = "INFO"


def _ensure_log_dir(log_file: str) -> None:
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)


def _clear_handlers(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)


def configure_loggers(
    log_file: str = DEFAULT_LOG_FILE, level: str = DEFAULT_LEVEL
) -> Tuple[logging.Logger, logging.Logger, logging.Logger]:
    """
    Configures and returns loggers for api, file, and console.

    Returns:
        (api_logger, file_logger, console_logger)
    """
    _ensure_log_dir(log_file)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    api_logger = logging.getLogger("api")
    file_logger = logging.getLogger("file")
    console_logger = logging.getLogger("console")

    for logger in (api_logger, file_logger, console_logger):
        logger.setLevel(level)
        logger.propagate = False
        _clear_handlers(logger)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    api_logger.addHandler(console_handler)
    file_logger.addHandler(file_handler)
    console_logger.addHandler(console_handler)

    return api_logger, file_logger, console_logger


def configure_loggers_with_targets(
    log_file: str = DEFAULT_LOG_FILE,
    level: str = DEFAULT_LEVEL,
    targets: List[str] = None,
) -> None:
    """
    Configure loggers with specific targets.

    Args:
        log_file: Path to the log file
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        targets: List of logging targets ('file', 'api', 'console')
    """
    if targets is None:
        targets = ["file", "api"]

    _ensure_log_dir(log_file)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    global api_logger, file_logger, console_logger

    api_logger = logging.getLogger("api")
    file_logger = logging.getLogger("file")
    console_logger = logging.getLogger("console")

    for logger in (api_logger, file_logger, console_logger):
        logger.setLevel(level)
        logger.propagate = False
        _clear_handlers(logger)

    # File handler
    if "file" in targets:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    if "console" in targets:
        console_logger.addHandler(console_handler)

    # API logger outputs to console OR file based on targets
    if "api" in targets:
        if "console" in targets:
            api_logger.addHandler(console_handler)
        elif "file" in targets:
            file_handler_api = logging.FileHandler(log_file, encoding="utf-8")
            file_handler_api.setLevel(level)
            file_handler_api.setFormatter(formatter)
            api_logger.addHandler(file_handler_api)


api_logger, file_logger, console_logger = configure_loggers()
