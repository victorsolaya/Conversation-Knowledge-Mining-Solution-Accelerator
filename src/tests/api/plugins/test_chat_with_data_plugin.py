import pytest
from unittest.mock import patch, MagicMock, AsyncMock, Mock
from plugins.chat_with_data_plugin import ChatWithDataPlugin
from azure.ai.agents.models import (RunStepToolCallDetails, MessageRole)


@pytest.fixture
def mock_config():
    config_mock = MagicMock()
    config_mock.azure_openai_deployment_model = "gpt-4"
    config_mock.azure_openai_endpoint = "https://test-openai.azure.com/"
    config_mock.azure_openai_api_version = "2024-02-15-preview"
    config_mock.azure_ai_search_endpoint = "https://search.test.azure.com/"
    config_mock.azure_ai_search_api_key = "search-api-key"
    config_mock.azure_ai_search_index = "test_index"
    config_mock.use_ai_project_client = False
    config_mock.azure_ai_project_conn_string = "test-connection-string"
    return config_mock


@pytest.fixture
def chat_plugin(mock_config):
    with patch("plugins.chat_with_data_plugin.Config", return_value=mock_config):
        plugin = ChatWithDataPlugin()
        return plugin


class TestChatWithDataPlugin:
    @patch("helpers.azure_openai_helper.Config")
    @patch("helpers.azure_openai_helper.get_bearer_token_provider")
    @patch("helpers.azure_openai_helper.openai.AzureOpenAI")
    @pytest.mark.asyncio
    async def test_greeting(self, mock_azure_openai, mock_token_provider, mock_config, chat_plugin):
        # Setup mock token provider
        mock_token_provider.return_value = lambda: "fake_token"
        
        # Setup mock client and completion response
        mock_config_instance = MagicMock()
        mock_config_instance.azure_openai_endpoint = "https://test-openai.azure.com/"
        mock_config_instance.azure_openai_api_version = "2024-02-15-preview"
        mock_config.return_value = mock_config_instance
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Hello, how can I help you?"
        mock_client.chat.completions.create.return_value = mock_completion
        mock_azure_openai.return_value = mock_client

        # Call the method
        result = await chat_plugin.greeting("Hello")

        # Assertions
        assert result == "Hello, how can I help you?"
        mock_azure_openai.assert_called_once_with(
            azure_endpoint="https://test-openai.azure.com/",
            azure_ad_token_provider=mock_token_provider.return_value,
            api_version="2024-02-15-preview"
        )
        mock_client.chat.completions.create.assert_called_once()
        args = mock_client.chat.completions.create.call_args[1]
        assert args["model"] == "gpt-4"
        assert args["temperature"] == 0
        assert len(args["messages"]) == 2
        assert args["messages"][0]["role"] == "system"
        assert args["messages"][1]["role"] == "user"
        assert args["messages"][1]["content"] == "Hello"

    @pytest.mark.asyncio
    @patch("plugins.chat_with_data_plugin.Config")
    @patch("plugins.chat_with_data_plugin.AIProjectClient")
    @patch("plugins.chat_with_data_plugin.DefaultAzureCredential")
    async def test_greeting_with_ai_project_client(self, mock_azure_credential, mock_ai_project_client, mock_config, chat_plugin):
        # Setup AIProjectClient
        chat_plugin.use_ai_project_client = True
        
        # Setup mock
        mock_config_instance = MagicMock()
        mock_config_instance.ai_project_endpoint = "https://test-openai.azure.com/"
        mock_config.return_value = mock_config_instance
        mock_credential_instance = MagicMock()
        mock_azure_credential.return_value = mock_credential_instance
        mock_project_instance = MagicMock()
        mock_ai_project_client.return_value = mock_project_instance
        mock_chat_client = MagicMock()
        mock_project_instance.inference.get_chat_completions_client.return_value = mock_chat_client
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Hello from AI Project Client"
        mock_chat_client.complete.return_value = mock_completion
        
        # Call the method
        result = await chat_plugin.greeting("Hello")
        
        # Assertions
        assert result == "Hello from AI Project Client"
        mock_ai_project_client.assert_called_once_with(
            endpoint=chat_plugin.ai_project_endpoint,
            credential=mock_credential_instance
        )
        mock_chat_client.complete.assert_called_once()
        args = mock_chat_client.complete.call_args[1]
        assert args["model"] == "gpt-4"
        assert args["temperature"] == 0
        assert len(args["messages"]) == 2
        assert args["messages"][0]["role"] == "system"
        assert args["messages"][1]["role"] == "user"
        assert args["messages"][1]["content"] == "Hello"

    @pytest.mark.asyncio
    @patch("helpers.azure_openai_helper.openai.AzureOpenAI")
    async def test_greeting_exception(self, mock_azure_openai, chat_plugin):
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_azure_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Test error")
        
        # Call the method
        result = await chat_plugin.greeting("Hello")
        
        # Assertions
        assert result == "Details could not be retrieved. Please try again later."

    @pytest.mark.asyncio
    @patch("helpers.azure_openai_helper.Config")
    @patch("helpers.azure_openai_helper.get_bearer_token_provider")
    @patch("plugins.chat_with_data_plugin.execute_sql_query")
    @patch("helpers.azure_openai_helper.openai.AzureOpenAI")
    async def test_get_sql_response(self, mock_azure_openai, mock_execute_sql, mock_token_provider, mock_config, chat_plugin):

        # Setup mocks
        mock_config_instance = MagicMock()
        mock_config_instance.azure_openai_endpoint = "https://test-openai.azure.com/"
        mock_config_instance.azure_openai_api_version = "2024-02-15-preview"
        mock_config.return_value = mock_config_instance
        mock_token_provider.return_value = lambda: "fake_token"
        mock_client = MagicMock()
        mock_azure_openai.return_value = mock_client
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "SELECT * FROM km_processed_data"
        mock_client.chat.completions.create.return_value = mock_completion
        
        mock_execute_sql.return_value = "Query results data"
        
        # Call the method
        result = await chat_plugin.get_sql_response("Show me all call data")
        
        # Assertions
        assert result == "Query results data"
        mock_azure_openai.assert_called_once_with(
            azure_endpoint="https://test-openai.azure.com/",
            azure_ad_token_provider=mock_token_provider.return_value,
            api_version="2024-02-15-preview"
        )
        mock_client.chat.completions.create.assert_called_once()
        mock_execute_sql.assert_called_once_with("SELECT * FROM km_processed_data")

    @pytest.mark.asyncio
    @patch("plugins.chat_with_data_plugin.Config")
    @patch("plugins.chat_with_data_plugin.execute_sql_query")
    @patch("plugins.chat_with_data_plugin.AIProjectClient")
    @patch("plugins.chat_with_data_plugin.DefaultAzureCredential")
    async def test_get_sql_response_with_ai_project_client(self, mock_azure_credential, mock_ai_project_client, mock_execute_sql, mock_config, chat_plugin):
        # Setup AIProjectClient
        chat_plugin.use_ai_project_client = True
        
        # Setup mocks
        mock_config_instance = MagicMock()
        mock_config_instance.ai_project_endpoint = "https://test-openai.azure.com/"
        mock_config.return_value = mock_config_instance
        mock_credential_instance = MagicMock()
        mock_azure_credential.return_value = mock_credential_instance
        mock_project_instance = MagicMock()
        mock_ai_project_client.return_value = mock_project_instance
        mock_client = MagicMock()
        mock_project_instance.inference.get_chat_completions_client.return_value = mock_client
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "```sql\nSELECT * FROM km_processed_data\n```"
        mock_client.complete.return_value = mock_completion
        
        mock_execute_sql.return_value = "Query results data with AI Project Client"
        
        # Call the method
        result = await chat_plugin.get_sql_response("Show me call data")
        
        # Assertions
        assert result == "Query results data with AI Project Client"
        mock_ai_project_client.assert_called_once_with(
            endpoint=chat_plugin.ai_project_endpoint,
            credential=mock_credential_instance
        )
        mock_execute_sql.assert_called_once_with("\nSELECT * FROM km_processed_data\n")

    @pytest.mark.asyncio
    @patch("plugins.chat_with_data_plugin.execute_sql_query")
    @patch("helpers.azure_openai_helper.openai.AzureOpenAI")
    async def test_get_sql_response_exception(self, mock_azure_openai, mock_execute_sql, chat_plugin):
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_azure_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Test error")
        
        # Call the method
        result = await chat_plugin.get_sql_response("Show me data")
        
        # Assertions
        assert result == "Details could not be retrieved. Please try again later."
        mock_execute_sql.assert_not_called()


    @pytest.mark.asyncio
    @patch("plugins.chat_with_data_plugin.SearchAgentFactory.get_agent", new_callable=AsyncMock)
    async def test_get_answers_from_calltranscripts_success(self, mock_get_agent, chat_plugin):
        # Use the fixture passed by pytest
        self.chat_plugin = chat_plugin  # or just use `chat_plugin` directly

        # Mock agent and client setup
        mock_agent = MagicMock()
        mock_agent.id = "mock-agent-id"
        mock_client = MagicMock()
        mock_get_agent.return_value = {"agent": mock_agent, "client": mock_client}

        # Mock thread creation
        mock_thread = MagicMock()
        mock_thread.id = "thread-id"
        mock_client.agents.threads.create.return_value = mock_thread

        # Mock run creation
        mock_run = MagicMock()
        mock_run.status = "succeeded"
        mock_run.id = "run-id"
        mock_client.agents.runs.create_and_process.return_value = mock_run

        # Mock run steps
        mock_run_step = MagicMock()
        mock_run_step.step_details = RunStepToolCallDetails(tool_calls=[
            {
                "azure_ai_search": {
                    "output": str({
                        "metadata": {
                            "get_urls": ["https://example.com/doc1"],
                            "titles": ["Document Title 1"]
                        }
                    })
                }
            }
        ])
        mock_client.agents.run_steps.list.return_value = [mock_run_step]

        # Mock agent message with answer
        mock_agent_msg = MagicMock()
        mock_agent_msg.role = MessageRole.AGENT
        mock_agent_msg.text_messages = [MagicMock(text=MagicMock(value="This is a test answer with citation 【3:0†source】"))]
        mock_client.agents.messages.list.return_value = [mock_agent_msg]

        # Mock thread deletion
        mock_client.agents.threads.delete.return_value = None

        # Call the method
        result = await chat_plugin.get_answers_from_calltranscripts("What is the summary?")

        # Assert
        assert isinstance(result, dict)
        assert result["answer"] == "This is a test answer with citation [1]"
        assert result["citations"] == [{"url": "https://example.com/doc1", "title": "Document Title 1"}]

    @pytest.mark.asyncio
    @patch("helpers.azure_openai_helper.openai.AzureOpenAI")
    async def test_get_answers_from_calltranscripts_exception(self, mock_azure_openai, chat_plugin):
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_azure_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Test error")
        
        # Call the method
        result = await chat_plugin.get_answers_from_calltranscripts("Question")
        
        # Assertions
        assert result == "Details could not be retrieved. Please try again later."
