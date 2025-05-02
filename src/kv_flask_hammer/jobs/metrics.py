from prometheus_client import Histogram

from kv_flask_hammer.observ.metrics import prefix_label


JOB_SECONDS = Histogram(
    prefix_label("job_seconds"),
    "Time taken for a job to complete",
    labelnames=[
        "job_id",
    ],
)
