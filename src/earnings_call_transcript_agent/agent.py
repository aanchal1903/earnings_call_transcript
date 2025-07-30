"""
agents/earnings_call_transcript_agent/src/earnings_call_transcript_agent/agent.py

Defines the core ADK LlmAgent and MCP toolset for the Earnings Call Transcript service.
This agent handles the end-to-end workflow for fetching and providing full, speaker-diarized 
transcripts of corporate earnings calls for any specified public company and quarter.
"""

import logging
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from config.config import settings
from utils.prompts_loader import load_prompt_file

logger = logging.getLogger(__name__)

def build_agent() -> LlmAgent:
    """
    Constructs and configures the Earnings Call Transcript LlmAgent.
    
    Returns:
        A fully configured LlmAgent instance.
    """
    mcp_host = (
        settings.EARNINGS_CALL_MCP_SERVICE_NAME
        if settings.APP_ENVIRONMENT == "docker"
        else "127.0.0.1"
    )
    mcp_port = settings.EARNINGS_CALL_MCP_PORT_INTERNAL
    mcp_server_url = f"http://{mcp_host}:{mcp_port}/mcp"
    
    logger.info(f"Earnings Call Transcript ADK Agent will connect to its MCP tool server at: {mcp_server_url}")
    
    earnings_call_tool_filter = [
        "get_transcript"
    ]
    
    toolset = MCPToolset(
        connection_params=SseConnectionParams(url=mcp_server_url),
        tool_filter=earnings_call_tool_filter,
    )
    
    instruction_prompt = load_prompt_file("earnings_call_agent_prompt.yaml")["instruction"]
    
    agent = LlmAgent(
        name="EarningsCallTranscriptAgent",
        model="gemini-2.5-flash",
        description=(
            "A specialized agent that fetches and provides full, speaker-diarized transcripts "
            "of corporate earnings calls for any specified public company and quarter. "
            "Unlocks qualitative insights by providing direct access to management's tone, "
            "unscripted answers in Q&A, and forward-looking guidance."
        ),
        instruction=instruction_prompt,
        tools=[toolset],
    )
    
    logger.info(f"LlmAgent '{agent.name}' has been built with {len(earnings_call_tool_filter)} tools.")
    return agent

earnings_call_transcript_agent: LlmAgent = build_agent()