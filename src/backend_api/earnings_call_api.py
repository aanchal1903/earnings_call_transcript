# import re
# import urllib.parse
# from typing import Optional, Dict, Any, List
# import logging
# import os
# from datetime import datetime
# import json

# import requests
# import yfinance as yf
# from bs4 import BeautifulSoup
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# import google.generativeai as genai

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Configure Gemini if available
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# if GOOGLE_API_KEY:
#     genai.configure(api_key=GOOGLE_API_KEY)
#     model = genai.GenerativeModel('gemini-2.0-flash-exp')

# # --- Pydantic Models ---
# class GetTranscriptRequest(BaseModel):
#     """Request model for getting a transcript."""
#     url: Optional[str] = None
#     company_ticker: Optional[str] = None
#     year: Optional[int] = None
#     quarter: Optional[int] = None

# # --- FastAPI App ---
# app = FastAPI(
#     title="LLM-Enhanced Earnings Transcript API",
#     description="Intelligent transcript fetcher using LLM for smart searching.",
#     version="5.0.0",
# )

# # --- EarningsCall API Handler ---
# class EarningsCallAPI:
#     """Handler for EarningsCall.biz API integration."""
    
#     def __init__(self):
#         self.base_url = "https://v2.api.earningscall.biz"
#         self.api_key = os.getenv("EARNINGSCALL_API_KEY", "demo")
#         self.headers = {
#             "X-API-Key": self.api_key,
#             "Accept": "application/json"
#         }
    
#     async def get_transcript(self, ticker: str, year: int, quarter: int) -> Optional[Dict[str, Any]]:
#         """Fetch transcript from EarningsCall API."""
#         try:
#             search_url = f"{self.base_url}/transcripts"
#             params = {
#                 "ticker": ticker.upper(),
#                 "year": year,
#                 "quarter": quarter,
#                 "limit": 1
#             }
            
#             logger.info(f"Searching EarningsCall API for {ticker} Q{quarter} {year}")
#             response = requests.get(search_url, headers=self.headers, params=params, timeout=10)
            
#             if response.status_code in [401, 429]:
#                 logger.warning(f"EarningsCall API: Status {response.status_code}")
#                 return None
            
#             if response.status_code != 200:
#                 return None
            
#             data = response.json()
            
#             if not data or (isinstance(data, dict) and data.get('count', 0) == 0):
#                 return None
            
#             transcripts = data.get('transcripts', [data]) if isinstance(data, dict) else data
#             if not transcripts:
#                 return None
            
#             transcript_data = transcripts[0] if isinstance(transcripts, list) else transcripts
            
#             transcript_text = transcript_data.get('text', '') or transcript_data.get('transcript', '')
#             if not transcript_text:
#                 return None
            
#             return {
#                 "success": True,
#                 "source": "EarningsCall API",
#                 "source_url": f"https://earningscall.biz/transcript/{ticker}/{year}/q{quarter}",
#                 "title": f"{ticker.upper()} Q{quarter} {year} Earnings Call Transcript",
#                 "transcript": transcript_text,
#                 "metadata": transcript_data
#             }
            
#         except Exception as e:
#             logger.error(f"EarningsCall API error: {e}")
#             return None


# class LLMPoweredSearch:
#     """Uses LLM to intelligently search for transcripts."""
    
#     def __init__(self):
#         self.headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
#         }
    
#     async def search_with_llm(self, ticker: str, year: int, quarter: int) -> Optional[Dict[str, Any]]:
#         """Use LLM to intelligently search for transcripts."""
#         if not GOOGLE_API_KEY:
#             # Fallback to enhanced traditional search
#             return await self.enhanced_traditional_search(ticker, year, quarter)
        
#         try:
#             # Get company info
#             company_info = self.get_company_info(ticker)
#             company_name = company_info.get('long_name', ticker)
            
#             # Step 1: Ask LLM to generate search strategies
#             search_prompt = f"""
#             I need to find the earnings call transcript for {company_name} ({ticker}) Q{quarter} {year}.
            
#             Generate 5 different search queries that would help find this transcript on Motley Fool.
#             Consider:
#             - The company might be referred to by full name or ticker
#             - Q4 earnings are often reported in January/February of the following year
#             - Q1: April-May, Q2: July, Q3: October, Q4: January-February (next year)
#             - Try variations like "fourth quarter" vs "Q4"
#             - Some companies have name changes (e.g., Facebook → Meta, Google → Alphabet)
            
