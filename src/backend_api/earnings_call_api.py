# """
# agents/earnings_call_transcript_agent/src/backend_api/earnings_call_api.py

# Backend API server for the Earnings Call Transcript Agent.
# This version uses enhanced web scraping with BeautifulSoup to get transcripts from AlphaStreet, Motley Fool, and Seeking Alpha.
# """

# import logging
# import uvicorn
# import re
# import asyncio
# from typing import Dict, Any, List, Optional
# from datetime import datetime
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel, Field
# import httpx
# from bs4 import BeautifulSoup
# import urllib.parse

# # Assuming a config file exists, if not, this part might need adjustment
# # from config.config import settings

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(title="Earnings Call Transcript Backend API", version="1.1.0")

# # --- Pydantic models ---
# class TranscriptRequest(BaseModel):
#     company_ticker: str = Field(..., description="Stock ticker symbol")
#     year: int = Field(..., description="Year of the earnings call")
#     quarter: int = Field(..., ge=1, le=4, description="Quarter (1-4)")

# class TranscriptListRequest(BaseModel):
#     company_ticker: str = Field(..., description="Stock ticker symbol")

# class TranscriptSearchRequest(BaseModel):
#     company_ticker: str = Field(..., description="Stock ticker symbol")
#     year: int = Field(..., description="Year of the earnings call")
#     quarter: int = Field(..., ge=1, le=4, description="Quarter (1-4)")
#     search_query: str = Field(..., description="Text to search for")

# class CompanyInfoRequest(BaseModel):
#     company_ticker: str = Field(..., description="Stock ticker symbol")

# class TickerValidationRequest(BaseModel):
#     company_ticker: str = Field(..., description="Stock ticker symbol to validate")


# class WebScrapingFinancialDataProvider:
#     """
#     Enhanced financial data provider that scrapes earnings call transcripts from multiple sources.
#     """
    
#     def __init__(self):
#         self.headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
#             'Accept-Language': 'en-US,en;q=0.9',
#             'Accept-Encoding': 'gzip, deflate, br',
#             'Connection': 'keep-alive',
#             'Upgrade-Insecure-Requests': '1',
#             'Sec-Fetch-Dest': 'document',
#             'Sec-Fetch-Mode': 'navigate',
#             'Sec-Fetch-Site': 'none',
#             'Cache-Control': 'max-age=0'
#         }
        
#     async def _get_page_content(self, url: str) -> Optional[str]:
#         """Fetch page content with proper error handling and retries."""
#         max_retries = 3
#         for attempt in range(max_retries):
#             try:
#                 timeout = httpx.Timeout(30.0, connect=10.0)
#                 async with httpx.AsyncClient(
#                     timeout=timeout, 
#                     headers=self.headers, 
#                     follow_redirects=True,
#                     verify=False  # Skip SSL verification for some sites
#                 ) as client:
#                     logger.info(f"Fetching URL (attempt {attempt + 1}): {url}")
#                     response = await client.get(url)
                    
#                     logger.info(f"Response status: {response.status_code}")
                    
#                     if response.status_code == 200:
#                         return response.text
#                     elif response.status_code in [403, 429]:
#                         logger.warning(f"Rate limited or forbidden: {response.status_code}")
#                         if attempt < max_retries - 1:
#                             await asyncio.sleep(2 ** attempt)  # Exponential backoff
#                             continue
#                     else:
#                         logger.warning(f"HTTP {response.status_code} for {url}")
                        
#             except httpx.TimeoutException:
#                 logger.error(f"Timeout fetching {url} (attempt {attempt + 1})")
#             except Exception as e:
#                 logger.error(f"Error fetching {url} (attempt {attempt + 1}): {str(e)}")
                
#             if attempt < max_retries - 1:
#                 await asyncio.sleep(1)
        
#         return None
    
#     def _clean_transcript_text(self, text: str) -> str:
#         """Clean and format transcript text."""
#         # Remove extra whitespace and normalize line breaks
#         text = re.sub(r'\n\s*\n+', '\n\n', text)
#         text = re.sub(r'[ \t]+', ' ', text)
#         text = re.sub(r'\r\n', '\n', text)
        
