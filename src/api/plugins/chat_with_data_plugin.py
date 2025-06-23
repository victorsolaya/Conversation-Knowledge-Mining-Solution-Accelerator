"""Plugin for handling chat interactions with data sources using Azure OpenAI and Azure AI Search.

This module provides functions for:
- Responding to greetings and general questions.
- Generating SQL queries and fetching results from a database.
- Answering questions using call transcript data from Azure AI Search.
"""

from typing import Annotated, Dict, Any
import ast

import requests
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import (
    AzureAISearchQueryType, 
    AzureAISearchTool, 
    ListSortOrder, 
    MessageRole, 
    RunStepToolCallDetails)
from azure.identity import DefaultAzureCredential

from common.database.sqldb_service import execute_sql_query
from common.config.config import Config
from helpers.azure_openai_helper import get_azure_openai_client


class ChatWithDataPlugin:
    def __init__(self):
        config = Config()
        self.azure_openai_deployment_model = config.azure_openai_deployment_model
        self.ai_project_endpoint = config.ai_project_endpoint
        self.azure_ai_search_endpoint = config.azure_ai_search_endpoint
        self.azure_ai_search_api_key = config.azure_ai_search_api_key
        self.azure_ai_search_connection_name = config.azure_ai_search_connection_name
        self.azure_ai_search_index = config.azure_ai_search_index
        self.use_ai_project_client = config.use_ai_project_client

    @kernel_function(name="Greeting",
                     description="Respond to any greeting or general questions")
    async def greeting(self, input: Annotated[str, "the question"]) -> Annotated[str, "The output is a string"]:
        query = input

        try:
            if self.use_ai_project_client:
                project = AIProjectClient(
                    endpoint=self.ai_project_endpoint,
                    credential=DefaultAzureCredential()
                )
                client = project.inference.get_chat_completions_client()

                completion = client.complete(
                    model=self.azure_openai_deployment_model,
                    messages=[
                        {"role": "system",
                         "content": "You are a helpful assistant to respond to any greeting or general questions."},
                        {"role": "user", "content": query},
                    ],
                    temperature=0,
                )
            else:
                client = get_azure_openai_client()

                completion = client.chat.completions.create(
                    model=self.azure_openai_deployment_model,
                    messages=[
                        {"role": "system",
                         "content": "You are a helpful assistant to respond to any greeting or general questions."},
                        {"role": "user", "content": query},
                    ],
                    temperature=0,
                )
            answer = completion.choices[0].message.content
        except Exception:
            answer = 'Details could not be retrieved. Please try again later.'
        return answer

    @kernel_function(name="ChatWithSQLDatabase",
                     description="Provides quantified results from the database.")
    async def get_SQL_Response(
            self,
            input: Annotated[str, "the question"]
    ):
        query = input

        sql_prompt = f'''Generate a valid T-SQL query to find {query} for tables and columns provided below:
                1. Table: km_processed_data
                Columns: ConversationId,EndTime,StartTime,Content,summary,satisfied,sentiment,topic,keyphrases,complaint
                2. Table: processed_data_key_phrases
                Columns: ConversationId,key_phrase,sentiment
                Use ConversationId as the primary key as the primary key in tables for queries but not for any other operations.
                **Always** return a valid T-SQL query with correct syntax. Only return the generated SQL query. Do not return anything else.'''

        try:
            if self.use_ai_project_client:
                project = AIProjectClient(
                    endpoint=self.ai_project_endpoint,
                    credential=DefaultAzureCredential()
                )
                client = project.inference.get_chat_completions_client()

                completion = client.complete(
                    model=self.azure_openai_deployment_model,
                    messages=[
                        {"role": "system", "content": "You are an assistant that helps generate valid T-SQL queries."},
                        {"role": "user", "content": sql_prompt},
                    ],
                    temperature=0,
                )
                sql_query = completion.choices[0].message.content
                sql_query = sql_query.replace("```sql", '').replace("```", '')
            else:
                client = get_azure_openai_client()

                completion = client.chat.completions.create(
                    model=self.azure_openai_deployment_model,
                    messages=[
                        {"role": "system", "content": "You are an assistant that helps generate valid T-SQL queries."},
                        {"role": "user", "content": sql_prompt},
                    ],
                    temperature=0,
                )
                sql_query = completion.choices[0].message.content
                sql_query = sql_query.replace("```sql", '').replace("```", '')

            answer = await execute_sql_query(sql_query)
            answer = answer[:20000] if len(answer) > 20000 else answer

        except Exception:
            answer = 'Details could not be retrieved. Please try again later.'
        return answer

    @kernel_function(name="ChatWithCallTranscripts",
                     description="Provides summaries or detailed explanations from the search index.")
    async def get_answers_from_calltranscripts(
            self,
            question: Annotated[str, "the question"]
    ):
        try:
            
            field_mapping = {
                "contentFields": ["content"],  # Fields containing the content to be searched
                "urlField": "sourceurl",
                "titleField": "chunk_id",
            }

            # Initialize the AIProjectClient with the endpoint and credentials
            project_client = AIProjectClient(
                endpoint=self.ai_project_endpoint,
                credential=DefaultAzureCredential(exclude_interactive_browser_credential=False),  # Use Azure Default Credential for authentication
                api_version="2025-05-01",
            )

            with project_client:
                # If you have a custom field mapping, create a Project Index to store the mapping
                project_index = None
                if field_mapping:
                    print("Creating project index...")
                    project_index = project_client.indexes.create_or_update(
                        name=f"project-index-{self.azure_ai_search_index}",
                        version="1",
                        body={
                            "connectionName": self.azure_ai_search_connection_name,
                            "indexName": self.azure_ai_search_index,
                            "type": "AzureSearch",
                            "fieldMapping": field_mapping
                        }
                    )
                    print(f"Created index, name: {project_index.name}, version: {project_index.version}")

                # Initialize the Azure AI Search tool with the required parameters
                # Use the project index if it was created above, otherwise use the search index directly

                ai_search = AzureAISearchTool(
                    index_asset_id=f"{project_index.name}/versions/{project_index.version}",  # Asset ID for the index created above
                    index_connection_id=None,
                    index_name=None,
                    query_type=AzureAISearchQueryType.VECTOR_SEMANTIC_HYBRID, 
                    top_k=5,
                    filter="",
                )

                # Create an agent with the specified model, name, instructions, and tools
                agent = project_client.agents.create_agent(
                    model=self.azure_openai_deployment_model,
                    name="ChatWithCallTranscriptsAgent",
                    instructions="You are a helpful agent. Use the tools provided and always cite your sources.",  # Instructions for the agent
                    tools=ai_search.definitions,
                    tool_resources=ai_search.resources,
                )
                print(f"Created agent, ID: {agent.id}")

                # Create a thread for communication with the agent
                thread = project_client.agents.threads.create()
                print(f"Created thread, ID: {thread.id}")

                # Send a message to the thread
                message = project_client.agents.messages.create(
                    thread_id=thread.id,
                    role=MessageRole.USER,
                    content=question,
                )
                print(f"Created message, ID: {message['id']}")

                # Create and process an agent run in the thread using the tool
                run = project_client.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id, tool_choice={"type": "azure_ai_search"})
                print(f"Run finished with status: {run.status}")

                if run.status == "failed":
                    print(f"Run failed: {run.last_error}")
                else:
                    # Create a credential using DefaultAzureCredential (supports Managed Identity, CLI login, etc.)
                    credential = DefaultAzureCredential()
                    token = credential.get_token("https://search.azure.com/.default")
                    access_token = token.token

                    # Initialize the final response structure
                    final_response: Dict[str, Any] = {
                        "answer": "",
                        "citations": []
                    }

                    # Step 1: Extract citation metadata
                    for run_step in project_client.agents.run_steps.list(thread_id=thread.id, run_id=run.id):
                        if isinstance(run_step.step_details, RunStepToolCallDetails):
                            for tool_call in run_step.step_details.tool_calls:
                                tool_output = ast.literal_eval(tool_call['azure_ai_search']['output'])
                                print(f"Tool output: {tool_output}", flush=True)
                                urls = tool_output["metadata"].get("get_urls", [])
                                titles = tool_output["metadata"].get("titles", [])
                                ids = tool_output["metadata"].get("ids", [])

                                for i, url in enumerate(urls):
                                    title = titles[i] if i < len(titles) else ""
                                    doc_id = ids[i] if i < len(ids) else ""
                                    final_response["citations"].append({
                                        "url": url,
                                        "title": title,
                                        "doc_id": doc_id
                                    })

                    # # Step 2: Fetch and add content for each citation using RBAC token
                    # for citation in final_response["citations"]:
                    #     try:
                    #         response = requests.get(
                    #             citation["url"],
                    #             headers={
                    #                 "Authorization": f"Bearer {access_token}",
                    #                 "Content-Type": "application/json"
                    #             },
                    #             timeout=10  # Set a timeout for the request
                    #         )
                    #         if response.status_code == 200:
                    #             data = response.json()
                    #             content = data.get("content", "")
                    #             citation["content"] = content[:20000] if len(content) > 20000 else content
                    #         else:
                    #             citation["content"] = f"Error: HTTP {response.status_code}"
                    #     except Exception as e:
                    #         citation["content"] = f"Exception: {str(e)}"

                    # Step 3: Get the answer from the last agent message
                    messages = project_client.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
                    for msg in messages:
                        if msg.role == MessageRole.AGENT and msg.text_messages:
                            final_response["answer"] = msg.text_messages[-1].text.value
                            break

                    # Output the final structured response
                    answer = final_response



                    messages = project_client.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
                    for message in messages:
                        if message.role == MessageRole.AGENT and message.url_citation_annotations:
                            placeholder_annotations = {
                                annotation.text: f" [see {annotation.url_citation.title}] ({annotation.url_citation.url})"
                                for annotation in message.url_citation_annotations
                            }
                            for message_text in message.text_messages:
                                message_str = message_text.text.value
                                for k, v in placeholder_annotations.items():
                                    message_str = message_str.replace(k, v)
                                print(f"{message.role}: {message_str}")
                        else:
                            for message_text in message.text_messages:
                                print(f"{message.role}: {message_text.text.value}")


                            

                    # Optional: clean up
                    project_client.agents.delete_agent(agent.id)
        except Exception as e:
            print(f"An error occurred: {e}", flush=True)
            answer = "Details could not be retrieved. Please try again later."
        print("Answer from get_answers_from_calltranscripts:", answer, flush=True)
        return answer
