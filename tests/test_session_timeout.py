import pytest
from requests import Response
from requests.adapters import HTTPAdapter
from requestspro.sessions import BaseSession


class MockAdapter(HTTPAdapter):
    """Mock adapter that captures send method calls and returns mock responses."""
    
    def __init__(self):
        super().__init__()
        self.captured_calls = []
        
    def send(self, request, stream=False, timeout=None, verify=None, cert=None, proxies=None):
        """Capture the call parameters and return a mock response."""
        self.captured_calls.append({
            'request': request,
            'timeout': timeout,
            'stream': stream,
            'verify': verify,
            'cert': cert,
            'proxies': proxies
        })
        
        # Create a mock response
        response = Response()
        response.status_code = 200
        response.headers['Content-Type'] = 'application/json'
        response._content = b'{"key": "value"}'
        response.url = request.url
        response.request = request
        return response


class TestBaseSessionTimeout:
    """Test timeout behavior in BaseSession."""

    def test_timeout_parameter(self):
        session = BaseSession(timeout=5.0)
        assert session.timeout == 5.0

    def test_timeout_class_attribute(self):
        class CustomSession(BaseSession):
            TIMEOUT = 10.0
        
        session = CustomSession()
        assert session.timeout == 10.0

    def test_timeout_parameter_overrides_class_attribute(self):
        class CustomSession(BaseSession):
            TIMEOUT = 10.0
        
        session = CustomSession(timeout=5.0)
        assert session.timeout == 5.0

    def test_no_timeout_default(self):
        session = BaseSession()
        assert session.timeout is None

    def test_timeout_none_explicit(self):
        session = BaseSession(timeout=None)
        assert session.timeout is None

    def test_session_timeout_applied_to_request(self):
        """Session timeout is used when no per-request timeout provided."""
        session = BaseSession(timeout=5.0)
        
        # Create mock adapter and mount it
        mock_adapter = MockAdapter()
        session.mount('http://', mock_adapter)
        session.mount('https://', mock_adapter)
        
        # Make request
        response = session.request('GET', 'http://example.com')
        
        # Verify timeout was passed to send method
        assert len(mock_adapter.captured_calls) == 1
        assert mock_adapter.captured_calls[0]['timeout'] == 5.0
        assert response.status_code == 200

    def test_per_request_timeout_overrides_session_timeout(self):
        """Per-request timeout takes precedence over session timeout."""
        session = BaseSession(timeout=5.0)
        
        # Create mock adapter and mount it
        mock_adapter = MockAdapter()
        session.mount('http://', mock_adapter)
        session.mount('https://', mock_adapter)
        
        # Make request with per-request timeout
        response = session.request('GET', 'http://example.com', timeout=10.0)
        
        # Verify per-request timeout was used
        assert len(mock_adapter.captured_calls) == 1
        assert mock_adapter.captured_calls[0]['timeout'] == 10.0
        assert response.status_code == 200

    def test_no_session_timeout_no_per_request_timeout(self):
        """No timeout applied when neither session nor per-request timeout provided."""
        session = BaseSession()
        
        # Create mock adapter and mount it
        mock_adapter = MockAdapter()
        session.mount('http://', mock_adapter)
        session.mount('https://', mock_adapter)
        
        # Make request without any timeout
        response = session.request('GET', 'http://example.com')
        
        # Verify no timeout was passed (should be None by default)
        assert len(mock_adapter.captured_calls) == 1
        assert mock_adapter.captured_calls[0]['timeout'] is None
        assert response.status_code == 200

    def test_timeout_tuple_support(self):
        """Session timeout supports tuple format (connect, read)."""
        session = BaseSession(timeout=(3.0, 10.0))
        assert session.timeout == (3.0, 10.0)
        
        # Create mock adapter and mount it
        mock_adapter = MockAdapter()
        session.mount('http://', mock_adapter)
        session.mount('https://', mock_adapter)
        
        # Make request
        response = session.request('GET', 'http://example.com')
        
        # Verify tuple timeout was passed to send method
        assert len(mock_adapter.captured_calls) == 1
        assert mock_adapter.captured_calls[0]['timeout'] == (3.0, 10.0)
        assert response.status_code == 200