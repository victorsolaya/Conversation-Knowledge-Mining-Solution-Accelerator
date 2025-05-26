import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import without global mocking
from api import history_routes 

app = FastAPI()
app.include_router(history_routes.router, prefix="/history")
client = TestClient(app)

# Fixtures
@pytest.fixture
def mock_user():
    return {"user_principal_id": "test_user"}

@pytest.fixture
def mock_history_service():
    """Create a fresh mock for each test"""
    with patch("api.history_routes.history_service") as mock_service:
        # Setup default mocks for commonly used methods
        mock_service.add_conversation = AsyncMock(return_value={"result": "ok"})
        mock_service.update_conversation = AsyncMock(return_value={"id": "123", "title": "Title", "updatedAt": "now"})
        mock_service.update_message_feedback = AsyncMock(return_value=True)
        mock_service.delete_conversation = AsyncMock(return_value=True)
        mock_service.get_conversation_messages = AsyncMock(return_value=[{"text": "hi"}])
        mock_service.rename_conversation = AsyncMock(return_value={"message": "renamed"})
        mock_service.get_conversations = AsyncMock(return_value=[{"id": "1"}])
        mock_service.clear_messages = AsyncMock(return_value=True)
        mock_service.ensure_cosmos = AsyncMock(return_value=(True, None))
        yield mock_service

GET_USER = "api.history_routes.get_authenticated_user_details"

@patch(GET_USER)
def test_add_conversation(mock_auth, mock_user, mock_history_service):
    mock_auth.return_value = mock_user
    
    response = client.post("/history/generate", json={"sample": "data"})
    assert response.status_code == 200
    assert response.json() == {"result": "ok"}
    mock_history_service.add_conversation.assert_called_once()


@patch(GET_USER)
def test_update_conversation(mock_auth, mock_user, mock_history_service):
    mock_auth.return_value = mock_user
    
    response = client.post("/history/update", json={
        "conversation_id": "123",
        "messages": [
            {"role": "user", "content": "Hi"},
            {"id": "abc", "role": "assistant", "content": "Hello"}
        ]
    })
    assert response.status_code == 200
    mock_history_service.update_conversation.assert_called_once()

@patch(GET_USER)
def test_update_conversation_missing_id(mock_auth, mock_user, mock_history_service):
    mock_auth.return_value = mock_user
    response = client.post("/history/update", json={})
    assert response.status_code == 500
    assert response.json() == {"error": "An internal error has occurred!"}


@patch(GET_USER)
def test_update_message_feedback_success(mock_auth, mock_user, mock_history_service):
    mock_auth.return_value = mock_user
    
    response = client.post("/history/message_feedback", json={
        "message_id": "mid", "message_feedback": "positive"
    })
    assert response.status_code == 200
    mock_history_service.update_message_feedback.assert_called_once()


@patch(GET_USER)
def test_update_message_feedback_missing_id(mock_auth, mock_user, mock_history_service):
    mock_auth.return_value = mock_user
    response = client.post("/history/message_feedback", json={"message_feedback": "positive"})
    assert response.status_code == 500
    assert response.json() == {"error": "An internal error has occurred!"}


@patch(GET_USER)
def test_update_message_feedback_missing_feedback(mock_auth, mock_user, mock_history_service):
    mock_auth.return_value = mock_user
    response = client.post("/history/message_feedback", json={"message_id": "mid"})
    assert response.status_code == 500
    assert response.json() == {"error": "An internal error has occurred!"}


@patch(GET_USER)
def test_delete_conversation_success(mock_auth, mock_user, mock_history_service):
    mock_auth.return_value = mock_user
    
    response = client.request("DELETE", "/history/delete", json={"conversation_id": "123"})
    assert response.status_code == 200
    mock_history_service.delete_conversation.assert_called_once()


@patch(GET_USER)
def test_list_conversations_success(mock_auth, mock_user, mock_history_service):
    mock_auth.return_value = mock_user
    
    response = client.get("/history/list")
    assert response.status_code == 200
    mock_history_service.get_conversations.assert_called_once()


@patch(GET_USER)
def test_get_conversation_messages(mock_auth, mock_user, mock_history_service):
    mock_auth.return_value = mock_user
    
    response = client.post("/history/read", json={"conversation_id": "123"})
    assert response.status_code == 200
    mock_history_service.get_conversation_messages.assert_called_once()


@patch(GET_USER)
def test_get_conversation_messages_missing_id(mock_auth, mock_user, mock_history_service):
    mock_auth.return_value = mock_user
    response = client.post("/history/read", json={})
    assert response.status_code == 500
    assert response.json() == {"error": "An internal error has occurred!"}


@patch(GET_USER)
def test_rename_conversation(mock_auth, mock_user, mock_history_service):
    mock_auth.return_value = mock_user
    
    response = client.post("/history/rename", json={
        "conversation_id": "123", "title": "new"
    })
    assert response.status_code == 200
    mock_history_service.rename_conversation.assert_called_once()


@patch(GET_USER)
def test_rename_conversation_missing_fields(mock_auth, mock_user, mock_history_service):
    mock_auth.return_value = mock_user

    r1 = client.post("/history/rename", json={"title": "missing id"})
    r2 = client.post("/history/rename", json={"conversation_id": "123"})

    assert r1.status_code == 500
    assert r1.json() == {"error": "An internal error has occurred!"}

    assert r2.status_code == 500
    assert r2.json() == {"error": "An internal error has occurred!"}


@patch(GET_USER)
def test_delete_all_conversations(mock_auth, mock_user, mock_history_service):
    mock_auth.return_value = mock_user
    
    response = client.delete("/history/delete_all")
    assert response.status_code == 200
    # Should call get_conversations to get list, then delete_conversation for each
    mock_history_service.get_conversations.assert_called_once()


@patch(GET_USER)
def test_clear_messages(mock_auth, mock_user, mock_history_service):
    mock_auth.return_value = mock_user
    
    response = client.post("/history/clear", json={"conversation_id": "123"})
    assert response.status_code == 200
    mock_history_service.clear_messages.assert_called_once()


@patch(GET_USER)
def test_clear_messages_missing_id(mock_auth, mock_user, mock_history_service):
    mock_auth.return_value = mock_user
    response = client.post("/history/clear", json={})
    assert response.status_code == 500
    assert response.json() == {"error": "An internal error has occurred!"}


def test_ensure_cosmos_success(mock_history_service):
    response = client.get("/history/history/ensure")
    assert response.status_code == 200
    mock_history_service.ensure_cosmos.assert_called_once()


def test_ensure_cosmos_failure(mock_history_service):
    mock_history_service.ensure_cosmos.return_value = (False, "some error")
    response = client.get("/history/history/ensure")
    assert response.status_code == 422


def test_ensure_cosmos_exception(mock_history_service):
    mock_history_service.ensure_cosmos.side_effect = Exception("Invalid credentials")
    response = client.get("/history/history/ensure")
    assert response.status_code == 401

    # Reset the side effect for the next test
    mock_history_service.ensure_cosmos.side_effect = Exception("Invalid CosmosDB database name")
    response = client.get("/history/history/ensure")
    assert response.status_code == 422

    # Reset the side effect for the next test
    mock_history_service.ensure_cosmos.side_effect = Exception("Unknown")
    response = client.get("/history/history/ensure")
    assert response.status_code == 500