"""
agents/earnings_call_transcript_agent/src/earnings_call_transcript_agent/server.py

Defines the main server for the Earnings Call Transcript Agent's A2A service.
This script constructs the agent's public-facing AgentCard, initializes the
A2A Starlette application with the agent's executor, and defines the main
function to launch the Uvicorn server.
"""

import logging
import uvicorn
from typing import List
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities, AgentProvider
from fastapi.responses import JSONResponse
from config.config import settings
from earnings_call_transcript_agent.agent_executor import EarningsCallTranscriptAgentExecutor 

logger = logging.getLogger(__name__)

def create_agent_card() -> AgentCard:
    """
    Builds and returns the public AgentCard for the Earnings Call Transcript Agent.
    The card advertises the agent's identity, capabilities, and how to
    communicate with it, following the A2A specification.
    
    Returns:
        A fully configured AgentCard instance.
    """
    skill = AgentSkill(
        id="earnings_call_transcript_retrieval",
        name="Earnings Call Transcript Retrieval and Analysis",
        description=(
            "Fetches and provides full, speaker-diarized transcripts of corporate earnings calls "
            "for any specified public company and quarter. Unlocks qualitative insights by providing "
            "direct access to management's tone, unscripted answers in Q&A, and forward-looking guidance."
        ),
        tags=["earnings", "transcripts", "financial-research", "qualitative-analysis", "corporate-calls"],
        examples=[
            "Get me the transcript for Microsoft's Q4 2023 earnings call.",
            "List all available earnings call dates for Apple in 2023.",
            "Who were the analysts that asked questions during the last Tesla earnings call?",
            "Search for mentions of 'AI' in Google's Q2 2024 earnings call.",
            "What did the CEO say about future guidance in Amazon's latest earnings call?"
        ],
    )
    
    return AgentCard(
        name="Earnings Call Transcript Agent",
        description=(
            "A specialized financial research agent that fetches and provides full, speaker-diarized "
            "transcripts of corporate earnings calls for any specified public company and quarter. "
            "Designed for equity researchers, portfolio managers, financial journalists, and "
            "quantitative analysts who need direct access to management commentary and Q&A sessions."
        ),
        url=str(settings.earnings_call_transcript_agent_a2a_url),
        version="1.0.0",
        provider=AgentProvider(
            organization="Intellilens, Inc.",
            url="https://www.intellilens.ai" 
        ),
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )

async def health_check(request):
    """A simple health check endpoint that returns a 200 OK status."""
    return JSONResponse({"status": "ok"})

def main() -> None:
    """Initializes and runs the A2A server for the Earnings Call Transcript Agent."""
    logging.basicConfig(
        level=settings.LOG_LEVEL.upper(),
        format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s'
    )
    
    request_handler = DefaultRequestHandler(
        agent_executor=EarningsCallTranscriptAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    
    server_app = A2AStarletteApplication(
        agent_card=create_agent_card(),
        http_handler=request_handler
    )
    
    app = server_app.build()
    app.add_route("/health", health_check, methods=["GET"])
    
    host = "0.0.0.0" if settings.APP_ENVIRONMENT == "docker" else "127.0.0.1"
    port = settings.EARNINGS_CALL_TRANSCRIPT_A2A_PORT_INTERNAL
    
    logger.info(f"Starting Earnings Call Transcript Agent A2A server on http://{host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=settings.LOG_LEVEL.lower()
    )

if __name__ == "__main__":
    main()