#             Examples of actual URLs to understand timing:
#             - Microsoft Q4 2021: July 28, 2021
#             - Apple Q4 2024: October 31, 2024
#             - Alphabet Q4 2024: February 5, 2025
#             - Nvidia Q1 2024: May 24, 2023
            
#             Return ONLY the search queries, one per line, no explanations.
#             """
            
#             response = model.generate_content(search_prompt)
#             search_queries = [q.strip() for q in response.text.strip().split('\n') if q.strip()]
            
#             logger.info(f"LLM generated {len(search_queries)} search queries")
            
#             # Try each search query
#             for query in search_queries[:5]:  # Limit to 5 queries
#                 result = await self.search_motley_fool(query, ticker, year, quarter)
#                 if result and result.get("success"):
#                     return result
            
#             # Step 2: If search fails, ask LLM to analyze why and suggest URLs
#             analysis_prompt = f"""
#             I couldn't find {company_name} ({ticker}) Q{quarter} {year} earnings transcript on Motley Fool through search.
            
#             Based on these Motley Fool URL patterns, suggest 3 possible direct URLs where this transcript might be located:
            
#             Examples:
#             - Microsoft Q4 2021: /2021/07/28/microsoft-msft-q4-2021-earnings-call-transcript/
#             - Apple Q4 2024: /2024/10/31/apple-aapl-q4-2024-earnings-call-transcript/
#             - Meta Q3 2024: /2024/10/30/meta-platforms-meta-q3-2024-earnings-call-transcri/
#             - IBM Q2 2023: /2023/07/19/international-business-machines-ibm-q2-2023-earnin/
#             - Alphabet Q4 2024: /2025/02/05/alphabet-goog-q4-2024-earnings-call-transcript/
#             - Alphabet Q1 2024: /2024/04/25/alphabet-googl-q1-2024-earnings-call-transcript/
#             - Nvidia Q1 2023: /2022/05/26/nvidia-nvda-q1-2023-earnings-call-transcript/
#             - Nvidia Q1 2024: /2023/05/24/nvidia-nvda-q1-2024-earnings-call-transcript/
            
#             Patterns to note:
#             - Q1: April-May
#             - Q2: July
#             - Q3: October  
#             - Q4: January-February of NEXT year
#             - URLs sometimes get truncated
#             - Company names vary (e.g., meta-platforms vs facebook, international-business-machines vs ibm)
            
#             Return ONLY the URLs, one per line, starting with https://www.fool.com
#             """
            
#             response = model.generate_content(analysis_prompt)
#             urls = [url.strip() for url in response.text.strip().split('\n') if url.strip().startswith('http')]
            
#             logger.info(f"LLM suggested {len(urls)} direct URLs")
            
#             # Try suggested URLs
#             for url in urls[:3]:
#                 try:
#                     result = self.scrape_fool_transcript(url)
#                     if result.get("success"):
#                         # Verify it's the right transcript
#                         if self.verify_transcript(result.get("transcript", ""), ticker, year, quarter):
#                             result["search_method"] = "llm_suggested_url"
#                             return result
#                 except:
#                     continue
                    
#         except Exception as e:
#             logger.error(f"LLM search error: {e}")
        
#         # Fallback to traditional search
#         return await self.enhanced_traditional_search(ticker, year, quarter)
    
#     async def search_motley_fool(self, query: str, ticker: str, year: int, quarter: int) -> Optional[Dict[str, Any]]:
#         """Search Motley Fool with a specific query."""
#         try:
#             encoded_query = urllib.parse.quote_plus(query)
#             search_url = f"https://www.fool.com/search/?q={encoded_query}"
            
#             logger.info(f"Searching with: {query}")
#             response = requests.get(search_url, headers=self.headers, timeout=20)
            
#             if response.status_code != 200:
#                 return None
            
#             soup = BeautifulSoup(response.content, 'html.parser')
            
