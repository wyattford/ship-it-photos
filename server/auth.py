"""Sign up, log in, log out. Passwords hashed with argon2; sessions are random tokens in the Sessions table."""

import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel

from .config import SESSION_COOKIE, SESSION_DAYS
from .db import Db, get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])
hasher = PasswordHasher()
USERNAME_RE = re.compile(r"[A-Za-z0-9._]{3,30}")
# Used to keep login timing similar whether or not the username exists.
_DUMMY_HASH = hasher.hash(secrets.token_hex(16))

DbDep = Annotated[Db, Depends(get_db)]


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None, microsecond=0)


def public_user(row: dict[str, Any]) -> dict[str, Any]:
    return {"id": row["UserID"], "username": row["Username"], "display_name": row["DisplayName"]}


def current_user_optional(
    db: DbDep, session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None
) -> dict[str, Any] | None:
    if not session or len(session) != 64:
        return None
    return db.one(
        "SELECT u.UserID, u.Username, u.DisplayName FROM Sessions s "
        "JOIN Users u ON u.UserID = s.UserID WHERE s.Token = ? AND s.ExpiresAt > ?",
        session, _now(),
    )


def current_user(user: Annotated[dict | None, Depends(current_user_optional)]) -> dict[str, Any]:
    if user is None:
        raise HTTPException(401, "Please log in first.")
    return user


OptionalUser = Annotated[dict | None, Depends(current_user_optional)]
RequiredUser = Annotated[dict, Depends(current_user)]


def _start_session(db: Db, response: Response, user_id: int) -> None:
    token = secrets.token_hex(32)
    db.run(
        "INSERT INTO Sessions (Token, UserID, ExpiresAt) VALUES (?, ?, ?)",
        token, user_id, _now() + timedelta(days=SESSION_DAYS),
    )
    response.set_cookie(
        SESSION_COOKIE, token, max_age=SESSION_DAYS * 86400, httponly=True, samesite="lax", path="/"
    )


class SignupIn(BaseModel):
    username: str
    display_name: str
    password: str


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/signup")
def signup(body: SignupIn, response: Response, db: DbDep):
    username = body.username.strip()
    display = body.display_name.strip()
    if not USERNAME_RE.fullmatch(username):
        raise HTTPException(400, "Username must be 3-30 letters, digits, dots or underscores.")
    if not 1 <= len(display) <= 60:
        raise HTTPException(400, "Display name must be 1-60 characters.")
    if len(body.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters.")
    if db.scalar("SELECT 1 FROM Users WHERE Username = ?", username):
        raise HTTPException(409, "That username is taken.")
    uid = db.scalar(
        "INSERT INTO Users (Username, DisplayName, PasswordHash) OUTPUT INSERTED.UserID VALUES (?, ?, ?)",
        username, display, hasher.hash(body.password),
    )
    _start_session(db, response, uid)
    return {"id": uid, "username": username, "display_name": display}


@router.post("/login")
def login(body: LoginIn, response: Response, db: DbDep):
    row = db.one(
        "SELECT UserID, Username, DisplayName, PasswordHash FROM Users WHERE Username = ?", body.username.strip()
    )
    try:
        hasher.verify(row["PasswordHash"] if row else _DUMMY_HASH, body.password)
    except (VerifyMismatchError, InvalidHashError):
        row = None
    if row is None:
        raise HTTPException(401, "Wrong username or password.")
    db.run("DELETE FROM Sessions WHERE UserID = ? AND ExpiresAt <= ?", row["UserID"], _now())
    _start_session(db, response, row["UserID"])
    return public_user(row)


@router.post("/logout")
def logout(
    response: Response, db: DbDep, session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None
):
    if session:
        db.run("DELETE FROM Sessions WHERE Token = ?", session)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@router.get("/me")
def me(user: OptionalUser):
    return public_user(user) if user else None