#         # Remove common website artifacts
#         artifacts = [
#             r'Subscribe to our newsletter.*?$',
#             r'Sign up for.*?$',
#             r'Click here.*?$',
#             r'Advertisement.*?$',
#             r'ADVERTISEMENT.*?$',
#             r'Sponsored by.*?$'
#         ]
        
#         for artifact in artifacts:
#             text = re.sub(artifact, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
#         return text.strip()
    
#     def _extract_speakers_and_qa(self, text: str) -> tuple:
#         """Extract speakers and Q&A section from transcript."""
#         speakers = []
#         qa_section = ""
        
#         # Enhanced speaker patterns
#         speaker_patterns = [
#             # Executive titles
#             r'^([A-Z][a-zA-Z\s]+(?:CEO|CFO|CTO|COO|President|Chairman|Director|VP|Vice President|Chief|Officer))\s*[:\-]',
#             # Analyst patterns
#             r'^([A-Z][a-zA-Z\s]+ (?:Analyst|Research))\s*[:\-]',
#             # Name patterns
#             r'^([A-Z][a-zA-Z]+ [A-Z][a-zA-Z]+)\s*[:\-]',
#             # Operator
#             r'^(Operator)\s*[:\-]',
#             # Company representatives
#             r'^([A-Z][A-Z\s]{2,20})\s*[:\-]'
#         ]
        
#         lines = text.split('\n')
#         for line in lines:
#             line_stripped = line.strip()
#             if len(line_stripped) < 5:
#                 continue
                
#             for pattern in speaker_patterns:
#                 match = re.search(pattern, line_stripped)
#                 if match:
#                     speaker = match.group(1).strip()
#                     # Filter out false positives
#                     if (len(speaker) > 2 and len(speaker) < 50 and 
#                         speaker not in speakers and
#                         not any(word in speaker.lower() for word in ['the', 'and', 'this', 'that', 'said', 'will'])):
#                         speakers.append(speaker)
        
#         # Enhanced Q&A section detection
#         qa_indicators = [
#             'questions and answers',
#             'question-and-answer',
#             'q&a session',
#             'q&a',
#             'analyst questions',
#             'questions from analysts',
#             'now we will begin the question'
#         ]
        
#         text_lower = text.lower()
#         best_qa_start = -1
        
#         for indicator in qa_indicators:
#             pos = text_lower.find(indicator)
#             if pos != -1 and (best_qa_start == -1 or pos < best_qa_start):
#                 best_qa_start = pos
        
#         if best_qa_start != -1:
#             qa_section = text[best_qa_start:]
#             # Limit Q&A section to reasonable length
#             if len(qa_section) > 5000:
#                 qa_section = qa_section[:5000] + "..."
        
#         return speakers[:15], qa_section  # Limit to first 15 speakers
    
#     def _is_valid_transcript_content(self, text: str, ticker: str, year: int) -> bool:
#         """
#         Validate if the scraped content is actually a transcript.
#         Enhanced to better distinguish transcripts from listing pages.
#         """
#         if not text or len(text) < 1000: # Increased minimum length
#             logger.warning("Content too short to be a transcript.")
#             return False
        
#         text_lower = text.lower()
#         ticker_lower = ticker.lower()
        
#         # Must contain company ticker
#         if ticker_lower not in text_lower:
#             logger.warning("Ticker not found in content.")
#             return False
        
#         # Must contain earnings-related terms
#         earnings_terms = ['earnings', 'quarterly', 'revenue', 'profit', 'financial results', 'conference call']
#         if not any(term in text_lower for term in earnings_terms):
#             logger.warning("Earnings-related terms not found.")
#             return False
        
#         # Must contain the year
#         if str(year) not in text:
#             logger.warning(f"Year '{year}' not found in content.")
#             return False
        
#         # CRITICAL CHECK: Must contain multiple speaker indicators to differentiate from a list.
#         # A real transcript has many speakers. A listing page has few or none.
#         speaker_indicators = ['operator:', 'analyst', 'ceo', 'cfo', 'management', 'question:', 'answer:']
#         speaker_count = sum(1 for indicator in speaker_indicators if indicator in text_lower)
        
#         # Check for multiple lines that look like a speaker is talking (e.g., "Name Name:")
#         # This is a strong signal of a real transcript.
#         speaker_line_matches = re.findall(r'^[A-Z][a-zA-Z\s\.\-]{5,40}:', text, re.MULTILINE)
        
