from collections.abc import Callable
from datetime import datetime, timedelta
from typing import TypedDict

from requests.adapters import BaseAdapter

from requestspro.utc import utc_now


class RequestDict(TypedDict):
    method: str
    url: str
    headers: dict[str, str]
    body: str | None


class ResponseDict(TypedDict):
    status_code: int
    headers: dict[str, str]
    body: str | None


class AuditDict(TypedDict):
    """Describes the structure of the dict used for audit. Useful for filter writers to get autocompletion."""

    audited_at: datetime
    elapsed: timedelta
    request: RequestDict
    response: ResponseDict


AuditFilterType = Callable[[AuditDict], AuditDict | None]


NOP: AuditFilterType = lambda kw: kw


class Audit(BaseAdapter):
    def __init__(self, adapter, audit_filter: AuditFilterType = NOP, now=utc_now):
        self.events: list[AuditDict] = []
        self.now = now
        self.adapter = adapter
        self.filter = audit_filter

    @classmethod
    def for_session(cls, session, schema="https://", audit_filter: AuditFilterType = NOP):
        original_adapter = session.get_adapter(schema)
        audit = cls(original_adapter, audit_filter=audit_filter)
        session.mount(schema, audit)
        return audit

    def send(self, request, **kwargs):
        # stream=True means the caller will read the body lazily; reading it here to
        # audit would consume the stream, so we record a placeholder instead.
        response = self.audit(self.adapter.send(request, **kwargs), stream=kwargs.get("stream", False))
        # The response.connection is set as the wrapped adapter.
        # We must update it so any retries would pass through the audit.
        response.connection = self
        return response

    def close(self):
        return self.adapter.close()

    def _safe_get_request_body(self, request):
        """Return a <stream> placeholder for stream-like request bodies; otherwise the body."""
        body = request.body

        if isinstance(body, str):
            return body

        # A file-like (has read) or non-bytes iterable (generator) body is a stream:
        # reading it to audit would consume the upload, so record a placeholder.
        if hasattr(body, "read") or (hasattr(body, "__iter__") and not isinstance(body, (bytes, str))):
            return "<stream>"

        # Bytes and None decode as before.
        return (body or b"").decode()

    def _safe_get_response_body(self, response, stream):
        """Return a <stream> placeholder for streamed responses; otherwise the text body."""
        if stream:
            return "<stream>"

        return response.text

    def audit(self, response, *, stream=False):
        """Turn a response and its request into a detailed log."""
        request = response.request

        data = self.filter(
            httplog(
                audited_at=self.now(),
                elapsed=response.elapsed,
                request_method=request.method,
                request_url=request.url,
                request_headers=dict(request.headers),
                request_body=self._safe_get_request_body(request),
                response_status=response.status_code,
                response_headers=dict(response.headers),
                response_body=self._safe_get_response_body(response, stream),
            )
        )

        if data:
            self.events.append(data)

        return response

    def __len__(self):
        return len(self.events)

    def __getitem__(self, index):
        return self.events[index]


def httplog(
    audited_at,
    elapsed,
    request_method,
    request_url,
    request_headers,
    request_body,
    response_status,
    response_headers,
    response_body,
) -> AuditDict:
    return {
        "audited_at": audited_at,
        "elapsed": elapsed,
        "request": {
            "method": request_method,
            "url": request_url,
            "headers": request_headers,
            "body": request_body,
        },
        "response": {
            "status_code": response_status,
            "headers": response_headers,
            "body": response_body,
        },
    }
