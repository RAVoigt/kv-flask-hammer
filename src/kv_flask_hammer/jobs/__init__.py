# coding=utf-8

import typing as t
import logging

from prometheus_client import Histogram


from kv_flask_hammer import config
from kv_flask_hammer.logger import get_logger
from kv_flask_hammer.utils.metrics import DefaultMetrics
from kv_flask_hammer.utils.scheduler import scheduler
from kv_flask_hammer.utils.scheduler import filter_apscheduler_logs


LOG = get_logger("jobs")
MINUTE_S = 60


def add_job(
    job_func: t.Callable,
    job_id: str,
    interval_seconds: int,
    metric: Histogram | None = None,
    metric_labels: dict[str, str] | None = None,
    run_immediately_via_thread: bool = False,
    *job_args,
    **job_kwargs,
):
    if config.observ.metrics_enabled:
        if metric is None:
            metric = DefaultMetrics().JOB_SECONDS()
        if metric == DefaultMetrics().JOB_SECONDS() and not metric_labels:
            metric_labels = dict(job_id=job_id)

    scheduler.add_job_on_interval(
        job_func,
        job_id=job_id,
        interval_seconds=interval_seconds,
        metric=metric,
        metric_labels=metric_labels,
        run_immediately_via_thread=run_immediately_via_thread,
        *job_args,
        **job_kwargs,
    )


def init(flask_app):
    filter_apscheduler_logs(LOG)

    # Jobs must be added before starting the scheduler?
    scheduler.start(flask_app=flask_app)


def stop():
    scheduler.stop()