#         if speaker_count < 2 and len(speaker_line_matches) < 5:
#             logger.warning(f"Not enough speaker indicators found (found {speaker_count} keywords, {len(speaker_line_matches)} line matches). Likely a listing page.")
#             return False

#         # Should not be mostly marketing content
#         marketing_terms = ['join a growing list', 'subscribe to our newsletter', 'sign up for', 'view all transcripts']
#         marketing_count = sum(1 for term in marketing_terms if term in text_lower)
#         if marketing_count > 2:
#             logger.warning("Content appears to be mostly marketing material or a listing page.")
#             return False
        
#         logger.info("Content validation passed.")
#         return True

#     async def _scrape_alphastreet(self, ticker: str, year: int, quarter: int) -> Optional[Dict[str, Any]]:
#         """Enhanced AlphaStreet scraper with multiple URL patterns and better content detection."""
#         try:
#             # Multiple URL patterns to try
#             url_patterns = [
#                 f"https://www.alphastreet.com/earnings-call-transcripts/{ticker.lower()}-q{quarter}-{year}-earnings-call-transcript",
#                 f"https://www.alphastreet.com/earnings-call-transcripts/{ticker.upper()}-Q{quarter}-{year}-earnings-call-transcript",
#                 f"https://www.alphastreet.com/earnings/{ticker.lower()}/q{quarter}-{year}",
#                 f"https://www.alphastreet.com/transcripts/{ticker.lower()}-q{quarter}-{year}",
#                 f"https://www.alphastreet.com/earnings-call-transcript/{ticker.lower()}-{year}-q{quarter}",
#             ]
            
#             for search_url in url_patterns:
#                 logger.info(f"Trying AlphaStreet URL: {search_url}")
#                 content = await self._get_page_content(search_url)
                
#                 if not content:
#                     continue
                
#                 soup = BeautifulSoup(content, 'html.parser')
                
#                 # Log page info for debugging
#                 title = soup.find('title')
#                 title_text = title.get_text() if title else 'No title'
#                 logger.info(f"Page title: {title_text}")
                
#                 # Check for error pages
#                 if any(error in content.lower() for error in ['404', 'not found', 'page not found', 'error occurred']):
#                     logger.info(f"Error page detected for {search_url}")
#                     continue
                
#                 # Enhanced content selectors
#                 transcript_selectors = [
#                     '.transcript-content',
#                     '.earnings-transcript',
#                     '.transcript-text',
#                     'article .content',
#                     '.post-content',
#                     'main .content',
#                     '.article-body',
#                     '#transcript',
#                     '.earnings-content',
#                     '[class*="transcript"]',
#                     '[id*="transcript"]'
#                 ]
                
#                 transcript_text = ""
#                 successful_selector = None
                
#                 for selector in transcript_selectors:
#                     elements = soup.select(selector)
#                     if elements:
#                         candidate_text = '\n'.join([elem.get_text(separator='\n', strip=True) for elem in elements])
                        
#                         if self._is_valid_transcript_content(candidate_text, ticker, year):
#                             transcript_text = candidate_text
#                             successful_selector = selector
#                             logger.info(f"Found valid content with selector '{selector}': {len(transcript_text)} chars")
#                             break
                
#                 # Fallback: try to find transcript in paragraphs
#                 if not transcript_text:
#                     logger.info("Trying paragraph-based extraction...")
                    
#                     # Look for paragraphs that might contain transcript content
#                     paragraphs = soup.find_all('p')
#                     all_p_text = '\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])
                    
#                     if self._is_valid_transcript_content(all_p_text, ticker, year):
#                         transcript_text = all_p_text
#                         successful_selector = 'paragraphs'
#                         logger.info(f"Found valid content in paragraphs: {len(transcript_text)} chars")
                
#                 # If we found valid content, process it
#                 if transcript_text:
#                     logger.info(f"Successfully extracted transcript using {successful_selector}")
                    
#                     # Extract company name
#                     company_name = ticker.upper()
#                     if title_text and ticker.upper() in title_text.upper():
#                         # Try to extract company name from title
#                         title_parts = title_text.split(' - ')
#                         if title_parts:
#                             company_name = title_parts[0].strip()
                    
#                     speakers, qa_section = self._extract_speakers_and_qa(transcript_text)
                    
