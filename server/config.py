"""Settings read from .env (never hard-code secrets)."""

import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DB_SERVER = os.getenv("DB_SERVER", "is-info430.ischool.uw.edu")
DB_PORT = int(os.getenv("DB_PORT", "1433"))
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "")

# Where uvicorn listens (python -m server). Read from the .env file itself so a PORT
# variable that tools set in the shell (e.g. a dev server's own port) can't override it.
PORT = int(dotenv_values(ROOT / ".env").get("PORT") or "8000")

UPLOAD_DIR = ROOT / "uploads"
WEB_DIST = ROOT / "web" / "dist"

MAX_PHOTOS_PER_POST = 10
MAX_PHOTO_BYTES = 10 * 1024 * 1024
SESSION_DAYS = 14
SESSION_COOKIE = "session"


def connection_string(database: str | None = None) -> str:
    db = database or DB_NAME or "master"
    return (
        f"Server=tcp:{DB_SERVER},{DB_PORT};Database={db};"
        f"Uid={DB_USER};Pwd={{{DB_PASSWORD.replace('}', '}}')}}};"
        "Encrypt=yes;TrustServerCertificate=yes;"
    )
