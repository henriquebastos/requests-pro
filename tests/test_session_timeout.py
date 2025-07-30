import pytest
import responses as responses_lib
from unittest.mock import patch, MagicMock

from requestspro.sessions import BaseSession, BaseUrlSession, CustomJsonSession, CustomResponseSession, ProSession


class TestBaseSessionTimeout:
    """Test timeout functionality in BaseSession and its subclasses."""

    def test_init_with_timeout_none(self):
        """Test that BaseSession initializes correctly with no timeout."""
        session = BaseSession()
        assert session.timeout is None

    def test_init_with_timeout_value(self):
        """Test that BaseSession initializes correctly with a timeout value."""
        session = BaseSession(timeout=5.0)
        assert session.timeout == 5.0

    def test_init_with_timeout_tuple(self):
        """Test that BaseSession initializes correctly with a (connect, read) timeout tuple."""
        timeout = (3.0, 10.0)
        session = BaseSession(timeout=timeout)
        assert session.timeout == timeout

    def test_class_attribute_timeout(self):
        """Test that BaseSession can use class-level TIMEOUT attribute."""
        
        class CustomSession(BaseSession):
            TIMEOUT = 15.0
        
        session = CustomSession()
        assert session.timeout == 15.0

    def test_init_timeout_overrides_class_timeout(self):
        """Test that init timeout parameter overrides class TIMEOUT attribute."""
        
        class CustomSession(BaseSession):
            TIMEOUT = 15.0
        
        session = CustomSession(timeout=7.0)
        assert session.timeout == 7.0

    def test_init_timeout_none_overrides_class_timeout(self):
        """Test that explicitly passing timeout=None overrides class TIMEOUT attribute."""
        
        class CustomSession(BaseSession):
            TIMEOUT = 15.0
        
        session = CustomSession(timeout=None)
        assert session.timeout is None

    @responses_lib.activate
    def test_request_uses_session_timeout(self):
        """Test that session timeout is applied when no per-request timeout is provided."""
        responses_lib.add(
            responses_lib.GET,
            "https://example.com/api",
            json={"success": True},
            status=200
        )
        
        session = BaseSession(timeout=5.0)
        
        with patch.object(session, 'request', wraps=session.request) as mock_request:
            # Call the parent request method to see what kwargs are passed
            with patch('requests.Session.request') as mock_parent_request:
                mock_parent_request.return_value = MagicMock()
                session.request('GET', 'https://example.com/api')
                
                # Verify that timeout was added to kwargs
                args, kwargs = mock_parent_request.call_args
                assert kwargs['timeout'] == 5.0

    @responses_lib.activate
    def test_per_request_timeout_overrides_session_timeout(self):
        """Test that per-request timeout takes precedence over session timeout."""
        responses_lib.add(
            responses_lib.GET,
            "https://example.com/api",
            json={"success": True},
            status=200
        )
        
        session = BaseSession(timeout=5.0)
        
        with patch('requests.Session.request') as mock_parent_request:
            mock_parent_request.return_value = MagicMock()
            session.request('GET', 'https://example.com/api', timeout=10.0)
            
            # Verify that per-request timeout was used
            args, kwargs = mock_parent_request.call_args
            assert kwargs['timeout'] == 10.0

    @responses_lib.activate
    def test_no_timeout_when_session_timeout_none(self):
        """Test that no timeout is applied when session timeout is None."""
        responses_lib.add(
            responses_lib.GET,
            "https://example.com/api",
            json={"success": True},
            status=200
        )
        
        session = BaseSession(timeout=None)
        
        with patch('requests.Session.request') as mock_parent_request:
            mock_parent_request.return_value = MagicMock()
            session.request('GET', 'https://example.com/api')
            
            # Verify that no timeout was added
            args, kwargs = mock_parent_request.call_args
            assert 'timeout' not in kwargs

    @responses_lib.activate
    def test_per_request_timeout_none_overrides_session_timeout(self):
        """Test that explicitly passing timeout=None per-request overrides session timeout."""
        responses_lib.add(
            responses_lib.GET,
            "https://example.com/api",
            json={"success": True},
            status=200
        )
        
        session = BaseSession(timeout=5.0)
        
        with patch('requests.Session.request') as mock_parent_request:
            mock_parent_request.return_value = MagicMock()
            session.request('GET', 'https://example.com/api', timeout=None)
            
            # Verify that per-request timeout=None was used
            args, kwargs = mock_parent_request.call_args
            assert kwargs['timeout'] is None