#                     return {
#                         "source": "AlphaStreet",
#                         "company_name": company_name,
#                         "transcript": self._clean_transcript_text(transcript_text),
#                         "speakers": speakers,
#                         "q_and_a_section": qa_section,
#                         "call_date": None,
#                         "url": search_url
#                     }
#                 else:
#                     logger.warning(f"No valid transcript content found at {search_url}")
            
#             logger.info(f"No valid AlphaStreet transcript found for {ticker} Q{quarter} {year}")
            
#         except Exception as e:
#             logger.error(f"Error scraping AlphaStreet for {ticker}: {str(e)}")
        
#         return None
    
#     async def _scrape_motley_fool(self, ticker: str, year: int, quarter: int) -> Optional[Dict[str, Any]]:
#         """Enhanced Motley Fool scraper."""
#         try:
#             # Search for transcripts on Motley Fool
#             search_queries = [
#                 f"{ticker} Q{quarter} {year} earnings call transcript",
#                 f"{ticker} {year} Q{quarter} earnings transcript",
#                 f"{ticker} quarterly earnings Q{quarter} {year}"
#             ]
            
#             for search_query in search_queries:
#                 logger.info(f"Searching Motley Fool for: {search_query}")
#                 search_url = f"https://www.fool.com/search/?q={urllib.parse.quote(search_query)}"
                
#                 content = await self._get_page_content(search_url)
#                 if not content:
#                     continue
                
#                 soup = BeautifulSoup(content, 'html.parser')
                
#                 # Look for search results
#                 search_results = soup.find_all('a', href=True)
#                 transcript_urls = []
                
#                 for link in search_results:
#                     href = link.get('href')
#                     link_text = link.get_text().lower()
                    
#                     if href and ('transcript' in href.lower() or 'earnings' in href.lower() or 
#                                 'transcript' in link_text or 'earnings' in link_text):
#                         if not href.startswith('http'):
#                             href = f"https://www.fool.com{href}"
#                         if href not in transcript_urls:
#                             transcript_urls.append(href)
                
#                 # Try to fetch promising transcript URLs
#                 for url in transcript_urls[:5]:  # Limit to first 5 results
#                     logger.info(f"Checking Motley Fool transcript URL: {url}")
#                     transcript_content = await self._get_page_content(url)
                    
#                     if not transcript_content:
#                         continue
                    
#                     transcript_soup = BeautifulSoup(transcript_content, 'html.parser')
                    
#                     # Enhanced content selectors for Motley Fool
#                     content_selectors = [
#                         'article .content',
#                         '.article-body',
#                         '.post-content',
#                         'main .content',
#                         '.transcript-content',
#                         '.article-content',
#                         '[class*="article"]',
#                         '.entry-content'
#                     ]
                    
#                     transcript_text = ""
#                     for selector in content_selectors:
#                         elements = transcript_soup.select(selector)
#                         if elements:
#                             candidate_text = '\n'.join([elem.get_text(separator='\n', strip=True) for elem in elements])
                            
#                             if self._is_valid_transcript_content(candidate_text, ticker, year):
#                                 transcript_text = candidate_text
#                                 break
                    
#                     # Fallback to paragraphs
#                     if not transcript_text:
#                         paragraphs = transcript_soup.find_all('p')
#                         all_text = '\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])
                        
#                         if self._is_valid_transcript_content(all_text, ticker, year):
#                             transcript_text = all_text
                    
#                     # If we found valid content
#                     if transcript_text:
#                         logger.info(f"Found valid Motley Fool transcript: {len(transcript_text)} chars")
                        
#                         company_name = ticker.upper()
#                         title_elem = transcript_soup.find('title')
#                         if title_elem:
#                             title_text = title_elem.get_text()
#                             if ticker.upper() in title_text.upper():
#                                 company_name = title_text.split(' - ')[0].strip()
                        
#                         speakers, qa_section = self._extract_speakers_and_qa(transcript_text)
                        
#                         return {
#                             "source": "Motley Fool",
#                             "company_name": company_name,
#                             "transcript": self._clean_transcript_text(transcript_text),
#                             "speakers": speakers,
#                             "q_and_a_section": qa_section,
#                             "call_date": None,
#                             "url": url
#                         }
        
#         except Exception as e:
#             logger.error(f"Error scraping Motley Fool for {ticker}: {str(e)}")
        
