from flask import Flask
from prometheus_client import Histogram
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics

from kv_flask_hammer import config
from kv_flask_hammer.logger import get_logger

LOG = get_logger("metrics")


def init_metrics(flask_app: Flask) -> GunicornPrometheusMetrics | None:

    if not config.observ.metrics_enabled:
        LOG.debug("Not initializing metrics server!")
        return

    LOG.debug("Initializing metrics server on port: %s", config.observ.metrics_port)

    return GunicornPrometheusMetrics(flask_app)


def prefix_label(label: str) -> str:
    prefix = config.observ.metrics_label_prefix
    if not prefix:
        return label
    return f"{prefix}_{label}"


SERVER_REQUEST_SECONDS = Histogram(
    prefix_label("server_request_seconds"),
    "Time taken for server to handle request",
    labelnames=["path"],
)


__all__ = [
    "init_metrics",
    "prefix_label",
    "SERVER_REQUEST_SECONDS",
]
