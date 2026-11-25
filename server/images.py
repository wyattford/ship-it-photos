"""Validate, clean and store uploaded photos (shared by the API and the seed script)."""

import io
import uuid
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

from .config import MAX_PHOTO_BYTES, UPLOAD_DIR

ALLOWED = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp", "GIF": "gif"}
MAX_SIDE = 2560      # originals are downscaled to at most this
THUMB_SIDE = 900     # feed thumbnails

Image.MAX_IMAGE_PIXELS = 60_000_000  # refuse decompression bombs


class BadImage(ValueError):
    pass


@dataclass
class StoredPhoto:
    file_path: str   # relative to uploads/
    thumb_path: str  # relative to uploads/
    width: int
    height: int


def store_image(data: bytes) -> StoredPhoto:
    """Check the bytes really are an allowed image, strip metadata (e.g. GPS), save original + thumbnail."""
    if len(data) > MAX_PHOTO_BYTES:
        raise BadImage(f"Each photo must be {MAX_PHOTO_BYTES // (1024 * 1024)} MB or smaller.")
    try:
        img = Image.open(io.BytesIO(data))
        fmt = img.format
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as e:
        raise BadImage("That file is not a readable image.") from e
    if fmt not in ALLOWED:
        raise BadImage("Only JPEG, PNG, WebP and GIF images are allowed.")

    name = uuid.uuid4().hex
    ext = ALLOWED[fmt]
    (UPLOAD_DIR / "thumbs").mkdir(parents=True, exist_ok=True)

    animated = fmt in ("GIF", "WEBP") and getattr(img, "is_animated", False)
    if animated:
        # Keep animations as-is (re-encoding would lose frames).
        (UPLOAD_DIR / f"{name}.{ext}").write_bytes(data)
        base = img.convert("RGB")
    else:
        # Re-encoding drops EXIF metadata (location etc.) and applies rotation.
        base = ImageOps.exif_transpose(img)
        if base.mode not in ("RGB", "RGBA"):
            base = base.convert("RGBA" if "transparency" in base.info or base.mode in ("LA", "P") else "RGB")
        base.thumbnail((MAX_SIDE, MAX_SIDE))
        out = base.convert("RGB") if fmt == "JPEG" else base
        save_kwargs = {"quality": 90} if fmt in ("JPEG", "WEBP") else {}
        out.save(UPLOAD_DIR / f"{name}.{ext}", fmt, **save_kwargs)

    width, height = base.size
    thumb = base.copy()
    thumb.thumbnail((THUMB_SIDE, THUMB_SIDE))
    thumb.save(UPLOAD_DIR / "thumbs" / f"{name}.webp", "WEBP", quality=82)

    return StoredPhoto(f"{name}.{ext}", f"thumbs/{name}.webp", width, height)


def delete_files(paths: list[str]) -> None:
    for p in paths:
        target = (UPLOAD_DIR / p).resolve()
        if target.is_relative_to(UPLOAD_DIR.resolve()) and target.is_file():
            target.unlink()
