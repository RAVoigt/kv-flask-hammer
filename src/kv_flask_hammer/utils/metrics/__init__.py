import typing as t
from prometheus_client import Counter
from prometheus_client import Gauge

from .default import DefaultMetrics
from .default import FlaskMetricsException
from .default import UnhandledExceptionSources


def inc(metric: Counter | Gauge, amount: int = 1, labels: dict | None = None):
    if labels:
        metric.labels(**labels).inc(amount=amount)
    else:
        metric.inc(amount=amount)


def dec(gauge: Gauge, amount: int = 1, labels: dict | None = None):
    if labels:
        gauge.labels(**labels).dec(amount=amount)
    else:
        gauge.dec()


def set_to(gauge: Gauge, value: int = 1, labels: dict | None = None):
    if labels:
        gauge.labels(**labels).set(value=value)
    else:
        gauge.set(value=value)


__all__ = [
    "inc",
    "dec",
    "set_to",
    "DefaultMetrics",
    "FlaskMetricsException",
    "UnhandledExceptionSources",
]
