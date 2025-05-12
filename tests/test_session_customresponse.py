from requests import Response

from requestspro.sessions import CustomResponseSession

import pytest


class SampleCustomResponse(Response):
    pass


class SampleCustomResponseSession(CustomResponseSession):
    RESPONSE_CLASS = SampleCustomResponse


class TestCustomResponseSession:
    @pytest.fixture(autouse=True)
    def mocked_get(self, responses):
        responses.add("GET", "https://h/data")

    def test_session_does_nothing_when_no_custom_response_exists(self):
        response = CustomResponseSession().get("https://h/data")
        assert response.__class__ is Response

    def test_session_swaps_response_with_custom_class_provided_on_init(self):
        response = CustomResponseSession(response_class=SampleCustomResponse).get("https://h/data")
        assert isinstance(response, SampleCustomResponse)

    def test_session_swaps_response_with_custom_class_provided_as_class_attr(self):
        response = SampleCustomResponseSession().get("https://h/data")
        assert isinstance(response, SampleCustomResponse)
