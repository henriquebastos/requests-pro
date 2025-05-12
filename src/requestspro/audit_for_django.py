from typing import Protocol

from requestspro.audit import httplog, utc_now


try:
    from django.http import HttpHeaders, HttpRequest
except ImportError:
    # Declare some types that will be used in the code
    type HttpHeaders = dict[str, str]

    class HttpRequest(Protocol):
        method: str
        META: dict
        body: bytes

        def build_absolute_uri(self) -> str: ...


def http_log_from_django_request(request: HttpRequest, status=201, now=utc_now):
    return httplog(
        audited_at=now(),
        elapsed=None,
        request_method=request.method,
        request_url=request.build_absolute_uri(),
        request_headers=dict(HttpHeaders(request.META)),
        request_body=request.body.decode(),
        response_status=status,
        response_headers={},
        response_body="",
    )
