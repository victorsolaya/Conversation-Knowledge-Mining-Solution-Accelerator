import pytest
import pyodbc
from unittest.mock import patch, MagicMock
from datetime import datetime
from common.database.sqldb_service import get_db_connection, adjust_processed_data_dates, fetch_filters_data, fetch_chart_data, execute_sql_query


@pytest.fixture
def mock_config():
    with patch("common.config.config.Config") as mock_config_class:
        mock = MagicMock()
        mock.sqldb_server = "server"
        mock.sqldb_database = "database"
        mock.sqldb_username = "user"
        mock.sqldb_password = "password"
        mock.driver = "{ODBC Driver}"
        mock.mid_id = "client-id"
        mock_config_class.return_value = mock
        yield mock


@pytest.fixture
def mock_pyodbc_connection():
    with patch("pyodbc.connect") as mock_connect:
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn


@pytest.fixture
def mock_token():
    with patch("common.database.sqldb_service.DefaultAzureCredential") as mock_cred:
        mock_instance = MagicMock()
        mock_instance.get_token.return_value.token = "dummy_token"
        mock_cred.return_value = mock_instance
        yield mock_instance


def test_adjust_processed_data_dates(mock_pyodbc_connection, mock_token):
    mock_cursor = mock_pyodbc_connection.cursor().__enter__()
    mock_cursor.fetchone.return_value = [datetime.now()]
    adjust_processed_data_dates()
    assert mock_cursor.execute.call_count >= 4
    assert mock_pyodbc_connection.commit.called


def test_get_db_connection_fallback(mock_token):
    def connect_side_effect(*args, **kwargs):
        if "attrs_before" in kwargs:
            raise pyodbc.Error("Token auth failed")
        return MagicMock()

    with patch("pyodbc.connect", side_effect=connect_side_effect) as mock_connect:
        conn = get_db_connection()
        assert conn is not None
        assert mock_connect.call_count == 2


def test_fetch_filters_data(mock_pyodbc_connection, mock_token):
    mock_cursor = mock_pyodbc_connection.cursor().__enter__()
    mock_cursor.fetchall.return_value = [
        ("Topic", "Billing", "Billing"),
        ("Sentiment", "positive", "positive"),
        ("Satisfaction", "yes", "yes"),
        ("DateRange", "Last 7 days", "Last 7 days"),
    ]
    mock_cursor.description = [("filter_name",), ("displayValue",), ("key1",)]

    result = fetch_filters_data()

    assert isinstance(result, list)
    filter_names = {item["filter_name"] for item in result}
    expected_filter_names = {"Topic", "Sentiment", "Satisfaction", "DateRange"}
    assert expected_filter_names.issubset(filter_names)
    for item in result:
        assert "filter_name" in item
        assert "filter_values" in item
        assert isinstance(item["filter_values"], list)
        for val in item["filter_values"]:
            assert "displayValue" in val
            assert "key" in val


@pytest.mark.asyncio
async def test_fetch_chart_data(mock_pyodbc_connection, mock_token):
    mock_cursor = mock_pyodbc_connection.cursor().__enter__()
    mock_cursor.fetchall.side_effect = [
        [("TOTAL_CALLS", "Total Calls", "card", "Total Calls", 100, "")],
        [("Topic A", "TOPICS", "Trending Topics", "table", "positive", 42)],
        [("keyphrase", "KEY_PHRASES", "Key Phrases", "wordcloud", 20, "positive")]
    ]
    description_values = [
        [("id",), ("chart_name",), ("chart_type",), ("name",), ("value",), ("unit_of_measurement",)],
        [("name",), ("id",), ("chart_name",), ("chart_type",), ("average_sentiment",), ("call_frequency",)],
        [("text",), ("id",), ("chart_name",), ("chart_type",), ("size",), ("average_sentiment",)],
    ]

    def execute_side_effect(*args, **kwargs):
        current_call = mock_cursor.execute.call_count - 1
        mock_cursor.description = description_values[current_call]

    mock_cursor.execute.side_effect = execute_side_effect

    mock_chart_filters = MagicMock()
    mock_chart_filters.model_dump.return_value = {
        "selected_filters": {
            "Topic": ["Topic A"],
            "Sentiment": ["positive"],
            "Satisfaction": ["yes"],
            "DateRange": ["Last 7 days"]
        }
    }

    result = await fetch_chart_data(chart_filters=mock_chart_filters)
    assert isinstance(result, list)
    assert len(result) == 3
    assert all("chart_value" in chart for chart in result)


@pytest.mark.asyncio
async def test_fetch_chart_data_empty_filters(mock_pyodbc_connection, mock_token):
    mock_cursor = mock_pyodbc_connection.cursor().__enter__()
    mock_cursor.fetchall.side_effect = [
        [("TOTAL_CALLS", "Total Calls", "card", "Total Calls", 100, "")],
        [("Topic A", "TOPICS", "Trending Topics", "table", "positive", 42)],
        [("keyphrase", "KEY_PHRASES", "Key Phrases", "wordcloud", 20, "positive")]
    ]
    description_values = [
        [("id",), ("chart_name",), ("chart_type",), ("name",), ("value",), ("unit_of_measurement",)],
        [("name",), ("id",), ("chart_name",), ("chart_type",), ("average_sentiment",), ("call_frequency",)],
        [("text",), ("id",), ("chart_name",), ("chart_type",), ("size",), ("average_sentiment",)],
    ]

    def execute_side_effect(*args, **kwargs):
        current_call = mock_cursor.execute.call_count - 1
        mock_cursor.description = description_values[current_call]

    mock_cursor.execute.side_effect = execute_side_effect

    mock_chart_filters = MagicMock()
    mock_chart_filters.model_dump.side_effect = Exception("Invalid model")

    result = await fetch_chart_data(chart_filters=mock_chart_filters)
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_fetch_chart_data_topic_only(mock_pyodbc_connection, mock_token):
    mock_cursor = mock_pyodbc_connection.cursor().__enter__()
    mock_cursor.fetchall.side_effect = [
        [("TOTAL_CALLS", "Total Calls", "card", "Total Calls", 100, "")],
        [("Topic A", "TOPICS", "Trending Topics", "table", "positive", 42)],
        [("keyphrase", "KEY_PHRASES", "Key Phrases", "wordcloud", 20, "positive")]
    ]
    description_values = [
        [("id",), ("chart_name",), ("chart_type",), ("name",), ("value",), ("unit_of_measurement",)],
        [("name",), ("id",), ("chart_name",), ("chart_type",), ("average_sentiment",), ("call_frequency",)],
        [("text",), ("id",), ("chart_name",), ("chart_type",), ("size",), ("average_sentiment",)],
    ]

    def execute_side_effect(*args, **kwargs):
        current_call = mock_cursor.execute.call_count - 1
        mock_cursor.description = description_values[current_call]

    mock_cursor.execute.side_effect = execute_side_effect

    mock_chart_filters = MagicMock()
    mock_chart_filters.model_dump.return_value = {
        "selected_filters": {
            "Topic": ["Billing"]
        }
    }

    result = await fetch_chart_data(chart_filters=mock_chart_filters)
    assert isinstance(result, list)
    assert len(result) == 3


def test_execute_sql_query(mock_pyodbc_connection, mock_token):
    mock_cursor = mock_pyodbc_connection.cursor().__enter__()
    mock_cursor.execute.return_value = None
    mock_cursor.fetchall.return_value = [(1,), (2,), (3,)]
    result = execute_sql_query("SELECT 1")
    assert result == "(1,)(2,)(3,)"
