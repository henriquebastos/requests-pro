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
        response = self.audit(self.adapter.send(request, **kwargs))
        # The response.connection is set as the wrapped adapter.
        # We must update it so any retries would pass through the audit.
        response.connection = self
        return response

    def close(self):
        return self.adapter.close()

    def _safe_get_request_body(self, request):
        """Safely extract request body, returning <stream> for stream-like objects."""
        body = request.body
        
        if isinstance(body, str):
            return body
        
        # Check if it's a stream-like object (has read method or is iterable but not bytes)
        if hasattr(body, 'read') or (hasattr(body, '__iter__') and not isinstance(body, (bytes, str))):
            return "<stream>"
        
        # Handle bytes and None as before
        return (body or b"").decode()

    def _safe_get_response_body(self, response):
        """Safely extract response body, returning <stream> for streamed responses."""
        # Check if response is being streamed
        if hasattr(response, 'raw') and hasattr(response.raw, 'isclosed') and not response.raw.isclosed():
            return "<stream>"
        
        # For normal responses, return text as before
        return response.text

    def audit(self, response):
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
                response_body=self._safe_get_response_body(response),
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
