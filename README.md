# Ship It Photos

A photo-sharing site for INFO 430's "Ship It by Noon" assignment ([original instructions](Docs/README.md)).
People make an account, post sets of up to 10 photos, like posts, and leave threaded comments.

```
web/ (React + TS, Vite on Deno)  -->  server/ (FastAPI on uvicorn)  -->  SQL Server (wjford_myapp)
```

## Setup (once)
Be on UW Wi-Fi or Husky OnNet. Fill in `DB_USER` / `DB_PASSWORD` in `.env` (copied from `.env.example`). Then:

```bash
uv sync
```

```bash
uv run python scripts/create_db.py
```

```bash
uv run python scripts/check.py
```

```bash
uv run python db/seed.py
```

```bash
cd web && deno install
```

`db/seed.py` **drops and recreates all tables** and downloads photos from Lorem Picsum. Every seeded user
(e.g. `mara_lens`, `old_town_owen`) has the test password set in `db/seed.py`.

## Run (development: two terminals)

```bash
uv run uvicorn server.main:app --reload --port 8000
```

```bash
cd web && deno task dev
```

Open <http://localhost:5173>. Vite forwards `/api` and `/uploads` to uvicorn on port 8000.

## Run (single server)

```bash
cd web && deno task build && cd .. && uv run uvicorn server.main:app --port 8000
```

Open <http://localhost:8000>. uvicorn serves the built React app too.

## Files
| Path | What |
| --- | --- |
| `db/schema.sql` | Tables: Users, Sessions, Posts, Photos, Comments (self-referencing for replies), Likes |
| `db/queries.sql` | The app's main queries with `@variables`, to run in VS Code |
| `db/seed.py` | Creates the tables and fills them with realistic rows |
| `server/` | FastAPI: `auth.py` (signup/login, argon2, session cookie), `posts.py` (posts, photos, comments, likes, profiles), `images.py` (validation, EXIF stripping, thumbnails) |
| `web/src/` | React pages: feed + search, post detail with comments, profile, new post, login/signup |
| `uploads/` | Photo files (gitignored); the database stores their paths |

## Checks
- **Safe?** Search for `' OR 1=1 --`: no results, because every value is a SQL parameter.
- **No secrets in git?** `.env` is gitignored.
- **mssql-python note:** `server/db.py` selects the driver's Rust provider (`MSSQL_PYTHON_NATIVE_PROVIDER=mssql-odbc`),
  because the default bundled ODBC driver can't load Homebrew's OpenSSL 4.
