import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from agents.search_agent_factory import SearchAgentFactory


@pytest.fixture(autouse=True)
def reset_search_agent_factory():
    SearchAgentFactory._agent = None
    yield
    SearchAgentFactory._agent = None


@pytest.mark.asyncio
@patch("agents.search_agent_factory.Config", autospec=True)
@patch("agents.search_agent_factory.DefaultAzureCredential", autospec=True)
@patch("agents.search_agent_factory.AIProjectClient", autospec=True)
@patch("agents.search_agent_factory.AzureAISearchTool", autospec=True)
async def test_get_agent_creates_new_instance(
    mock_search_tool,
    mock_project_client_class,
    mock_credential,
    mock_config_class
):
    # Mock config
    mock_config = MagicMock()
    mock_config.ai_project_endpoint = "https://fake-endpoint"
    mock_config.azure_ai_search_connection_name = "fake-connection"
    mock_config.azure_ai_search_index = "fake-index"
    mock_config.azure_openai_deployment_model = "fake-model"
    mock_config.solution_name = "fake-solution"
    mock_config_class.return_value = mock_config

    # Mock project client
    mock_project_client = MagicMock()
    mock_project_client_class.return_value = mock_project_client

    mock_index = MagicMock()
    mock_index.name = "index-name"
    mock_index.version = "1"
    mock_project_client.indexes.create_or_update.return_value = mock_index

    # Mock search tool
    mock_tool = MagicMock()
    mock_tool.definitions = ["tool-def"]
    mock_tool.resources = ["tool-res"]
    mock_search_tool.return_value = mock_tool

    # Mock agent
    mock_agent = MagicMock()
    mock_project_client.agents.create_agent.return_value = mock_agent

    # Run the factory
    result = await SearchAgentFactory.get_agent()

    assert result["agent"] == mock_agent
    assert result["client"] == mock_project_client
    mock_project_client.indexes.create_or_update.assert_called_once_with(
        name="project-index-fake-index-fake-solution",
        version="1",
        body={
            "connectionName": "fake-connection",
            "indexName": "fake-index",
            "type": "AzureSearch",
            "fieldMapping": {
                "contentFields": ["content"],
                "urlField": "sourceurl",
                "titleField": "chunk_id",
            }
        }
    )
    mock_project_client.agents.create_agent.assert_called_once()


@pytest.mark.asyncio
async def test_get_agent_returns_existing_instance():
    SearchAgentFactory._agent = {"agent": MagicMock(), "client": MagicMock()}
    result = await SearchAgentFactory.get_agent()
    assert result == SearchAgentFactory._agent


@pytest.mark.asyncio
async def test_delete_agent_removes_agent():
    mock_agent = MagicMock()
    mock_agent.id = "mock-agent-id"

    mock_client = MagicMock()
    mock_client.agents.delete_agent = MagicMock()

    SearchAgentFactory._agent = {
        "agent": mock_agent,
        "client": mock_client
    }

    await SearchAgentFactory.delete_agent()

    mock_client.agents.delete_agent.assert_called_once_with("mock-agent-id")
    assert SearchAgentFactory._agent is None


@pytest.mark.asyncio
def test_delete_agent_does_nothing_if_none():
    SearchAgentFactory._agent = None
    SearchAgentFactory.delete_agent()