#         return None
    
#     async def _scrape_seeking_alpha(self, ticker: str, year: int, quarter: int) -> Optional[Dict[str, Any]]:
#         """
#         Scrapes Seeking Alpha. This is a multi-step process:
#         1. Go to the main transcript listing page for the ticker.
#         2. Find the specific link for the desired year and quarter.
#         3. Navigate to that link and scrape the actual transcript content.
#         This prevents incorrectly scraping the listing page itself.
#         """
#         try:
#             # Step 1: Go to the main listing page for transcripts
#             listing_url = f"https://seekingalpha.com/symbol/{ticker.upper()}/earnings/transcripts"
#             logger.info(f"Trying Seeking Alpha listing URL: {listing_url}")
#             listing_content = await self._get_page_content(listing_url)
            
#             if not listing_content:
#                 logger.warning("Could not fetch Seeking Alpha listing page.")
#                 return None

#             soup = BeautifulSoup(listing_content, 'html.parser')
            
#             # Step 2: Find the correct link on the listing page
#             target_link = None
#             # Define search terms to find the specific transcript link
#             search_terms = [
#                 ticker.upper(),
#                 f"q{quarter}",
#                 str(year),
#                 "earnings call transcript"
#             ]

#             all_links = soup.find_all('a', href=True)
#             for link in all_links:
#                 link_text = link.get_text(strip=True)
#                 # Check if all search terms are in the link's text
#                 if all(term.lower() in link_text.lower() for term in search_terms):
#                     href = link.get('href')
#                     if href.startswith('/article/'):
#                         target_link = f"https://seekingalpha.com{href}"
#                         logger.info(f"Found potential transcript link: {target_link}")
#                         break # Found the most likely link, stop searching
            
#             if not target_link:
#                 logger.warning(f"Could not find a specific link for {ticker} Q{quarter} {year} on Seeking Alpha.")
#                 return None

#             # Step 3: Navigate to the specific transcript page and scrape it
#             logger.info(f"Fetching content from specific transcript URL: {target_link}")
#             transcript_page_content = await self._get_page_content(target_link)
            
#             if not transcript_page_content:
#                 logger.error(f"Failed to fetch content from {target_link}")
#                 return None
            
#             transcript_soup = BeautifulSoup(transcript_page_content, 'html.parser')
            
#             # Use selectors to find the main content body of the transcript
#             content_selectors = [
#                 '[data-test-id="content-container"]',
#                 '.article-content',
#                 '#content-container',
#                 'article',
#                 '.transcript-content'
#             ]
            
#             for selector in content_selectors:
#                 elements = transcript_soup.select(selector)
#                 if elements:
#                     candidate_text = '\n'.join([elem.get_text(separator='\n', strip=True) for elem in elements])
                    
#                     # Use the robust validation function
#                     if self._is_valid_transcript_content(candidate_text, ticker, year):
#                         logger.info(f"Successfully validated and extracted transcript from {target_link}")
#                         speakers, qa_section = self._extract_speakers_and_qa(candidate_text)
                        
#                         return {
#                             "source": "Seeking Alpha",
#                             "company_name": ticker.upper(),
#                             "transcript": self._clean_transcript_text(candidate_text),
#                             "speakers": speakers,
#                             "q_and_a_section": qa_section,
#                             "call_date": None,
#                             "url": target_link # Return the specific URL
#                         }
            
#             logger.warning(f"Found a link for {ticker} Q{quarter} {year}, but failed to extract valid transcript content.")

#         except Exception as e:
#             logger.error(f"Error scraping Seeking Alpha for {ticker}: {str(e)}")
        
#         return None
    
#     async def get_transcript(self, ticker: str, year: int, quarter: int) -> Dict[str, Any]:
#         """Fetch earnings call transcript by trying multiple sources."""
#         try:
#             logger.info(f"Fetching transcript for {ticker} Q{quarter} {year}")
            
#             # Try multiple sources in order of preference
#             sources = [
#                 ("Seeking Alpha", self._scrape_seeking_alpha),
#                 ("AlphaStreet", self._scrape_alphastreet),
#                 ("Motley Fool", self._scrape_motley_fool),
#             ]
            
#             for source_name, scraper_func in sources:
#                 logger.info(f"Trying {source_name} for {ticker} Q{quarter} {year}")
#                 result = await scraper_func(ticker, year, quarter)
                
