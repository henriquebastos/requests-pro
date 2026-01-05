# How to Build a Professional API Client with RequestsPro

This guide walks you through building a production-ready API client using RequestsPro. By the end, you'll understand the library's architecture and be able to create clients that handle authentication, error handling, token management, and auditing transparently.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Quick Start](#quick-start)
3. [Step-by-Step Guide](#step-by-step-guide)
4. [Component Reference](#component-reference)
5. [Advanced Topics](#advanced-topics)

---

## Architecture Overview

RequestsPro follows a layered, composable architecture:

```
┌─────────────────────────────────────────────────────────┐
│                     MainClient                          │
│  (Your API client with from_credentials factory)        │
├─────────────────────────────────────────────────────────┤
│                     SubClients                          │
│  (Domain-specific clients: users, sales, products...)   │
├─────────────────────────────────────────────────────────┤
│                     ProSession                          │
│  (HTTP session with base URL, JSON encoding, response)  │
├─────────────────────────────────────────────────────────┤
│                  RecoverableAuth                        │
│  (Transparent authentication with auto-renewal)         │
├─────────────────────────────────────────────────────────┤
│                    TokenStore                           │
│  (Token persistence: in-memory, Django cache, etc.)     │
├─────────────────────────────────────────────────────────┤
│                      Audit                              │
│  (HTTP request/response logging and inspection)         │
└─────────────────────────────────────────────────────────┘
```

**Key Principles:**
- **Separation of Concerns**: Each component handles one responsibility
- **Composability**: Mix and match components as needed
- **Transparency**: Authentication, retries, and errors are handled automatically
- **Extensibility**: Override only what you need to customize

---

## Quick Start

Here's a minimal API client in under 30 lines:

```python
from requestspro.auth import RecoverableAuth
from requestspro.client import Client, MainClient
from requestspro.sessions import ProSession
from requestspro.token import TokenStore


class MySession(ProSession):
    BASE_URL = "https://api.example.com"


class MyAuth(RecoverableAuth):
    SESSION_CLASS = MySession

    def __init__(self, token, api_key):
        self.api_key = api_key
        super().__init__(token)

    def renew(self):
        r = self.session_class().post("/auth/token", json={"api_key": self.api_key})
        r.raise_for_status()
        data = r.json()
        return data["token"], data["expires_in"]


class MyClient(MainClient):
    @classmethod
    def from_credentials(cls, api_key):
        token = TokenStore.in_memory()
        auth = MyAuth(token, api_key)
        session = MySession(auth=auth)
        return cls(session)

    def get_users(self):
        return self.get("/users")


# Usage
client = MyClient.from_credentials("your-api-key")
users = client.get_users()
```

---

## Step-by-Step Guide

### Step 1: Define Your Custom Response Class (Optional)

If your API has specific error handling needs, create a custom response class:

```python
from requests.exceptions import RequestException
from requestspro.sessions import ProResponse


class MyAPIError(RequestException):
    """Custom exception for API errors."""

    def __init__(self, message, code=None, response=None):
        self.code = code
        super().__init__(message, response=response)


class MyResponse(ProResponse):
    """Handle API-specific error responses."""

    # Status codes that indicate API errors
    ERROR_STATUSES = {400, 401, 403, 404, 422, 500}

    def raise_for_status(self):
        if self.status_code in self.ERROR_STATUSES:
            data = self.json()
            # Adapt this to your API's error format
            error_code = data.get("error", {}).get("code", "UNKNOWN")
            error_message = data.get("error", {}).get("message", "Unknown error")
            raise MyAPIError(error_message, code=error_code, response=self)

        # Fall back to standard HTTP error handling
        super().raise_for_status()
```

### Step 2: Create Your Session Class

The session handles base URL, JSON encoding/decoding, and response class:

```python
from requestspro.sessions import ProSession


class MySession(ProSession):
    # Required: Base URL for all requests
    BASE_URL = "https://api.example.com/v1"

    # Optional: Custom response class
    RESPONSE_CLASS = MyResponse

    # Optional: Session-level timeout in seconds
    TIMEOUT = 30

    # Optional: Custom JSON encoder for complex types
    # JSON_ENCODER = MyJsonEncoder
    # JSON_DECODER = MyJsonDecoder
```

**Using Custom JSON Encoding:**

```python
import jsonstar as json  # pip install python-jsonstar


class MyJsonEncoder(json.JSONEncoder):
    """Handle datetime, UUID, Decimal, etc."""
    pass


class MySession(ProSession):
    BASE_URL = "https://api.example.com"
    JSON_ENCODER = MyJsonEncoder
```

### Step 3: Implement Authentication

Create an auth class that handles token acquisition and renewal:

```python
from requestspro.auth import RecoverableAuth


class MyAuth(RecoverableAuth):
    # Use your session class for auth requests
    SESSION_CLASS = MySession

    # Optional: Path to the auth endpoint
    AUTH_PATH = "/oauth/token"

    def __init__(self, token, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        super().__init__(token)

    def authorize(self, req):
        """Add authentication to each request."""
        # Default is Bearer token in Authorization header
        req.headers["Authorization"] = f"Bearer {self.token}"
        return req

    def renew(self) -> tuple[str, int]:
        """Fetch a new token when expired or on 401."""
        response = self.session_class().post(
            self.AUTH_PATH,
            json={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        )
        response.raise_for_status()

        data = response.json()
        token = data["access_token"]
        expires_in = data["expires_in"]  # TTL in seconds

        return token, expires_in
```

**Different Authorization Schemes:**

```python
# API Key in header
def authorize(self, req):
    req.headers["X-API-Key"] = self.token
    return req

# Custom token header
def authorize(self, req):
    req.headers["Token"] = self.token
    return req

# Query parameter
def authorize(self, req):
    from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
    parsed = urlparse(req.url)
    params = parse_qs(parsed.query)
    params["token"] = self.token
    req.url = urlunparse(parsed._replace(query=urlencode(params, doseq=True)))
    return req
```

### Step 4: Build Your Client Classes

Create the main client and sub-clients for different API domains:

```python
from requestspro.client import Client, MainClient
from requestspro.token import TokenStore


class MyClient(MainClient):
    """Main client with factory method and sub-clients."""

    @classmethod
    def from_credentials(cls, client_id, client_secret):
        """Factory to create a fully configured client."""
        # Choose token storage strategy
        token = TokenStore.in_memory()  # or use Django cache, Redis, etc.

        # Create auth handler
        auth = MyAuth(token, client_id, client_secret)

        # Create configured session
        session = MySession(auth=auth)

        return cls(session)

    def __init__(self, session):
        super().__init__(session)

        # Initialize sub-clients
        self.users = UsersSubClient(session)
        self.products = ProductsSubClient(session)
        self.orders = OrdersSubClient(session)


class UsersSubClient(Client):
    """Sub-client for user operations."""

    def list(self, page=1, per_page=20):
        return self.get("/users", params={"page": page, "per_page": per_page})

    def get(self, user_id):
        return self.get(f"/users/{user_id}")

    def create(self, data):
        return self.post("/users", json=data)

    def update(self, user_id, data):
        return self.put(f"/users/{user_id}", json=data)

    def delete(self, user_id):
        return self.delete(f"/users/{user_id}")


class ProductsSubClient(Client):
    """Sub-client for product operations."""

    def list(self, category=None):
        params = {"category": category} if category else None
        return self.get("/products", params=params)

    def get(self, product_id):
        return self.get(f"/products/{product_id}")


class OrdersSubClient(Client):
    """Sub-client for order operations."""

    def list(self, status=None):
        params = {"status": status} if status else None
        return self.get("/orders", params=params)

    def create(self, items):
        return self.post("/orders", json={"items": items})

    def cancel(self, order_id):
        return self.post(f"/orders/{order_id}/cancel")
```

### Step 5: Use Your Client

```python
# Create client from credentials
client = MyClient.from_credentials(
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# Use sub-clients for different operations
users = client.users.list(page=1)
user = client.users.get(123)
new_user = client.users.create({"name": "John", "email": "john@example.com"})

products = client.products.list(category="electronics")

order = client.orders.create([
    {"product_id": 1, "quantity": 2},
    {"product_id": 3, "quantity": 1}
])

# Access audit logs
for event in client.audit:
    print(f"{event['request']['method']} {event['request']['url']}")
    print(f"  Status: {event['response']['status_code']}")
    print(f"  Elapsed: {event['elapsed']}")
```

---

## Component Reference

### TokenStore

Manages token persistence with automatic expiration:

```python
from requestspro.token import TokenStore

# In-memory storage (default)
token = TokenStore.in_memory()

# With Django cache
from django.core.cache import cache
token = TokenStore(cache, key="my_api_token")

# With Redis or any cache-like object
token = TokenStore(redis_client, key="my_api_token")

# With offset to renew tokens before they expire
token = TokenStore.in_memory(offset=60)  # Renew 60 seconds early
```

### ProSession

The session class provides:
- **Base URL handling**: Relative URLs are automatically prefixed
- **Custom JSON encoding/decoding**: Handle complex types like datetime, UUID
- **Custom response class**: API-specific error handling
- **Session-level timeout**: Set default timeout for all requests

```python
from requestspro.sessions import ProSession

class MySession(ProSession):
    BASE_URL = "https://api.example.com"
    RESPONSE_CLASS = MyResponse
    TIMEOUT = 30
    JSON_ENCODER = MyJsonEncoder
    JSON_DECODER = MyJsonDecoder
    REQUEST_CONTENT_TYPE = "application/json"
    REQUEST_BODY_ENCODING = "utf-8"
```

### RecoverableAuth

Handles authentication with automatic token renewal and 401 recovery:

```python
from requestspro.auth import RecoverableAuth

class MyAuth(RecoverableAuth):
    SESSION_CLASS = MySession

    def authorize(self, req):
        """Add authentication to the request."""
        req.headers["Authorization"] = f"Bearer {self.token}"
        return req

    def renew(self) -> tuple[str, int]:
        """Return (token, ttl_in_seconds)."""
        # Make auth request and return new token
        ...
```

### Audit

Captures all HTTP traffic for debugging and logging:

```python
# Access audit logs
for event in client.audit:
    print(event["audited_at"])
    print(event["elapsed"])
    print(event["request"]["method"])
    print(event["request"]["url"])
    print(event["request"]["headers"])
    print(event["request"]["body"])
    print(event["response"]["status_code"])
    print(event["response"]["headers"])
    print(event["response"]["body"])

# Disable audit
client = MyClient.from_credentials(..., audit=False)

# Custom audit filter
from requestspro.audit import Audit

def redact_sensitive_data(event):
    """Filter function to redact sensitive headers."""
    event["request"]["headers"].pop("Authorization", None)
    return event

audit = Audit.for_session(session, audit_filter=redact_sensitive_data)
```

---

## Advanced Topics

### Custom Token Storage with Django

```python
from django.core.cache import cache
from requestspro.token import TokenStore

class MyClient(MainClient):
    @classmethod
    def from_credentials(cls, client_id, client_secret, cache_key="myapi_token"):
        token = TokenStore(cache, key=cache_key, offset=60)
        auth = MyAuth(token, client_id, client_secret)
        session = MySession(auth=auth)
        return cls(session)
```

### Handling Rate Limits

```python
import time
from requests.adapters import HTTPAdapter


class RateLimitAdapter(HTTPAdapter):
    def send(self, request, **kwargs):
        response = super().send(request, **kwargs)
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 1))
            time.sleep(retry_after)
            return super().send(request, **kwargs)
        return response


# Mount the adapter
session = MySession(auth=auth)
session.mount("https://", RateLimitAdapter())
```

### Adding Request Retries

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)

session = MySession(auth=auth)
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
```

### Sandbox/Production Environments

```python
class MySession(ProSession):
    PRODUCTION_URL = "https://api.example.com"
    SANDBOX_URL = "https://sandbox.api.example.com"

    def __init__(self, sandbox=False, **kwargs):
        self.BASE_URL = self.SANDBOX_URL if sandbox else self.PRODUCTION_URL
        super().__init__(**kwargs)


class MyClient(MainClient):
    @classmethod
    def from_credentials(cls, client_id, client_secret, sandbox=False):
        token = TokenStore.in_memory()
        auth = MyAuth(token, client_id, client_secret)
        session = MySession(auth=auth, sandbox=sandbox)
        return cls(session)


# Usage
prod_client = MyClient.from_credentials("id", "secret")
sandbox_client = MyClient.from_credentials("id", "secret", sandbox=True)
```

### Testing Your Client

```python
import pytest
from unittest.mock import Mock, patch


def test_users_list():
    # Mock the session
    mock_session = Mock()
    mock_session.request.return_value.json.return_value = [
        {"id": 1, "name": "John"}
    ]

    client = MyClient(mock_session)
    users = client.users.list()

    assert len(users) == 1
    assert users[0]["name"] == "John"


def test_auth_renewal():
    # Test that expired tokens are renewed
    token = TokenStore.in_memory()
    auth = MyAuth(token, "client_id", "client_secret")

    with patch.object(auth, "renew", return_value=("new_token", 3600)):
        assert auth.token == "new_token"
```

---

## Complete Example

See [demo/eduzz.py](../demo/eduzz.py) for a complete, production-ready API client implementation that demonstrates all these concepts.

---

## Summary

Building a professional API client with RequestsPro involves:

1. **Define a Response class** (optional) - Handle API-specific errors
2. **Create a Session class** - Set base URL, JSON encoding, timeouts
3. **Implement Auth class** - Handle token acquisition and renewal
4. **Build Client classes** - Create MainClient with sub-clients
5. **Use the factory method** - `from_credentials()` composes everything

The library handles the complexity of authentication, token management, error handling, and auditing, letting you focus on your API's business logic.
