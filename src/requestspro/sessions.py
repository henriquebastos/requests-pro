import json
from urllib.parse import urljoin, urlparse

from requests import Response, Session
from requests.exceptions import InvalidJSONError

from requestspro.auth import RecoverableAuth


class BaseSession(Session):
    """A base class for requests.Session that accepts kwargs to ease complex inheritance hierarchies."""

    def __init__(self, **kwargs):
        super().__init__()


class BaseUrlSession(BaseSession):
    """Taken from https://github.com/requests/toolbelt/"""

    BASE_URL = ""

    def __init__(self, base_url="", **kwargs):
        self.base_url = base_url or self.BASE_URL
        super().__init__(**kwargs)

    @staticmethod
    def is_absolute(url):
        return bool(urlparse(url).netloc)

    def ensure_absolute_url(self, url):
        return url if self.is_absolute(url) else urljoin(self.base_url, url)

    def prepare_request(self, request):
        """Prepare the request after generating the complete URL."""
        request.url = self.ensure_absolute_url(request.url)
        return super().prepare_request(request)


class CustomResponseSession(BaseSession):
    RESPONSE_CLASS = None

    def __init__(self, response_class=None, **kwargs):
        self.response_class = response_class or self.RESPONSE_CLASS
        super().__init__(**kwargs)

    def send(self, request, **kwargs):
        response = super().send(request, **kwargs)
        if self.response_class:
            response = self._cast_response(response, self.response_class)
        return response

    @staticmethod
    def _cast_response(response, response_class, **kwargs):  # Must keep kwargs due to how hooks work.
        """Magic to force the response object to user our Response class code."""
        response.__class__ = response_class
        return response


class ProResponse(Response):
    """A Response class for requests that knows its json decoder."""

    def __init__(self, json_decoder=None, json_decoder_options=None):
        self.json_decoder = json_decoder
        self.json_decoder_options = json_decoder_options or {}
        super().__init__()

    def __repr__(self):
        return f"<Response [{self.status_code}] {self.url}>"

    def json(self, **kwargs):
        """Decodes data with custom json decoder and caches the resulting dictionary."""
        params = {**self.json_decoder_options, "cls": self.json_decoder, **kwargs}
        return super().json(**params)


class CustomJsonSession(BaseSession):
    """Allows for customization of json encoding and decoding."""

    JSON_ENCODER = None
    JSON_ENCODER_OPTIONS = None
    JSON_DECODER = None
    JSON_DECODER_OPTIONS = None
    REQUEST_BODY_ENCODING = "utf-8"
    REQUEST_CONTENT_TYPE = "application/json"

    def __init__(
        self,
        json_encoder=None,
        json_encoder_options=None,
        json_decoder=None,
        json_decoder_options=None,
        request_body_encoding=None,
        request_content_type=None,
        **kwargs,
    ):
        self.json_encoder = json_encoder or self.JSON_ENCODER
        self.json_encoder_options = json_encoder_options or self.JSON_ENCODER_OPTIONS or {}
        self.json_decoder = json_decoder or self.JSON_DECODER
        self.json_decoder_options = json_decoder_options or self.JSON_DECODER_OPTIONS or {}
        self.request_body_encoding = request_body_encoding or self.REQUEST_BODY_ENCODING
        self.request_content_type = request_content_type or self.REQUEST_CONTENT_TYPE

        super().__init__(**kwargs)

    def send(self, request, **kwargs):
        """Inspects if our response is a ProResponse to inform its desired decoder."""
        response = super().send(request, **kwargs)
        if isinstance(response, ProResponse):
            response.json_decoder = self.json_decoder
            response.json_decoder_options = self.json_decoder_options
        return response

    def prepare_request(self, request):
        """
        Override of requests.Session.prepare_request to ensure json is encoded with our custom encoder.

        This is how requests turn a json dictionary into data bytes:

        1. requests.Session.request will call requests.Session.prepare_request to build the actual request details.
        2. requests.Session.prepare_request will instantiate a PrepareRequest objects.
        3. PrepareRequest.prepare will do the heavy lifting, and at some point will call PrepareRequest.prepare_body
        4. PrepareRequest.prepare_body will encode the json to bytes and set request.data if data is not defined.

        Before requests.Session.prepare_request is called, we anticipate and encode json with our custom encoder
        and provide the results as request.data bypassing PrepareRequest.prepare_body encoding process.
        """
        self.before_prepare_body(request)
        return super().prepare_request(request)

    def before_prepare_body(self, request):
        """Encode json using custom encoder before PrepareRequest.prepare_body is called."""

        # When Request has data but no json, there is nothing to encode.
        if request.data and request.json is None:
            return

        # Snippet from requests.PreparedRequest.prepare_body
        try:
            data = json.dumps(request.json, cls=self.json_encoder, **self.json_encoder_options)
        except ValueError as ve:
            raise InvalidJSONError(ve, request=self) from ve

        if not isinstance(data, bytes):
            data = data.encode(self.request_body_encoding)

        request.data = data
        request.json = None

        # Ensure request has a content-type.
        if "content-type" not in request.headers:
            request.headers["Content-Type"] = self.request_content_type


class ProSession(BaseUrlSession, CustomJsonSession, CustomResponseSession):
    """The session for all API clients.

    Initialization parameters:
        base_url (default: ""): Base URL to prepend to all requests.
        json_encoder (default: json.JSONEncoder): Custom JSON encoder class.
        json_encoder_options (default: None): Additional options for JSON encoder.
        json_decoder (default: json.JSONDecoder): Custom JSON decoder class.
        json_decoder_options (default: None): Additional options for JSON decoder.
        request_content_type (default: "application/json"): Content-Type header for requests.
        request_body_encoding (default: "utf-8"): Encoding for request body.
        response_class (default: requests.Response): Custom Response class to use.

    Notes:
        The default Python JSON encoder does not support many common data types like datetime,
        UUID, or custom classes. We strongly recommend using python-jsonstar's encoder which
        provides better serialization support and customization options:

        ```python
            # pip install python-jsonstar

            import jsonstar as json

            class MyJsonEncoder(json.JSONEncoder):
                pass

            class MySession(ProSession):
                JSON_ENCODER = MyJsonEncoder
        ```

        This will handle most common data types automatically and allows easy customization
        through encoder hooks.
    """

    def __init__(self, auth: RecoverableAuth | None = None, headers: dict[str, str] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.auth = auth
        if headers:
            self.headers.update(headers)
