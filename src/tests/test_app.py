import sys
import types
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Mock problematic imports before importing app
sys.modules["api.api_routes"] = MagicMock()
sys.modules["api.history_routes"] = MagicMock()

from app import app, create_app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_create_app_returns_fastapi_instance():
    app_instance = create_app()
    assert hasattr(app_instance, "openapi")
    assert isinstance(app_instance, type(app))

@patch("app.CORSMiddleware")
@patch("app.FastAPI")
def test_create_app_configuration(mock_fastapi, mock_cors):
    mock_app = MagicMock()
    mock_fastapi.return_value = mock_app

    from app import create_app
    result = create_app()

    mock_fastapi.assert_called_once_with(
        title="Conversation Knowledge Mining Solution Accelerator",
        version="1.0.0"
    )
    mock_app.add_middleware.assert_called_once()
    assert mock_app.include_router.call_count == 2
    assert result == mock_app
