"""Anteater Racing addition: find git even when it isn't on PATH.

GitHub Desktop ships its own git inside its app folder and doesn't add it to PATH, so on
a PC with only GitHub Desktop `git` isn't found. Put the first git we can find on PATH
for this process, so every `git` call (publish, pull, boards) works.
"""
import glob
import os
import re
import shutil
import sys
from pathlib import Path


def _candidates():
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA", "")
        # newest GitHub Desktop first (app-3.6.10 sorts after app-3.6.9 by version, not text)
        apps = sorted(glob.glob(os.path.join(local, "GitHubDesktop", "app-*")),
                      key=lambda p: [int(x) if x.isdigit() else 0 for x in os.path.basename(p)[4:].split(".")],
                      reverse=True)
        yield from (os.path.join(a, "resources", "app", "git", "cmd", "git.exe") for a in apps)
        for root in (os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", ""), local + r"\Programs"):
            yield os.path.join(root, "Git", "cmd", "git.exe")
    elif sys.platform == "darwin":
        yield "/Applications/GitHub Desktop.app/Contents/Resources/app/git/bin/git"
        yield os.path.expanduser("~/Applications/GitHub Desktop.app/Contents/Resources/app/git/bin/git")
        yield "/opt/homebrew/bin/git"
        yield "/usr/local/bin/git"


def native_path(path):
    """A path printed by git, as a Path this Python can use. MSYS2/Cygwin git on Windows
    prints /c/Users/... or /cygdrive/c/Users/..., which Python would read as C:\\c\\Users."""
    path = path.strip()
    if os.name == "nt":
        m = re.match(r"^/(?:cygdrive/|mnt/)?([a-zA-Z])(/.*)?$", path)
        if m:
            path = f"{m.group(1).upper()}:{m.group(2) or '/'}"
    return Path(path)


def ensure_git():
    """Path to git (adding its folder to PATH if needed), or None."""
    found = shutil.which("git")
    if found:
        return found
    for path in _candidates():
        if path and os.path.isfile(path):
            os.environ["PATH"] = os.path.dirname(path) + os.pathsep + os.environ.get("PATH", "")
            return path
    return None
