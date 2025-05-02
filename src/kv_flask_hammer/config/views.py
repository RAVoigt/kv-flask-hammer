# coding=utf-8
import typing as t

# Healthz view
default_healthz_enabled = False
healthz_route_prefix = ""
healthz_liveness_callback: t.Callable[[], bool] | None = None
healthz_readiness_callback: t.Callable[[], bool] | None = None

# Meta view
default_meta_enabled = False
meta_route_prefix = "meta"
meta_debug_info_callback: t.Callable[[], str] | None = None
