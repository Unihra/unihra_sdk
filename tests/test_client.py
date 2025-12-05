import pytest
from unittest.mock import MagicMock, patch
from unihra import UnihraClient
from unihra.exceptions import (
    UnihraValidationError, 
    UnihraApiError, 
    ParserError, 
    UnihraConnectionError
)

@pytest.fixture
def client():
    """Fixture to create a client instance before each test."""
    return UnihraClient(api_key="test_key_123")

def test_init_headers(client):
    """Ensure that Authorization and User-Agent headers are set correctly."""
    headers = client.session.headers
    assert headers["Authorization"] == "Bearer test_key_123"
    assert "UnihraPythonSDK" in headers["User-Agent"]
    assert headers["Content-Type"] == "application/json"

def test_validation_empty_competitors(client):
    """Client should raise validation error if competitor list is empty."""
    with pytest.raises(UnihraValidationError) as exc:
        client.analyze("http://site.com", [])
    assert "cannot be empty" in str(exc.value)

def test_validation_invalid_lang(client):
    """Client should validate the language parameter."""
    with pytest.raises(UnihraValidationError) as exc:
        client.analyze("http://site.com", ["http://comp.com"], lang="fr")
    assert "Language must be" in str(exc.value)

@patch("unihra.client.requests.Session.post")
@patch("unihra.client.requests.Session.get")
def test_analyze_success_flow(mock_get, mock_post, client):
    """
    Test the full successful analysis flow:
    1. POST request creates a task.
    2. GET request streams SSE events.
    3. Client waits for SUCCESS state and returns the result.
    """
    # 1. Mock POST response (Task creation)
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"task_id": "uuid-123"}

    # 2. Mock GET response (SSE Stream)
    # We simulate the bytes stream yielded by requests.iter_lines()
    mock_stream_response = MagicMock()
    mock_stream_response.status_code = 200
    mock_stream_response.iter_lines.return_value = [
        b'', # Keep-alive ping
        b'data: {"state": "PENDING", "progress": 0}',
        b'data: {"state": "PROCESSING", "progress": 50}',
        b'data: {"state": "SUCCESS", "result": {"data": "ok"}}'
    ]
    
    # Mock the context manager behavior: with session.get(...)
    mock_get.return_value.__enter__.return_value = mock_stream_response

    # 3. Execute
    result = client.analyze("http://mysite.com", ["http://comp.com"])

    # 4. Assertions
    assert result == {"data": "ok"}
    mock_post.assert_called_once()
    assert "process/status/uuid-123" in mock_get.call_args[0][0]

@patch("unihra.client.requests.Session.post")
@patch("unihra.client.requests.Session.get")
def test_analyze_specific_error(mock_get, mock_post, client):
    """
    Test error mapping:
    If API returns FAILURE with code 1001, SDK should raise ParserError.
    """
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"task_id": "uuid-err"}

    mock_stream_response = MagicMock()
    mock_stream_response.iter_lines.return_value = [
        b'data: {"state": "FAILURE", "error_code": 1001, "message": "Failed to parse"}'
    ]
    mock_get.return_value.__enter__.return_value = mock_stream_response

    with pytest.raises(ParserError) as exc:
        client.analyze("http://bad-site.com", ["http://comp.com"])
    
    assert "Failed to parse" in str(exc.value)

@patch("unihra.client.requests.Session.post")
def test_auth_error(mock_post, client):
    """Test handling of 401 Unauthorized response."""
    mock_post.return_value.status_code = 401
    mock_post.return_value.text = "Unauthorized"

    with pytest.raises(UnihraApiError) as exc:
        client.analyze("http://site.com", ["http://comp.com"])
    
    assert exc.value.code == 401

def test_health_check(client):
    """Test the health check method."""
    with patch("unihra.client.requests.Session.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "healthy"}
        
        status = client.health()
        assert status["status"] == "healthy"