"""
This is a simple yet complete example of how to use RequestsPro to build a professional API client.
It's a client for the Eduzz API V2. Doc at https://api2.eduzz.com/

Here is how it is structured:

The `EduzzClient` is the main client that will be used to interact with the API.
It contains two subclients: `EduzzUserClient` and `EduzzSalesClient`.

The `EduzzUserSubClient` is used to manage your profile in Eduzz.
The `EduzzSalesSubClient` is used to manage your sales in Eduzz.

The `EduzzSession` is the session that will be used to make the requests.

The `EduzzAuth` is the authentication handler that will be used to transparently authenticate the requests.

The `EduzzResponse` is the response class that handles errors transparently the API error particularities.

The `EduzzAPIError` is the exception that will be raised when the API returns an error.
For simplicity I chose to not build an extended exception hierarchy.

The magic happens in the `from_credentials` factory that will instantiate and compose all the pieces.

The Client and SubClients are simple because we handled all the API crazyness before, so they are just thin
wrappers around the API.
"""

from datetime import datetime
from typing import Any, TypeVar

import pytz
from requests.exceptions import RequestException

from requestspro.auth import RecoverableAuth
from requestspro.client import Client, MainClient
from requestspro.sessions import ProResponse, ProSession
from requestspro.token import TokenStore
from requestspro.utc import utc_now


# Type variables for more descriptive API types
JSON = TypeVar("JSON", bound=dict[str, Any])
Params = TypeVar("Params", bound=dict[str, Any] | None)
Data = TypeVar("Data", bound=dict[str, Any])
TokenData = TypeVar("TokenData", bound=str)
TokenExpiry = TypeVar("TokenExpiry", bound=int)

SAO_PAULO = pytz.timezone("America/Sao_Paulo")


class EduzzAPIError(RequestException):
    """The exception raised for all Eduzz API errors."""

    def __init__(self, message: str, response: ProResponse | None = None):
        super().__init__(message, response=response)


class EduzzResponse(ProResponse):
    """Handles all the API error particularities."""

    ERROR_STATUSES = {400, 401, 403, 404, 405, 409, 422, 500}

    def raise_for_status(self):
        """Handle API logic errors and delegate HTTP errors to the superclass."""
        if self.status_code in self.ERROR_STATUSES:
            json = self.json()
            code, details = json["code"], json["details"]

            msg = f"{code} {details}"
            raise EduzzAPIError(msg, response=self)

        super().raise_for_status()


class EduzzSession(ProSession):
    """Custom session for Eduzz API with proper response handling and JSON encoding."""

    RESPONSE_CLASS = EduzzResponse
    BASE_URL = "https://api2.eduzz.com"


class EduzzAuth(RecoverableAuth):
    """Eduzz V2 API authentication handler."""

    AUTH_PATH = "/credential/generate_token"
    SESSION_CLASS = EduzzSession

    def __init__(self, token, email, publickey, apikey):
        self.credentials = {"email": email, "publickey": publickey, "apikey": apikey}
        super().__init__(token)

    def authorize(self, req):
        req.headers["Token"] = self.token
        return req

    def renew(self, now=utc_now) -> tuple[TokenData, TokenExpiry]:
        """Renew the authentication token."""
        r = self.session_class().post(self.AUTH_PATH, params=self.credentials)
        r.raise_for_status()

        json = r.json()
        token = json["data"]["token"]
        token_valid_until = json["data"]["token_valid_until"]

        # Token expiration date is provided without the explicit TZ, so we need to
        # convert it to the correct timezone and then to UTC.
        dt = datetime.fromisoformat(token_valid_until)
        dt.replace(tzinfo=SAO_PAULO)
        dt = dt.astimezone(pytz.UTC)
        ttl = (dt - now()).total_seconds()

        return token, ttl


class EduzzClient(MainClient):
    """Main client for Eduzz V2 API."""

    @classmethod
    def from_credentials(cls, email, publickey, apikey):
        token = TokenStore.in_memory()
        auth = EduzzAuth(token, email, publickey, apikey)
        session = EduzzSession(auth=auth)
        return cls(session)

    def __init__(self, session: EduzzSession):
        super().__init__(session)

        self.user = EduzzUserSubClient(session)
        self.sales = EduzzSalesSubClient(session)


class EduzzUserSubClient(Client):
    """SubClient for managing your profile in Eduzz."""

    def get_me(self) -> JSON:
        return self.get("/user/get_me")

    def set_me(self, data: Data) -> JSON:
        return self.post("/user/set_me", json=data)

    def set_me_as_producer(self) -> JSON:
        return self.post("/user/set_me_as_producer")

    def change_password(self, data: Data) -> JSON:
        return self.post("/user/change_password", json=data)

    def my_buys_list(self, params: Params = None) -> JSON:
        return self.get("/user/my_buys_list", params=params)


class EduzzSalesSubClient(Client):
    """SubClient for managing sales in Eduzz."""

    def list(self, params: Params = None) -> JSON:
        return self.get("/sales/get_sale_list", params=params)

    def retrieve(self, sale_id: int) -> JSON:
        return self.get(f"/sale/get_sale/{sale_id}")

    def last_days_amount(self, params: Params = None) -> JSON:
        return self.get("/sale/last_days_amount", params=params)

    def tracking_code(self, sale_id: int, data: Data) -> JSON:
        return self.post(f"/sale/tracking_code/{sale_id}", json=data)

    def get_total(self, params: Params = None) -> JSON:
        return self.get("/sale/get_total", params=params)


if __name__ == "__main__":
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument("pubkey", default=os.getenv("EDUZZ_PUBLICKEY"))
    parser.add_argument("apikey", default=os.getenv("EDUZZ_APIKEY"))
    parser.add_argument("email", default=os.getenv("EDUZZ_EMAIL"))

    try:
        args = parser.parse_args()
    except SystemExit:
        parser.print_help()
        sys.exit(1)

    client = EduzzClient.from_credentials(args.email, args.pubkey, args.apikey)

    # Do stuff
    print(client.user.get_me())  # noqa: T201
