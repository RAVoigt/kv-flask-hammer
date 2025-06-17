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
        name_prefix: str | None = None,
        full_name_override: str | None = None,
    ) -> Gauge:
        return t.cast(
            Gauge,
            self.get_or_create(
                metric_class=Gauge,
                name="app_info",
                description="App Info.",
                labelnames=["version", "workers"],
                name_prefix=name_prefix,
                full_name_override=full_name_override,
                multiprocess_mode="mostrecent",
            ),
        )

    def HTTP_RESPONSE_COUNT(
        self,
        name_prefix: str | None = None,
        full_name_override: str | None = None,
    ) -> Counter:
        return t.cast(
            Counter,
            self.get_or_create(
                metric_class=Counter,
                name="http_response_total",
                description="Count of HTTP responses by status code.",
                labelnames=["code", "path"],
                name_prefix=name_prefix,
                full_name_override=full_name_override,
            ),
        )

    def JOB_SECONDS(
        self,
        name_prefix: str | None = None,
        full_name_override: str | None = None,
    ) -> Histogram:
        return t.cast(
            Histogram,
            self.get_or_create(
                metric_class=Histogram,
                name="job_seconds",
                description="Time taken for a job to complete.",
                labelnames=["job_id"],
                name_prefix=name_prefix,
                full_name_override=full_name_override,
            ),
        )

    def SCHEDULER_JOB_EVENT(
        self,
        name_prefix: str | None = None,
        full_name_override: str | None = None,
    ) -> Counter:
        return t.cast(
            Counter,
            self.get_or_create(
                metric_class=Counter,
                name="scheduler_job_event_total",
                description="Count of scheduled job events by job id and event key.",
                labelnames=["job_id", "event"],
                name_prefix=name_prefix,
                full_name_override=full_name_override,
            ),
        )

    def SERVER_REQUEST_SECONDS(
        self,
        name_prefix: str | None = None,
        full_name_override: str | None = None,
    ) -> Histogram:
        return t.cast(
            Histogram,
            self.get_or_create(
                metric_class=Histogram,
                name="server_request_seconds",
                description="Time taken for server to handle request.",
                labelnames=["path"],
                name_prefix=name_prefix,
                full_name_override=full_name_override,
            ),
        )

    def UNHANDLED_EXCEPTIONS(
        self,
        name_prefix: str | None = None,
        full_name_override: str | None = None,
    ) -> Counter:
        return t.cast(
            Counter,
            self.get_or_create(
                metric_class=Counter,
                name="unhandled_exceptions_total",
                description="Count of unhandled exceptions.",
                labelnames=["exc_cls_name", "source"],
                name_prefix=name_prefix,
                full_name_override=full_name_override,
            ),
        )