class TestInheritedSessionTimeout:
    """Test that timeout functionality is inherited by all session subclasses."""

    def test_base_url_session_timeout(self):
        """Test that BaseUrlSession inherits timeout functionality."""
        session = BaseUrlSession(base_url="https://api.example.com", timeout=8.0)
        assert session.timeout == 8.0
        assert session.base_url == "https://api.example.com"

    def test_custom_json_session_timeout(self):
        """Test that CustomJsonSession inherits timeout functionality."""
        session = CustomJsonSession(timeout=12.0)
        assert session.timeout == 12.0

    def test_custom_response_session_timeout(self):
        """Test that CustomResponseSession inherits timeout functionality."""
        session = CustomResponseSession(timeout=6.0)
        assert session.timeout == 6.0

    def test_pro_session_timeout(self):
        """Test that ProSession inherits timeout functionality."""
        session = ProSession(
            base_url="https://api.example.com",
            timeout=20.0
        )
        assert session.timeout == 20.0
        assert session.base_url == "https://api.example.com"

    def test_pro_session_class_timeout(self):
        """Test that ProSession can define class-level TIMEOUT."""
        
        class CustomProSession(ProSession):
            TIMEOUT = 30.0
        
        session = CustomProSession(base_url="https://api.example.com")
        assert session.timeout == 30.0

    @responses_lib.activate
    def test_pro_session_request_with_timeout(self):
        """Test that ProSession applies timeout to requests."""
        responses_lib.add(
            responses_lib.GET,
            "https://api.example.com/data",
            json={"data": "test"},
            status=200
        )
        
        session = ProSession(
            base_url="https://api.example.com",
            timeout=15.0
        )
        
        with patch('requests.Session.request') as mock_parent_request:
            mock_parent_request.return_value = MagicMock()
            session.request('GET', '/data')
            
            # Verify that timeout was applied
            args, kwargs = mock_parent_request.call_args
            assert kwargs['timeout'] == 15.0


class TestEdgeCases:
    """Test edge cases and validation."""

    def test_timeout_zero(self):
        """Test that timeout=0 is valid and preserved."""
        session = BaseSession(timeout=0)
        assert session.timeout == 0

    def test_timeout_negative_value(self):
        """Test that negative timeout values are preserved (requests will handle validation)."""
        session = BaseSession(timeout=-1)
        assert session.timeout == -1

    def test_timeout_with_other_kwargs(self):
        """Test that timeout works alongside other initialization kwargs."""
        session = BaseUrlSession(
            base_url="https://example.com",
            timeout=5.0
        )
        assert session.timeout == 5.0
        assert session.base_url == "https://example.com"

    @responses_lib.activate 
    def test_request_preserves_other_kwargs(self):
        """Test that timeout handling doesn't interfere with other request kwargs."""
        responses_lib.add(
            responses_lib.POST,
            "https://example.com/api",
            json={"success": True},
            status=200
        )
        
        session = BaseSession(timeout=5.0)
        
        with patch('requests.Session.request') as mock_parent_request:
            mock_parent_request.return_value = MagicMock()
            session.request(
                'POST',
                'https://example.com/api',
                json={"test": "data"},
                headers={"Authorization": "Bearer token"}
            )
            
            # Verify that all kwargs were preserved plus timeout was added
            args, kwargs = mock_parent_request.call_args
            assert kwargs['timeout'] == 5.0
            assert kwargs['json'] == {"test": "data"}
            assert kwargs['headers'] == {"Authorization": "Bearer token"}