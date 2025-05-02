import typing as t

from kv_flask_hammer.logger import get_logger
from kvcommon.flask_utils.responses import HTTPResponse


LOG = get_logger("")


class UnknownResponse(HTTPResponse):
    def __init__(self, err_msg: str = "[None]", **kwargs) -> None:
        response_msg: str = f"Ambiguous error (500) for request with error/exception: {err_msg}"
        status_code = 500
        LOG.warning("UnknownResponse: %s", response_msg)
        super().__init__(response_msg, status=status_code, **kwargs)


class MetaResponse(HTTPResponse):
    def __init__(
        self,
        msg: str | bytes = "Ok",
        status: int = 200,
        do_metrics=False,
        **kwargs,
    ) -> None:
        super().__init__(
            msg,
            status=status,
            do_metrics=do_metrics,
            **kwargs,
        )


class HealthzLiveResponse(MetaResponse):
    def __init__(self, do_metrics=False):
        super().__init__("Ok", status=200, do_metrics=do_metrics)


class HealthzReadyResponse(MetaResponse):
    def __init__(self, do_metrics=False):
        super().__init__("Ready", status=200, do_metrics=do_metrics)
