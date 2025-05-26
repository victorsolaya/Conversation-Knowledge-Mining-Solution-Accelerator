import sys
import pytest
import json
import time
import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch, call

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from semantic_kernel.exceptions.agent_exceptions import AgentException

# Import service under test with patching applied before import
with patch("common.config.config.Config", MagicMock()), \
     patch("openai.AzureOpenAI", MagicMock()), \
     patch("openai.AsyncAzureOpenAI", MagicMock()), \
     patch("azure.identity.aio.DefaultAzureCredential", MagicMock()), \
     patch("semantic_kernel.agents.AzureAIAgent", MagicMock()), \
     patch("semantic_kernel.agents.AzureAIAgentThread", MagicMock()), \
     patch("azure.ai.projects.models.TruncationObject", MagicMock()), \
     patch("helpers.utils.format_stream_response", MagicMock()), \
     patch("plugins.chat_with_data_plugin.ChatWithDataPlugin", MagicMock()), \
     patch("cachetools.TTLCache", MagicMock()):
    from services.chat_service import ChatService

@pytest.fixture
def chat_service():
    return ChatService()

@pytest.fixture
def mock_config_instance():
    config = MagicMock()
    config.azure_openai_endpoint = "https://test-openai.azure.com/"
    config.azure_openai_api_key = "test-api-key"
    config.azure_openai_api_version = "2024-02-15-preview"
    config.azure_openai_deployment_model = "gpt-4o-mini"
    config.azure_ai_project_conn_string = "test-connection-string"
    return config

@pytest.fixture
def mock_openai_client():
    client = MagicMock()
    chat_completion = MagicMock()
    client.chat.completions.create.return_value = chat_completion
    return client

