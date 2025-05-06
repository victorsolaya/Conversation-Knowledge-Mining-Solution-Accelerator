# Workshop challenge: run each function in the notebooks to see how they work

1. Open the [knowledge_mining_api notebook](./knowledge_mining_api.ipynb) from the Challenge-3-and-4 folder
2. Run the first cell to initialize the SQL connection 
3. The second cell defines a class that is used to define the plugin for the Azure AI Project Client. This contains the various functions that power different behaviors such as greeting, query Azure SQL database and query Azure AI Search. Run cell 2 and 3 to see the results when a user says Hello. 
4. Next we will explore the results when a user asks a question and run the query Azure SQL function. Update the user_input list in cell 3 with the below code and rerun cell 3. We will see that we get a result from the Azure SQL Database but the result could be easier for a user to read.
    - This cell is the main function that initializes the Azure AI Project Client and creates an agent. It sets up the agent with the necessary instructions and plugins, and then starts a conversation with the user.

```shell
user_inputs = [
                # "Hello",
                "Give a summary of billing issues"
                # "Total number of calls by date for the last 7 days",
                # "Show average handling time by topics in minutes",
                # "What are the top 7 challenges users reported?",
                # "When customers call in about unexpected charges, what types of charges are they seeing?",
            ]
```

5. Now uncomment the get_answers_from_calltranscripts() function in cell 2 as shown in the below code sample, to query the Azure AI Search. Run cell 2 and 3 to see a better result from the Azure AI Search query.    
```shell
@kernel_function(name="ChatWithCallTranscripts",
                     description="Provides summaries or detailed explanations from the search index.")
    def get_answers_from_calltranscripts(
            self,
            question: Annotated[str, "the question"]
    ):
        client = openai.AzureOpenAI(
            azure_endpoint=self.azure_openai_endpoint,
            api_key=self.azure_openai_api_key,
            api_version=self.azure_openai_api_version
        )

        query = question
        system_message = '''You are an assistant who provides an analyst with helpful information about data.
        You have access to the call transcripts, call data, topics, sentiments, and key phrases.
        You can use this information to answer questions.
        If you cannot answer the question, always return - I cannot answer this question from the data available. Please rephrase or add more details.'''
        answer = ''
        try:
            completion = client.chat.completions.create(
                model=self.azure_openai_deployment_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_message
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                seed=42,
                temperature=0,
                max_tokens=800,
                extra_body={
                    "data_sources": [
                        {
                            "type": "azure_search",
                            "parameters": {
                                "endpoint": self.azure_ai_search_endpoint,
                                "index_name": self.azure_ai_search_index,
                                "semantic_configuration": "my-semantic-config",
                                "query_type": "vector_simple_hybrid",  # "vector_semantic_hybrid"
                                "fields_mapping": {
                                    "content_fields_separator": "\n",
                                    "content_fields": ["content"],
                                    "filepath_field": "chunk_id",
                                    "title_field": "sourceurl",  # null,
                                    "url_field": "sourceurl",
                                    "vector_fields": ["contentVector"]
                                },
                                "in_scope": "true",
                                "role_information": system_message,
                                # "vector_filter_mode": "preFilter", #VectorFilterMode.PRE_FILTER,
                                # "filter": f"client_id eq '{ClientId}'", #"", #null,
                                "strictness": 3,
                                "top_n_documents": 5,
                                "authentication": {
                                    "type": "api_key",
                                    "key": self.azure_ai_search_api_key
                                },
                                "embedding_dependency": {
                                    "type": "deployment_name",
                                    "deployment_name": "text-embedding-ada-002"
                                },

                            }
                        }
                    ]
                }
            )
            answer = completion.choices[0]
            
        except BaseException:
            answer = 'Details could not be retrieved. Please try again later.'
        print("Answer from azurecalltranscripts: ", flush=True)
        print(answer, flush=True)
        return answer
```