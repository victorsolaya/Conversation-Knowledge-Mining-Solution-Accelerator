import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from agents.agent_factory import AgentFactory


@pytest.fixture(autouse=True)
def reset_agent_factory():
    AgentFactory._instance = None
    yield
    AgentFactory._instance = None


@pytest.fixture
def config_mock():
    return MagicMock(
        azure_ai_project_conn_string="fake_conn_str",
        azure_openai_deployment_model="gpt-4"
    )


@pytest.mark.asyncio
@patch("agents.agent_factory.ChatWithDataPlugin", autospec=True)
@patch("agents.agent_factory.AzureAIAgent", autospec=True)
@patch("agents.agent_factory.DefaultAzureCredential", autospec=True)
async def test_get_instance_creates_new_agent(
    mock_credential,
    mock_azure_agent,
    mock_plugin,
    config_mock
):
    mock_client = AsyncMock()
    mock_agent_definition = MagicMock()
    mock_client.agents.create_agent.return_value = mock_agent_definition
    mock_azure_agent.create_client.return_value = mock_client

    agent_instance = MagicMock()
    mock_azure_agent.return_value = agent_instance

    result = await AgentFactory.get_instance(config_mock)

    assert result == agent_instance
    mock_azure_agent.create_client.assert_called_once_with(
        credential=mock_credential.return_value,
        conn_str="fake_conn_str"
    )
    mock_client.agents.create_agent.assert_awaited_once()
    mock_azure_agent.assert_called_once()


@pytest.mark.asyncio
async def test_get_instance_returns_existing_instance(config_mock):
    AgentFactory._instance = MagicMock()
    result = await AgentFactory.get_instance(config_mock)
    assert result == AgentFactory._instance


@pytest.mark.asyncio
@patch("agents.agent_factory.AzureAIAgentThread", autospec=True)
@patch("agents.agent_factory.AzureAIAgent", autospec=True)
@patch("agents.agent_factory.ChatService", autospec=True)
async def test_delete_instance_deletes_agent_and_threads(
    mock_chat_service,
    mock_azure_agent,
    mock_agent_thread
):
    # Setup instance
    mock_client = AsyncMock()
    mock_agent = MagicMock()
    mock_agent.id = "test-id"
    mock_agent.client = mock_client
    AgentFactory._instance = mock_agent

    # Setup thread cache
    mock_chat_service.thread_cache = {
        "conv1": "thread1",
        "conv2": "thread2"
    }

    mock_thread_instance = AsyncMock()
    mock_agent_thread.side_effect = lambda client, thread_id: mock_thread_instance

    await AgentFactory.delete_instance()

    mock_agent_thread.assert_any_call(client=mock_client, thread_id="thread1")
    mock_agent_thread.assert_any_call(client=mock_client, thread_id="thread2")
    assert mock_thread_instance.delete.await_count == 2
    mock_client.agents.delete_agent.assert_awaited_once_with("test-id")
    assert AgentFactory._instance is None


@pytest.mark.asyncio
@patch("agents.agent_factory.AzureAIAgent", autospec=True)
@patch("agents.agent_factory.ChatService", autospec=True)
async def test_delete_instance_handles_missing_thread_cache(
    mock_chat_service,
    mock_azure_agent
):
    mock_client = AsyncMock()
    mock_agent = MagicMock()
    mock_agent.id = "some-id"
    mock_agent.client = mock_client
    AgentFactory._instance = mock_agent

    del mock_chat_service.thread_cache  # simulate attribute not existing

    await AgentFactory.delete_instance()

    mock_client.agents.delete_agent.assert_awaited_once_with("some-id")
    assert AgentFactory._instance is None


@pytest.mark.asyncio
@patch("agents.agent_factory.AzureAIAgent", autospec=True)
async def test_delete_instance_does_nothing_if_none(mock_azure_agent):
    AgentFactory._instance = None
    await AgentFactory.delete_instance()
    # No assertion needed — test passes if nothing throws
