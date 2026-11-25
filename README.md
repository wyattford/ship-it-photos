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
deno task create-db
```

```bash
deno task check
```

```bash
uv run python db/seed.py
```

```bash
cd web && deno install
```

`db/seed.py` is kept local (gitignored), so a fresh clone doesn't include it. It **drops and recreates all tables** and downloads photos from Lorem Picsum. Every seeded user
(e.g. `mara_lens`, `old_town_owen`) has the test password set in `db/seed.py`.

## Run (development: two terminals)

```bash
uv run python -m server --reload
```

```bash
cd web && deno task dev
```

Open <http://localhost:5173>. Vite forwards `/api` and `/uploads` to uvicorn on `PORT` from `.env`.

## Run (single server)

```bash
deno task serve
```

Builds the React app into `web/dist`, then starts uvicorn, which serves both the page and the API.
Open `http://localhost:<PORT>` (`PORT` in `.env`, default 8000). Re-run it after frontend changes (it serves a fixed build, no hot reload).

To only build (for example, before starting uvicorn yourself):

```bash
deno task build
```

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
