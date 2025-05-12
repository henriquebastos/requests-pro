from datetime import datetime

from requestspro.token import ExpireValue, TokenStore
from requestspro.utc import UTC

import pytest
from freezegun import freeze_time


NOW = datetime(2021, 12, 4, 0, 0, 0, tzinfo=UTC)


@freeze_time(NOW)
@pytest.mark.parametrize("cache", [ExpireValue()])
class TestToken:
    def test_token_expiration_logic(self, cache):
        store = TokenStore(cache, key="shared-test-token")

        assert store() is None, "Token should be empty."

        store("TOKEN", 1)
        assert store() == "TOKEN", "Token should be valid on the limit."

        store("EXPIRED", 0)
        assert store() is None, "Token should be just expired."

    def test_token_with_offset(self, cache):
        store = TokenStore(cache, key="shared-test-token", offset=10)

        store("TOKEN", 10)
        assert store() is None, "Token valid for 10s minus offset of 10s should be expired."

        store("TOKEN", 11)
        assert store() == "TOKEN", "Token valid for 11s minus offset of 10s should be valid."
