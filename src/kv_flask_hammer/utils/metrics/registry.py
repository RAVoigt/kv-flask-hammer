from dataclasses import dataclass
import typing as t

from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import Histogram


from kv_flask_hammer.exceptions import FlaskHammerError


class MetricAlreadyExistsError(FlaskHammerError):
    pass


def add_prefix(label: str, prefix: str | None = None) -> str:
    if not prefix:
        return label
    return f"{prefix}_{label}"


@dataclass(kw_only=True)
class MetricDefinition:
    metric_class: t.Type[Counter|Histogram|Gauge]
    name: str
    description: str
    labelnames: list[str]
    multiprocess_mode: t.Literal[
        "all", "liveall", "min", "livemin", "max", "livemax", "sum", "livesum", "mostrecent", "livemostrecent"
    ] = "mostrecent"

    @property
    def key(self) -> str:
        return f"{self.metric_class.__name__}{self.name}"

    @property
    def metric_class_name(self) -> str:
        return self.metric_class.__name__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MetricDefinition):
            return False
        if self.metric_class != other.metric_class:
            return False
        if self.name != other.name:
            return False
        if self.labelnames != other.labelnames:
            return False
        return True

    def __repr__(self) -> str:
        return f"<MetricDefinition: {self.name}-{self.metric_class_name}-labelnames:\'{','.join(self.labelnames)}\'>"


class MetricRegistry:
    """
    Prometheus Metrics raise errors when trying to re-instantiate with the same name.
    For usability, do a get-or-create instead; so that we can provide default metrics from KVFLH

    Singleton-like registry for metrics by type, name, and labelnames.
    * Ensures that multiple attempts to create the same metric are idempotent if arguments match
    * Raises if conflicting labelnames are used.

    """
    _metric_defs: dict[str, MetricDefinition]
    _metrics: dict[str, Counter|Gauge|Histogram]

    def __init__(self):
        self._metric_defs = dict()
        self._metrics = dict()

    def get_or_create(
        self,
        metric_class: t.Type[Counter | Gauge | Histogram],
        name: str,
        description: str | None = None,
        labelnames: list[str] | None = None,
        multiprocess_mode: t.Literal[
            "all", "liveall", "min", "livemin", "max", "livemax", "sum", "livesum", "mostrecent", "livemostrecent"
        ] = "mostrecent",
        name_prefix: str | None = None,
        full_name_override: str | None = None,
    ):
        metric_name = name
        if full_name_override:
            metric_name = full_name_override
        else:
            if name_prefix:
                metric_name = add_prefix(name, name_prefix)

        if labelnames is None:
            labelnames = []

        description = description or ""

        new_def = MetricDefinition(
            metric_class=metric_class,
            name=metric_name,
            description=description,
            labelnames=labelnames,
            multiprocess_mode=multiprocess_mode
        )

        if new_def.key in self._metrics:
            existing_def: MetricDefinition = self._metric_defs[new_def.key]

            if existing_def != new_def:
                raise MetricAlreadyExistsError(
                    f"Conflicting definitions for metric '{metric_name}' of type '{new_def.metric_class_name}' with labelnames '{labelnames}'.\n"
                    f"Existing: {existing_def}\n"
                    f"New: {new_def}"
                )
            return self._metrics[new_def.key]


        metric = metric_class(metric_name, description, labelnames=labelnames)
        self._metrics[new_def.key] = metric
        self._metric_defs[new_def.key] = new_def

        return metric
