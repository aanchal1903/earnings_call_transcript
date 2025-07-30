import sys
import os
import uvicorn
from dotenv import load_dotenv

# This code goes up two directories to find the .env file in the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# The rest of the original script content (e.g., import sys, import uvicorn...) goes below this.

def main():
    """Launcher for the Backend API server."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(project_root, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    uvicorn.run(
        "backend_api.earnings_call_api:app",
        host="127.0.0.1",
        port=8082,
        reload=True,
        reload_dirs=[src_path]
    )

if __name__ == "__main__":
    main()