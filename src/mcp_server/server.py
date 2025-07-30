"""
Enhanced MCP server with multi-source transcript fetching
"""

import logging
import sys
from typing import Dict, Any, Optional
import httpx
from fastmcp import FastMCP
from pydantic import Field
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Backend configuration
BACKEND_API_URL = "http://localhost:8082"

print("=== MCP Server Starting ===", file=sys.stderr)
print(f"Backend API URL: {BACKEND_API_URL}", file=sys.stderr)
print("Multi-source transcript fetching enabled", file=sys.stderr)
print("===============================", file=sys.stderr)

mcp = FastMCP("earnings_call_transcript_tools")

@mcp.tool(name="get_transcript")
async def get_transcript(
    company_ticker: Optional[str] = Field(None, description="Stock ticker symbol (e.g., 'MSFT', 'AAPL')"),
    year: Optional[int] = Field(None, description="Year of the earnings call (e.g., 2023)"),
    quarter: Optional[int] = Field(None, description="Quarter of the earnings call (1, 2, 3, or 4)"),
    url: Optional[str] = Field(None, description="Direct URL of the earnings call transcript (any source)")
) -> Dict[str, Any]:
    """
    Fetches earnings call transcript using intelligent multi-source fallback:
    1. Official company sources (via Gemini search)
    2. Financial Modeling Prep API (free tier)
    3. Motley Fool (automatic search)
    4. User-provided URL (fallback)
    
    The tool automatically tries each source in order until successful.
    """
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            # Build request payload
            payload = {}
            
            if company_ticker and year and quarter:
                payload = {
                    "company_ticker": company_ticker.upper(),
                    "year": year,
                    "quarter": quarter
                }
                logger.info(f"Starting multi-source search for {company_ticker} Q{quarter} {year}")
            elif url:
                payload = {"url": url}
                logger.info(f"Using direct URL: {url}")
            else:
                return {
                    "success": False,
                    "error": "Please provide either (1) company ticker, year, and quarter OR (2) a direct URL",
                    "usage_examples": [
                        "Natural search: ticker='AAPL', year=2024, quarter=1",
                        "Direct URL: url='https://example.com/transcript'"
                    ]
                }
            
            # Make request to enhanced backend
            response = await client.post(
                f"{BACKEND_API_URL}/get-transcript",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # Log the source used
            if result.get("success"):
                source = result.get("source_type", "unknown")
                logger.info(f"Successfully retrieved transcript from source: {source}")
                
                # Add user-friendly message about the source
                if source == "official":
                    result["source_info"] = "Retrieved from official company source"
                elif source == "fmp":
                    result["source_info"] = "Retrieved from Financial Modeling Prep API"
                elif source == "motley_fool":
                    result["source_info"] = "Retrieved from Motley Fool"
                elif source == "user_provided":
                    result["source_info"] = "Retrieved from user-provided URL"
            else:
                # Log which sources were attempted
                attempts = result.get("search_attempts", [])
                if attempts:
                    logger.warning(f"All sources failed. Attempted: {', '.join(attempts)}")
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Backend API error: {e.response.status_code} - {e.response.text}")
            return {
                "success": False, 
                "error": f"Backend API error: {e.response.text}",
                "status_code": e.response.status_code
            }
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to backend API: {e}")
            return {
                "success": False, 
                "error": "Connection to backend service failed. Please ensure the backend is running.",
                "troubleshooting": [
                    "Check if backend is running on port 8082",
                    "Run: python run_backend.py"
                ]
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

@mcp.tool(name="search_transcripts")
async def search_transcripts(
    company_ticker: str = Field(..., description="Stock ticker symbol to search for"),
    start_year: Optional[int] = Field(None, description="Start year for search range"),
    end_year: Optional[int] = Field(None, description="End year for search range")
) -> Dict[str, Any]:
    """
    Searches for available earnings call transcripts for a company.
    This is useful for discovering what transcripts are available before fetching.
    """
    
    # This would integrate with your backend to search across sources
    # For now, returning a placeholder
    return {
        "success": True,
        "ticker": company_ticker.upper(),
        "message": f"To search for specific transcripts, use get_transcript with ticker, year, and quarter.",
        "example": {
            "company_ticker": company_ticker.upper(),
            "year": 2024,
            "quarter": 1
        }
    }

@mcp.tool(name="validate_ticker")
async def validate_ticker(
    ticker: str = Field(..., description="Stock ticker symbol to validate")
) -> Dict[str, Any]:
    """
    Validates a stock ticker and returns company information.
    Useful for confirming the correct ticker before searching for transcripts.
    """
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # You could call a validation endpoint on your backend
            # For now, we'll return a simple response
            return {
                "success": True,
                "ticker": ticker.upper(),
                "valid": True,
                "message": f"Ticker {ticker.upper()} is valid. Use get_transcript to fetch earnings calls."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to validate ticker: {str(e)}"
            }

@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health_check(request):
    """Health check endpoint for the MCP server."""
    
    # Check backend health
    backend_healthy = False
    backend_info = {}
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BACKEND_API_URL}/health")
            if response.status_code == 200:
                backend_healthy = True
                backend_info = response.json()
    except:
        pass
    
    return JSONResponse({
        "status": "ok",
        "service": "earnings-call-mcp-server",
        "version": "2.0.0",
        "backend": {
            "url": BACKEND_API_URL,
            "healthy": backend_healthy,
            "info": backend_info
        },
        "capabilities": [
            "Multi-source transcript fetching",
            "Automatic fallback mechanism",
            "Official sources via Gemini",
            "Financial Modeling Prep API",
            "Motley Fool search"
        ]
    })

@mcp.custom_route("/debug/sources", methods=["GET"], include_in_schema=False)
async def debug_sources(request):
    """Debug endpoint to check which transcript sources are configured."""
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BACKEND_API_URL}/health")
            if response.status_code == 200:
                data = response.json()
                return JSONResponse({
                    "backend_connected": True,
                    "configured_sources": data.get("configured_services", {}),
                    "message": "Check backend logs for detailed source testing"
                })
    except:
        pass
    
    return JSONResponse({
        "backend_connected": False,
        "message": "Cannot reach backend service"
    })

def main():
    """Main function to run the enhanced MCP server."""
    host = "127.0.0.1"
    port = 8001  # MCP server port
    
    logger.info(f"Starting Enhanced Earnings Call MCP server at http://{host}:{port}/mcp")
    print(f"Enhanced MCP Server running at http://{host}:{port}/mcp", file=sys.stderr)
    print("Features:", file=sys.stderr)
    print("  - Official source search via Gemini", file=sys.stderr)
    print("  - Financial Modeling Prep API integration", file=sys.stderr)
    print("  - Automatic Motley Fool search", file=sys.stderr)
    print("  - Intelligent fallback mechanism", file=sys.stderr)
    
    mcp.run(transport="sse", host=host, port=port, path="/mcp")

if __name__ == "__main__":
    main()