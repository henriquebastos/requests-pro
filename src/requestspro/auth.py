from requests import Session
from requests.auth import AuthBase


class RecoverableAuth(AuthBase):
    SESSION_CLASS = Session

    def __init__(self, token, session_class=None):
        self.session_class = session_class or self.SESSION_CLASS
        self._token = token

    def __call__(self, req):
        """Requests will call this method for when preparing each http request."""
        return self._recover(self.authorize(req))

    def authorize(self, req):
        """Override this if you need to authorize the request differently."""
        req.headers["Authorization"] = f"Bearer {self.token}"
        return req

    def _recover(self, req):
        """Adds the hook to the request, so it can attempt to recover from 401 errors."""
        req.register_hook("response", self.handle_401)
        return req

    @property
    def token(self):
        if value := self._token():
            return value

        return self._token(*self.renew())

    @token.setter
    def token(self, values):
        """For testing purpose only."""
        self._token(*values)

    @property
    def stored_token(self):
        """For testing purpose only."""
        return self._token()

    def renew(self) -> tuple[str, int]:
        raise NotImplementedError

    def _recovery_request(self, original_request):
        """Build a dict representing a recovery request avoiding loops on handling 401."""
        r = original_request
        return {
            "method": r.method,
            "url": r.url,
            "data": r.body,
            "headers": r.headers.copy() if r.headers else None,
            # Filter out handle_401 hooks.
            "hooks": {"response": [h for h in r.hooks["response"] if h != self.handle_401]},
        }

    def handle_401(self, response, *, recover_401=True, **kwargs):
        """Hook to handle 401 responses and retry the originator request."""

        # The hook is always called, but we only care about 401.
        if response.status_code != 401:
            return response

        # Consume content and release the original connection to be reused.
        response.content  # noqa: B018
        response.close()

        session = self.session_class()
        recovery_request = self._recovery_request(response.request)

        # Ensure we reuse the same adapter from previous attempt.
        session.mount(recovery_request["url"], response.connection)

        # Run the recovered request with no recovery from a new 401.
        recovery_response = session.request(**recovery_request, auth=self.authorize, **kwargs)
        recovery_response.raise_for_status()
        return recovery_response
