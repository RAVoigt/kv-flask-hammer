import typing as t
from flask import Blueprint

from kv_flask_hammer.responses import HealthzLiveResponse
from kv_flask_hammer.responses import HealthzReadyResponse
from kv_flask_hammer.responses import UnknownResponse


def setup_default_healthz(
    prefix: str,
    liveness_callback: t.Callable[[], bool] | None = None,
    readiness_callback: t.Callable[[], bool] | None = None,
) -> Blueprint:
    url_prefix = None
    if prefix:
        url_prefix = f"/{prefix}/"
    blueprint = Blueprint("healthz", __name__, url_prefix=url_prefix)

    # Liveness/Readiness endpoints
    @blueprint.route("/healthz")
    @blueprint.route("/livez")
    def healthz():
        if not liveness_callback or liveness_callback() == True:
            return HealthzLiveResponse()
        return UnknownResponse()

    @blueprint.route("/readyz")
    def readyz():
        if not readiness_callback or readiness_callback() == True:
            return HealthzReadyResponse()
        return UnknownResponse()

    return blueprint
