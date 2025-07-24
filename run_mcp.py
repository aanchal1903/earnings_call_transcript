import sys
import os
import runpy

def main():
    """
    Sets up the Python path and runs the MCP server as a module.
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
    runpy.run_module("mcp_server.server", run_name="__main__")

if __name__ == "__main__":
    main()