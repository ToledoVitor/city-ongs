import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable

from django.db import transaction
from django.http import HttpRequest

logger = logging.getLogger(__name__)


class DetailedFormatter(logging.Formatter):
    """
    Custom formatter that includes additional details in logs.
    """

    def format(self, record):
        # Adds ISO timestamp
        record.timestamp = datetime.now(timezone.utc).isoformat()

        # Adds user information if available
        if hasattr(record, "request"):
            user_email = (
                record.request.user.email
                if record.request.user.is_authenticated
                else "anonymous"
            )
            record.user = user_email

        # Formats exceptions in a more readable way
        if record.exc_info:
            record.exc_text = self.formatException(record.exc_info)

        return super().format(record)


def log_database_operation(operation: str) -> Callable:
    """
    Decorator to log database operations with automatic rollback in
    case of error.

    Args:
        operation (str): Name of the operation being performed
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                with transaction.atomic():
                    result = func(*args, **kwargs)
                    logger.info(
                        "Operation %s performed successfully",
                        operation,
                        extra={
                            "operation": operation,
                            "args": args,
                            "kwargs": kwargs,
                            "result": str(result),
                        },
                    )

                    return result

            except Exception as e:
                logger.error(
                    "Error in operation %s",
                    operation,
                    exc_info=True,
                    extra={
                        "operation": operation,
                        "args": args,
                        "kwargs": kwargs,
                        "error": str(e),
                    },
                )
                raise

        return wrapper

    return decorator


def log_view_access(view_func: Callable) -> Callable:
    """
    Decorator to log view access with performance metrics.
    """

    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
        start_time = datetime.now()

        try:
            response = view_func(request, *args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                "Access to view %s",
                view_func.__name__,
                extra={
                    "view_name": view_func.__name__,
                    "method": request.method,
                    "path": request.path,
                    "user": request.user.email
                    if request.user.is_authenticated
                    else "anonymous",
                    "duration": duration,
                    "status_code": response.status_code,
                },
            )

            return response

        except Exception as e:
            logger.error(
                "Error accessing the view %s",
                view_func.__name__,
                exc_info=True,
                extra={
                    "view_name": view_func.__name__,
                    "method": request.method,
                    "path": request.path,
                    "user": request.user.email
                    if request.user.is_authenticated
                    else "anonymous",
                    "error": str(e),
                },
            )
            raise

    return wrapper


def setup_logging(debug: bool = False) -> None:
    """
    Configures the logging system with appropriate handlers.

    Args:
        debug (bool): If True, enables debug logs
    """
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "()": DetailedFormatter,
                "format": "%(timestamp)s [%(levelname)s] %(name)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "detailed",
                "level": "DEBUG" if debug else "INFO",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "app.log",
                "maxBytes": 1024 * 1024 * 5,  # 5 MB
                "backupCount": 5,
                "formatter": "detailed",
                "level": "INFO",
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": "DEBUG" if debug else "INFO",
                "propagate": True,
            }
        },
    }

    logging.config.dictConfig(config)
