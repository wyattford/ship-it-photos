"""Start the app on the PORT from .env.

Run with: uv run python -m server            (add --reload while developing)
"""

import sys

import uvicorn

from .config import PORT, ROOT

if __name__ == "__main__":
    reload = "--reload" in sys.argv[1:]
    uvicorn.run(
        "server.main:app",
        host="127.0.0.1",
        port=PORT,
        reload=reload,
        reload_dirs=[str(ROOT / "server")] if reload else None,
    )
