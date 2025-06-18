from __future__ import annotations
import logging
import threading
import typing as t

from typing import Callable

from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.events import EVENT_JOB_MISSED
from apscheduler.events import JobExecutionEvent
from apscheduler.schedulers import SchedulerNotRunningError
from flask_apscheduler import APScheduler
from prometheus_client import Counter
from prometheus_client import Histogram

from kv_flask_hammer import config
from kv_flask_hammer.utils import metrics

from kvcommon.logger import get_logger


LOG = get_logger("kvc-flask-scheduler")


def filter_apscheduler_logs(logger: logging.Logger = LOG):
    # Filter to reduce log spam from APScheduler
    class SuppressThreadPoolExecutorLogging(logging.Filter):
        def filter(self, record):
            return "ThreadPoolExecutor" not in record.getMessage()

    logger.addFilter(SuppressThreadPoolExecutorLogging())


# TODO: Support setting labels for job_event_metric
class SchedulerEventTracker(object):
    """
    Emits metrics for job events
    """

    job_event_metric: Counter

    def __init__(self, job_event_metric: Counter) -> None:
        self.job_event_metric = job_event_metric

    def get_event_listener(self) -> t.Callable[[JobExecutionEvent], None]:

        def event_listener(event):
            if isinstance(event, JobExecutionEvent):
                event_str = "Unknown"
                if event.exception or event.code == EVENT_JOB_ERROR:
                    event_str = "Error"
                else:
                    if event.code == EVENT_JOB_EXECUTED:
                        event_str = "Executed"
                    elif event.code == EVENT_JOB_MISSED:
                        event_str = "Missed"

                # LOG.debug(f"Scheduler Event Listener: {event}: Job <'{event.job_id}'>")
                metrics.inc(self.job_event_metric.labels(job_id=event.job_id, event=event_str.lower()))

            else:
                LOG.warning(f"Scheduler Event Listener: Unexpected event type: '{type(event).__name__}'")

        return event_listener


class Scheduler:
    """
    Wraps APScheduler with some convenience functions and adds logging and metrics
    """

    ap_scheduler: APScheduler
    event_tracker: SchedulerEventTracker | None
    job_time_metric: Histogram | None

    def __init__(
        self,
        job_time_metric: Histogram | None = None,
        job_event_metric: Counter | None = None,
        api_enabled: bool = False,
    ) -> None:
        scheduler = APScheduler()
        scheduler.api_enabled = api_enabled
        self.ap_scheduler = scheduler

        if job_time_metric is None:
            job_time_metric = metrics.DefaultMetrics().JOB_SECONDS(name_prefix=config.observ.metrics_label_prefix)

        if job_event_metric is None:
            job_event_metric = metrics.DefaultMetrics().SCHEDULER_JOB_EVENT(name_prefix=config.observ.metrics_label_prefix)

        self.job_time_metric = job_time_metric

        self.event_tracker = None
        if job_event_metric is not None:
            self.event_tracker = SchedulerEventTracker(job_event_metric)

    def add_job_on_interval(
        self,
        job_func: Callable,
        job_id: str,
        interval_seconds: int = 300,
        misfire_grace_time: int = 900,
        metric: Histogram | None = None,
        metric_labels: dict[str, str] | None = None,
        run_immediately_via_thread: bool = False,
        verbose_logging: bool = False,
        *job_args,
        **job_kwargs,
    ):
        LOG.debug("Scheduler: Adding job with ID: '%s', Interval: %s (s)", job_id, interval_seconds)

        metric_labels = metric_labels or dict()

        # Wrapping the job in a closure
        @self.ap_scheduler.task("interval", id=job_id, seconds=interval_seconds, misfire_grace_time=misfire_grace_time)
        def job():
            if verbose_logging:
                LOG.debug(f"Scheduler: Executing Job:'{job_id}'")

            if not metric:
                job_func(*job_args, **job_kwargs)
                return

            # Wrap the call with a Histogram metric time() if supplied
            try:
                with metric.labels(**metric_labels).time():
                    job_func(*job_args, **job_kwargs)
            except Exception as ex:
                metrics.inc(
                    metrics.DefaultMetrics().UNHANDLED_EXCEPTIONS(),
                    labels=dict(
                        exc_cls_name=ex.__class__.__name__,
                        source=metrics.UnhandledExceptionSources.JOB
                    ),
                )
                raise

        if run_immediately_via_thread:
            thread = threading.Thread(target=job)
            thread.start()

    def start(self, flask_app):
        self.ap_scheduler.init_app(flask_app)
        logging.getLogger("apscheduler").setLevel(logging.WARNING)
        LOG.debug(f"Scheduler: Starting jobs")

        if self.event_tracker:
            self.ap_scheduler.add_listener(
                self.event_tracker.get_event_listener(),
                EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED,
            )
        self.ap_scheduler.start()

    def stop(self):
        LOG.debug(f"Scheduler: Stopping jobs and shutting down")
        try:
            self.ap_scheduler.pause()
            self.ap_scheduler.shutdown()
        except SchedulerNotRunningError:
            pass
