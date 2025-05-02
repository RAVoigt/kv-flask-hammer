# coding=utf-8
import logging
import typing as t

from kvcommon.logger import get_logger as kvc_get_logger

from kv_flask_hammer.config import logs


def get_logger(
    name: str, console_log_level=logging.DEBUG, filters: t.Iterable[logging.Filter] | None = None
) -> logging.Logger:

    return kvc_get_logger(
        name=f"{logs.prefix}{name}",
        console_log_level=console_log_level,
        logging_format_string=logs.format_string,
        logging_format_time=logs.format_time,
        filters=filters,
    )
