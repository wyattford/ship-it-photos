"""FastAPI app. Run with: uv run uvicorn server.main:app --reload --port 8000"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import auth, posts
from .config import UPLOAD_DIR, WEB_DIST

app = FastAPI(title="Ship It Photos")
app.include_router(auth.router)
app.include_router(posts.router)

UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/api/health")
def health():
    return {"ok": True}


@app.exception_handler(Exception)
async def unexpected(_request: Request, exc: Exception):
    # Don't leak SQL or stack traces to the browser; uvicorn still logs them.
    if isinstance(exc, HTTPException):
        raise exc
    return JSONResponse({"detail": "Something went wrong on the server."}, status_code=500)


# Production: serve the built React app (deno task build) with client-side routing fallback.
if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404)
        candidate = (WEB_DIST / path).resolve()
        if path and candidate.is_relative_to(WEB_DIST.resolve()) and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(WEB_DIST / "index.html")
