import sys

from loguru import logger

from src.app.core.config import get_settings

__all__ = ["logger", "setup_logger"]

_PRETTY_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level:<8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def setup_logger() -> None:
    settings = get_settings()
    logger.remove()
    if settings.log_format == "json":
        _ = logger.add(sys.stderr, level=settings.log_level, serialize=True)
    else:
        _ = logger.add(sys.stderr, level=settings.log_level, format=_PRETTY_FORMAT)