#             # Find all links that might be transcripts
#             potential_links = []
#             for link in soup.find_all('a', href=True):
#                 href = link.get('href', '')
#                 if '/earnings/call-transcripts/' in href:
#                     full_url = href if href.startswith('http') else f"https://www.fool.com{href}"
#                     text = link.get_text(strip=True)
#                     potential_links.append((full_url, text))
            
#             # If we have LLM, ask it to pick the best match
#             if GOOGLE_API_KEY and potential_links:
#                 links_text = "\n".join([f"{i+1}. {text} - {url}" for i, (url, text) in enumerate(potential_links[:10])])
                
#                 selection_prompt = f"""
#                 Which of these links is most likely the earnings transcript for {ticker} Q{quarter} {year}?
                
#                 {links_text}
                
#                 Return ONLY the number (1-{len(potential_links[:10])}) of the best match, or 0 if none match.
#                 """
                
#                 try:
#                     response = model.generate_content(selection_prompt)
#                     selection = int(response.text.strip())
                    
#                     if 1 <= selection <= len(potential_links):
#                         url = potential_links[selection-1][0]
#                         result = self.scrape_fool_transcript(url)
#                         if result.get("success"):
#                             result["search_method"] = "llm_assisted_search"
#                             return result
#                 except:
#                     pass
            
#             # Fallback: try all links
#             for url, _ in potential_links[:5]:
#                 result = self.scrape_fool_transcript(url)
#                 if result.get("success") and self.verify_transcript(result.get("transcript", ""), ticker, year, quarter):
#                     result["search_method"] = "traditional_search"
#                     return result
                    
#         except Exception as e:
#             logger.error(f"Search error: {e}")
        
#         return None
    
#     def verify_transcript(self, transcript: str, ticker: str, year: int, quarter: int) -> bool:
#         """Verify that a transcript matches what we're looking for."""
#         if not transcript:
#             return False
        
#         transcript_lower = transcript.lower()
        
#         # Must contain ticker
#         if ticker.lower() not in transcript_lower:
#             return False
        
#         # Must contain year
#         if str(year) not in transcript:
#             return False
        
#         # Should contain quarter reference
#         quarter_terms = [f"q{quarter}", f"quarter {quarter}", "fourth quarter" if quarter == 4 else f"quarter {quarter}"]
#         if not any(term in transcript_lower for term in quarter_terms):
#             return False
        
#         return True
    
#     async def enhanced_traditional_search(self, ticker: str, year: int, quarter: int) -> Optional[Dict[str, Any]]:
#         """Enhanced traditional search without LLM."""
#         company_info = self.get_company_info(ticker)
#         company_name = company_info.get('long_name', ticker)
        
#         # Try multiple search strategies
#         search_strategies = [
#             f'"{ticker}" "Q{quarter} {year}" earnings transcript',
#             f'{company_name} Q{quarter} {year} earnings call',
#             f'{ticker} {["first", "second", "third", "fourth"][quarter-1]} quarter {year}',
#             f'"{ticker}" "{year}" "Q{quarter}" site:fool.com'
#         ]
        
#         for query in search_strategies:
#             result = await self.search_motley_fool(query, ticker, year, quarter)
#             if result:
#                 return result
        
#         return None
    
#     def get_company_info(self, ticker: str) -> Dict[str, Any]:
#         """Get company info from yfinance."""
#         try:
#             stock = yf.Ticker(ticker)
#             info = stock.info
#             return {
#                 'long_name': info.get('longName', ticker),
#                 'short_name': info.get('shortName', ticker)
#             }
#         except:
#             return {'long_name': ticker, 'short_name': ticker}
    
#     def scrape_fool_transcript(self, url: str) -> Dict[str, Any]:
#         """Scrape Motley Fool transcript."""
#         try:
#             response = requests.get(url, headers=self.headers, timeout=20)
#             response.raise_for_status()
#             soup = BeautifulSoup(response.content, 'html.parser')
            
#             # Find article content
#             content_selectors = [
#                 '#article-body', '.article-body', '.tailwind-article-body', 
#                 'article', '[data-id="article-body"]'
#             ]
            
#             article_content = None
#             for selector in content_selectors:
#                 article_content = soup.select_one(selector)
#                 if article_content:
#                     break
            
#             if not article_content:
#                 return {"success": False, "error": "Could not find article content"}
            
