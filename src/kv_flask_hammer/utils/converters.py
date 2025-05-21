import typing as t
import requests

from flask import make_response
from flask.wrappers import Response


def headers_dict_to_flask_headers(headers: dict) -> list:
    """
    The requests lib typically handles headers in a dict-like structure.
    Flask expects a list of (key, value) tuples.

    Returns:
        Headers as a list of key-value tuples
    """
    return [(k, v) for k, v in headers.items()]


def flask_headers_from_requests_response(
    requests_response: requests.Response, discard_keys: list | tuple | None = None
) -> dict:
    if not discard_keys:
        return dict(requests_response.headers)

    response_headers = dict()
    for key, value in requests_response.headers.items():
        if key not in discard_keys:
            response_headers[key] = value
    return response_headers


def get_stream_chunk_generator_for_requests_response(response: requests.Response, as_text: bool) -> t.Callable:
    def generate():
        for chunk in response.raw.stream(decode_content=as_text):
            yield chunk

    return generate


def requests_response_to_flask_response(
    requests_response: requests.Response, discard_headers: list | tuple | None = None
) -> Response:
    content = requests_response.content
    status_code = requests_response.status_code
    headers = flask_headers_from_requests_response(requests_response)
    flask_response = make_response(content, status_code)

    for key, value in headers.items():
        flask_response.headers[key] = value

    return flask_response
