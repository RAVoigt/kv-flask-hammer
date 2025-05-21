import typing as t
import flask

from kvcommon.logger import get_logger

LOG = get_logger("kvc-flask")

FLASK_CONTEXT_PREFIX = "kvc-flask_"


def set_context_prefix(prefix: str):
    global FLASK_CONTEXT_PREFIX
    FLASK_CONTEXT_PREFIX = prefix or FLASK_CONTEXT_PREFIX


def get_flask_context_local(
    key: str, default: t.Optional[t.Any] = None, prefix: str = FLASK_CONTEXT_PREFIX
):
    key = f"{prefix}{key}"
    return flask.g.get(key, default)


def set_flask_context_local(key: str, value: t.Any = None, prefix: str = FLASK_CONTEXT_PREFIX):
    key = f"{prefix}{key}"
    return setattr(flask.g, key, value)


def get_config_value(config_key: str):
    return flask.current_app.config.get(config_key)


def get_config_value_bool(config_key: str) -> bool:
    val = get_config_value(config_key)
    if isinstance(val, str):
        if val.lower() in ["true", "yes", "y"]:
            val = True
        elif not val or val.lower() in ["false", "no", "n"]:
            val = False
    if not isinstance(val, bool):
        raise TypeError(
            f"Retrieved non-bool value for get_config_value_bool - key={config_key}, value={val}"
        )
    return val
