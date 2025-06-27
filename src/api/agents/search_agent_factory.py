import asyncio
from typing import Optional

from azure.ai.agents.models import AzureAISearchQueryType, AzureAISearchTool
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from common.config.config import Config


class SearchAgentFactory:
    _lock = asyncio.Lock()
    _agent: Optional[dict] = None

    @classmethod
    async def get_agent(cls) -> dict:
        async with cls._lock:
            if cls._agent is None:
                config = Config()
                endpoint = config.ai_project_endpoint
                azure_ai_search_connection_name = config.azure_ai_search_connection_name
                azure_ai_search_index_name = config.azure_ai_search_index
                deployment_model = config.azure_openai_deployment_model

                field_mapping = {
                    "contentFields": ["content"],
                    "urlField": "sourceurl",
                    "titleField": "chunk_id",
                }

                project_client = AIProjectClient(
                    endpoint=endpoint,
                    credential=DefaultAzureCredential(exclude_interactive_browser_credential=False),
                    api_version="2025-05-01",
                )

                project_index = project_client.indexes.create_or_update(
                    name=f"project-index-{azure_ai_search_index_name}",
                    version="1",
                    body={
                        "connectionName": azure_ai_search_connection_name,
                        "indexName": azure_ai_search_index_name,
                        "type": "AzureSearch",
                        "fieldMapping": field_mapping
                    }
                )

                ai_search = AzureAISearchTool(
                    index_asset_id=f"{project_index.name}/versions/{project_index.version}",
                    index_connection_id=None,
                    index_name=None,
                    query_type=AzureAISearchQueryType.VECTOR_SEMANTIC_HYBRID,
                    top_k=5,
                    filter=""
                )

                agent = project_client.agents.create_agent(
                    model=deployment_model,
                    name="ChatWithCallTranscriptsAgent",
                    instructions="You are a helpful agent. Use the tools provided and always cite your sources.",
                    tools=ai_search.definitions,
                    tool_resources=ai_search.resources,
                )

                cls._agent = {
                    "agent": agent,
                    "client": project_client
                }
        return cls._agent

    @classmethod
    async def delete_agent(cls):
        if cls._agent is not None:
            cls._agent["client"].agents.delete_agent(cls._agent["agent"].id)
            cls._agent = None