#             full_text = article_content.get_text(separator='\n', strip=True)
#             cleaned_text = re.sub(r'\n\s*\n+', '\n\n', full_text)
            
#             title = soup.find('title')
#             title_text = title.get_text(strip=True) if title else "Earnings Call Transcript"
            
#             return {
#                 "success": True,
#                 "source": "Motley Fool",
#                 "source_url": url,
#                 "title": title_text,
#                 "transcript": cleaned_text
#             }
            
#         except Exception as e:
#             return {"success": False, "error": f"Failed to scrape: {str(e)}"}


# # Initialize handlers
# earnings_call_api = EarningsCallAPI()
# llm_search = LLMPoweredSearch()

# # --- Main API Endpoint ---

# @app.post("/get-transcript")
# async def get_transcript(request: GetTranscriptRequest):
#     """
#     Fetches transcript with intelligent LLM-powered search:
#     1. EarningsCall API (free tier)
#     2. LLM-powered intelligent search on Motley Fool
#     3. User-provided URL (fallback)
#     """
    
#     # If user provides direct URL, use it
#     if request.url:
#         logger.info(f"Using user-provided URL: {request.url}")
        
#         if "fool.com" in request.url:
#             result = llm_search.scrape_fool_transcript(request.url)
#         else:
#             # Generic scraping for other sites
#             result = llm_search.scrape_fool_transcript(request.url)
        
#         if result.get("success"):
#             result["message"] = "Successfully retrieved transcript from provided URL"
#         return result
    
#     # Validate required parameters
#     if not (request.company_ticker and request.year and request.quarter):
#         return {
#             "success": False,
#             "error": "Please provide either (1) company ticker, year, and quarter OR (2) a direct URL"
#         }
    
#     ticker = request.company_ticker.upper()
#     year = request.year
#     quarter = request.quarter
    
#     logger.info(f"Starting search for {ticker} Q{quarter} {year}")
    
#     # Step 1: Try EarningsCall API
#     logger.info("Step 1: Trying EarningsCall API...")
#     earnings_call_result = await earnings_call_api.get_transcript(ticker, year, quarter)
    
#     if earnings_call_result and earnings_call_result.get("success"):
#         logger.info("Successfully retrieved from EarningsCall API")
#         earnings_call_result["message"] = "Retrieved from EarningsCall API (free tier)"
#         return earnings_call_result
    
#     # Step 2: LLM-powered search
#     logger.info("Step 2: Using intelligent search...")
#     search_result = await llm_search.search_with_llm(ticker, year, quarter)
    
#     if search_result and search_result.get("success"):
#         logger.info(f"Successfully found via {search_result.get('search_method', 'search')}")
#         search_result["message"] = f"Retrieved via intelligent search"
#         return search_result
    
#     # Step 3: Ask user for URL
#     logger.info("All automatic methods failed")
    
#     return {
#         "success": False,
#         "error": f"Could not find transcript for {ticker} Q{quarter} {year}",
#         "fallback_message": (
#             f"I couldn't find the earnings transcript for {ticker} Q{quarter} {year}. "
#             f"Please provide a direct URL to the transcript from any source."
#         ),
#         "search_attempts": [
#             "EarningsCall API",
#             "Intelligent LLM-powered search" if GOOGLE_API_KEY else "Enhanced traditional search"
#         ],
#         "suggestion": "Please provide a direct URL to the transcript"
#     }


# @app.get("/health")
# async def health_check():
#     """Health check endpoint."""
#     return {
#         "status": "healthy",
#         "service": "llm-enhanced-transcript-api",
#         "version": "5.0.0",
#         "features": {
#             "earningscall_api": "enabled",
#             "llm_search": "enabled" if GOOGLE_API_KEY else "disabled (using traditional search)",
#             "gemini_model": "gemini-2.0-flash-exp" if GOOGLE_API_KEY else "not configured"
#         }
#     }

from dotenv import load_dotenv

load_dotenv() 

import re
import urllib.parse
from typing import Optional, Dict, Any, List
import logging
import os
from datetime import datetime
import json
import traceback

import requests
import yfinance as yf
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
logger.info(f"Google API Key configured: {bool(GOOGLE_API_KEY)}")

if GOOGLE_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("Gemini model initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini: {e}")
        GOOGLE_API_KEY = None
