from requests import HTTPError, Session

from requestspro.client import Client

import pytest
from unittest.mock import MagicMock


class TestClient:
    def test_init(self):
        # given: a session
        session = "session"

        # when: instantiating the client with a session
        instance = Client(session)

        # then: the instance is created with the session
        assert instance.session == session

    def test_highlevel_request_returns_dict(self, responses):
        responses.add("GET", "https://h/first", status=200, json={"great": "success"})

        # given: a client
        client = Client(Session())

        # when: calling the high level request method
        result = client.request("GET", "https://h/first")

        # then: the response content is returned as a dict
        assert result == {"great": "success"}

    def test_highlevel_request_raises_on_error(self, responses):
        responses.add("GET", "https://h/first", status=400)

        # given: a client
        client = Client(Session())

        # when: calling the high level request method
        # then: an exception is raised for errored responses
        with pytest.raises(HTTPError):
            client.request("GET", "https://h/first")

    @pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"])
    def test_client_has_http_methods(self, method):
        # given: an instance of the Client
        instance = Client(session := MagicMock())

        # when: calling the request method
        client_method = getattr(instance, method.lower())
        client_method(url="url", params="params", json="json", foo="bar")

        # then: the session request is called as expected
        session.request.assert_called_once_with(method, "url", params="params", json="json", foo="bar")
