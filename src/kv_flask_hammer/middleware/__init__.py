import dataclasses
import logging
import typing as t
from urllib.parse import ParseResult

from flask import Request
from flask import Response
from flask_http_middleware import BaseHTTPMiddleware

from prometheus_client import Histogram

from kvcommon.urls import urlparse_ignore_scheme
from kvcommon.flask_utils.context import set_flask_context_local

from kv_flask_hammer import config
from kv_flask_hammer.constants import default_meta_view_prefix
from kv_flask_hammer.observ import metrics


def is_meta_url(url: str, prefix: str | None = "meta") -> bool:
    if not prefix:
        return False
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    if not prefix.endswith("/"):
        prefix = f"{prefix}/"
    return url.startswith(prefix)


def is_healthz_url(url: str) -> bool:
    return url.startswith("/healthz/") or url.startswith("/livez/")


@dataclasses.dataclass(kw_only=True)
class PreDispatchResult:
    url_parts: ParseResult
    is_meta: bool = False
    is_healthz: bool = False


class FlaskHammerMiddleware(BaseHTTPMiddleware):
    _meta_view_prefix: str = default_meta_view_prefix
    _metrics_enabled: bool = False
    _metrics_path_label_enabled: bool = False
    _server_request_metric: Histogram | None

    def __init__(self):
        super().__init__()
        self._metrics_enabled = config.observ.metrics_enabled
        self._metrics_path_label_enabled = config.middleware.metrics_path_label_enabled
        self._meta_prefix = config.views.meta_route_prefix
        self._server_request_metric = config.middleware.server_request_metric

    def _pre_dispatch(self, request) -> PreDispatchResult:
        url_parts = urlparse_ignore_scheme(request.url, request.scheme)
        url_path: str = url_parts.path
        set_flask_context_local("url_parts", url_parts)

        is_meta: bool = is_meta_url(url_path, prefix=self._meta_view_prefix)
        set_flask_context_local("is_meta_request", is_meta)
        is_healthz: bool = is_healthz_url(url_path)
        set_flask_context_local("is_healthz_request", is_healthz)

        # Return this result for use in subclasses calling super()
        return PreDispatchResult(url_parts=url_parts, is_meta=is_meta, is_healthz=is_healthz)

    def _dispatch(self, request, call_next, **labels):
        if not self._metrics_enabled or not self._server_request_metric:
            return call_next(request)

        with self._server_request_metric.labels(**labels).time():
            return call_next(request)

    def dispatch(self, request, call_next):
        self._pre_dispatch(request=request)
        return self._dispatch(request=request, call_next=call_next)
