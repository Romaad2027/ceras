import logging
import os
from typing import Optional


def _get_log_level(env_name: str = "LOG_LEVEL", default: str = "INFO") -> int:
    level_str = os.getenv(env_name, default).upper()
    return getattr(logging, level_str, logging.INFO)


def configure_logging(
    *,
    level: Optional[int] = None,
    fmt: Optional[str] = None,
    datefmt: Optional[str] = None,
) -> None:
    """
    Configure application-wide logging for the 'risk_analysis' logger hierarchy.
    Respects LOG_LEVEL env var. Intended to be called once during startup.
    """
    effective_level = level if level is not None else _get_log_level()
    effective_fmt = (
        fmt if fmt is not None else "%(asctime)s %(levelname)s %(name)s - %(message)s"
    )
    effective_datefmt = datefmt if datefmt is not None else "%Y-%m-%d %H:%M:%S"

    root_logger = logging.getLogger()
                                        
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(effective_fmt, effective_datefmt))
        root_logger.addHandler(handler)

                                                 
    logging.getLogger("risk_analysis").setLevel(effective_level)
    root_logger.setLevel(effective_level)

                                                         
    logging.getLogger("aiokafka").setLevel(
        _get_log_level("LOG_LEVEL_AIOKAFKA", "WARNING")
    )
    logging.getLogger("sqlalchemy.engine").setLevel(
        _get_log_level("LOG_LEVEL_SQLA_ENGINE", "WARNING")
    )
                                                                            
    logging.getLogger("uvicorn").setLevel(_get_log_level("LOG_LEVEL_UVICORN", "INFO"))
    logging.getLogger("uvicorn.error").setLevel(
        _get_log_level("LOG_LEVEL_UVICORN_ERROR", "INFO")
    )
    logging.getLogger("uvicorn.access").setLevel(
        _get_log_level("LOG_LEVEL_UVICORN_ACCESS", "WARNING")
    )
