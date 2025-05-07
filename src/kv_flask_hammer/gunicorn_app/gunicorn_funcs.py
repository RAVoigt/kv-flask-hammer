import logging
import typing as t

from gunicorn import glogging
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics


def child_exit(server, worker):
    GunicornPrometheusMetrics.mark_process_dead_on_child_exit(worker.pid)


def get_when_ready_func(
    workers_count: int, metrics_enabled: bool, metrics_bind_ip: str, metrics_bind_port: int
) -> t.Callable:

    def when_ready(server):
        server.log.info(f"Gunicorn: Server is ready. Spawning {workers_count} workers")

        if not metrics_enabled:
            server.log.info(f"Gunicorn: Skipping Prometheus Metrics server as FlaskHammer metrics are disabled.")
            return

        server.log.info(
            f"Gunicorn: Starting HTTP Prometheus Metrics server when ready on: {metrics_bind_ip}:{metrics_bind_port}"
        )
        GunicornPrometheusMetrics.start_http_server_when_ready(port=metrics_bind_port, host=metrics_bind_ip)

    return when_ready


def get_post_fork_func(flask_hammer_app):

    # Avoiding circular imports
    from kv_flask_hammer import FlaskHammer
    flask_hammer_app = t.cast(FlaskHammer, flask_hammer_app)

    def post_fork(server, worker):
        server.log.info("Gunicorn: Worker spawned (pid: %s)", worker.pid)
        if not flask_hammer_app.started:
            flask_hammer_app.start()

    return post_fork


def pre_fork(server, worker):
    pass


def pre_exec(server):
    server.log.info("Gunicorn: Forked child, re-executing.")


def get_worker_int_func(callbacks: list[t.Callable]):
    def worker_int(worker):
        worker.log.info("Gunicorn: Worker received INT or QUIT signal")

        ## get traceback info
        import threading, sys, traceback

        id2name = {th.ident: th.name for th in threading.enumerate()}
        code = []
        for threadId, stack in sys._current_frames().items():
            code.append("\n# Thread: %s(%d)" % (id2name.get(threadId, ""), threadId))
            for filename, lineno, name, line in traceback.extract_stack(stack):
                code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
                if line:
                    code.append("  %s" % (line.strip()))
        worker.log.debug("\n".join(code))

        for cb in callbacks:
            cb()

    return worker_int


def get_worker_abort_func(callbacks: list[t.Callable]):
    def worker_abort(worker):
        worker.log.info("Gunicorn: Worker received SIGABRT signal")
        for cb in callbacks:
            cb()

    return worker_abort


def configure_gunicorn_log(logging_format_string: str, logging_format_time: str) -> type[glogging.Logger]:

    class CustomLogger(glogging.Logger):
        def setup(self, cfg):
            super().setup(cfg)
            formatter = logging.Formatter(fmt=logging_format_string, datefmt=logging_format_time)
            self._set_handler(self.error_log, cfg.errorlog, formatter)
            self._set_handler(self.access_log, cfg.accesslog, formatter)

    return CustomLogger
