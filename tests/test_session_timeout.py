import pytest
import responses
from requestspro.sessions import BaseSession


class TestBaseSessionTimeout:
    """Test timeout behavior in BaseSession."""

    @responses.activate
    def test_timeout_parameter(self):
        responses.add(responses.GET, "http://example.com", json={"key": "value"})
        
        session = BaseSession(timeout=5.0)
        assert session.timeout == 5.0

    @responses.activate
    def test_timeout_class_attribute(self):
        class CustomSession(BaseSession):
            TIMEOUT = 10.0
        
        session = CustomSession()
        assert session.timeout == 10.0

    @responses.activate
    def test_timeout_parameter_overrides_class_attribute(self):
        class CustomSession(BaseSession):
            TIMEOUT = 10.0
        
        session = CustomSession(timeout=5.0)
        assert session.timeout == 5.0

    @responses.activate
    def test_no_timeout_default(self):
        session = BaseSession()
        assert session.timeout is None

    @responses.activate
    def test_timeout_none_explicit(self):
        session = BaseSession(timeout=None)
        assert session.timeout is None

    @responses.activate
    def test_session_timeout_applied_to_request(self):
        """Session timeout is used when no per-request timeout provided."""
        responses.add(responses.GET, "http://example.com", json={"key": "value"})
        
        session = BaseSession(timeout=5.0)
        
        # Mock the parent request method to capture kwargs
        original_request = BaseSession.__bases__[0].request
        captured_kwargs = {}
        
        def mock_request(self, method, url, **kwargs):
            captured_kwargs.update(kwargs)
            return original_request(self, method, url, **kwargs)
        
        BaseSession.__bases__[0].request = mock_request
        
        try:
            session.request('GET', 'http://example.com')
            assert captured_kwargs['timeout'] == 5.0
        finally:
            BaseSession.__bases__[0].request = original_request

    @responses.activate
    def test_per_request_timeout_overrides_session_timeout(self):
        """Per-request timeout takes precedence over session timeout."""
        responses.add(responses.GET, "http://example.com", json={"key": "value"})
        
        session = BaseSession(timeout=5.0)
        
        # Mock the parent request method to capture kwargs
        original_request = BaseSession.__bases__[0].request
        captured_kwargs = {}
        
        def mock_request(self, method, url, **kwargs):
            captured_kwargs.update(kwargs)
            return original_request(self, method, url, **kwargs)
        
        BaseSession.__bases__[0].request = mock_request
        
        try:
            session.request('GET', 'http://example.com', timeout=10.0)
            assert captured_kwargs['timeout'] == 10.0
        finally:
            BaseSession.__bases__[0].request = original_request

    @responses.activate
    def test_no_session_timeout_no_per_request_timeout(self):
        """No timeout applied when neither session nor per-request timeout provided."""
        responses.add(responses.GET, "http://example.com", json={"key": "value"})
        
        session = BaseSession()
        
        # Mock the parent request method to capture kwargs
        original_request = BaseSession.__bases__[0].request
        captured_kwargs = {}
        
        def mock_request(self, method, url, **kwargs):
            captured_kwargs.update(kwargs)
            return original_request(self, method, url, **kwargs)
        
        BaseSession.__bases__[0].request = mock_request
        
        try:
            session.request('GET', 'http://example.com')
            assert 'timeout' not in captured_kwargs
        finally:
            BaseSession.__bases__[0].request = original_request

    @responses.activate
    def test_timeout_tuple_support(self):
        """Session timeout supports tuple format (connect, read)."""
        responses.add(responses.GET, "http://example.com", json={"key": "value"})
        
        session = BaseSession(timeout=(3.0, 10.0))
        assert session.timeout == (3.0, 10.0)
        
        # Mock the parent request method to capture kwargs
        original_request = BaseSession.__bases__[0].request
        captured_kwargs = {}
        
        def mock_request(self, method, url, **kwargs):
            captured_kwargs.update(kwargs)
            return original_request(self, method, url, **kwargs)
        
        BaseSession.__bases__[0].request = mock_request
        
        try:
            session.request('GET', 'http://example.com')
            assert captured_kwargs['timeout'] == (3.0, 10.0)
        finally:
            BaseSession.__bases__[0].request = original_request