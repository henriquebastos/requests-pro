from datetime import datetime

import requests
from requests import HTTPError, PreparedRequest, Session

from requestspro.auth import RecoverableAuth
from requestspro.token import TokenStore
from requestspro.utc import UTC

import pytest
from freezegun import freeze_time
from unittest.mock import patch


NOW = datetime(2021, 12, 4, 0, 0, 0, tzinfo=UTC)


class SampleAuth(RecoverableAuth):
    def renew(self):
        return "TOKEN", 60


class TestRecoverableAuth:
    """Tests the RecoverableAuth class behavior ensuring token renewal and a single retry for 401."""

    @pytest.fixture
    def auth(self):
        return SampleAuth(TokenStore.in_memory(), Session)

    def test_token_refreshed_on_first_acces(self, auth, responses):
        assert auth.token == "TOKEN"

    def test_auth_renew_when_token_empty(self, auth, responses):
        request = PreparedRequest()
        request.prepare("GET", "https://h/first", auth=auth)

        assert request.headers["Authorization"] == "Bearer TOKEN"

    @freeze_time(NOW)
    def test_auth_renew_when_token_expired(self, auth, responses):
        auth.token = ("EXPIRED", 0)

        request = PreparedRequest()
        request.prepare("GET", "https://h/first", auth=auth)

        assert request.headers["Authorization"] == "Bearer TOKEN"

    @freeze_time(NOW)
    def test_auth_recover_from_undetected_expired_token(self, auth, responses):
        # First renew is due to auth without token.
        auth.token = ("EXPIRED", -1)
        # Then we try a GET and force a 401 as if the token expiration was not detected.
        responses.add("GET", "https://h/first", status=401)
        # The 401 will trigger auth.handle_401 that will renew the token once more
        # The auth.handle_401 will then retry the failed request.
        responses.add("GET", "https://h/first", status=200)

        r = requests.get("https://h/first", auth=auth)

        assert auth.stored_token == "TOKEN"  # Checking without triggering renewal.
        assert len(responses.calls) == 2
        assert r.status_code == 200

    @freeze_time(NOW)
    def test_auth_dont_recover_twice(self, auth, responses):
        # First renew is due to auth without token.
        auth.token = ("EXPIRED1", -1)
        # Then we try a GET and force a 401 as if the token expiration was not detected.
        responses.add("GET", "https://h/first", status=401)
        # The 401 will trigger auth.handle_401 that will renew the token once more
        patch.object(auth, "renew", return_value=("EXPIRED2", -1))
        # The auth.handle_401 will then retry the failed request.
        responses.add("GET", "https://h/first", status=401, json={"Message": "No Token"})

        with pytest.raises(HTTPError, match="401"):
            requests.get("https://h/first", auth=auth)

        assert len(responses.calls) == 2
