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


__all__ = [
    "init_metrics",
]
