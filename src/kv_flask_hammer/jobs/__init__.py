# coding=utf-8

import typing as t
import logging

from prometheus_client import Histogram


from kv_flask_hammer import config
from kv_flask_hammer.logger import get_logger
from kvcommon.flask_utils.metrics.metrics import metric_name_prefix
from kvcommon.flask_utils.scheduler import scheduler
from kvcommon.flask_utils.scheduler import filter_apscheduler_logs


LOG = get_logger("jobs")
MINUTE_S = 60


JOB_SECONDS = None
def get_default_job_seconds_metric():
    global JOB_SECONDS
    if not JOB_SECONDS:
        JOB_SECONDS = config.jobs.default_job_time_metric
    if not JOB_SECONDS:
        JOB_SECONDS = Histogram(
            metric_name_prefix("job_seconds", config.observ.metrics_label_prefix),
            "Time taken for a job to complete",
            labelnames=["job_id"],
        )
    return JOB_SECONDS


def add_job(
    job_func: t.Callable,
    job_id: str,
    interval_seconds: int,
    metric: Histogram | None = None,
    metric_labels: dict[str, str] | None = None,
    run_immediately_via_thread: bool = False,
    *job_args,
    **job_kwargs
):
    if config.observ.metrics_enabled:
        if metric is None:
            metric = get_default_job_seconds_metric()
        if metric == JOB_SECONDS and not metric_labels:
            metric_labels = dict(job_id=job_id)

    scheduler.add_job_on_interval(
        job_func,
        job_id=job_id,
        interval_seconds=interval_seconds,
        metric=metric,
        metric_labels=metric_labels,
        run_immediately_via_thread=run_immediately_via_thread,
        *job_args,
        **job_kwargs
    )


def init(flask_app):
    filter_apscheduler_logs(LOG)

    # Jobs must be added before starting the scheduler?
    scheduler.start(flask_app=flask_app)


def stop():
    scheduler.stop()
