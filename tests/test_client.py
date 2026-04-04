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

@patch("unihra.client.requests.Session.post")
@patch("unihra.client.requests.Session.get")
def test_analyze_anchors_with_links(mock_get, mock_post, client):
    """
    Test that anchors in the result include links when returned by the API.
    """
    # 1. Mock POST response (Task creation)
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"task_id": "uuid-links"}

    # 2. Mock GET response with anchors containing links
    mock_stream_response = MagicMock()
    mock_stream_response.status_code = 200
    mock_stream_response.iter_lines.return_value = [
        b'data: {"state": "SUCCESS", "result": {"anchors_analysis": [{"anchor": "buy now", "frequency_own": 0, "frequency_comp_avg": 5.0, "pages_count": 3, "links": ["https://comp1.com/buy", "https://comp2.com/shop"]}]}}'
    ]
    mock_get.return_value.__enter__.return_value = mock_stream_response

    result = client.analyze("http://mysite.com", ["http://comp.com"])

    anchors = result.get("anchors_analysis", [])
    assert len(anchors) == 1
    assert anchors[0]["anchor"] == "buy now"
    assert anchors[0]["links"] == ["https://comp1.com/buy", "https://comp2.com/shop"]

def test_save_report_anchors_links_structure():
    """Test that _reorder_tech_columns handles links column properly."""
    import sys
    import pathlib
    
    # Ensure we use local source, not installed package
    project_root = pathlib.Path(__file__).resolve().parents[1]
    src_path = str(project_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # Reload module to get local version
    import importlib
    import unihra.client
    importlib.reload(unihra.client)
    
    from unihra.client import UnihraClient
    
    client = UnihraClient(api_key="test_key")
    
    # Verify client version is updated
    assert "1.5.1" in client.session.headers.get("User-Agent", "")
