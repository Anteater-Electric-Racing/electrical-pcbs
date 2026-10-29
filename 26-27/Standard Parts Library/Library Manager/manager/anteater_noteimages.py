"""Anteater Racing addition: pictures in a part's Notes (pinouts, wiring, photos...).

Images are saved in appdata/note-images/ under a name made from their content hash, so they
are shared through Publish and two people adding images can never clash. The Notes text
refers to them as [image: 1a2b3c4d5e6f7a8b.png]; the app shows them when a part is opened.
"""
import hashlib
import re

from .storage import APPDATA

FOLDER = APPDATA + "/note-images"
MAX_BYTES = 5 * 1024 * 1024
NAME = re.compile(r"^[0-9a-f]{16}\.(png|jpg|gif|webp)$")
TYPES = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}


def _kind(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    raise ValueError("Use a PNG, JPG, GIF or WebP image")


def save(lib, data):
    """Store an image; returns its file name for the Notes text."""
    if len(data) > MAX_BYTES:
        raise ValueError("Image is over 5 MB. Crop it or save it as a JPG first.")
    name = f"{hashlib.sha256(data).hexdigest()[:16]}.{_kind(data)}"
    if not (lib.root / FOLDER / name).is_file():
        lib.transaction({f"{FOLDER}/{name}": data})
    return name


def read(lib, name):
    """(bytes, content type) of a stored image."""
    m = NAME.match(name)
    if not m:
        raise ValueError("Not a note image")
    return (lib.root / FOLDER / name).read_bytes(), TYPES[m.group(1)]
