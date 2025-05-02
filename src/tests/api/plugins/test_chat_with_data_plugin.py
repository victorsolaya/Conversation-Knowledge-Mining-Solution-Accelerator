from unittest.mock import patch, MagicMock
import pytest
from plugins.chat_with_data_plugin import ChatWithDataPlugin


@pytest.fixture
def mock_config():
    return {
        "azure_openai_deployment_model": "test-model",
        "azure_openai_endpoint": "https://test-endpoint",
        "azure_openai_api_key": "test-api-key",
        "azure_openai_api_version": "2023-03-15-preview",
        "azure_ai_search_endpoint": "https://test-search-endpoint",
        "azure_ai_search_api_key": "test-search-api-key",
        "azure_ai_search_index": "test-index",
        "use_ai_project_client": False,
        "azure_ai_project_conn_string": "test-connection-string",
    }


@pytest.fixture
def plugin(mock_config):
    with patch("plugins.chat_with_data_plugin.Config") as MockConfig:
        MockConfig.return_value = MagicMock(**mock_config)
        return ChatWithDataPlugin()


@patch("plugins.chat_with_data_plugin.openai.AzureOpenAI")
def test_greeting(mock_openai, plugin):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Hello! How can I help you?"))]
    )

    response = plugin.greeting("Hi")

    assert response == "Hello! How can I help you?"
    mock_client.chat.completions.create.assert_called_once()


@patch("plugins.chat_with_data_plugin.AIProjectClient")
@patch("plugins.chat_with_data_plugin.DefaultAzureCredential")
def test_greeting_with_ai_project_client(
        mock_credential, mock_ai_project_client, plugin):
    mock_project = MagicMock()
    mock_ai_project_client.from_connection_string.return_value = mock_project
    mock_client = MagicMock()
    mock_project.inference.get_chat_completions_client.return_value = mock_client
    mock_client.complete.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Hello! How can I help you?"))]
    )
    plugin.use_ai_project_client = True
    response = plugin.greeting("Hi")
    assert response == "Hello! How can I help you?"
    mock_ai_project_client.from_connection_string.assert_called_once_with(
        conn_str="test-connection-string", credential=mock_credential.return_value
    )
    mock_project.inference.get_chat_completions_client.assert_called_once()
    mock_client.complete.assert_called_once()


@patch("plugins.chat_with_data_plugin.openai.AzureOpenAI")
def test_greeting_exception(mock_openai, plugin):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("Greeting API Error")
    response = plugin.greeting("Hi")
    assert response == "Greeting API Error"
    mock_client.chat.completions.create.assert_called_once()


@patch("plugins.chat_with_data_plugin.execute_sql_query")
@patch("plugins.chat_with_data_plugin.openai.AzureOpenAI")
def test_get_sql_response(mock_openai, mock_execute_sql_query, plugin):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content="""SELECT CAST(EndTime AS DATE) AS call_date, COUNT(*) AS total_calls FROM km_processed_data WHERE EndTime >= DATEADD(DAY, -7, GETDATE()) GROUP BY CAST(EndTime AS DATE) ORDER BY call_date;"""))])

    mock_execute_sql_query.return_value = "(datetime.date(2025, 4, 26), 11)(datetime.date(2025, 4, 27), 20)(datetime.date(2025, 4, 28), 29)(datetime.date(2025, 4, 29), 17)(datetime.date(2025, 4, 30), 19)(datetime.date(2025, 5, 1), 16)"

    response = plugin.get_SQL_Response("Total number of calls by date for last 7 days")

    assert response == "(datetime.date(2025, 4, 26), 11)(datetime.date(2025, 4, 27), 20)(datetime.date(2025, 4, 28), 29)(datetime.date(2025, 4, 29), 17)(datetime.date(2025, 4, 30), 19)(datetime.date(2025, 5, 1), 16)"
    mock_client.chat.completions.create.assert_called_once()
    mock_execute_sql_query.assert_called_once_with(
        """SELECT CAST(EndTime AS DATE) AS call_date, COUNT(*) AS total_calls FROM km_processed_data WHERE EndTime >= DATEADD(DAY, -7, GETDATE()) GROUP BY CAST(EndTime AS DATE) ORDER BY call_date;""")


