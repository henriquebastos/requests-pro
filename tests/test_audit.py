from datetime import datetime

from requests import HTTPError, Session
from requests.adapters import HTTPAdapter, Response

from requestspro.audit import Audit, AuditDict
from requestspro.auth import RecoverableAuth
from requestspro.token import TokenStore
from requestspro.utc import UTC

import pytest


class TestAudit:
    def test_audit(self, responses):
        responses.add("GET", "https://abc.de", status=200)

        audit = Audit(HTTPAdapter())
        session = Session()
        session.mount("https://", audit)

        r = session.get("https://abc.de")

        assert isinstance(r, Response)
        assert len(audit) == 1
        for event in audit:
            assert {"audited_at", "elapsed", "request", "response"} == set(event)


class SampleAuth(RecoverableAuth):
    def renew(self) -> tuple[str, int]:
        r = Session().post("https://auth")
        d = r.json()
        return d["access_token"], d["expires_in"]


class SampleClient:
    def __init__(self, now):
        token = TokenStore.in_memory(now=now)
        auth = SampleAuth(token, Session)
        session = Session()
        session.auth = auth

        self.audit = Audit.for_session(session)
        self.session = session


class TestSampleSessionWithAuthAudit:
    @pytest.fixture
    def client(self):
        NOW = lambda: datetime(2021, 12, 4, 0, 0, 0, tzinfo=UTC)
        return SampleClient(NOW)

    def auth_response(self, status=200, token="ey1.ey2.ey3", expires_in=3600):
        return {
            "method": "POST",
            "url": "https://auth",
            "content_type": "application/json",
            "status": status,
            "json": {
                "access_token": token,
                "expires_in": expires_in,
                "token_type": "Bearer",
            },
        }

    def test_client_should_not_log_auth_requests(self, client, responses):
        # First renew is due to auth without token.
        responses.add(**self.auth_response(token="EXPIRED", expires_in=-1))
        # Then we try a GET and force a 401 as if the token expiration was not detected.
        responses.add("GET", "https://h/first", status=401)
        # The 401 will trigger auth.handle_401 that will renew the token once more
        responses.add(**self.auth_response(token="VALID"))
        # The auth.handle_401 will then retry the failed request.
        responses.add("GET", "https://h/first", status=200, json={"Message": "Ok"})

        data = client.session.get("https://h/first").json()

        assert len(responses.calls) == 4
        assert len(client.audit) == 2
        assert [e["request"]["url"] for e in client.audit] == ["https://h/first", "https://h/first"]
        assert data == {"Message": "Ok"}

    def test_client_should_log_recovery_errors(self, client, responses):
        # First renew is due to auth without token.
        responses.add(**self.auth_response(token="EXPIRED1", expires_in=-1))
        # Then we try a GET and force a 401 as if the token expiration was not detected.
        responses.add("GET", "https://h/first", status=401, json={})
        # The 401 will trigger auth.handle_401 that will renew the token once more
        responses.add(**self.auth_response(token="EXPIRED2", expires_in=-1))
        # The auth.handle_401 will then retry the failed request.
        responses.add("GET", "https://h/first", status=401, json={"Message": "No Token"})

        with pytest.raises(HTTPError, match="401"):
            client.session.get("https://h/first")

        # 4 http exchanges happened. 2 for auth. 2 for data.
        assert len(responses.calls) == 4
        # We only audit data http exchanges.
        assert len(client.audit) == 2
        # Ensure the logged urls are from data exchanges.
        assert [e["request"]["url"] for e in client.audit] == ["https://h/first", "https://h/first"]
        # We do log failed http exchages.
        assert [e["response"]["status_code"] for e in client.audit] == [401, 401]


class TestAuditFilter:
    @pytest.fixture
    def client(self):
        NOW = lambda: datetime(2021, 12, 4, 0, 0, 0, tzinfo=UTC)
        return SampleClient(NOW)

    @pytest.fixture(autouse=True)
    def setup(self, responses):
        responses.add("GET", "https://h/first", status=401, json={})
        responses.add("GET", "https://h/first", status=200, json={"Message": "Ok"})

    def test_no_filter(self):
        session = Session()
        audit = Audit.for_session(session)
        session.get("https://h/first")
        session.get("https://h/first")

        assert len(audit) == 2

    def test_supression_filter(self):
        def skip_non_2xx(d: AuditDict) -> AuditDict | None:
            return d if d["response"]["status_code"] == 200 else None

        session = Session()
        audit = Audit.for_session(session, audit_filter=skip_non_2xx)
        session.get("https://h/first")
        session.get("https://h/first")

        assert len(audit) == 1

    def test_editing_filter(self):
        def exclude_headers(d: AuditDict) -> AuditDict:
            d["request"]["headers"] = {}
            d["response"]["headers"] = {}
            return d

        session = Session()
        audit = Audit.for_session(session, audit_filter=exclude_headers)
        session.get("https://h/first")
        session.get("https://h/first")

        assert len(audit) == 2
        for log in audit:
            assert log["request"]["headers"] == {}
            assert log["response"]["headers"] == {}
