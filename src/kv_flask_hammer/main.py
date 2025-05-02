import logging
import os
import typing as t

from flask import Blueprint
from flask import Flask
from flask_http_middleware import BaseHTTPMiddleware
from flask_http_middleware import MiddlewareManager
from prometheus_client import Histogram

from kvcommon.flask_utils.scheduler import Scheduler
from kvcommon.singleton import SingletonMeta

from kv_flask_hammer import config
from kv_flask_hammer import constants
from kv_flask_hammer import jobs
from kv_flask_hammer.exceptions import AlreadyStartedError
from kv_flask_hammer.exceptions import FlaskHammerError
from kv_flask_hammer.exceptions import ImmutableConfigError
from kv_flask_hammer.gunicorn_app import FlaskHammerGunicornApp
from kv_flask_hammer.gunicorn_app import gunicorn_funcs
from kv_flask_hammer.logger import get_logger
from kv_flask_hammer.middleware import FlaskHammerMiddleware
from kv_flask_hammer.observ.metrics import init_metrics
from kv_flask_hammer.observ.traces import init_traces
from kv_flask_hammer.views.healthz import setup_default_healthz
from kv_flask_hammer.views.meta import setup_default_meta


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

    def traces_set_endpoint_url(self, url: str):
        self._raise_if_started()
        config.observ.traces_endpoint_url = url


class FlaskHammer(metaclass=SingletonMeta):
    _flask_app: Flask
    _config: FlaskHammer_Interface_Config
    _started: bool = False
    version: str | None = None

    def __init__(self, flask_app: Flask | None = None, version: str | None = None) -> None:
        self._config = FlaskHammer_Interface_Config()
        self._flask_app = flask_app or Flask(__name__)
        self.version = version

    @property
    def config(self):
        if not self._started:
            return self._config
        raise ImmutableConfigError("Config is immutable once FlaskHammer has been started.")

    @property
    def flask_app(self) -> Flask:
        return self._flask_app

    @property
    def job_scheduler(self) -> Scheduler:
        """
        APScheduler instance can be retrieved from 'ap_scheduler' attr of the object returned by this property
        """
        return jobs.scheduler

    @property
    def started(self) -> bool:
        return self._started

    def start(self):
        if not self._config.modified:
            self.get_logger("kv-flh").warning(
                "Starting FlaskHammer with default config. Config cannot be modified once started."
            )
        self._config.mark_immutable()
        flask_app: Flask = self.flask_app

        if config.misc.flask_secret_key:
            flask_app.secret_key = config.misc.flask_secret_key

        # ======== Middleware

        if config.middleware.enabled:
            flask_app.wsgi_app = MiddlewareManager(flask_app)

            if config.middleware.middleware_cls:
                flask_app.wsgi_app.add_middleware(config.middleware.middleware_cls)

        # ======== Default Views

        if config.views.default_healthz_enabled:
            bp_healthz = setup_default_healthz(
                prefix=config.views.healthz_route_prefix,
                liveness_callback=config.views.healthz_liveness_callback,
                readiness_callback=config.views.healthz_readiness_callback,
            )
            self._flask_app.register_blueprint(bp_healthz)

        if config.views.default_healthz_enabled:
            bp_meta = setup_default_meta(
                prefix=config.views.meta_route_prefix,
                debug_info_callback=config.views.meta_debug_info_callback,
            )
            self._flask_app.register_blueprint(bp_meta)

        # ======== Observ - Metrics
        if config.observ.metrics_enabled:
            init_metrics(flask_app)

        # ======== Observ - Traces
        if config.observ.traces_enabled:
            init_traces(flask_app)

        # ======== Periodic Jobs
        if config.jobs.enabled:
            jobs.init(flask_app)

        # ======== Finish up
        self._started = True

        return self._flask_app

    @staticmethod
    def get_logger(name: str, console_log_level=logging.DEBUG, filters: t.Iterable[logging.Filter] | None = None):
        return get_logger(name, console_log_level, filters)

    def register_blueprint(self, bp: Blueprint):
        self.flask_app.register_blueprint(bp)

    def add_periodic_job(
        self,
        job_func: t.Callable,
        job_id: str,
        interval_seconds: int,
        metric: Histogram | None = None,
        metric_labels: dict[str, str] | None = None,
    ):
        if self._started:
            raise AlreadyStartedError("Cannot add jobs after FlaskHammer has started")
        jobs.add_job(job_func, job_id, interval_seconds, metric, metric_labels)

    def run_with_gunicorn(self):

        if not self.started:
            self.start()

        options = dict(
            preload_app=True,
            bind=f"{config.app.bind_ip}:{config.app.bind_port}",
            workers=config.app.gunicorn_worker_count,
            worker_class=config.app.gunicorn_worker_type,
            timeout=config.app.gunicorn_worker_timeout,
            keepalive=config.app.gunicorn_keepalive,
            errorlog="-",
            loglevel=config.app.gunicorn_log_level,
            accesslog="-",
            access_log_format=config.app.gunicorn_accesslog_format,
            child_exit=gunicorn_funcs.child_exit,
            when_ready=gunicorn_funcs.get_when_ready_func(
                workers_count=config.app.gunicorn_worker_count,
                metrics_enabled=config.observ.metrics_enabled,
                metrics_bind_ip=config.observ.metrics_ip,
                metrics_bind_port=config.observ.metrics_port,
            ),
            pre_fork=gunicorn_funcs.pre_fork,
            post_fork=gunicorn_funcs.post_fork,
            pre_exec=gunicorn_funcs.pre_exec,
            worker_int=gunicorn_funcs.get_worker_int_func(callbacks=[jobs.stop]),
            worker_abort=gunicorn_funcs.get_worker_abort_func(callbacks=[jobs.stop]),
            logger_class=gunicorn_funcs.configure_gunicorn_log(
                config.logs.logging_format_string, config.logs.logging_format_time
            ),
        )

        FlaskHammerGunicornApp.run_with_config(self.flask_app, options)