#                 if result:
#                     logger.info(f"Successfully found transcript from {source_name}")
#                     return {
#                         "success": True,
#                         "data": {
#                             "company_ticker": ticker.upper(),
#                             "company_name": result["company_name"],
#                             "year": year,
#                             "quarter": quarter,
#                             "call_date": result.get("call_date"),
#                             "transcript": result["transcript"],
#                             "speakers": result["speakers"],
#                             "q_and_a_section": result["q_and_a_section"],
#                             "analyst_questions": [],
#                             "management_responses": [],
#                             "source": result["source"],
#                             "source_url": result.get("url")
#                         }
#                     }
#                 else:
#                     logger.info(f"No transcript found from {source_name}")
            
#             error_msg = f"Transcript not found for {ticker} Q{quarter} {year} from any source."
#             logger.error(error_msg)
#             return {"success": False, "error": error_msg}
            
#         except Exception as e:
#             error_msg = f"An error occurred while fetching transcript for {ticker}: {str(e)}"
#             logger.error(error_msg)
#             return {"success": False, "error": error_msg}
    
#     async def list_available_transcripts(self, ticker: str) -> Dict[str, Any]:
#         """List available transcripts (limited functionality with scraping)."""
#         return {
#             "success": True,
#             "data": {
#                 "company_ticker": ticker.upper(),
#                 "available_transcripts": [
#                     "Web scraping-based transcript retrieval",
#                     "Try recent quarters (2023-2024) for better availability",
#                     "Sources: Seeking Alpha, AlphaStreet, Motley Fool",
#                     "Specific availability depends on source content"
#                 ],
#                 "suggested_quarters": [
#                     {"year": 2024, "quarter": 2},
#                     {"year": 2024, "quarter": 1},
#                     {"year": 2023, "quarter": 4},
#                     {"year": 2023, "quarter": 3}
#                 ]
#             }
#         }
    
#     async def validate_ticker(self, ticker: str) -> Dict[str, Any]:
#         """Enhanced ticker validation."""
#         if not ticker or len(ticker) < 1 or len(ticker) > 10:
#             return {"success": False, "error": "Invalid ticker format"}
        
#         # Clean ticker
#         clean_ticker = re.sub(r'[^A-Z0-9]', '', ticker.upper())
        
#         # Basic format validation
#         if not re.match(r'^[A-Z]{1,5}$', clean_ticker):
#             return {"success": False, "error": "Ticker should be 1-5 alphabetic characters"}
        
#         return {
#             "success": True,
#             "data": {
#                 "ticker": clean_ticker,
#                 "is_valid": True,
#                 "note": "Basic format validation - actual transcript availability depends on sources"
#             }
#         }


# # --- API Endpoints ---
# financial_provider = WebScrapingFinancialDataProvider()

# @app.get("/health")
# async def health_check():
#     """Health check endpoint."""
#     return {"status": "healthy", "service": "Earnings Call Transcript API"}

# @app.post("/get-transcript")
# async def get_transcript(request: TranscriptRequest) -> Dict[str, Any]:
#     """Get earnings call transcript for a specific company, year, and quarter."""
#     logger.info(f"API request: get-transcript for {request.company_ticker} Q{request.quarter} {request.year}")
#     result = await financial_provider.get_transcript(request.company_ticker, request.year, request.quarter)
#     if not result["success"]:
#         raise HTTPException(status_code=404, detail=result.get("error"))
#     return result

# @app.post("/list-transcripts")
# async def list_transcripts(request: TranscriptListRequest) -> Dict[str, Any]:
#     """List available transcripts for a company."""
#     result = await financial_provider.list_available_transcripts(request.company_ticker)
#     if not result["success"]:
#         raise HTTPException(status_code=404, detail=result.get("error"))
#     return result

# @app.post("/search-transcript")
# async def search_transcript(request: TranscriptSearchRequest) -> Dict[str, Any]:
#     """Search for specific text within a transcript."""
#     logger.info(f"API request: search-transcript for {request.company_ticker} Q{request.quarter} {request.year}, query: '{request.search_query}'")
    
#     transcript_result = await financial_provider.get_transcript(request.company_ticker, request.year, request.quarter)
#     if not transcript_result.get("success"):
#         raise HTTPException(status_code=404, detail=transcript_result.get("error"))
    
