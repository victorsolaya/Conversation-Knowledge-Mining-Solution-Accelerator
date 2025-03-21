import logging
import os
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from api.models.input_models import ChartFilters
from services.chat_service import ChatService
from services.chart_service import ChartService

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.get("/fetchChartData")
async def fetch_chart_data():
    try:
        chartService = ChartService()
        response = chartService.fetch_chart_data()
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"Error in fetch_chart_data: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": "Failed to fetch chart data"}, status_code=500)


@router.post("/fetchChartDataWithFilters")
async def fetch_chart_data_with_filters(chart_filters: ChartFilters):
    try:
        chartservice = ChartService()
        response = await chartservice.fetch_chart_data_with_filters(chart_filters)
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"Error in fetch_chart_data_with_filters: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": "Failed to fetch chart data"}, status_code=500)


@router.get("/fetchFilterData")
async def fetch_filter_data():
    try:
        chartservice = ChartService()
        response = chartservice.fetch_filter_data()
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"Error in fetch_filter_data: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": "Failed to fetch filter data"}, status_code=500)


@router.post("/chat")
async def conversation(request: Request):
    try:
        # Get the request JSON and last RAG response from the client
        request_json = await request.json()

        last_rag_response = request_json.get("last_rag_response")
        logger.info(f"Received last_rag_response: {last_rag_response}")

        query_separator = "&" if os.getenv("USE_GRAPHRAG", "false").lower() == "true" else "?"
        query = request_json.get("messages")[-1].get("content")
        is_chart_query = any(
            term in query.lower()
            for term in ["chart", "graph", "visualize", "plot"]
        )
        chatservice = ChatService()
        if not is_chart_query:
            result = chatservice.stream_chat_request(request_json, query_separator, query)
            return StreamingResponse(result, media_type="application/json-lines")
        else:
            result = await chatservice.complete_chat_request(query, last_rag_response)
            return JSONResponse(content=result)
    except Exception as ex:
        logger.exception("Error in conversation endpoint")
        return JSONResponse(content={"error": str(ex)}, status_code=getattr(ex, "status_code", 500))