else:
    logger.warning("No Google API key found - LLM features disabled")

# --- Pydantic Models ---
class GetTranscriptRequest(BaseModel):
    url: Optional[str] = None
    company_ticker: Optional[str] = None
    year: Optional[int] = None
    quarter: Optional[int] = None

# --- FastAPI App ---
app = FastAPI(
    title="Fixed Earnings Transcript API",
    description="Debugged version with better error handling",
    version="5.1.0",
)

# --- EarningsCall API Handler ---
class EarningsCallAPI:
    def __init__(self):
        self.base_url = "https://v2.api.earningscall.biz"
        self.api_key = os.getenv("EARNINGSCALL_API_KEY", "demo")
        self.headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json"
        }
        logger.info(f"EarningsCall API initialized with key: {self.api_key[:4]}...")
    
    async def get_transcript(self, ticker: str, year: int, quarter: int) -> Optional[Dict[str, Any]]:
        try:
            search_url = f"{self.base_url}/transcripts"
            params = {
                "ticker": ticker.upper(),
                "year": year,
                "quarter": quarter,
                "limit": 1
            }
            
            logger.debug(f"EarningsCall API request: {search_url} with params {params}")
            response = requests.get(search_url, headers=self.headers, params=params, timeout=10)
            logger.debug(f"EarningsCall API response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"EarningsCall API returned {response.status_code}")
                return None
            
            data = response.json()
            logger.debug(f"EarningsCall API response: {json.dumps(data)[:200]}...")
            
            if not data:
                return None
            
            # Handle response format
            transcripts = data if isinstance(data, list) else data.get('transcripts', [])
            if not transcripts:
                return None
            
            transcript_data = transcripts[0] if transcripts else None
            if not transcript_data:
                return None
            
            transcript_text = (
                transcript_data.get('text', '') or 
                transcript_data.get('transcript', '') or
                transcript_data.get('content', '')
            )
            
            if transcript_text:
                logger.info(f"EarningsCall API: Found transcript ({len(transcript_text)} chars)")
                return {
                    "success": True,
                    "source": "EarningsCall API",
                    "source_url": f"https://earningscall.biz/transcript/{ticker}/{year}/q{quarter}",
                    "title": f"{ticker.upper()} Q{quarter} {year} Earnings Call Transcript",
                    "transcript": transcript_text
                }
            
        except Exception as e:
            logger.error(f"EarningsCall API error: {e}")
            logger.debug(traceback.format_exc())
        
        return None


class MotleyFoolSearch:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_company_info(self, ticker: str) -> Dict[str, Any]:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                'long_name': info.get('longName', ticker),
                'short_name': info.get('shortName', ticker)
            }
        except:
            return {'long_name': ticker, 'short_name': ticker}
    
    async def search_with_llm(self, ticker: str, year: int, quarter: int) -> Optional[Dict[str, Any]]:
        """Use LLM to find transcripts."""
        if not GOOGLE_API_KEY:
            logger.warning("LLM search requested but no API key")
            return await self.fallback_search(ticker, year, quarter)
        
        try:
            logger.info(f"Starting LLM search for {ticker} Q{quarter} {year}")
            
            # First, try direct URL construction based on patterns
            logger.debug("Trying known URL patterns...")
            direct_urls = self.construct_likely_urls(ticker, year, quarter)
            
            for url in direct_urls[:5]:
                logger.debug(f"Trying URL: {url}")
                result = await self.try_url(url)
                if result:
                    logger.info(f"Success with direct URL: {url}")
                    result["search_method"] = "pattern_matching"
                    return result
            
            # If that fails, use LLM to generate search queries
            company_info = self.get_company_info(ticker)
            company_name = company_info.get('long_name', ticker)
            
            search_prompt = f"""Generate 5 search queries to find {company_name} ({ticker}) Q{quarter} {year} earnings transcript on Motley Fool.

Consider:
- Q1: April-May, Q2: July, Q3: October, Q4: January-February (next year)
- Microsoft Q4 2021 was on July 28, 2021
- Try variations like "Q4" vs "fourth quarter"

Return only the queries, one per line."""
            
            logger.debug("Asking LLM for search queries...")
            response = model.generate_content(search_prompt)
            queries = [q.strip() for q in response.text.strip().split('\n') if q.strip()][:5]
            
            logger.info(f"LLM generated {len(queries)} search queries")
            
            # Try each query
            for query in queries:
                result = await self.search_motley_fool(query, ticker, year, quarter)
                if result:
                    return result
            
            # If search fails, ask LLM for direct URLs
            url_prompt = f"""Based on these Motley Fool URL examples:
- Microsoft Q4 2021: https://www.fool.com/earnings/call-transcripts/2021/07/28/microsoft-msft-q4-2021-earnings-call-transcript/
- Apple Q4 2024: https://www.fool.com/earnings/call-transcripts/2024/10/31/apple-aapl-q4-2024-earnings-call-transcript/
- Alphabet Q4 2024: https://www.fool.com/earnings/call-transcripts/2025/02/05/alphabet-goog-q4-2024-earnings-call-transcript/

Generate 3 possible URLs for {company_name} ({ticker}) Q{quarter} {year}.
Return only the complete URLs, one per line."""
            
            logger.debug("Asking LLM for direct URLs...")
            response = model.generate_content(url_prompt)
            urls = [u.strip() for u in response.text.strip().split('\n') if u.strip().startswith('http')][:3]
            
            for url in urls:
                result = await self.try_url(url)
                if result:
                    logger.info(f"Success with LLM-suggested URL: {url}")
                    result["search_method"] = "llm_url_suggestion"
                    return result
                    
        except Exception as e:
            logger.error(f"LLM search error: {e}")
            logger.debug(traceback.format_exc())
        
        # Final fallback
        return await self.fallback_search(ticker, year, quarter)
    
    def construct_likely_urls(self, ticker: str, year: int, quarter: int) -> List[str]:
        """Construct URLs based on known patterns."""
        urls = []
        
        # Known patterns
        patterns = {
            1: [(4, 20, 30), (5, 1, 31)],
            2: [(7, 15, 31)],
            3: [(10, 15, 31)],
            4: [(1, 15, 31), (2, 1, 15)]
        }
        
        company_names = {
            "MSFT": ["microsoft"],
            "AAPL": ["apple"],
            "GOOGL": ["alphabet", "google"],
            "META": ["meta-platforms", "facebook"],
            "IBM": ["ibm", "international-business-machines"],
            "NVDA": ["nvidia"]
        }.get(ticker.upper(), [ticker.lower()])
        
        for month, start, end in patterns.get(quarter, []):
            report_year = year + 1 if quarter == 4 else year
            
            for day in range(start, min(end + 1, 32)):
                for name in company_names:
                    urls.append(
                        f"https://www.fool.com/earnings/call-transcripts/{report_year}/"
                        f"{month:02d}/{day:02d}/{name}-{ticker.lower()}-q{quarter}-{year}-"
                        f"earnings-call-transcript/"
                    )
        
        return urls
    
    async def try_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Try to fetch and validate a specific URL."""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                result = self.scrape_fool_transcript(url, response.text)
                if result.get("success"):
                    return result
        except:
            pass
        return None
    
    async def search_motley_fool(self, query: str, ticker: str, year: int, quarter: int) -> Optional[Dict[str, Any]]:
        """Search Motley Fool with a query."""
        try:
            encoded_query = urllib.parse.quote_plus(query)
            search_url = f"https://www.fool.com/search/?q={encoded_query}"
            
            logger.debug(f"Searching: {query}")
            response = requests.get(search_url, headers=self.headers, timeout=20)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all transcript links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/earnings/call-transcripts/' in href:
                    full_url = href if href.startswith('http') else f"https://www.fool.com{href}"
                    
                    # Quick validation
                    if (ticker.lower() in href.lower() and 
                        str(year) in href and 
                        f'q{quarter}' in href.lower()):
                        
                        result = await self.try_url(full_url)
                        if result:
                            result["search_method"] = "search"
                            return result
                            
        except Exception as e:
            logger.error(f"Search error: {e}")
        
        return None
    
    async def fallback_search(self, ticker: str, year: int, quarter: int) -> Optional[Dict[str, Any]]:
        """Traditional search without LLM."""
        logger.info(f"Using fallback search for {ticker} Q{quarter} {year}")
        
        company_info = self.get_company_info(ticker)
        queries = [
            f"{ticker} Q{quarter} {year} earnings transcript",
            f'"{ticker}" "Q{quarter}" "{year}" site:fool.com',
            f"{company_info['long_name']} {year} Q{quarter}"
        ]
        
        for query in queries:
            result = await self.search_motley_fool(query, ticker, year, quarter)
            if result:
                return result
        
        return None
    
    def scrape_fool_transcript(self, url: str, html: str = None) -> Dict[str, Any]:
        """Scrape Motley Fool transcript."""
        try:
            if not html:
                response = requests.get(url, headers=self.headers, timeout=20)
                response.raise_for_status()
                html = response.text
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find content
            content = None
            for selector in ['#article-body', '.article-body', '.tailwind-article-body', 'article']:
                content = soup.select_one(selector)
                if content:
                    break
            
            if not content:
                return {"success": False, "error": "No content found"}
            
            text = content.get_text(separator='\n', strip=True)
            text = re.sub(r'\n\s*\n+', '\n\n', text)
            
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else "Earnings Call Transcript"
            
            return {
                "success": True,
                "source": "Motley Fool",
                "source_url": url,
                "title": title_text,
                "transcript": text
            }
            
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return {"success": False, "error": str(e)}


# Initialize services
earnings_call_api = EarningsCallAPI()
motley_fool = MotleyFoolSearch()

@app.post("/get-transcript")
async def get_transcript(request: GetTranscriptRequest):
    """Get transcript with better error handling."""
    
    # Direct URL provided
    if request.url:
        logger.info(f"Using provided URL: {request.url}")
        result = motley_fool.scrape_fool_transcript(request.url)
        if result.get("success"):
            result["message"] = "Retrieved from provided URL"
        return result
    
    # Validate parameters
    if not (request.company_ticker and request.year and request.quarter):
        return {
            "success": False,
            "error": "Please provide ticker, year, and quarter OR a direct URL"
        }
    
    ticker = request.company_ticker.upper()
    year = request.year
    quarter = request.quarter
    
    logger.info(f"=== Starting search for {ticker} Q{quarter} {year} ===")
    
    # Step 1: EarningsCall API
    logger.info("Step 1: Checking EarningsCall API...")
    ec_result = await earnings_call_api.get_transcript(ticker, year, quarter)
    
    if ec_result and ec_result.get("success"):
        logger.info("✓ Found on EarningsCall API")
        ec_result["message"] = "Retrieved from EarningsCall API"
        return ec_result
    else:
        logger.info("✗ Not found on EarningsCall API")
    
    # Step 2: Motley Fool search
    logger.info("Step 2: Searching Motley Fool...")
    mf_result = await motley_fool.search_with_llm(ticker, year, quarter)
    
    if mf_result and mf_result.get("success"):
        logger.info(f"✓ Found on Motley Fool via {mf_result.get('search_method')}")
        mf_result["message"] = f"Retrieved from Motley Fool ({mf_result.get('search_method', 'search')})"
        return mf_result
    else:
        logger.info("✗ Not found on Motley Fool")
    
    # All methods failed
    logger.info("=== All search methods failed ===")
    
    return {
        "success": False,
        "error": f"Could not find transcript for {ticker} Q{quarter} {year}",
        "fallback_message": (
            f"I couldn't find the earnings transcript for {ticker} Q{quarter} {year}. "
            f"Please provide a direct URL to the transcript."
        ),
        "debug_info": {
            "earningscall_checked": True,
            "motley_fool_checked": True,
            "llm_enabled": bool(GOOGLE_API_KEY)
        }
    }


@app.get("/health")
async def health_check():
    """Health check with debug info."""
    return {
        "status": "healthy",
        "version": "5.1.0",
        "features": {
            "google_api_key": bool(GOOGLE_API_KEY),
            "earningscall_api": earnings_call_api.api_key[:4] + "...",
            "debug": "Check logs for detailed information"
        }
    }


@app.get("/test/{ticker}")
async def test_ticker(ticker: str, year: int = 2021, quarter: int = 4):
    """Quick test endpoint."""
    return await get_transcript(
        GetTranscriptRequest(
            company_ticker=ticker,
            year=year,
            quarter=quarter
        )
    )