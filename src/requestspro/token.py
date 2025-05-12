from datetime import timedelta

from requestspro.utc import utc_now


class ExpireValue:
    """In-memory value that expires implemented with the same interface of a cache."""

    def __init__(self, now=utc_now):
        self._token = None
        self._token_valid_until = None
        self._now = now

    @property
    def _is_expired(self):
        if self._token_valid_until is None:
            return True

        return self._now() >= self._token_valid_until

    def set(self, key, value, seconds_to_expire: int):
        self._token = value
        self._token_valid_until = self._now() + timedelta(seconds=seconds_to_expire)
        return value

    def get(self, key, default=None):
        if self._is_expired:
            return default

        return self._token


class TokenStore:
    """
    Generic token storage interface to work with Auth.
    It expects a cache-like object that can be Django's cache, ExpireValue, or others.
    """

    UNDEFINED = object()

    def __init__(self, cache, key=None, offset=0):
        self._key = key
        self._offset = offset
        self._cache = cache

    def __call__(self, value=UNDEFINED, expires_in=0):
        if value is self.UNDEFINED:
            return self._cache.get(self._key)

        self._cache.set(self._key, value, expires_in - self._offset)
        return value

    @classmethod
    def in_memory(cls, offset=0, now=utc_now):
        return cls(ExpireValue(now=now), offset=offset)
