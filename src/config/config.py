# src/config/config.py

import os
from typing import Optional
from pathlib import Path #
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class Settings:
    """Application settings and configuration."""
    
    # Environment Configuration
    APP_ENVIRONMENT: str = os.getenv("APP_ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    # Port Configuration
    EARNINGS_CALL_TRANSCRIPT_A2A_PORT_INTERNAL: int = int(os.getenv("EARNINGS_CALL_TRANSCRIPT_A2A_PORT_INTERNAL", "8080"))
    EARNINGS_CALL_MCP_PORT_INTERNAL: int = int(os.getenv("EARNINGS_CALL_MCP_PORT_INTERNAL", "8081"))
    EARNINGS_CALL_BACKEND_PORT_INTERNAL: int = int(os.getenv("EARNINGS_CALL_BACKEND_PORT_INTERNAL", "8082"))

    # Service names for Docker environment
    EARNINGS_CALL_MCP_SERVICE_NAME: str = os.getenv("EARNINGS_CALL_MCP_SERVICE_NAME", "earnings-call-mcp-server")
    EARNINGS_CALL_BACKEND_SERVICE_NAME: str = os.getenv("EARNINGS_CALL_BACKEND_SERVICE_NAME", "earnings-call-backend")

    # External API Configuration
    GCP_FINANCIAL_DATA_API_KEY: str = os.getenv("GCP_FINANCIAL_DATA_API_KEY", "your-financial-data-api-key")
    FINANCIAL_DATA_API_BASE_URL: str = os.getenv("FINANCIAL_DATA_API_BASE_URL", "https://api.finnhub.io/api/v1")

    @property
    def earnings_call_transcript_agent_a2a_url(self) -> str:
        """URL for the Earnings Call Transcript Agent A2A service."""
        host = "earnings-call-agent" if self.APP_ENVIRONMENT == "docker" else "127.0.0.1"
        return f"http://{host}:{self.EARNINGS_CALL_TRANSCRIPT_A2A_PORT_INTERNAL}"

# Create a global settings instance
settings = Settings()