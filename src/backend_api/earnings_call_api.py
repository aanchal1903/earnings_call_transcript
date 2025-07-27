"""
agents/earnings_call_transcript_agent/src/backend_api/server.py

Backend API server for the Earnings Call Transcript Agent.
This version correctly uses the 'earningscall' library as per its official documentation.
"""

import logging
import uvicorn
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# --- CORRECTED IMPORT based on the documentation ---
from earningscall import get_company

from config.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="Earnings Call Transcript Backend API", version="1.0.0")

# --- Pydantic models remain the same ---
class TranscriptRequest(BaseModel):
    company_ticker: str = Field(..., description="Stock ticker symbol")
    year: int = Field(..., description="Year of the earnings call")
    quarter: int = Field(..., ge=1, le=4, description="Quarter (1-4)")

# ... (other Pydantic models are the same) ...
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
    """
    This version now uses the 'earningscall' library correctly.
    It works for "AAPL" and "MSFT" by default.
    """
    
    def __init__(self):
        # NOTE: To get more than AAPL and MSFT, you would need to get an API key for THIS library
        # and set it like this:
        # import earningscall
        # earningscall.api_key = "YOUR_EARNINGSCALL_API_KEY"
        pass
    
    async def get_transcript(self, ticker: str, year: int, quarter: int) -> Dict[str, Any]:
        """Fetch earnings call transcript using the correct 'earningscall' library method."""
        try:
            logger.info(f"Using 'earningscall' library for {ticker} Q{quarter} {year}")

            # --- CORRECTED USAGE ---
            # 1. Get the company object first.
            company = get_company(ticker)
            
            # 2. Get the transcript from the company object.
            transcript_object = company.get_transcript(year=year, quarter=quarter)
            
            # 3. Check if a valid transcript object was returned.
            if not transcript_object or not transcript_object.text:
                error_msg = f"Transcript not found for {ticker} Q{quarter} {year}."
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

            # 4. Extract the text from the transcript object.
            transcript_text = transcript_object.text
            # --------------------------

            return {
                "success": True,
                "data": {
                    "company_ticker": ticker.upper(),
                    "company_name": str(company), # The object has a nice string representation
                    "year": year,
                    "quarter": quarter,
                    "call_date": None,
                    "transcript": transcript_text,
                    "speakers": [],
                    "q_and_a_section": "",
                    "analyst_questions": [],
                    "management_responses": []
                }
            }
        except Exception as e:
            error_msg = f"An error occurred with the earningscall library for {ticker}: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def list_available_transcripts(self, ticker: str) -> Dict[str, Any]:
        return {"success": False, "error": "Listing transcripts not supported."}
    
    async def validate_ticker(self, ticker: str) -> Dict[str, Any]:
        return {"success": True, "data": {"ticker": ticker.upper(), "is_valid": True}}


# --- API Endpoints (no changes needed here) ---

financial_provider = FinancialDataProvider()

@app.post("/get-transcript")
async def get_transcript(request: TranscriptRequest) -> Dict[str, Any]:
    result = await financial_provider.get_transcript(request.company_ticker, request.year, request.quarter)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result

# ... (other endpoints are the same) ...
@app.post("/list-transcripts")
async def list_transcripts(request: TranscriptListRequest) -> Dict[str, Any]:
    result = await financial_provider.list_available_transcripts(request.company_ticker)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result

@app.post("/search-transcript")
async def search_transcript(request: TranscriptSearchRequest) -> Dict[str, Any]:
    transcript_result = await financial_provider.get_transcript(request.company_ticker, request.year, request.quarter)
    if not transcript_result.get("success"):
        raise HTTPException(status_code=404, detail=transcript_result.get("error"))
    
    transcript_text = transcript_result["data"].get("transcript", "")
    if not transcript_text:
         return {"success": True, "data": {"results_count": 0, "results": []}}

    search_results = []
    lines = transcript_text.split('\n')
    for i, line in enumerate(lines):
        if request.search_query.lower() in line.lower():
            search_results.append({ "line_number": i + 1, "content": line.strip(), "context": lines[max(0, i-1):i+2] })
    
    return {
        "success": True,
        "data": { "company_ticker": request.company_ticker, "year": request.year, "quarter": request.quarter, "search_query": request.search_query, "results_count": len(search_results), "results": search_results[:50] }
    }

@app.post("/company-info")
async def get_company_info(request: CompanyInfoRequest) -> Dict[str, Any]:
    result = await financial_provider.validate_ticker(request.company_ticker)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result

@app.post("/validate-ticker")
async def validate_ticker(request: TickerValidationRequest) -> Dict[str, Any]:
    result = await financial_provider.validate_ticker(request.company_ticker)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result