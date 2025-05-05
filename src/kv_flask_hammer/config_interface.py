import typing as t

from flask_http_middleware import BaseHTTPMiddleware
from prometheus_client import Histogram

from kvcommon.singleton import SingletonMeta

from kv_flask_hammer import config
from kv_flask_hammer import constants
from kv_flask_hammer.exceptions import FlaskHammerError
from kv_flask_hammer.exceptions import ImmutableConfigError
from kv_flask_hammer.middleware import FlaskHammerMiddleware


class FlaskHammer_Interface_Config(metaclass=SingletonMeta):
    _started: bool = False
    _modified: bool = False

    def _raise_if_started(self):
        self._modified = True
        if self._started:
            raise ImmutableConfigError("Config is immutable once FlaskHammer has been started.")

    def mark_immutable(self):
        self._started = True

    @property
    def modified(self) -> bool:
        return self._modified

    @property
    def started(self) -> bool:
        return self._started

    # TODO: we can probably ditch the self._raise_if_started() calls with some attr metamagic

    # ======== Flask
    def set_ip_port(self, ip: str = constants.default_bind_ip, port: str | int = constants.default_bind_port):
        self._raise_if_started()
        config.app.bind_ip = ip
        config.app.bind_port = port

    def flask_set_secret_key(self, key: str):
        self._raise_if_started()
        config.misc.flask_secret_key = key

    # ======== Gunicorn
    def gunicorn_set_worker_count(self, workers: int):
        self._raise_if_started()
        config.app.gunicorn_worker_count = workers

    def gunicorn_set_worker_timeout(self, timeout: int):
        self._raise_if_started()
        config.app.gunicorn_worker_timeout = timeout

    def gunicorn_set_worker_type(self, worker_type: str):
        self._raise_if_started()
        allowed_types = ("gthread", "sync", "gevent")
        if worker_type not in allowed_types:
            raise FlaskHammerError(f"Worker type must be one of: {allowed_types}")
        config.app.gunicorn_worker_type = worker_type

    def gunicorn_set_keepalive(self, keepalive: int):
        self._raise_if_started()
        config.app.gunicorn_keepalive = keepalive

    def gunicorn_set_log_level(self, log_level: str):
        self._raise_if_started()
        allowed_levels = ("debug", "info", "warning", "error", "critical")
        if log_level not in allowed_levels:
            raise FlaskHammerError(f"Gunicorn log level must be one of: {allowed_levels}")
        config.app.gunicorn_log_level = log_level

    def gunicorn_set_accesslog_format(self, log_format: str):
        self._raise_if_started()
        config.app.gunicorn_accesslog_format = log_format

    # ======== Jobs
    def jobs_enable(self):
        self._raise_if_started()
        config.jobs.enabled = True

    def jobs_disable(self):
        self._raise_if_started()
        config.jobs.enabled = False

    def set_default_job_time_metric(self, metric: Histogram):
        self._raise_if_started()
        config.jobs.default_job_time_metric = metric

    # ======== Logging
    def logging_set_prefix(self, prefix: str):
        self._raise_if_started()
        config.logs.prefix = prefix

    def logging_set_format_string(self, format_string: str):
        self._raise_if_started()
        config.logs.format_string = format_string

    def logging_set_format_time(self, format_time: str):
        self._raise_if_started()
        config.logs.format_time = format_time

    # ======== Healthz routes
    def healthz_view_enable(self):
        self._raise_if_started()
        config.views.default_healthz_enabled = True

    def healthz_set_route_prefix(self, prefix: str):
        self._raise_if_started()
        config.views.healthz_route_prefix = prefix

    def healthz_set_callbacks(self, liveness: t.Callable[[], bool], readiness: t.Callable[[], bool]):
        self._raise_if_started()
        config.views.healthz_liveness_callback = liveness
        config.views.healthz_readiness_callback = readiness

    # ======== Meta routes
    def meta_view_enable(self):
        self._raise_if_started()
        config.views.default_meta_enabled = True

    def meta_view_set_debug_info_callback(self, debug: t.Callable[[], str]):
        self._raise_if_started()
        config.views.meta_debug_info_callback = debug

    # ======== Middleware
    def middleware_enable(self):
        self._raise_if_started()
        config.middleware.enabled = True
        self.middleware_set_cls(FlaskHammerMiddleware)

    def middleware_set_cls(self, middleware_cls: t.Type[BaseHTTPMiddleware]):
        self._raise_if_started()
        config.middleware.middleware_cls = middleware_cls

    def middleware_add_server_request_metric(self, metric: Histogram):
        self._raise_if_started()
        config.middleware.server_request_metric = metric

    # ======== Metrics
    def metrics_enable(self):
        self._raise_if_started()
        config.observ.metrics_enabled = True

    def metrics_disable(self):
        self._raise_if_started()
        config.observ.metrics_enabled = False

    def metrics_set_prefix(self, prefix: str):
        self._raise_if_started()
        config.observ.metrics_label_prefix = prefix

    def metrics_set_ip_port(
        self, ip: str = constants.default_metrics_ip, port: str | int = constants.default_metrics_port
    ):
        self._raise_if_started()
        config.observ.metrics_ip = ip
        config.observ.metrics_port = port

    # ======== Traces
    def traces_enable(self):
        self._raise_if_started()
        config.observ.traces_enabled = True

    def traces_disable(self):
        self._raise_if_started()
        config.observ.traces_enabled = False

    def traces_set_endpoint_url(self, url: str):
        self._raise_if_started()
        config.observ.traces_endpoint_url = url