import sys
import os
import runpy
from dotenv import load_dotenv

# Load environment variables from project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

def main():
    """
    Sets up the Python path and runs the MCP server as a module.
    """
    # Get the absolute path to the 'src' directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(project_root, 'src')

    # Add the 'src' directory to the Python path
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    print(f"Python path includes: {src_path}")
    print("Starting MCP server...")
    
    # Use runpy to execute the module using the correct path
    runpy.run_module("mcp_server.server", run_name="__main__")

if __name__ == "__main__":
    main()