@patch("plugins.chat_with_data_plugin.execute_sql_query")
@patch("plugins.chat_with_data_plugin.AIProjectClient")
@patch("plugins.chat_with_data_plugin.DefaultAzureCredential")
def test_get_SQL_Response_with_ai_project_client(
        mock_credential,
        mock_ai_project_client,
        mock_execute_sql_query,
        plugin):
    mock_project = MagicMock()
    mock_ai_project_client.from_connection_string.return_value = mock_project
    mock_client = MagicMock()
    mock_project.inference.get_chat_completions_client.return_value = mock_client
    mock_client.complete.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content="""SELECT CAST(EndTime AS DATE) AS call_date, COUNT(*) AS total_calls FROM km_processed_data WHERE EndTime >= DATEADD(DAY, -7, GETDATE()) GROUP BY CAST(EndTime AS DATE) ORDER BY call_date;"""))])
    plugin.use_ai_project_client = True

    mock_execute_sql_query.return_value = "(datetime.date(2025, 4, 26), 11)(datetime.date(2025, 4, 27), 20)(datetime.date(2025, 4, 28), 29)(datetime.date(2025, 4, 29), 17)(datetime.date(2025, 4, 30), 19)(datetime.date(2025, 5, 1), 16)"

    response = plugin.get_SQL_Response("Total number of calls by date for last 7 days")
    assert response == "(datetime.date(2025, 4, 26), 11)(datetime.date(2025, 4, 27), 20)(datetime.date(2025, 4, 28), 29)(datetime.date(2025, 4, 29), 17)(datetime.date(2025, 4, 30), 19)(datetime.date(2025, 5, 1), 16)"
    mock_ai_project_client.from_connection_string.assert_called_once_with(
        conn_str="test-connection-string", credential=mock_credential.return_value
    )
    mock_project.inference.get_chat_completions_client.assert_called_once()
    mock_execute_sql_query.assert_called_once_with(
        """SELECT CAST(EndTime AS DATE) AS call_date, COUNT(*) AS total_calls FROM km_processed_data WHERE EndTime >= DATEADD(DAY, -7, GETDATE()) GROUP BY CAST(EndTime AS DATE) ORDER BY call_date;""")

@patch("plugins.chat_with_data_plugin.openai.AzureOpenAI")
def test_get_sql_response_exception(mock_openai, plugin):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("SQL Generation Error")
    response = plugin.get_SQL_Response("Total number of calls by date for last 7 days")
    assert response == "SQL Generation Error"
    mock_client.chat.completions.create.assert_called_once()


