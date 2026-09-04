"""
JudiQ AI — Root Deployment ASGI Entrypoint Shim
-----------------------------------------------
This entrypoint allows PaaS platforms (e.g. Render, Railway, Heroku, Docker)
that launch from the repository root to seamlessly resolve the FastAPI application
defined in backend/main.py.

For direct backend development or container builds, backend/main.py remains
the primary application module.
"""

import sys
import os

# Add root directory and backend directory to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(root_dir, "backend")

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if root_dir not in sys.path:
    sys.path.insert(1, root_dir)

# Import app from backend.main
import backend.main as backend_main
app = backend_main.app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=False)
