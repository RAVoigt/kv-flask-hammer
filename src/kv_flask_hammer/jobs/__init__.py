# coding=utf-8

import typing as t
import logging

from prometheus_client import Histogram

from apscheduler.schedulers import SchedulerNotRunningError

from kvcommon.flask_utils.scheduler import scheduler
from kv_flask_hammer.logger import get_logger

from . import metrics


LOG = get_logger("jobs")
MINUTE_S = 60


# Filter to reduce log spam from APScheduler
class SuppressThreadPoolExecutorLogging(logging.Filter):
    def filter(self, record):
        return "ThreadPoolExecutor" not in record.getMessage()


def add_job(
    job_func: t.Callable,
    job_id: str,
    interval_seconds: int,
    metric: Histogram | None = metrics.JOB_SECONDS,
    metric_labels: dict[str, str] | None = None,
):

    if metric == metrics.JOB_SECONDS and not metric_labels:
        metric_labels = dict(job_id=job_id)

    scheduler.add_job_on_interval(
        job_func,
        job_id=job_id,
        interval_seconds=interval_seconds,
        metric=metric,
        metric_labels=metric_labels,
    )


def init(flask_app):
    LOG.addFilter(SuppressThreadPoolExecutorLogging())

    # Jobs must be added before starting the scheduler?
    scheduler.start(flask_app=flask_app)


def stop():
    try:
        scheduler.stop()
    except SchedulerNotRunningError:
        pass
