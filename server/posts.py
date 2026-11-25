"""Posts (with photos), comments, likes and user profiles."""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from .auth import OptionalUser, RequiredUser, public_user
from .config import MAX_PHOTO_BYTES, MAX_PHOTOS_PER_POST
from .db import Db, get_db
from .images import BadImage, delete_files, store_image

router = APIRouter(prefix="/api", tags=["posts"])
DbDep = Annotated[Db, Depends(get_db)]

MAX_CAPTION = 2000
MAX_COMMENT = 2000


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None, microsecond=0)


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() + "Z" if dt else None


def _photo(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["PhotoID"],
        "url": f"/uploads/{row['FilePath']}",
        "thumb_url": f"/uploads/{row['ThumbPath']}",
        "width": row["Width"],
        "height": row["Height"],
    }


def _like_pattern(text: str) -> str:
    """Escape LIKE wildcards so user input is matched literally."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_").replace("[", "\\[")
    return f"%{escaped}%"


# The feed query. WHERE pieces are fixed SQL text; every user value is a ? parameter.
POST_SELECT = """
SELECT TOP (?)
    p.PostID, p.Caption, p.CreatedAt, p.UpdatedAt,
    u.UserID, u.Username, u.DisplayName,
    (SELECT COUNT(*) FROM Likes l WHERE l.PostID = p.PostID) AS LikeCount,
    (SELECT COUNT(*) FROM Comments c WHERE c.PostID = p.PostID AND c.IsDeleted = 0) AS CommentCount,
    CASE WHEN EXISTS (SELECT 1 FROM Likes l WHERE l.PostID = p.PostID AND l.UserID = ?)
         THEN 1 ELSE 0 END AS LikedByMe
