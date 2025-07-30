# src/config/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

# --- ROBUST PATH LOGIC ---
# This assumes config.py is in src/config/
# It goes up two levels to find the project root where .env should be.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
env_path = PROJECT_ROOT / '.env'

# Check if the .env file exists and then load it
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"INFO: Loaded environment variables from: {env_path}")
else:
    print(f"WARNING: .env file not found at {env_path}. Using system environment variables if available.")

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

    # --- External API Configuration ---
    
    # Finnhub API Configuration
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "default_finnhub_key")
    FINNHUB_BASE_URL: str = "https://finnhub.io/api/v1" # This is constant, so no need for .env

    # Google API Key
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "your-google-api-key")

    @property
    def earnings_call_transcript_agent_a2a_url(self) -> str:
        """URL for the Earnings Call Transcript Agent A2A service."""
        host = "earnings-call-agent" if self.APP_ENVIRONMENT == "docker" else "127.0.0.1"
        return f"http://{host}:{self.EARNINGS_CALL_TRANSCRIPT_A2A_PORT_INTERNAL}"

# Create a global settings instance
settings = Settings()