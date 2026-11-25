"""Create your own database on the class server (DB_NAME in .env, e.g. wjford_myapp).

Run with: uv run python scripts/create_db.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.config import DB_NAME  # noqa: E402
from server.db import connect  # noqa: E402

if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*_myapp", DB_NAME):
    sys.exit(f'DB_NAME in .env is "{DB_NAME}". Set it to <your NetID>_myapp, e.g. wjford_myapp.')

try:
    conn = connect("master", autocommit=True)
    # A database name cannot be a parameter; it was validated above and is wrapped in [ ].
    conn.cursor().execute(f"IF DB_ID(N'{DB_NAME}') IS NULL CREATE DATABASE [{DB_NAME}];")
    conn.close()
    print(f"OK: database {DB_NAME} is ready. Now run: uv run python scripts/check.py")
except Exception as e:
    print(f"FAILED: {e}")
    print("Check: are you on UW Wi-Fi or Husky OnNet? Are DB_USER / DB_PASSWORD in .env right?")
    sys.exit(1)
