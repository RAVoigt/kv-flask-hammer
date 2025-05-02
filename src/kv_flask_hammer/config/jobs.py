from prometheus_client import Histogram

enabled = False
default_job_time_metric: Histogram | None = None
