import sys
import functools
import time
from loguru import logger
from config.settings import settings


def setup_logging():
    """Configure loguru logger with structured output."""
    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True,
    )

    # File handler
    logger.add(
        "logs/app.log",
        format=log_format,
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )

    logger.info(f"Logging initialized for {settings.APP_NAME} v{settings.APP_VERSION}")


def log_execution(func=None, *, log_args: bool = True, log_result: bool = False):
    """Aspect-based logging decorator for functions."""
    if func is None:
        return functools.partial(log_execution, log_args=log_args, log_result=log_result)

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__qualname__}"
        log_data = {"function": func_name}
        if log_args and kwargs:
            log_data["kwargs"] = {k: v for k, v in kwargs.items() if k != "password"}

        logger.debug(f"ENTER {func_name}", **log_data)
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.debug(f"EXIT {func_name} [{elapsed:.3f}s]")
            if log_result:
                logger.debug(f"RESULT {func_name}: {result}")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(f"ERROR {func_name} [{elapsed:.3f}s]: {e}")
            raise

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__qualname__}"
        logger.debug(f"ENTER (async) {func_name}")
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.debug(f"EXIT (async) {func_name} [{elapsed:.3f}s]")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(f"ERROR (async) {func_name} [{elapsed:.3f}s]: {e}")
            raise

    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


import os
os.makedirs("logs", exist_ok=True)
setup_logging()