FROM Posts p
JOIN Users u ON u.UserID = p.UserID
"""


def _load_posts(db: Db, where: list[str], params: list[Any], limit: int, viewer_id: int) -> list[dict[str, Any]]:
    sql = POST_SELECT + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY p.PostID DESC"
    rows = db.all(sql, limit, viewer_id, *params)
    if not rows:
        return []
    ids = [r["PostID"] for r in rows]
    placeholders = ", ".join("?" for _ in ids)
    photos: dict[int, list] = {i: [] for i in ids}
    for ph in db.all(
        f"SELECT PhotoID, PostID, FilePath, ThumbPath, Width, Height FROM Photos "
        f"WHERE PostID IN ({placeholders}) ORDER BY PostID, SortOrder",
        *ids,
    ):
        photos[ph["PostID"]].append(_photo(ph))
    return [
        {
            "id": r["PostID"],
            "caption": r["Caption"],
            "created_at": _iso(r["CreatedAt"]),
            "updated_at": _iso(r["UpdatedAt"]),
            "author": public_user(r),
            "like_count": r["LikeCount"],
            "comment_count": r["CommentCount"],
            "liked_by_me": bool(r["LikedByMe"]),
            "photos": photos[r["PostID"]],
        }
        for r in rows
    ]


def _get_post(db: Db, post_id: int, viewer_id: int) -> dict[str, Any]:
    posts = _load_posts(db, ["p.PostID = ?"], [post_id], 1, viewer_id)
    if not posts:
        raise HTTPException(404, "Post not found.")
    return posts[0]


def _require_owner(db: Db, table: str, id_col: str, row_id: int, user_id: int) -> dict[str, Any]:
    # table / id_col are fixed strings from this file, never user input.
    row = db.one(f"SELECT * FROM {table} WHERE {id_col} = ?", row_id)
    if row is None:
        raise HTTPException(404, "Not found.")
    if row["UserID"] != user_id:
        raise HTTPException(403, "You can only change your own content.")
    return row


# ---------- Posts ----------

@router.get("/posts")
def list_posts(
    db: DbDep,
    viewer: OptionalUser,
    q: Annotated[str | None, Query(max_length=100)] = None,
    user: Annotated[str | None, Query(max_length=30)] = None,
    before: int | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 12,
):
    where: list[str] = []
    params: list[Any] = []
    if q and q.strip():
        pat = _like_pattern(q.strip())
        where.append(
            "(p.Caption LIKE ? ESCAPE '\\' OR u.Username LIKE ? ESCAPE '\\' OR u.DisplayName LIKE ? ESCAPE '\\')"
        )
        params += [pat, pat, pat]
    if user:
        where.append("u.Username = ?")
        params.append(user)
    if before:
        where.append("p.PostID < ?")
        params.append(before)
    posts = _load_posts(db, where, params, limit + 1, viewer["UserID"] if viewer else 0)
    has_more = len(posts) > limit
    posts = posts[:limit]
    return {"posts": posts, "next_before": posts[-1]["id"] if has_more else None}


@router.post("/posts", status_code=201)
def create_post(
    db: DbDep,
    user: RequiredUser,
    photos: Annotated[list[UploadFile], File()],
    caption: Annotated[str, Form(max_length=MAX_CAPTION)] = "",
):
    if not 1 <= len(photos) <= MAX_PHOTOS_PER_POST:
        raise HTTPException(400, f"Attach between 1 and {MAX_PHOTOS_PER_POST} photos.")
    stored = []
    try:
        for f in photos:
            data = f.file.read(MAX_PHOTO_BYTES + 1)
            try:
                stored.append(store_image(data))
            except BadImage as e:
                raise HTTPException(400, f"{f.filename}: {e}") from e
        post_id = db.scalar(
            "INSERT INTO Posts (UserID, Caption) OUTPUT INSERTED.PostID VALUES (?, ?)",
            user["UserID"], caption.strip(),
        )
        for order, st in enumerate(stored):
            db.run(
                "INSERT INTO Photos (PostID, SortOrder, FilePath, ThumbPath, Width, Height) VALUES (?, ?, ?, ?, ?, ?)",
                post_id, order, st.file_path, st.thumb_path, st.width, st.height,
            )
        db.commit()
    except Exception:
        delete_files([p for st in stored for p in (st.file_path, st.thumb_path)])
        raise
    return _get_post(db, post_id, user["UserID"])


@router.get("/posts/{post_id}")
def get_post(post_id: int, db: DbDep, viewer: OptionalUser):
    viewer_id = viewer["UserID"] if viewer else 0
    post = _get_post(db, post_id, viewer_id)
    rows = db.all(
        "SELECT c.CommentID, c.ParentCommentID, c.Body, c.IsDeleted, c.CreatedAt, c.UpdatedAt, "
        "u.UserID, u.Username, u.DisplayName "
        "FROM Comments c JOIN Users u ON u.UserID = c.UserID "
        "WHERE c.PostID = ? ORDER BY c.CreatedAt, c.CommentID",
        post_id,
    )
    post["comments"] = [
        {
            "id": r["CommentID"],
            "parent_id": r["ParentCommentID"],
            "body": None if r["IsDeleted"] else r["Body"],
            "deleted": bool(r["IsDeleted"]),
            "created_at": _iso(r["CreatedAt"]),
            "updated_at": _iso(r["UpdatedAt"]),
            "author": None if r["IsDeleted"] else public_user(r),
        }
        for r in rows
    ]
    return post


class CaptionIn(BaseModel):
    caption: str


@router.patch("/posts/{post_id}")
def edit_post(post_id: int, body: CaptionIn, db: DbDep, user: RequiredUser):
    if len(body.caption) > MAX_CAPTION:
        raise HTTPException(400, f"Caption must be at most {MAX_CAPTION} characters.")
    _require_owner(db, "Posts", "PostID", post_id, user["UserID"])
    db.run("UPDATE Posts SET Caption = ?, UpdatedAt = ? WHERE PostID = ?", body.caption.strip(), _now(), post_id)
    return _get_post(db, post_id, user["UserID"])


@router.delete("/posts/{post_id}")
def delete_post(post_id: int, db: DbDep, user: RequiredUser):
    _require_owner(db, "Posts", "PostID", post_id, user["UserID"])
    files = db.all("SELECT FilePath, ThumbPath FROM Photos WHERE PostID = ?", post_id)
    # Children first (no cascades). One statement removes every comment, so self-references are fine.
    db.run("DELETE FROM Likes WHERE PostID = ?", post_id)
    db.run("DELETE FROM Comments WHERE PostID = ?", post_id)
    db.run("DELETE FROM Photos WHERE PostID = ?", post_id)
    db.run("DELETE FROM Posts WHERE PostID = ?", post_id)
    db.commit()
    delete_files([p for f in files for p in (f["FilePath"], f["ThumbPath"])])
    return {"ok": True}


# ---------- Likes ----------

def _like_state(db: Db, post_id: int, user_id: int) -> dict[str, Any]:
    return {
        "liked_by_me": bool(db.scalar("SELECT 1 FROM Likes WHERE PostID = ? AND UserID = ?", post_id, user_id)),
        "like_count": db.scalar("SELECT COUNT(*) FROM Likes WHERE PostID = ?", post_id),
    }


@router.put("/posts/{post_id}/like")
def like(post_id: int, db: DbDep, user: RequiredUser):
    if not db.scalar("SELECT 1 FROM Posts WHERE PostID = ?", post_id):
        raise HTTPException(404, "Post not found.")
    db.run(
        "IF NOT EXISTS (SELECT 1 FROM Likes WHERE PostID = ? AND UserID = ?) "
        "INSERT INTO Likes (UserID, PostID) VALUES (?, ?)",
        post_id, user["UserID"], user["UserID"], post_id,
    )
    return _like_state(db, post_id, user["UserID"])


@router.delete("/posts/{post_id}/like")
def unlike(post_id: int, db: DbDep, user: RequiredUser):
    db.run("DELETE FROM Likes WHERE PostID = ? AND UserID = ?", post_id, user["UserID"])
    return _like_state(db, post_id, user["UserID"])


# ---------- Comments ----------

class CommentIn(BaseModel):
    body: str
    parent_id: int | None = None


class CommentEditIn(BaseModel):
    body: str


def _clean_body(body: str) -> str:
    text = body.strip()
    if not 1 <= len(text) <= MAX_COMMENT:
        raise HTTPException(400, f"Comments must be 1-{MAX_COMMENT} characters.")
    return text


@router.post("/posts/{post_id}/comments", status_code=201)
def add_comment(post_id: int, body: CommentIn, db: DbDep, user: RequiredUser):
    text = _clean_body(body.body)
    if not db.scalar("SELECT 1 FROM Posts WHERE PostID = ?", post_id):
        raise HTTPException(404, "Post not found.")
    if body.parent_id is not None and not db.scalar(
        "SELECT 1 FROM Comments WHERE CommentID = ? AND PostID = ? AND IsDeleted = 0", body.parent_id, post_id
    ):
        raise HTTPException(400, "The comment you're replying to doesn't exist.")
    row = db.one(
        "INSERT INTO Comments (PostID, UserID, ParentCommentID, Body) "
        "OUTPUT INSERTED.CommentID, INSERTED.CreatedAt VALUES (?, ?, ?, ?)",
        post_id, user["UserID"], body.parent_id, text,
    )
    return {
        "id": row["CommentID"],
        "parent_id": body.parent_id,
        "body": text,
        "deleted": False,
        "created_at": _iso(row["CreatedAt"]),
        "updated_at": None,
        "author": public_user(user),
    }


@router.patch("/comments/{comment_id}")
def edit_comment(comment_id: int, body: CommentEditIn, db: DbDep, user: RequiredUser):
    text = _clean_body(body.body)
    row = _require_owner(db, "Comments", "CommentID", comment_id, user["UserID"])
    if row["IsDeleted"]:
        raise HTTPException(404, "Not found.")
    now = _now()
    db.run("UPDATE Comments SET Body = ?, UpdatedAt = ? WHERE CommentID = ?", text, now, comment_id)
    return {"id": comment_id, "body": text, "updated_at": _iso(now)}


@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, db: DbDep, user: RequiredUser):
    _require_owner(db, "Comments", "CommentID", comment_id, user["UserID"])
    if db.scalar("SELECT 1 FROM Comments WHERE ParentCommentID = ?", comment_id):
        # Has replies: keep the row so the thread stays intact, but hide its text.
        db.run("UPDATE Comments SET IsDeleted = 1, Body = N'' WHERE CommentID = ?", comment_id)
        return {"ok": True, "soft": True}
    db.run("DELETE FROM Comments WHERE CommentID = ?", comment_id)
    return {"ok": True, "soft": False}


# ---------- Users ----------

@router.get("/users/{username}")
def get_user(username: str, db: DbDep):
    row = db.one(
        "SELECT u.UserID, u.Username, u.DisplayName, u.Bio, u.CreatedAt, "
        "(SELECT COUNT(*) FROM Posts p WHERE p.UserID = u.UserID) AS PostCount, "
        "(SELECT COUNT(*) FROM Likes l JOIN Posts p ON p.PostID = l.PostID WHERE p.UserID = u.UserID) AS LikesReceived "
        "FROM Users u WHERE u.Username = ?",
        username,
    )
    if row is None:
        raise HTTPException(404, "User not found.")
    return {
        **public_user(row),
        "bio": row["Bio"],
        "joined_at": _iso(row["CreatedAt"]),
        "post_count": row["PostCount"],
        "likes_received": row["LikesReceived"],
    }
