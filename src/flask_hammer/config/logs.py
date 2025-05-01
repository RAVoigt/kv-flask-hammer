# coding=utf-8
import logging
import typing as t

from kvcommon.logger import get_logger as kvc_get_logger
from kvcommon.logger import logging_format_string
from kvcommon.logger import logging_format_string
from kvcommon.logger import logging_format_time

prefix = "kv-flh-"
format_string = logging_format_string
format_time = logging_format_time

def get_logger(
        name: str,
        console_log_level=logging.DEBUG,
        filters: t.Iterable[logging.Filter] | None = None
    ) -> logging.Logger:

    return kvc_get_logger(
        name=f"{prefix}{name}",
        console_log_level=console_log_level,
        logging_format_string=format_string,
        logging_format_time=format_time,
        filters=filters
    )
