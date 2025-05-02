import logging
import typing as t

from flask import Request
from flask import Response
from flask_http_middleware import BaseHTTPMiddleware


from kvcommon.urls import urlparse_ignore_scheme
from kvcommon.flask_utils.context import set_flask_context_local

from kv_flask_hammer import config
from kv_flask_hammer.constants import default_meta_view_prefix
from kv_flask_hammer.observ import metrics


def is_meta_url(url: str, prefix: str = default_meta_view_prefix) -> bool:
    return url.startswith(prefix)


def is_healthz_url(url: str) -> bool:
    return url.startswith("/healthz/") or url.startswith("/livez/")


class FlaskHammerMiddleware(BaseHTTPMiddleware):
    _meta_view_prefix: str = default_meta_view_prefix
    _metrics_enabled: bool = False
    _metrics_path_label_enabled: bool = False

    def __init__(self):
        super().__init__()
        self._metrics_enabled = config.observ.metrics_enabled
        self._metrics_path_label_enabled = config.middleware.metrics_path_label_enabled

    def dispatch(self, request: Request, call_next: t.Callable) -> Response:
        url_parts = urlparse_ignore_scheme(request.url, request.scheme)
        url_path = url_parts.path
        is_meta = is_meta_url(url_path, prefix=self._meta_view_prefix)
        is_healthz = is_healthz_url(url_path)
        if not is_meta:
            url_parts = urlparse_ignore_scheme(url_path, "", force_scheme=True)

        set_flask_context_local("is_meta_request", is_meta)
        set_flask_context_local("is_healthz_request", is_healthz)
        set_flask_context_local("url_parts", url_parts)

        if self._metrics_enabled:
            labels = dict(path="")
            if self._metrics_path_label_enabled:
                # Warning: Can blow up metric cardinality if url_paths are varied
                labels["path"] = url_path

            with metrics.SERVER_REQUEST_SECONDS.labels(**labels).time():
                response = call_next(request)
        else:
            response = call_next(request)

        return response
