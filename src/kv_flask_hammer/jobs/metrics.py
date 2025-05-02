from prometheus_client import Histogram

from kv_flask_hammer import config


def prefix_label(label: str) -> str:
    prefix = config.observ.metrics_label_prefix
    if not prefix:
        return label
    return f"{prefix}_{label}"


JOB_SECONDS = Histogram(
    prefix_label("job_seconds"),
    "Time taken for a job to complete",
    labelnames=[
        "job_id",
    ],
)
