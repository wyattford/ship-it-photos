# Rules for AI coding assistants

Student project for INFO 430 (database systems) at the UW iSchool, adapted from
[billhowe/ship-it-by-noon](https://github.com/billhowe/ship-it-by-noon) (original instructions in `Docs/`).
The app: a photo-sharing site (accounts, posts with multiple photos, threaded comments, likes).

## Architecture (keep to it)
```
web/ (React + TS, Vite, Deno)  -->  server/ (FastAPI on uvicorn)  -->  SQL Server (class server, wjford_myapp)
the page                            runs SQL, returns JSON               the data
```
- `web/` is a Vite + React + TypeScript app run with **Deno** (`deno task dev`). It only calls this app's own
  `/api/...` routes with `fetch`. It never talks to the database.
- `server/` is a FastAPI app (`uv run uvicorn server.main:app`). Each `/api` route runs SQL and returns JSON.
  It also serves uploaded images from `/uploads` and, in production, the built `web/dist`.
- `db/` holds SQL: `schema.sql` (CREATE TABLE), `queries.sql` (the app's main queries, runnable in VS Code),
  `seed.py` (creates tables and fills them with realistic rows + Lorem Picsum photos).
- Photo files live on disk in `uploads/` (gitignored); the database stores their paths.
- Connection settings come from `.env` (see `.env.example`). Driver: `mssql-python`.

## Database
- SQL Server 2022 on `is-info430.ischool.uw.edu`, reached only from UW Wi-Fi or the Husky OnNet VPN.
- The student's tables go in `wjford_myapp`. Class databases `olist`, `stackexchange`, `gtfs` are read-only.
- T-SQL syntax: `TOP (n)`, not `LIMIT`. Avoid multiple cascade paths; deletes are done explicitly in a transaction.
- `uv run python scripts/create_db.py` creates the database; `uv run python scripts/check.py` tests the connection.

## Rules
- Any value from the user goes into SQL as a parameter (`?` placeholders with mssql-python). Never build SQL by
  pasting strings together.
- Never put a password in code. Never commit `.env`.
- Passwords are hashed with argon2. Sessions are random tokens stored in the `Sessions` table, sent as an HttpOnly cookie.
- Only the author may edit/delete their own posts and comments; check this on the server.
- Explain changes in plain language and say exactly how to run and test them.
