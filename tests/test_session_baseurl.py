from requestspro.sessions import BaseUrlSession


class TestBaseUrlSession:
    def test_baseurl(self):
        s = BaseUrlSession(base_url="https://host")

        assert s.ensure_absolute_url("/data") == "https://host/data"
        assert s.ensure_absolute_url("https://other/data") == "https://other/data"
        assert s.ensure_absolute_url("//other/data") == "//other/data"
