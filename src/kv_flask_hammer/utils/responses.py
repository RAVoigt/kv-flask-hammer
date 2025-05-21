from flask.wrappers import Response as Flask_Response
from prometheus_client import Counter

from kv_flask_hammer.utils import metrics


class HTTPResponse(Flask_Response):
    _METRIC: Counter | None = None # Override this with a valid Counter to have it inc'd on each instance of this response
    _metrics_labels: dict
    _metrics_emitted_doonce: bool = False

    def __init__(
        self,
        *args,
        do_metrics=True,
        defer_metrics=False,
        metrics_labels: dict | None = None,
        **kwargs,
    ) -> None:
        """
        A generic Flask response that can optionally emit metrics on instantiation, or later by
        calling obj.inc_metrics().
        Metrics can only be emitted once for a given instance.

        Params:
            do_metrics:     Toggle metrics for this response (Default: True)
            defer_metrics:  If True, emit metrics on instantiation, else wait for .inc_metrics()
                            to be called (Default: True)
            metrics_labels: Optional dict of key-value pairs of labels to add to the emitted metrics
        """
        super().__init__(*args, **kwargs)

        self._do_metrics = do_metrics
        self._defer_metrics = defer_metrics
        self._metrics_labels = dict(code=str(self.status_code))
        if isinstance(metrics_labels, dict):
            self._metrics_labels.update(metrics_labels)

        if not defer_metrics:
            self.inc_metrics()

    def inc_metrics(self):
        if self._metrics_emitted_doonce:
            raise metrics.FlaskMetricsException(
                "An attempt to emit metrics from this HTTP Response has already been made."
            )
        self._metrics_emitted_doonce = True
        if self._do_metrics and self._METRIC:
            metric_labels_to_incr = self._METRIC.labels(**self._metrics_labels)
            if metric_labels_to_incr:
                metric_labels_to_incr.inc()


def HealthzReadyResponse(do_metrics=False):
    return HTTPResponse("Ready", status=200, do_metrics=do_metrics)


def HTTP_400(msg="", headers={}):
    return HTTPResponse(msg, status=400, headers=headers)


HTTP_BAD_REQUEST = HTTP_400


def HTTP_401(msg="", headers={}):
    return HTTPResponse(msg, status=401, headers=headers)


HTTP_UNAUTHORIZED = HTTP_401


def HTTP_403(msg="", headers={}):
    return HTTPResponse(msg, status=400, headers=headers)


HTTP_FORBIDDEN = HTTP_403


def HTTP_500(msg="", headers={}):
    return HTTPResponse(msg, status=500, headers=headers)