@patch("plugins.chat_with_data_plugin.openai.AzureOpenAI")
def test_get_answers_from_calltranscripts(mock_openai, plugin):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(
            message=MagicMock(
                content="Here is a summary of the billing issues discussed in the retrieved documents:\n\n1. **Unusual Charges**: Clara reported unusual charges on her bill, which she could not account for. Chris from customer service identified that the additional charges were related to international calling, which Clara did not recall making. An investigation was initiated to trace these charges [doc1].\n\n2. **Higher Bill Amount**: Juan noticed that his bill amount was higher than usual and was concerned about the billing cycle calculation. Upon review, it was found that there were additional usage charges for international calls, which Juan disputed as he did not make any international calls. Jenny, the customer service representative, offered to investigate these charges further and provide a detailed breakdown of the call logs [doc2].\n\n3. **Payment Method Issues**: Juan also wanted to switch his payment method from credit card to automatic bank transfer. He was informed that he would need to provide his bank account information securely over the phone or through a secure online session [doc2].\n\n4. **Account Update Problems**: Joanna faced issues updating her account information on the website, receiving an error message when trying to submit changes. Jenny confirmed that the updates were not reflected in the system and offered to manually update the address but noted that for security reasons, direct credit card information could not be taken over the phone [doc3].\n\n5. **Feedback on Billing Preferences**: Louis provided feedback about receiving excessive paper bills despite opting for paperless billing. The representative assured him that his preference would be updated to ensure he only receives digital invoices moving forward [doc4].",
                context={
                    "citations": [
                        {
                            "content": "Clara reported unusual charges on her bill...",
                            "title": "convo_bd2bd056-8ba6-41f2-bfda-17707571379c.json",
                            "url": "https://example.com/doc1",
                            "filepath": "bd2bd056-8ba6-41f2-bfda-17707571379c_01",
                            "chunk_id": "0"
                        },
                        {
                            "content": "Juan noticed that his bill amount was higher...",
                            "title": "convo_125a64bc-6f09-47bb-9244-e0a4f429638b.json",
                            "url": "https://example.com/doc2",
                            "filepath": "125a64bc-6f09-47bb-9244-e0a4f429638b_01",
                            "chunk_id": "0"
                        }
                    ]
                }
            )
        )]
    )

    response = plugin.get_answers_from_calltranscripts(
        "Give a summary of billing issues")

    expected_content = "Here is a summary of the billing issues discussed in the retrieved documents:\n\n1. **Unusual Charges**: Clara reported unusual charges on her bill, which she could not account for. Chris from customer service identified that the additional charges were related to international calling, which Clara did not recall making. An investigation was initiated to trace these charges [doc1].\n\n2. **Higher Bill Amount**: Juan noticed that his bill amount was higher than usual and was concerned about the billing cycle calculation. Upon review, it was found that there were additional usage charges for international calls, which Juan disputed as he did not make any international calls. Jenny, the customer service representative, offered to investigate these charges further and provide a detailed breakdown of the call logs [doc2].\n\n3. **Payment Method Issues**: Juan also wanted to switch his payment method from credit card to automatic bank transfer. He was informed that he would need to provide his bank account information securely over the phone or through a secure online session [doc2].\n\n4. **Account Update Problems**: Joanna faced issues updating her account information on the website, receiving an error message when trying to submit changes. Jenny confirmed that the updates were not reflected in the system and offered to manually update the address but noted that for security reasons, direct credit card information could not be taken over the phone [doc3].\n\n5. **Feedback on Billing Preferences**: Louis provided feedback about receiving excessive paper bills despite opting for paperless billing. The representative assured him that his preference would be updated to ensure he only receives digital invoices moving forward [doc4]."
    expected_citations = [
        {
            "content": "Clara reported unusual charges on her bill...",
            "title": "convo_bd2bd056-8ba6-41f2-bfda-17707571379c.json",
            "url": "https://example.com/doc1",
            "filepath": "bd2bd056-8ba6-41f2-bfda-17707571379c_01",
            "chunk_id": "0"
        },
        {
            "content": "Juan noticed that his bill amount was higher...",
            "title": "convo_125a64bc-6f09-47bb-9244-e0a4f429638b.json",
            "url": "https://example.com/doc2",
            "filepath": "125a64bc-6f09-47bb-9244-e0a4f429638b_01",
            "chunk_id": "0"
        }
    ]

    assert response.message.content == expected_content
    assert response.message.context["citations"] == expected_citations
    mock_client.chat.completions.create.assert_called_once()
    

@patch("plugins.chat_with_data_plugin.openai.AzureOpenAI")
def test_get_answers_from_calltranscripts_exception(mock_openai, plugin):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    response = plugin.get_answers_from_calltranscripts("What is the summary of the call transcripts?")
    assert response == "Details could not be retrieved. Please try again later."
    mock_client.chat.completions.create.assert_called_once()