#     transcript_text = transcript_result["data"].get("transcript", "")
#     if not transcript_text:
#          return {"success": True, "data": {"results_count": 0, "results": []}}

#     search_results = []
#     lines = transcript_text.split('\n')
    
#     for i, line in enumerate(lines):
#         if request.search_query.lower() in line.lower():
#             # Get context lines
#             start_context = max(0, i-2)
#             end_context = min(len(lines), i+3)
#             context = lines[start_context:end_context]
            
#             search_results.append({
#                 "line_number": i + 1,
#                 "content": line.strip(),
#                 "context": context,
#                 "match_position": line.lower().find(request.search_query.lower())
#             })
    
#     return {
#         "success": True,
#         "data": {
#             "company_ticker": request.company_ticker,
#             "year": request.year,
#             "quarter": request.quarter,
#             "search_query": request.search_query,
#             "results_count": len(search_results),
#             "results": search_results[:50],  # Limit results
#             "source": transcript_result["data"].get("source")
#         }
#     }

# @app.post("/company-info")
# async def get_company_info(request: CompanyInfoRequest) -> Dict[str, Any]:
#     """Get basic company information."""
#     result = await financial_provider.validate_ticker(request.company_ticker)
#     if not result.get("success"):
#         raise HTTPException(status_code=404, detail=result.get("error"))
#     return result

# @app.post("/validate-ticker")
# async def validate_ticker(request: TickerValidationRequest) -> Dict[str, Any]:
#     """Validate a stock ticker symbol."""
#     result = await financial_provider.validate_ticker(request.company_ticker)
#     if not result.get("success"):
#         raise HTTPException(status_code=404, detail=result.get("error"))
#     return result

# if __name__ == "__main__":
#     logger.info("Starting Earnings Call Transcript Backend API server...")
#     uvicorn.run(app, host="127.0.0.1", port=8082)

import re
import urllib.parse
from typing import Optional, Dict, Any

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

# --- Pydantic Models ---

class GetTranscriptRequest(BaseModel):
    """Request model for getting a transcript by URL."""
    url: str  # The Motley Fool URL

# --- FastAPI App ---

app = FastAPI(
    title="Earnings Transcript Scraper API",
    description="A simple API to scrape earnings call transcripts from The Motley Fool URLs.",
    version="1.0.0",
)

# --- Helper Function ---

def scrape_fool_transcript(url: str) -> dict:
    """Scrapes and parses the earnings call transcript from a Motley Fool URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the main article content using a list of potential selectors
        content_selectors = ['#article-body', '.article-body', '.tailwind-article-body', 'article']
        article_content = next((soup.select_one(s) for s in content_selectors if soup.select_one(s)), None)
        
        if not article_content:
            return {"success": False, "error": "Could not find the main article content on the page."}

        full_text = article_content.get_text(separator='\n', strip=True)
        # Standardize line breaks
        cleaned_text = re.sub(r'\n\s*\n+', '\n\n', full_text)

        # Split the content into summary and the main transcript
        split_keyword = "Full Conference Call Transcript"
        parts = re.split(split_keyword, cleaned_text, maxsplit=1, flags=re.IGNORECASE)
        
        summary_section = parts[0].strip() if len(parts) > 1 else "Summary not found."
        transcript_section = parts[1].strip() if len(parts) > 1 else cleaned_text

        title = soup.find('title').get_text(strip=True) if soup.find('title') else "No Title Found"

        return {
            "success": True,
            "source_url": url,
            "title": title,
            "summary": summary_section,
            "transcript": transcript_section  # Changed from full_transcript to match MCP expectation
        }
    except requests.RequestException as e:
        return {"success": False, "error": f"Failed to fetch or access the URL: {e}"}
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred during scraping: {e}"}


# --- API Endpoints ---

@app.post("/get-transcript")
async def get_transcript(request: GetTranscriptRequest):
    """
    Fetches the transcript from a Motley Fool URL.
    This is the only endpoint the MCP server needs.
    """
    # Validate it's a Motley Fool URL
    if "fool.com" not in request.url:
        return {
            "success": False,
            "error": "URL must be from fool.com"
        }
    
    # Scrape the transcript
    result = scrape_fool_transcript(request.url)
    return result


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "earnings-transcript-backend"}