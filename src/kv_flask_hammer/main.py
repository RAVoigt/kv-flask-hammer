import logging
import typing as t

from flask import Blueprint
from flask import Flask
from flask_http_middleware import MiddlewareManager
from prometheus_client import Histogram

from kvcommon.flask_utils.scheduler import Scheduler
from kvcommon.singleton import SingletonMeta

from kv_flask_hammer import config
from kv_flask_hammer import jobs
from kv_flask_hammer.config_interface import FlaskHammer_Interface_Config
from kv_flask_hammer.exceptions import AlreadyStartedError
from kv_flask_hammer.exceptions import ImmutableConfigError
from kv_flask_hammer.gunicorn_app import FlaskHammerGunicornApp
from kv_flask_hammer.gunicorn_app import gunicorn_funcs
from kv_flask_hammer.logger import get_logger
from kv_flask_hammer.observ.metrics import init_metrics
from kv_flask_hammer.observ.traces import init_traces
from kv_flask_hammer.views.healthz import setup_default_healthz
from kv_flask_hammer.views.meta import setup_default_meta


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
        run_immediately_via_thread: bool = False,
        *job_args,
        **job_kwargs,
    ):
        if self._started:
            raise AlreadyStartedError("Cannot add jobs after FlaskHammer has started")
        jobs.add_job(
            job_func,
            job_id,
            interval_seconds,
            metric,
            metric_labels,
            run_immediately_via_thread,
            *job_args,
            **job_kwargs,
        )

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
