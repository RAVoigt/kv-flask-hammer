# coding=utf-8
import typing as t

from flask_http_middleware import BaseHTTPMiddleware
from prometheus_client import Histogram


enabled: bool = False
middleware_cls: t.Type[BaseHTTPMiddleware] | None = None

metrics_path_label_enabled: bool = False

server_request_metric: Histogram | None = None