class TestChatService:
    def test_init(self, mock_config_instance):
        """Test service initialization with config values"""
        with patch("services.chat_service.Config", return_value=mock_config_instance):
            service = ChatService()
            assert service.azure_openai_endpoint == mock_config_instance.azure_openai_endpoint
            assert service.azure_openai_api_key == mock_config_instance.azure_openai_api_key
            assert service.azure_openai_api_version == mock_config_instance.azure_openai_api_version
            assert service.azure_openai_deployment_name == mock_config_instance.azure_openai_deployment_model
            assert service.azure_ai_project_conn_string == mock_config_instance.azure_ai_project_conn_string

    @patch("services.chat_service.openai.AzureOpenAI")
    def test_process_rag_response_success(self, mock_azure_openai, chat_service, mock_openai_client):
        """Test successful processing of RAG response"""
        # Setup
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = """```json
        {
            "type": "bar",
            "data": {
                "labels": ["Jan", "Feb", "Mar"],
                "datasets": [
                    {
                        "label": "Sales",
                        "data": [100, 200, 300]
                    }
                ]
            }
        }
        ```"""
        mock_azure_openai.return_value = mock_openai_client
        mock_openai_client.chat.completions.create.return_value = mock_completion

        # Test
        result = chat_service.process_rag_response("Test RAG response with numbers 10, 20, 30", "Show me sales data")

        # Assert
        assert "type" in result
        assert result["type"] == "bar"
        assert "data" in result
        assert "labels" in result["data"]
        assert "datasets" in result["data"]
        mock_openai_client.chat.completions.create.assert_called_once()

    @patch("services.chat_service.openai.AzureOpenAI")
    def test_process_rag_response_exception(self, mock_azure_openai, chat_service, mock_openai_client):
        """Test exception handling in process_rag_response"""
        # Setup
        mock_azure_openai.return_value = mock_openai_client
        mock_openai_client.chat.completions.create.side_effect = Exception("Test error")

        # Test
        result = chat_service.process_rag_response("Test RAG response", "Test query")

        # Assert
        assert "error" in result
        assert result["error"] == "Chart could not be generated from this data. Please ask a different question."

    @patch("services.chat_service.DefaultAzureCredential")
    @patch("services.chat_service.AzureAIAgent")
    @pytest.mark.asyncio
    async def test_stream_openai_text_success(self, mock_agent_class, mock_credential, chat_service):
        """Test successful streaming of OpenAI text"""
        # Create a async context manager mock for DefaultAzureCredential
        mock_creds_context = AsyncMock()
        mock_creds = AsyncMock()
        mock_creds_context.__aenter__.return_value = mock_creds
        mock_creds_context.__aexit__.return_value = None
        mock_credential.return_value = mock_creds_context

        # Setup mock agent
        mock_agent = MagicMock()
        mock_client = AsyncMock()
        mock_agent_definition = MagicMock()

        # Configure mocks for AzureAIAgent client context manager
        client_context = AsyncMock()
        client_context.__aenter__.return_value = mock_client
        client_context.__aexit__.return_value = None
        mock_agent_class.create_client.return_value = client_context

        mock_client.agents.create_agent = AsyncMock(return_value=mock_agent_definition)
        mock_agent_class.return_value = mock_agent

        # Setup mock response from invoke_stream
        async def mock_invoke_stream(*args, **kwargs):
            yield MagicMock(content="Test response")

        mock_agent.invoke_stream = mock_invoke_stream

        # Test
        responses = []
        async for response in chat_service.stream_openai_text("conv-123", "Test query"):
            responses.append(response)

        # Assert
        assert len(responses) == 1
        assert responses[0] == "Test response"
        mock_client.agents.create_agent.assert_awaited_once()

    @patch("services.chat_service.DefaultAzureCredential")
    @patch("services.chat_service.AzureAIAgent")
    @pytest.mark.asyncio
    async def test_stream_openai_text_empty_query(self, mock_agent_class, mock_credential, chat_service):
        """Test handling of empty query in stream_openai_text"""
        # Create a async context manager mock for DefaultAzureCredential
        mock_creds_context = AsyncMock()
        mock_creds = AsyncMock()
        mock_creds_context.__aenter__.return_value = mock_creds
        mock_creds_context.__aexit__.return_value = None
        mock_credential.return_value = mock_creds_context

        # Setup mock agent
        mock_agent = MagicMock()
        mock_client = AsyncMock()
        mock_agent_definition = MagicMock()

        # Configure mocks for AzureAIAgent client context manager
        client_context = AsyncMock()
        client_context.__aenter__.return_value = mock_client
        client_context.__aexit__.return_value = None
        mock_agent_class.create_client.return_value = client_context

        mock_client.agents.create_agent = AsyncMock(return_value=mock_agent_definition)
        mock_agent_class.return_value = mock_agent

        # Setup mock response from invoke_stream
        async def mock_invoke_stream(*args, **kwargs):
            # Capture the actual query that would be sent to the service
            captured_query = kwargs.get('messages')
            # Assert the empty query was replaced with the default message
            assert captured_query == "Please provide a query."
            yield MagicMock(content="Response for default query")

        mock_agent.invoke_stream = mock_invoke_stream

        # Test with empty query
        responses = []
        async for response in chat_service.stream_openai_text("conv-123", ""):
            responses.append(response)

        # Assert
        assert len(responses) == 1
        assert responses[0] == "Response for default query"
        mock_client.agents.create_agent.assert_awaited_once()

        # Also test with None as query
        mock_agent.invoke_stream = mock_invoke_stream
        responses = []
        async for response in chat_service.stream_openai_text("conv-123", None):
            responses.append(response)

        # Assert again
        assert len(responses) == 1
        assert responses[0] == "Response for default query"

    @patch("services.chat_service.DefaultAzureCredential")
    @patch("services.chat_service.AzureAIAgent")
    @pytest.mark.asyncio
    async def test_stream_openai_text_fallback(self, mock_agent_class, mock_credential, chat_service):
        """Test fallback response in stream_openai_text"""
        # Create a async context manager mock for DefaultAzureCredential
        mock_creds_context = AsyncMock()
        mock_creds = AsyncMock()
        mock_creds_context.__aenter__.return_value = mock_creds
        mock_creds_context.__aexit__.return_value = None
        mock_credential.return_value = mock_creds_context

        # Setup mock agent
        mock_agent = MagicMock()
        mock_client = AsyncMock()
        mock_agent_definition = MagicMock()

        # Configure mocks for AzureAIAgent client context manager
        client_context = AsyncMock()
        client_context.__aenter__.return_value = mock_client
        client_context.__aexit__.return_value = None
        mock_agent_class.create_client.return_value = client_context

        mock_client.agents.create_agent = AsyncMock(return_value=mock_agent_definition)
        mock_agent_class.return_value = mock_agent

        # Setup mock response from invoke_stream
        async def mock_invoke_stream(*args, **kwargs):
            yield MagicMock(content="")

        mock_agent.invoke_stream = mock_invoke_stream

        # Test
        responses = []
        complete_response = ""
        async for response in chat_service.stream_openai_text("conv-123", "Test query"):
            complete_response += response
            responses.append(response)

        # Assert
        assert complete_response == "I cannot answer this question with the current data. Please rephrase or add more details."
        mock_client.agents.create_agent.assert_awaited_once()

    @patch("services.chat_service.DefaultAzureCredential")
    @patch("services.chat_service.AzureAIAgent")
    @pytest.mark.asyncio
    async def test_stream_openai_text_rate_limit_error(self, mock_agent_class, mock_credential, chat_service):
        """Test rate limit error handling in stream_openai_text"""
        # Create a async context manager mock for DefaultAzureCredential
        mock_creds_context = AsyncMock()
        mock_creds = AsyncMock()
        mock_creds_context.__aenter__.return_value = mock_creds
        mock_creds_context.__aexit__.return_value = None
        mock_credential.return_value = mock_creds_context

        # Setup mock agent
        mock_agent = MagicMock()
        mock_client = AsyncMock()
        mock_agent_definition = MagicMock()
        
        # Configure mocks
        mock_client.agents.create_agent = AsyncMock(return_value=mock_agent_definition)
        mock_agent_class.create_client.return_value.__aenter__.return_value = mock_client
        mock_agent_class.return_value = mock_agent
        
        # Setup mock response with rate limit error
        async def mock_invoke_stream_error(*args, **kwargs):
            raise RuntimeError("Rate limit is exceeded. Try again in 60 seconds")
            yield

        mock_agent.invoke_stream = mock_invoke_stream_error

        # Test
        with pytest.raises(Exception) as exc_info:
            async for response in chat_service.stream_openai_text("conv-123", "Test query"):
                pass
            
        # Assert
        assert "Rate limit is exceeded" in str(exc_info.value)

    @patch("services.chat_service.DefaultAzureCredential")
    @patch("services.chat_service.AzureAIAgent")
    @pytest.mark.asyncio
    async def test_stream_openai_text_other_runtime_error(self, mock_agent_class, mock_credential, chat_service):
        """Test handling of non-rate-limit RuntimeError in stream_openai_text"""
        # Create a async context manager mock for DefaultAzureCredential
        mock_creds_context = AsyncMock()
        mock_creds = AsyncMock()
        mock_creds_context.__aenter__.return_value = mock_creds
        mock_creds_context.__aexit__.return_value = None
        mock_credential.return_value = mock_creds_context

        # Setup mock agent
        mock_agent = MagicMock()
        mock_client = AsyncMock()
        mock_agent_definition = MagicMock()

        # Configure mocks
        client_context = AsyncMock()
        client_context.__aenter__.return_value = mock_client
        client_context.__aexit__.return_value = None
        mock_agent_class.create_client.return_value = client_context

        mock_client.agents.create_agent = AsyncMock(return_value=mock_agent_definition)
        mock_agent_class.return_value = mock_agent

        # Setup mock response with a non-rate-limit RuntimeError
        async def mock_invoke_stream_runtime_error(*args, **kwargs):
            raise RuntimeError("Some other runtime error")
            yield

        mock_agent.invoke_stream = mock_invoke_stream_runtime_error

        # Test - The code should raise an AgentException with our runtime error message
        with pytest.raises(Exception) as exc_info:
            async for response in chat_service.stream_openai_text("conv-123", "Test query"):
                pass
            
        # Assert that the error message contains the expected text from the 'else' branch
        assert "An unexpected runtime error occurred" in str(exc_info.value)
        assert "Some other runtime error" in str(exc_info.value)

    @patch("services.chat_service.DefaultAzureCredential")
    @patch("services.chat_service.AzureAIAgent")
    @pytest.mark.asyncio
    async def test_stream_openai_text_generic_error(self, mock_agent_class, mock_credential, chat_service):
        """Test generic error handling in stream_openai_text"""
        # Create a async context manager mock for DefaultAzureCredential
        mock_creds_context = AsyncMock()
        mock_creds = AsyncMock()
        mock_creds_context.__aenter__.return_value = mock_creds
        mock_creds_context.__aexit__.return_value = None
        mock_credential.return_value = mock_creds_context

        # Setup mock agent
        mock_agent = MagicMock()
        mock_client = AsyncMock()
        mock_agent_definition = MagicMock()
        
        # Configure mocks
        mock_client.agents.create_agent = AsyncMock(return_value=mock_agent_definition)
        mock_agent_class.create_client.return_value.__aenter__.return_value = mock_client
        mock_agent_class.return_value = mock_agent
        
        # Setup mock response with generic error
        mock_agent.invoke_stream.side_effect = Exception("Generic error")

        # Test
        with pytest.raises(HTTPException) as exc_info:
            async for response in chat_service.stream_openai_text("conv-123", "Test query"):
                pass
        
        # Assert
        assert exc_info.value.status_code == 500
        assert "Error streaming OpenAI text" in exc_info.value.detail

    @patch.object(ChatService, "stream_openai_text")
    @patch("services.chat_service.json.dumps")
    @patch("services.chat_service.format_stream_response")
    @pytest.mark.asyncio
    async def test_stream_chat_request_success(self, mock_format_stream_response, mock_json_dumps, mock_stream_openai_text, chat_service):
        """Test successful streaming chat request"""
        # Setup
        mock_format_stream_response.return_value = {"formatted": "response"}
        mock_json_dumps.return_value = '{"formatted": "response"}'
        
        async def mock_stream_inner_gen(*args, **kwargs):
            yield "Response chunk 1"
            yield "Response chunk 2"
        
        mock_stream_openai_text.return_value = mock_stream_inner_gen()
        
        request_body = {
            "history_metadata": {"some": "metadata"}
        }
        conversation_id = "conv-123"
        query = "Test query"
    
        # Test
        async_gen_obj = await chat_service.stream_chat_request(request_body, conversation_id, query)
    
        # Assert it's an async generator (not callable)
        from typing import AsyncGenerator
        assert isinstance(async_gen_obj, AsyncGenerator)
    
        # Consume the async generator object
        result = [chunk async for chunk in async_gen_obj]
        
        # Assert
        assert len(result) == 2
        expected_chunk_output = '{"formatted": "response"}\n\n'
        for res_chunk in result:
            assert res_chunk == expected_chunk_output

        mock_stream_openai_text.assert_called_once_with(conversation_id, query)
        mock_format_stream_response.assert_called()
        mock_json_dumps.assert_called()
        
    @patch.object(ChatService, "stream_openai_text")
    @pytest.mark.asyncio
    async def test_stream_chat_request_agent_exception_rate_limit(self, mock_stream_openai_text, chat_service):
        """Test agent exception handling in stream_chat_request"""        
        # Setup - configure the mock to raise an AgentException with our error message
        mock_stream_openai_text.side_effect = AgentException("Rate limit is exceeded. Try again in 60 seconds")
        
        request_body = {"history_metadata": {}}
        conversation_id = "conv-123"
        query = "Test query"
        
        # Test
        async_gen_obj = await chat_service.stream_chat_request(request_body, conversation_id, query)
        
        # Execute the generator and collect results
        result = [chunk async for chunk in async_gen_obj]

        # Assert
        assert len(result) == 1
        assert "Rate limit is exceeded" in result[0]
        assert "Try again in 60 seconds" in result[0]
        
    @patch.object(ChatService, "stream_openai_text")
    @pytest.mark.asyncio
    async def test_stream_chat_request_agent_exception_generic(self, mock_stream_openai_text, chat_service):
        """Test generic exception handling in stream_chat_request"""
        # Setup
        mock_stream_openai_text.side_effect = AgentException("Generic error")
        
        request_body = {"history_metadata": {}}
        conversation_id = "conv-123"
        query = "Test query"
        
        # Test
        async_gen_obj = await chat_service.stream_chat_request(request_body, conversation_id, query)
        
        # Execute the generator and collect results
        result = [chunk async for chunk in async_gen_obj]

        # Assert
        assert len(result) == 1
        assert "An error occurred. Please try again later." in result[0]

    @patch.object(ChatService, "stream_openai_text")
    @pytest.mark.asyncio
    async def test_stream_chat_request_generic_exception(self, mock_stream_openai_text, chat_service):
        """Test generic exception handling in stream_chat_request"""
        # Setup
        mock_stream_openai_text.side_effect = Exception("Generic error")
        
        request_body = {"history_metadata": {}}
        conversation_id = "conv-123"
        query = "Test query"
        
        # Test
        async_gen_obj = await chat_service.stream_chat_request(request_body, conversation_id, query)
        
        # Execute the generator and collect results
        result = [chunk async for chunk in async_gen_obj]

        # Assert
        assert len(result) == 1
        assert "An error occurred while processing the request." in result[0]

    @patch.object(ChatService, "process_rag_response")
    @pytest.mark.asyncio
    async def test_complete_chat_request_success(self, mock_process_rag_response, chat_service):
        """Test successful complete chat request"""
        # Setup
        chart_data = {
            "type": "bar",
            "data": {
                "labels": ["Jan", "Feb", "Mar"],
                "datasets": [{"label": "Sales", "data": [100, 200, 300]}]
            }
        }
        mock_process_rag_response.return_value = chart_data
        
        # Test
        result = await chat_service.complete_chat_request("Show sales data", "Sales were 100 in Jan, 200 in Feb, and 300 in Mar")
        
        # Assert
        assert "id" in result
        assert "model" in result
        assert "created" in result
        assert result["object"] == chart_data
        mock_process_rag_response.assert_called_once()

    @patch.object(ChatService, "process_rag_response")
    @pytest.mark.asyncio
    async def test_complete_chat_request_no_rag(self, mock_process_rag_response, chat_service):
        """Test complete chat request with no RAG response"""
        # Test
        result = await chat_service.complete_chat_request("Show sales data", None)
        
        # Assert
        assert "error" in result
        assert "previous RAG response is required" in result["error"]
        mock_process_rag_response.assert_not_called()

    @patch.object(ChatService, "process_rag_response")
    @pytest.mark.asyncio
    async def test_complete_chat_request_process_error(self, mock_process_rag_response, chat_service):
        """Test complete chat request with processing error"""
        # Setup
        mock_process_rag_response.return_value = {"error": "Cannot generate chart"}
        
        # Test
        result = await chat_service.complete_chat_request("Show sales data", "Some RAG response")
        
        # Assert
        assert "error" in result
        assert "Chart could not be generated" in result["error"]
        assert "error_desc" in result
        mock_process_rag_response.assert_called_once()