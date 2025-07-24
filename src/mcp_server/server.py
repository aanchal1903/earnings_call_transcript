"""
agents/earnings_call_transcript_agent/src/mcp_server/server.py

Defines the MCP (Model Context Protocol) server for the Earnings Call Transcript Agent.

It acts as a facade, exposing a clean MCP tool interface that the ADK
agent can call. Internally, it translates these tool calls into HTTP requests
to this agent's own dedicated backend API service, which contains the core
business logic for fetching earnings call transcripts.
"""

import logging
from typing import Dict, Any, List, Optional
import httpx
from fastmcp import FastMCP
from pydantic import Field
from fastapi.responses import JSONResponse 
from config.config import settings

logger = logging.getLogger(__name__)

mcp = FastMCP("earnings_call_transcript_tools")

async def call_backend_api(endpoint: str, payload: dict) -> Dict[str, Any]:
    """
    A reusable helper to make HTTP POST requests to the backend API service.

    Args:
        endpoint: The API endpoint path.
        payload: The JSON payload to send in the request body.

    Returns:
        A dictionary parsed from the JSON response of the backend.
    """
    host = (
        settings.EARNINGS_CALL_BACKEND_SERVICE_NAME
        if settings.APP_ENVIRONMENT == "docker"
        else "127.0.0.1"
    )
    backend_url = f"http://{host}:{settings.EARNINGS_CALL_BACKEND_PORT_INTERNAL}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            full_url = f"{backend_url}{endpoint}"
            logger.info(f"MCP Server calling Backend API: POST {full_url}")
            logger.debug(f"Payload: {payload}")
            response = await client.post(full_url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Backend API error: {e.response.status_code} - {e.response.text}")
            return {"error": "Backend API request failed", "details": e.response.text}
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to backend API at {e.request.url}: {e}")
            return {"error": "Connection to backend service failed", "details": str(e)}

@mcp.tool(name="get_transcript")
async def get_transcript(
    company_ticker: str = Field(description="The stock ticker symbol of the company (e.g., 'MSFT', 'AAPL')."),
    year: int = Field(description="The year of the earnings call (e.g., 2023)."),
    quarter: int = Field(description="The quarter of the earnings call (1, 2, 3, or 4).")
) -> Dict[str, Any]:
    """Fetches the full, speaker-diarized transcript for a specific company's earnings call."""
    return await call_backend_api("/get-transcript", {
        "company_ticker": company_ticker,
        "year": year,
        "quarter": quarter
    })

@mcp.tool(name="list_available_transcripts")
async def list_available_transcripts(
    company_ticker: str = Field(description="The stock ticker symbol of the company.")
) -> Dict[str, Any]:
    """Lists all available earnings call transcripts for a given company."""
    return await call_backend_api("/list-transcripts", {"company_ticker": company_ticker})

@mcp.tool(name="search_transcript_content")
async def search_transcript_content(
    company_ticker: str = Field(description="The stock ticker symbol of the company."),
    year: int = Field(description="The year of the earnings call."),
    quarter: int = Field(description="The quarter of the earnings call."),
    search_query: str = Field(description="The text to search for within the transcript.")
) -> Dict[str, Any]:
    """Searches for specific content within an earnings call transcript."""
    return await call_backend_api("/search-transcript", {
        "company_ticker": company_ticker,
        "year": year,
        "quarter": quarter,
        "search_query": search_query
    })

@mcp.tool(name="get_company_info")
async def get_company_info(
    company_ticker: str = Field(description="The stock ticker symbol of the company.")
) -> Dict[str, Any]:
    """Gets basic information about a company including name, sector, and market cap."""
    return await call_backend_api("/company-info", {"company_ticker": company_ticker})

@mcp.tool(name="validate_company_ticker")
async def validate_company_ticker(
    company_ticker: str = Field(description="The stock ticker symbol to validate.")
) -> Dict[str, Any]:
    """Validates if a company ticker symbol is valid and publicly traded."""
    return await call_backend_api("/validate-ticker", {"company_ticker": company_ticker})

@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health_check(request):
    """A simple health check endpoint that returns a 200 OK status."""
    return JSONResponse({"status": "ok"})

def main():
    """Main function to run the Uvicorn server for the MCP application."""
    host = "0.0.0.0" if settings.APP_ENVIRONMENT == "docker" else "127.0.0.1"
    port = settings.EARNINGS_CALL_MCP_PORT_INTERNAL
    logger.info(f"Starting Earnings Call Transcript MCP server at http://{host}:{port}/mcp")
    mcp.run(transport="sse", host=host, port=port, path="/mcp")

if __name__ == "__main__":
    main()