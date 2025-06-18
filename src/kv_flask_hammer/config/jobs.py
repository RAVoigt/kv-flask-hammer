from prometheus_client import Counter
from prometheus_client import Histogram

from kv_flask_hammer import constants

enabled = False
job_event_metric: Counter | None = constants.default_job_event_metric
job_time_metric: Histogram | None = constants.default_job_time_metric
