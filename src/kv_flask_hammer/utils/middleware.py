import dataclasses
from urllib.parse import ParseResult
import typing as t

import flask

from flask_http_middleware import BaseHTTPMiddleware
from flask_http_middleware import MiddlewareManager
from prometheus_client import Histogram

from kvcommon import logger
from kvcommon.urls import urlparse_ignore_scheme
from kv_flask_hammer.utils.context import set_flask_context_local


LOG = logger.get_logger("kvc-flask")


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


class BaseFlaskHammerMiddleware(BaseHTTPMiddleware):
    _meta_prefix: str
    _server_request_metric: Histogram | None

    def __init__(self, meta_prefix: str | None, server_request_metric: Histogram | None = None):
        if meta_prefix:
            self._meta_prefix = meta_prefix
        self._server_request_metric = server_request_metric
        super().__init__()

    def _pre_dispatch(self, request) -> PreDispatchResult:
        url_parts = urlparse_ignore_scheme(request.url, request.scheme)
        url_path: str = url_parts.path
        set_flask_context_local("url_parts", url_parts)

        is_meta: bool = is_meta_url(url_path, prefix=self._meta_prefix)
        set_flask_context_local("is_meta_request", is_meta)
        is_healthz: bool = is_healthz_url(url_path)
        set_flask_context_local("is_healthz_request", is_healthz)

        # Return this result for use in subclasses calling super()
        return PreDispatchResult(url_parts=url_parts, is_meta=is_meta, is_healthz=is_healthz)

    def _dispatch(self, request, call_next, **labels):
        if not self._server_request_metric:
            return call_next(request)

        with self._server_request_metric.labels(**labels).time():
            return call_next(request)

    def dispatch(self, request, call_next):
        self._pre_dispatch(request=request)
        return self._dispatch(request=request, call_next=call_next)


def setup_middleware(flask_app: flask.Flask, middleware_cls: t.Type[BaseHTTPMiddleware]):
    flask_app.wsgi_app = MiddlewareManager(flask_app)
    flask_app.wsgi_app.add_middleware(middleware_cls)
