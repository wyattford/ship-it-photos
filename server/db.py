"""Database helpers. Every user-supplied value is passed as a `?` parameter."""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

# Use mssql-python's Rust-based driver. The default bundled ODBC driver looks for
# OpenSSL 1.x/3 at /opt/homebrew/opt/openssl, which Homebrew now points at OpenSSL 4.
os.environ.setdefault("MSSQL_PYTHON_NATIVE_PROVIDER", "mssql-odbc")

import mssql_python  # noqa: E402

from .config import connection_string


def connect(database: str | None = None, autocommit: bool = False):
    return mssql_python.connect(connection_string(database), autocommit=autocommit, timeout=15)


def rows_as_dicts(cursor) -> list[dict[str, Any]]:
    if cursor.description is None:
        return []
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


class Db:
    """Thin wrapper around one connection, used for the length of one request."""

    def __init__(self, conn):
        self.conn = conn

    def all(self, sql: str, *params: Any) -> list[dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return rows_as_dicts(cur)

    def one(self, sql: str, *params: Any) -> dict[str, Any] | None:
        rows = self.all(sql, *params)
        return rows[0] if rows else None

    def scalar(self, sql: str, *params: Any) -> Any:
        cur = self.conn.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row else None

    def run(self, sql: str, *params: Any) -> int:
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.rowcount

    def commit(self) -> None:
        self.conn.commit()

    def rollback(self) -> None:
        self.conn.rollback()


def get_db() -> Iterator[Db]:
    """FastAPI dependency: one connection per request; rolls back on error."""
    conn = connect()
    db = Db(conn)
    try:
        yield db
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def session(database: str | None = None) -> Iterator[Db]:
    conn = connect(database)
    try:
        yield Db(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
