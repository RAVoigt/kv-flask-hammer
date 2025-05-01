import typing as t
from flask import Blueprint

from kvcommon.flask_utils.views import get_url_map


def setup_default_meta(
        prefix: str = "meta",
        debug_info_callback: t.Callable[[], str] | None = None,
    ) -> Blueprint:
    url_prefix = ""
    if prefix:
        url_prefix = f"/{prefix}/"
    blueprint = Blueprint("meta", __name__, url_prefix=url_prefix)

    @blueprint.route("/debug_info", methods=["GET"])
    def debug_info():
        if debug_info_callback:
            return debug_info_callback()
        return "No debug info callback configured"

    @blueprint.route("/url_map", methods=["GET"])
    def view_url_map():
        return get_url_map()

    return blueprint
