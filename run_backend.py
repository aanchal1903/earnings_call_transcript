import sys
import os
import uvicorn

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