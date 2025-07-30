"""
Simplified MCP server that only uses URL-based transcript fetching
"""

import logging
import sys
from typing import Dict, Any
import httpx
from fastmcp import FastMCP
from pydantic import Field
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Backend configuration
BACKEND_API_URL = "http://localhost:8082"  # Adjust port as needed

print("=== MCP Server Starting ===", file=sys.stderr)
print(f"Backend API URL: {BACKEND_API_URL}", file=sys.stderr)
print("===============================", file=sys.stderr)

mcp = FastMCP("earnings_call_transcript_tools")

@mcp.tool(name="get_transcript")
async def get_transcript(
    url: str = Field(description="The Motley Fool URL of the earnings call transcript (e.g., 'https://www.fool.com/earnings/call-transcripts/...')")
) -> Dict[str, Any]:
    """Fetches the earnings call transcript from a Motley Fool URL."""
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{BACKEND_API_URL}/get-transcript",
                json={"url": url}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Backend API error: {e.response.status_code} - {e.response.text}")
            return {"success": False, "error": f"Backend API error: {e.response.text}"}
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to backend API: {e}")
            return {"success": False, "error": "Connection to backend service failed"}

@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health_check(request):
    """A simple health check endpoint."""
    return JSONResponse({"status": "ok"})

def main():
    """Main function to run the MCP server."""
    host = "127.0.0.1"
    port = 8001  # MCP server port
    
    logger.info(f"Starting Earnings Call Transcript MCP server at http://{host}:{port}/mcp")
    print(f"MCP Server running at http://{host}:{port}/mcp", file=sys.stderr)
    
    mcp.run(transport="sse", host=host, port=port, path="/mcp")

if __name__ == "__main__":
    main()