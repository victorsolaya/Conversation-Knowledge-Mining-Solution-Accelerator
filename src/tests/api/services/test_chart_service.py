import sys
import types
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

# ---- Mock common.database.sqldb_service ----
mock_sqldb_service = types.ModuleType("common.database.sqldb_service")
mock_sqldb_service.adjust_processed_data_dates = MagicMock()
mock_sqldb_service.fetch_filters_data = MagicMock()
mock_sqldb_service.fetch_chart_data = AsyncMock()
sys.modules["common.database.sqldb_service"] = mock_sqldb_service

# ---- Mock api.models.input_models ----
mock_input_models = types.ModuleType("api.models.input_models")
mock_input_models.ChartFilters = MagicMock()
sys.modules["api.models.input_models"] = mock_input_models

# ---- Import service under test ----
from services.chart_service import ChartService #type:ignore

@pytest.fixture
def chart_service():
    return ChartService()


@patch("services.chart_service.adjust_processed_data_dates")
@patch("services.chart_service.fetch_filters_data")
def test_fetch_filter_data_success(mock_fetch_filters_data, mock_adjust_dates, chart_service):
    mock_adjust_dates.return_value = None
    mock_fetch_filters_data.return_value = {"data": "filter_data"}

    result = chart_service.fetch_filter_data()
    assert result == {"data": "filter_data"}


@patch("services.chart_service.adjust_processed_data_dates", side_effect=Exception("Failed"))
@patch("services.chart_service.fetch_filters_data")
def test_fetch_filter_data_failure(mock_fetch_filters_data, mock_adjust_dates, chart_service):
    with pytest.raises(HTTPException) as exc_info:
        chart_service.fetch_filter_data()
    assert exc_info.value.status_code == 500


@patch("services.chart_service.fetch_chart_data", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_fetch_chart_data_success(mock_fetch_chart_data, chart_service):
    mock_fetch_chart_data.return_value = {"data": "chart_data"}
    result = await chart_service.fetch_chart_data()
    assert result == {"data": "chart_data"}


@patch("services.chart_service.fetch_chart_data", new_callable=AsyncMock, side_effect=Exception("DB error"))
@pytest.mark.asyncio
async def test_fetch_chart_data_failure(mock_fetch_chart_data, chart_service):
    with pytest.raises(HTTPException) as exc_info:
        await chart_service.fetch_chart_data()
    assert exc_info.value.status_code == 500


@patch("services.chart_service.fetch_chart_data", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_fetch_chart_data_with_filters_success(mock_fetch_chart_data, chart_service):
    mock_fetch_chart_data.return_value = {"data": "filtered_chart_data"}
    fake_filters = MagicMock()

    result = await chart_service.fetch_chart_data_with_filters(fake_filters)
    assert result == {"data": "filtered_chart_data"}


@patch("services.chart_service.fetch_chart_data", new_callable=AsyncMock, side_effect=Exception("Failure"))
@pytest.mark.asyncio
async def test_fetch_chart_data_with_filters_failure(mock_fetch_chart_data, chart_service):
    fake_filters = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await chart_service.fetch_chart_data_with_filters(fake_filters)
    assert exc_info.value.status_code == 500
