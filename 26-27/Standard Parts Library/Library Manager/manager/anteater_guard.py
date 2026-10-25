"""Anteater Racing addition: detect git merge-conflict markers inside the library.

A conflicted pull in GitHub Desktop can commit raw <<<<<<< / ======= / >>>>>>>
lines into the catalog and KiCad tables, which breaks the app (blank page) and
KiCad (missing tables). Everything that reads or publishes the library checks
this first and explains what to do instead of failing mysteriously.
"""
import re
from pathlib import Path

MARKER = re.compile(rb"^(<<<<<<< |=======\r?$|>>>>>>> )", re.MULTILINE)
SKIP_DIRS = {"backups", "original-downloads", "generic_models"}
BINARY = {".sqlite", ".step", ".stp", ".wrl", ".zip", ".png", ".jpg", ".pdf"}

MESSAGE = (
    "The parts library contains unresolved git merge-conflict markers in:\n{files}\n\n"
    "This happens when a GitHub Desktop pull hits a conflict. The launcher usually repairs it\n"
    "automatically; if you're seeing this, don't edit or publish. Close this window and\n"
    "message the library owner (all parts on both sides of the conflict can be kept)."
)


def conflicted_files(library_root):
    root = Path(library_root)
    found = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if not path.is_file() or path.suffix.lower() in BINARY or SKIP_DIRS & set(rel.parts):
            continue
        try:
            if MARKER.search(path.read_bytes()):
                found.append(rel.as_posix())
        except OSError:
            continue
    return found


def check(library_root):
    """Raise ValueError with instructions if the library has conflict markers."""
    files = conflicted_files(library_root)
    if files:
        raise ValueError(MESSAGE.format(files="\n".join("  - " + f for f in files)))
