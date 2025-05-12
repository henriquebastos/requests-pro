from functools import partialmethod

from requestspro.audit import Audit


class Client:
    """Base class for all API clients. Use it on your subclients."""

    def __init__(self, session):
        self.session = session

    def request(self, method, url, params=None, json=None, **kwargs):
        response = self.session.request(method, url, params=params, json=json, **kwargs)
        response.raise_for_status()
        return response.json()

    get = partialmethod(request, "GET")
    post = partialmethod(request, "POST")
    put = partialmethod(request, "PUT")
    delete = partialmethod(request, "DELETE")
    head = partialmethod(request, "HEAD")
    options = partialmethod(request, "OPTIONS")
    patch = partialmethod(request, "PATCH")


class MainClient(Client):
    """Base class for main API clients that handle credentials and audit setup."""

    def __init__(self, session, *, audit=True):
        super().__init__(session)
        self.audit = Audit.for_session(session) if audit else None

    @classmethod
    def from_credentials(cls, *args, **kwargs):
        """Create a new client instance from credentials.

        This method should be implemented by subclasses to handle their specific
        credential types and create the appropriate auth, session, and adapters instances.
        """
        raise NotImplementedError
