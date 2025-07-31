import pytest
from unittest.mock import MagicMock
from requests import Response
from requests.adapters import BaseAdapter
from requestspro.sessions import BaseSession


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
        mock_adapter = MagicMock(spec=BaseAdapter)
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.headers['Content-Type'] = 'application/json'
        mock_response._content = b'{"key": "value"}'
        mock_adapter.send.return_value = mock_response
        session.mount('http://', mock_adapter)
        
        # Make request
        response = session.request('GET', 'http://example.com')
        
        # Verify timeout was passed to send method
        mock_adapter.send.assert_called_once()
        args, kwargs = mock_adapter.send.call_args
        assert kwargs['timeout'] == 5.0
        assert response.status_code == 200

    def test_per_request_timeout_overrides_session_timeout(self):
        """Per-request timeout takes precedence over session timeout."""
        session = BaseSession(timeout=5.0)
        
        # Create mock adapter and mount it
        mock_adapter = MagicMock(spec=BaseAdapter)
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.headers['Content-Type'] = 'application/json'
        mock_response._content = b'{"key": "value"}'
        mock_adapter.send.return_value = mock_response
        session.mount('http://', mock_adapter)
        
        # Make request with per-request timeout
        response = session.request('GET', 'http://example.com', timeout=10.0)
        
        # Verify per-request timeout was used
        mock_adapter.send.assert_called_once()
        args, kwargs = mock_adapter.send.call_args
        assert kwargs['timeout'] == 10.0
        assert response.status_code == 200

    def test_no_session_timeout_no_per_request_timeout(self):
        """No timeout applied when neither session nor per-request timeout provided."""
        session = BaseSession()
        
        # Create mock adapter and mount it
        mock_adapter = MagicMock(spec=BaseAdapter)
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.headers['Content-Type'] = 'application/json'
        mock_response._content = b'{"key": "value"}'
        mock_adapter.send.return_value = mock_response
        session.mount('http://', mock_adapter)
        
        # Make request without any timeout
        response = session.request('GET', 'http://example.com')
        
        # Verify no timeout was passed (should be None by default)
        mock_adapter.send.assert_called_once()
        args, kwargs = mock_adapter.send.call_args
        assert kwargs['timeout'] is None
        assert response.status_code == 200

    def test_timeout_tuple_support(self):
        """Session timeout supports tuple format (connect, read)."""
        session = BaseSession(timeout=(3.0, 10.0))
        assert session.timeout == (3.0, 10.0)
        
        # Create mock adapter and mount it
        mock_adapter = MagicMock(spec=BaseAdapter)
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.headers['Content-Type'] = 'application/json'
        mock_response._content = b'{"key": "value"}'
        mock_adapter.send.return_value = mock_response
        session.mount('http://', mock_adapter)
        
        # Make request
        response = session.request('GET', 'http://example.com')
        
        # Verify tuple timeout was passed to send method
        mock_adapter.send.assert_called_once()
        args, kwargs = mock_adapter.send.call_args
        assert kwargs['timeout'] == (3.0, 10.0)
        assert response.status_code == 200