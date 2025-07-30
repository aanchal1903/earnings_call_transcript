import sys
import os
import runpy
from dotenv import load_dotenv

# This code goes up two directories to find the .env file in the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# The rest of the original script content (e.g., import sys, import uvicorn...) goes below this.

def main():
    """
    Sets up the Python path and runs the A2A server as a module.
    """
    # Get the absolute path to the 'src' directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(project_root, 'src')

    # Add the 'src' directory to the Python path
    # This ensures that modules like 'config' can be found directly.
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Use runpy to execute the module. Because 'src' is now in the path,
    # we can refer to the module without the 'src.' prefix.
    runpy.run_module("earnings_call_transcript_agent.server", run_name="__main__")

if __name__ == "__main__":
    main()