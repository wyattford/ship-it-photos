"""Setup check: can this laptop reach the class database with the settings in .env?

Run with: uv run python scripts/check.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.db import connect  # noqa: E402

try:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT @@SERVERNAME, DB_NAME(), SUSER_NAME()")
    server, db, login = cur.fetchone()
    conn.close()
    print(f"OK: connected to {server}, database {db}, as {login}. You are ready.")
except Exception as e:
    print(f"NOT CONNECTED: {e}")
    print(
        "Check: are you on UW Wi-Fi or Husky OnNet? Is .env filled in (DB_USER / DB_PASSWORD)? "
        "If it says Login failed, have you run scripts/create_db.py yet?"
    )
    sys.exit(1)
