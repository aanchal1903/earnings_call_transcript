"""
agents/earnings_call_transcript_agent/src/backend_api/server.py

Backend API server for the Earnings Call Transcript Agent.
Handles the core business logic for fetching earnings call transcripts
from external financial data providers like Finnhub, Alpha Vantage, etc.
"""

import logging
import uvicorn
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import httpx
from datetime import datetime
from config.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="Earnings Call Transcript Backend API", version="1.0.0")

class TranscriptRequest(BaseModel):
    company_ticker: str = Field(..., description="Stock ticker symbol")
    year: int = Field(..., description="Year of the earnings call")
    quarter: int = Field(..., ge=1, le=4, description="Quarter (1-4)")

class TranscriptListRequest(BaseModel):
    company_ticker: str = Field(..., description="Stock ticker symbol")

class TranscriptSearchRequest(BaseModel):
    company_ticker: str = Field(..., description="Stock ticker symbol")
    year: int = Field(..., description="Year of the earnings call")
    quarter: int = Field(..., ge=1, le=4, description="Quarter (1-4)")
    search_query: str = Field(..., description="Text to search for")

class CompanyInfoRequest(BaseModel):
    company_ticker: str = Field(..., description="Stock ticker symbol")

class TickerValidationRequest(BaseModel):
    company_ticker: str = Field(..., description="Stock ticker symbol to validate")

class FinancialDataProvider:
    """Interface for financial data providers."""
    
    def __init__(self):
        self.api_key = settings.GCP_FINANCIAL_DATA_API_KEY
        self.base_url = settings.FINANCIAL_DATA_API_BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_transcript(self, ticker: str, year: int, quarter: int) -> Dict[str, Any]:
        """Fetch earnings call transcript from the financial data provider."""
        try:
            # Example API call structure - adapt based on your provider
            endpoint = f"{self.base_url}/earnings/transcript"
            params = {
                "symbol": ticker.upper(),
                "year": year,
                "quarter": quarter,
                "token": self.api_key
            }
            
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Transform response to standardized format
            return {
                "success": True,
                "data": {
                    "company_ticker": ticker.upper(),
                    "company_name": data.get("company_name", "Unknown"),
                    "year": year,
                    "quarter": quarter,
                    "call_date": data.get("call_date"),
                    "transcript": data.get("transcript", ""),
                    "speakers": data.get("speakers", []),
                    "q_and_a_section": data.get("q_and_a", ""),
                    "analyst_questions": data.get("analyst_questions", []),
                    "management_responses": data.get("management_responses", [])
                }
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"API error fetching transcript: {e}")
            return {
                "success": False,
                "error": f"Failed to fetch transcript: {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def list_available_transcripts(self, ticker: str) -> Dict[str, Any]:
        """List all available transcripts for a company."""
        try:
            endpoint = f"{self.base_url}/earnings/list"
            params = {
                "symbol": ticker.upper(),
                "token": self.api_key
            }
            
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "data": {
                    "company_ticker": ticker.upper(),
                    "company_name": data.get("company_name", "Unknown"),
                    "available_transcripts": data.get("transcripts", [])
                }
            }
        except Exception as e:
            logger.error(f"Error listing transcripts: {e}")
            return {
                "success": False,
                "error": f"Failed to list transcripts: {str(e)}"
            }
    
    async def validate_ticker(self, ticker: str) -> Dict[str, Any]:
        """Validate if a ticker symbol is valid."""
        try:
            endpoint = f"{self.base_url}/company/profile"
            params = {
                "symbol": ticker.upper(),
                "token": self.api_key
            }
            
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "data": {
                    "ticker": ticker.upper(),
                    "is_valid": bool(data.get("name")),
                    "company_name": data.get("name", ""),
                    "exchange": data.get("exchange", ""),
                    "sector": data.get("sector", "")
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to validate ticker: {str(e)}"
            }

# Initialize the financial data provider
financial_provider = FinancialDataProvider()

@app.post("/get-transcript")
async def get_transcript(request: TranscriptRequest) -> Dict[str, Any]:
    """Get earnings call transcript for a specific company and quarter."""
    logger.info(f"Fetching transcript for {request.company_ticker} Q{request.quarter} {request.year}")
    
    result = await financial_provider.get_transcript(
        request.company_ticker, 
        request.year, 
        request.quarter
    )
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@app.post("/list-transcripts")
async def list_transcripts(request: TranscriptListRequest) -> Dict[str, Any]:
    """List all available transcripts for a company."""
    logger.info(f"Listing transcripts for {request.company_ticker}")
    
    result = await financial_provider.list_available_transcripts(request.company_ticker)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@app.post("/search-transcript")
async def search_transcript(request: TranscriptSearchRequest) -> Dict[str, Any]:
    """Search for specific content within a transcript."""
    logger.info(f"Searching transcript for {request.company_ticker} Q{request.quarter} {request.year}")
    
    # First get the transcript
    transcript_result = await financial_provider.get_transcript(
        request.company_ticker, 
        request.year, 
        request.quarter
    )
    
    if not transcript_result["success"]:
        raise HTTPException(status_code=404, detail=transcript_result["error"])
    
    # Search within the transcript
    transcript_text = transcript_result["data"]["transcript"]
    search_results = []
    
    # Simple search implementation - can be enhanced with more sophisticated search
    lines = transcript_text.split('\n')
    for i, line in enumerate(lines):
        if request.search_query.lower() in line.lower():
            search_results.append({
                "line_number": i + 1,
                "content": line.strip(),
                "context": lines[max(0, i-1):i+2]  # Include some context
            })
    
    return {
        "success": True,
        "data": {
            "company_ticker": request.company_ticker,
            "year": request.year,
            "quarter": request.quarter,
            "search_query": request.search_query,
            "results_count": len(search_results),
            "results": search_results[:50]  # Limit results
        }
    }

@app.post("/company-info")
async def get_company_info(request: CompanyInfoRequest) -> Dict[str, Any]:
    """Get basic information about a company."""
    logger.info(f"Fetching company info for {request.company_ticker}")
    
    result = await financial_provider.validate_ticker(request.company_ticker)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result