from enum import StrEnum
import typing as t
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import Histogram

from kvcommon.singleton import SingletonMeta

from kv_flask_hammer.exceptions import FlaskHammerError

from .registry import MetricRegistry


class FlaskMetricsException(FlaskHammerError):
    pass


class UnhandledExceptionSources(StrEnum):
    MIDDLEWARE = "middleware"
    JOB = "job"


class DefaultMetrics(MetricRegistry, metaclass=SingletonMeta):

    def APP_INFO(
        self,
        description: str = "App Info.",
        labelnames: list[str] | None = None,
        name_prefix: str | None = None,
        full_name_override: str | None = None,
    ) -> Gauge:
        if labelnames is None:
            labelnames = ["version", "workers"]
        return t.cast(
            Gauge,
            self.get_or_create(
                metric_class=Gauge,
                name="app_info",
                description=description,
                labelnames=labelnames,
                name_prefix=name_prefix,
                full_name_override=full_name_override,
                multiprocess_mode="mostrecent",
            ),
        )

    def HTTP_RESPONSE_COUNT(
        self,
        description: str = "Count of HTTP responses by status code.",
        labelnames: list[str] | None = None,
        name_prefix: str | None = None,
        full_name_override: str | None = None,
    ) -> Counter:
        if labelnames is None:
            labelnames = ["code", "path"]
        return t.cast(
            Counter,
            self.get_or_create(
                metric_class=Counter,
                name="http_response_total",
                description=description,
                labelnames=labelnames,
                name_prefix=name_prefix,
                full_name_override=full_name_override,
            ),
        )

    def JOB_SECONDS(
        self,
        description: str = "Time taken for a job to complete.",
        labelnames: list[str] | None = None,
        name_prefix: str | None = None,
        full_name_override: str | None = None,
    ) -> Histogram:
        if labelnames is None:
            labelnames = ["job_id"]
        return t.cast(
            Histogram,
            self.get_or_create(
                metric_class=Histogram,
                name="job_seconds",
                description=description,
                labelnames=labelnames,
                name_prefix=name_prefix,
                full_name_override=full_name_override,
            ),
        )

    def SCHEDULER_JOB_EVENT(
        self,
        description: str = "Count of scheduled job events by job id and event key.",
        labelnames: list[str] | None = None,
        name_prefix: str | None = None,
        full_name_override: str | None = None,
    ) -> Counter:
        if labelnames is None:
            labelnames = ["job_id", "event"]
        return t.cast(
            Counter,
            self.get_or_create(
                metric_class=Counter,
                name="scheduler_job_event_total",
                description=description,
                labelnames=labelnames,
                name_prefix=name_prefix,
                full_name_override=full_name_override,
            ),
        )

    def SERVER_REQUEST_SECONDS(
        self,
        description: str = "Time taken for server to handle request.",
        labelnames: list[str] | None = None,
        name_prefix: str | None = None,
        full_name_override: str | None = None,
    ) -> Histogram:
        if labelnames is None:
            labelnames = ["path"]
        return t.cast(
            Histogram,
            self.get_or_create(
                metric_class=Histogram,
                name="server_request_seconds",
                description=description,
                labelnames=labelnames,
                name_prefix=name_prefix,
                full_name_override=full_name_override,
            ),
        )

    def UNHANDLED_EXCEPTIONS(
        self,
        description: str = "Count of unhandled exceptions.",
        labelnames: list[str] | None = None,
        name_prefix: str | None = None,
        full_name_override: str | None = None,
    ) -> Counter:
        if labelnames is None:
            labelnames = ["exc_cls_name", "source"]
        return t.cast(
            Counter,
            self.get_or_create(
                metric_class=Counter,
                name="unhandled_exceptions_total",
                description=description,
                labelnames=labelnames,
                name_prefix=name_prefix,
                full_name_override=full_name_override,
            ),
        )
