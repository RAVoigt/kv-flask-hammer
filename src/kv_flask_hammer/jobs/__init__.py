# coding=utf-8
from dataclasses import dataclass
from dataclasses import field
import typing as t

from prometheus_client import Histogram

from flask import Flask

from kv_flask_hammer import config
from kv_flask_hammer.logger import get_logger
from kv_flask_hammer.utils.metrics import DefaultMetrics
from kv_flask_hammer.utils.scheduler import Scheduler
from kv_flask_hammer.utils.scheduler import filter_apscheduler_logs


LOG = get_logger("jobs")
MINUTE_S = 60

@dataclass(kw_only=True)
class JobDefinition:
    job_func: t.Callable
    job_id: str
    interval_seconds: int
    metric: Histogram | None = None
    metric_labels: dict[str, str] | None = None
    job_args: tuple = ()
    job_kwargs: dict[str, t.Any] = field(default_factory=dict)


jobs_to_add: t.List[JobDefinition] = []

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
    global jobs_to_add

    if config.observ.metrics_enabled:
        if metric is None:
            metric = DefaultMetrics().JOB_SECONDS()
        if metric == DefaultMetrics().JOB_SECONDS() and not metric_labels:
            metric_labels = dict(job_id=job_id)

    jobs_to_add.append(
        JobDefinition(
            job_func=job_func,
            job_id=job_id,
            interval_seconds=interval_seconds,
            metric=metric,
            metric_labels=metric_labels,
            job_args=job_args,
            job_kwargs=job_kwargs,
        )
    )


scheduler: Scheduler


def init(flask_app: Flask, init_scheduler: Scheduler):
    filter_apscheduler_logs(LOG)

    # Jobs must be added before starting the scheduler?
    init_scheduler.start(flask_app=flask_app)

    LOG.info("Job Scheduler initialized. Adding %d queued jobs.", len(jobs_to_add))

    for job_def in jobs_to_add:
        init_scheduler.add_job_on_interval(
            job_def.job_func,
            job_id=job_def.job_id,
            interval_seconds=job_def.interval_seconds,
            metric=job_def.metric,
            metric_labels=job_def.metric_labels,
            *job_def.job_args,
            **job_def.job_kwargs,
        )

    global scheduler
    scheduler = init_scheduler


def stop(scheduler: Scheduler):
    if scheduler:
        scheduler.stop()
    raise ValueError("stop() called without valid 'scheduler' obj.")
