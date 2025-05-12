from json import JSONDecoder, JSONEncoder

from requestspro.sessions import CustomJsonSession, CustomResponseSession, ProResponse

import pytest


class SampleDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        self.custom_kwargs = {}

        if "a" in kwargs:
            self.custom_kwargs["a"] = kwargs.pop("a")

        super().__init__(*args, **kwargs)

    def decode(self, obj, *args, **kwargs):
        result = super().decode(obj)
        result["test"] = "from decoder"
        result["custom_kwargs"] = self.custom_kwargs
        return result


class SampleEncoder(JSONEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def encode(self, obj, *args, **kwargs):
        obj["data"] = "changed on SampleEncoder"
        return super().encode(obj)


class TestProResponse:
    def test_default_encoder(self):
        response = ProResponse()
        response._content = b'{"a": 1}'
        # Default behavior, nothing new
        assert response.json() == {"a": 1}

    def test_custom_decoder_and_options(self):
        response = ProResponse(json_decoder=SampleDecoder, json_decoder_options={"a": 42})
        response._content = b'{"a": 1, "b": 1.23}'
        response.encoding = "utf8"

        assert response.json() == {"a": 1, "b": 1.23, "test": "from decoder", "custom_kwargs": {"a": 42}}


class SampleCustomJsonSession(CustomJsonSession, CustomResponseSession):
    JSON_ENCODER = SampleEncoder
    JSON_ENCODER_OPTIONS = {"ensure_ascii": False, "sort_keys": True}
    JSON_DECODER = SampleDecoder
    JSON_DECODER_OPTIONS = {"a": 42}
    RESPONSE_CLASS = ProResponse


class TestCustomJsonSession:
    @pytest.fixture(autouse=True)
    def mocked_post(self, responses):
        responses.add("POST", "https://h/data", body='{"a": 1, "b": 1.23}')

    def test_session_uses_configured_params(self):
        # Given: class with configured params in the class attributes
        session = SampleCustomJsonSession()

        # When: we make a request
        response = session.post(
            "https://h/data",
            json={"key2": "á", "key1": "Á"},
        )

        # Then: response should be the expected instance
        assert isinstance(response, ProResponse)

        # And the response should've used the Decoder class and custom params
        assert response.json() == {
            "a": 1,
            "b": 1.23,  # Ensures decoder options were processed
            "test": "from decoder",  # Ensure custom decoder class executed,
            "custom_kwargs": {"a": 42},
        }

        # And the encoder should've respected the custom class and params
        # The key1 and key2 have accented chars, which was made possible by the param "ensure_ascii=False"
        assert response.request.body.decode("utf8") == '{"data": "changed on SampleEncoder", "key1": "Á", "key2": "á"}'

    def test_session_uses_default_class_attributes(self):
        default = SampleCustomJsonSession()
        assert default.json_encoder == SampleEncoder
        assert default.json_encoder_options == {"ensure_ascii": False, "sort_keys": True}
        assert default.json_decoder == SampleDecoder
        assert default.json_decoder_options == {"a": 42}
        assert default.request_body_encoding == "utf-8"
        assert default.request_content_type == "application/json"

    def test_session_accepts_init_params(self):
        customized_via_init = SampleCustomJsonSession(
            json_encoder="json_encoder",
            json_encoder_options="json_encoder_options",
            json_decoder="json_decoder",
            json_decoder_options="json_decoder_options",
            request_body_encoding="request_body_encoding",
            request_content_type="request_content_type",
        )

        assert customized_via_init.json_encoder == "json_encoder"
        assert customized_via_init.json_encoder_options == "json_encoder_options"
        assert customized_via_init.json_decoder == "json_decoder"
        assert customized_via_init.json_decoder_options == "json_decoder_options"
        assert customized_via_init.request_body_encoding == "request_body_encoding"
        assert customized_via_init.request_content_type == "request_content_type"
