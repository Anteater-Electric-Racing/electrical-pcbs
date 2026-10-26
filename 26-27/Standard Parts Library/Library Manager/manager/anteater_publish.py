"""Anteater Racing: publish library changes to GitHub from the manager UI.

Only the library folder is staged. Concurrent edits by other people are merged
automatically where that is safe: catalog rows are merged by part ID, and the
generated indexes (SQLite, KiCad tables) are rebuilt from the merged catalog.
Anything else (two people changing the same part) is reported with the other
author's name so the intern can contact them; nothing is lost because the
local commit is kept and the rebase is aborted.
"""
import csv
import io
import os
import shutil
import subprocess
from pathlib import Path

from .storage import Library, csv_bytes

DERIVED = (
    "appdata/parts.sqlite",
    "appdata/parts.kicad_dbl",
    "appdata/sym-lib-table",
    "appdata/fp-lib-table",
    "appdata/category-libraries.json",
    "appdata/generated/",
)
CATALOG = "appdata/components.csv"
# Files KiCad keeps open while it runs. Windows can't replace them then, so a git update
# that changes one must wait for KiCad to close. parts.sqlite is generated locally (not in
# git) so normally nothing here changes; this covers older history that still tracked it.
KICAD_LOCKED = {"appdata/parts.sqlite"}


class Git:
    def __init__(self, lib):
        if not shutil.which("git"):
            raise ValueError("Git is not installed. Install GitHub Desktop or Git for Windows, then reopen the manager.")
        self.lib = lib
        top = self.run("rev-parse", "--show-toplevel", cwd=lib.root, check=False)
        if top.returncode:
            raise ValueError("This library is not inside a git repository")
        self.top = Path(top.stdout.strip())
        self.rel = lib.root.resolve().relative_to(self.top.resolve()).as_posix()

    def run(self, *args, cwd=None, check=True, env=None):
        r = subprocess.run(["git", *args], cwd=cwd or self.top, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           env={**os.environ, "GIT_TERMINAL_PROMPT": "0", **(env or {})})
        if check and r.returncode:
            raise ValueError(f"git {args[0]} failed: {(r.stderr or r.stdout).strip()[-600:]}")
        return r

    def out(self, *args):
        return self.run(*args).stdout.strip()

    def lib_path(self, repo_path):
        """Repo-relative path -> library-relative path, or None if outside the library."""
        prefix = self.rel + "/"
        return repo_path[len(prefix):] if repo_path.startswith(prefix) else None


def _part_label(lib_path, names):
    parts = lib_path.split("/")
    if parts[0] == "components" and len(parts) >= 3:
        return names.get("/".join(parts[:3]), parts[2])
    return None


def _catalog_rows(text):
    if not text:
        return [], {}
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    rows = list(reader)
    return reader.fieldnames or [], {r["ID"]: r for r in rows}


def status(lib):
    g = Git(lib)
    names = {r["AssetFolder"]: f"{r['Manufacturer']} {r['MPN']}".strip() for r in lib.rows() if r.get("AssetFolder")}
    porcelain = g.out("status", "--porcelain", "-uall", "--", g.rel)
    changed = set()
    catalog_changed = False
    for line in porcelain.splitlines():
        path = line[3:].strip().strip('"').split(" -> ")[-1]
        lp = g.lib_path(path)
        if lp is None or lp.startswith("appdata/backups/"):
            continue
        if lp == CATALOG:
            catalog_changed = True
        label = _part_label(lp, names)
        if label:
            changed.add(label)
    added, edited, removed = [], [], []
    if catalog_changed:
        head = g.run("show", f"HEAD:{g.rel}/{CATALOG}", check=False).stdout
        _, old = _catalog_rows(head)
        _, new = _catalog_rows((lib.appdata / "components.csv").read_text(encoding="utf-8-sig"))
        label = lambda r: f"{r['Manufacturer']} {r['MPN']}".strip()
        added = sorted(label(r) for i, r in new.items() if i not in old)
        removed = sorted(label(r) for i, r in old.items() if i not in new)
        edited = sorted(label(r) for i, r in new.items() if i in old and r != old[i])
    branch = g.out("rev-parse", "--abbrev-ref", "HEAD")
    upstream = g.run("rev-parse", "--abbrev-ref", "@{u}", check=False).stdout.strip()
    behind = 0
    if upstream:
        # see whether teammates have published since the last pull (offline is fine)
        g.run("fetch", "--quiet", check=False)
        behind = int(g.out("rev-list", "--count", "HEAD..@{u}") or 0)
    ahead = int(g.out("rev-list", "--count", "@{u}..HEAD")) if upstream else 0
    return dict(
        branch=branch,
        upstream=upstream,
        user=g.run("config", "user.name", check=False).stdout.strip(),
        dirty=bool(porcelain.strip()),
        ahead=ahead,
        behind=behind,
        added=added, edited=edited, removed=removed,
        parts=sorted(changed - set(added) - set(removed)),
    )


def _merge_catalog(base, ours, theirs, prefer=None):
    """Three-way merge of components.csv by part ID. ours=upstream, theirs=local. None on a real conflict."""
    hb, b = _catalog_rows(base)
    ho, o = _catalog_rows(ours)
    ht, t = _catalog_rows(theirs)
    if ho != ht:
        return None, ["catalog columns differ (different Library Manager versions)"]
    merged, clashes = dict(o), []
    for ident in set(b) | set(t):
        bv, ov, tv = b.get(ident), o.get(ident), t.get(ident)
        if tv == bv or tv == ov:
            continue  # local did not change this row, or both made the same change
        if ov == bv:
            if tv is None:
                merged.pop(ident, None)
            else:
                merged[ident] = tv
        elif bv and ov and tv:
            # both edited the same part: merge field by field, clash only on the same field
            row = {}
            for col in ho:
                b_, o_, t_ = bv.get(col), ov.get(col), tv.get(col)
                if t_ == b_ or t_ == o_:
                    row[col] = o_
                elif o_ == b_:
                    row[col] = t_
                elif col == "UpdatedUTC":
                    row[col] = max(o_ or "", t_ or "")
                elif prefer:
                    row[col] = t_ if prefer == "mine" else o_
                else:
                    clashes.append(f"{ident}.{col}")
            merged[ident] = row
        elif prefer:
            if prefer == "mine":
                if tv is None:
                    merged.pop(ident, None)
                else:
                    merged[ident] = tv
        else:
            clashes.append(ident)
    if clashes:
        return None, clashes
    order = [i for i in o if i in merged] + [i for i in t if i in merged and i not in o]
    return csv_bytes([merged[i] for i in order]).decode("utf-8"), []


def _resolve(g, prefer=None):
    """Resolve the current rebase step's conflicts. Returns (unresolved repo paths, clashing part IDs)."""
    unresolved, clash_ids = [], []
    for path in g.out("diff", "--name-only", "--diff-filter=U").splitlines():
        lp = g.lib_path(path)
        if lp == CATALOG:
            stage = lambda n: g.run("show", f":{n}:{path}", check=False).stdout
            merged, clashes = _merge_catalog(stage(1), stage(2), stage(3), prefer)
            if merged is None:
                unresolved.append(path)
                clash_ids += [c.split(".")[0] for c in clashes]
                continue
            (g.top / path).write_text(merged, encoding="utf-8", newline="")
            g.run("add", "--", path)
        elif lp == "appdata/boards.json":
            from .anteater_boards import merge as merge_boards

            stage = lambda n: g.run("show", f":{n}:{path}", check=False).stdout
            merged, clashes = merge_boards(stage(1), stage(2), stage(3), prefer)
            if merged is None:
                unresolved.append(path)
                clash_ids += [c.split(" on ")[0] for c in clashes]
                continue
            (g.top / path).write_text(merged, encoding="utf-8", newline="")
            g.run("add", "--", path)
        elif lp and lp.startswith(DERIVED):
            # take upstream's copy; it is regenerated from the merged catalog afterwards
            if g.run("checkout", "--ours", "--", path, check=False).returncode:
                g.run("rm", "-q", "--cached", "--", path, check=False)
            else:
                g.run("add", "--", path)
        elif prefer:
            # rebase: --ours is upstream (theirs to the intern), --theirs is the intern's commit
            side = "--theirs" if prefer == "mine" else "--ours"
            if g.run("checkout", side, "--", path, check=False).returncode:
                g.run("rm", "-q", "--", path, check=False)
            else:
                g.run("add", "--", path)
        else:
            unresolved.append(path)
    return unresolved, clash_ids


def publish(lib, message, prefer=None):
    """prefer: None, "mine" or "theirs" for parts both people changed."""
    if prefer not in (None, "mine", "theirs"):
        raise ValueError("Unknown conflict choice")
    from .anteater_guard import check

    check(lib.root)  # never push a library containing merge-conflict markers
    g = Git(lib)
    if (lib.appdata / ".writer.lock").exists() or (lib.appdata / "pending-transaction.json").exists():
        raise ValueError("Finish or recover the current library edit before publishing")
    if not g.run("config", "user.name", check=False).stdout.strip():
        raise ValueError("Git doesn't know who you are. Open GitHub Desktop > File > Options > Git, set your name and email, then try again.")
    if not g.run("rev-parse", "--abbrev-ref", "@{u}", check=False).stdout.strip():
        raise ValueError("This branch has no GitHub upstream. Publish it once from GitHub Desktop.")
    if (g.top / ".git" / "rebase-merge").exists() or (g.top / ".git" / "rebase-apply").exists():
        raise ValueError("A git rebase is already in progress in this repository; finish it in GitHub Desktop first.")

    g.run("add", "-A", "--", g.rel)
    if g.run("diff", "--cached", "--quiet", check=False).returncode:
        g.run("commit", "-m", (message or "").strip() or "Update parts library", "--", g.rel)

    for attempt in range(3):
        g.run("fetch", "--quiet")
        local, upstream = g.out("rev-parse", "HEAD"), g.out("rev-parse", "@{u}")
        base = g.out("merge-base", "HEAD", "@{u}")
        merged_others = upstream != base
        if merged_others:
            from . import kicad

            locked = [p for p in g.out("diff", "--name-only", "HEAD", upstream).splitlines()
                      if g.lib_path(p) in KICAD_LOCKED]
            if os.name == "nt" and locked and kicad.running():
                # Windows can't replace a file KiCad has open; git would stop halfway and leave
                # a half-updated library. Your changes stay committed locally.
                raise ValueError("Close KiCad first: teammates published new parts, and KiCad keeps the "
                                 "parts database locked so they can't be merged in while it's open. "
                                 "Your changes are saved; click Publish again after closing KiCad.")
            r = g.run("rebase", "--autostash", "@{u}", check=False, env={"GIT_EDITOR": "true"})
            while r.returncode:
                unresolved, clash_ids = _resolve(g, prefer)
                if unresolved:
                    g.run("rebase", "--abort", check=False)
                    return _conflict_report(g, lib, unresolved, clash_ids, base, upstream)
                r = g.run("-c", "core.editor=true", "rebase", "--continue", check=False,
                          env={"GIT_EDITOR": "true"})
        _rebuild(g, lib)  # always: also repairs indexes left stale by an earlier failed attempt
        if g.out("rev-list", "--count", "@{u}..HEAD") == "0":
            return dict(ok=True, pushed=False, merged=merged_others,
                        message="You're up to date with everyone's parts." if merged_others
                        else "Nothing new to publish.")
        push = g.run("push", "--quiet", check=False)
        if push.returncode == 0:
            return dict(ok=True, pushed=True, merged=merged_others,
                        commit=g.out("rev-parse", "--short", "HEAD"),
                        message="Published. Notion updates in a few minutes.")
        if "rejected" not in push.stderr and "fetch first" not in push.stderr:
            raise ValueError("Push failed: " + push.stderr.strip()[-600:]
                             + "\nCheck that you are signed in to GitHub (GitHub Desktop).")
    raise ValueError("Someone else keeps publishing at the same moment; wait a minute and try again.")


def _same(path, data):
    if not path.exists():
        return False
    disk = path.read_bytes()
    if disk == data or path.suffix != ".sqlite":
        return disk == data
    # a database written while KiCad had it open differs in header bytes only
    import sqlite3
    dump = lambda c: list(c.iterdump())
    a, b = sqlite3.connect(":memory:"), sqlite3.connect(":memory:")
    try:
        a.deserialize(disk)
        b.deserialize(data)
        return dump(a) == dump(b)
    finally:
        a.close()
        b.close()


def _rebuild(g, lib):
    """Regenerate the indexes from the catalog if they are stale (e.g. after a merge)."""
    fresh = Library(lib.root)
    writes = fresh.compiled(fresh.rows())
    stale = [k for k, v in writes.items() if not _same(fresh.root / k, v)]
    if not stale:
        return
    try:
        fresh.transaction(writes, fresh.revision())
    except PermissionError:
        raise ValueError("KiCad has the parts database open. Close KiCad, then click Publish again "
                         "(your changes are saved).")
    g.run("add", "-A", "--", g.rel)
    if g.run("diff", "--cached", "--quiet", check=False).returncode:
        g.run("commit", "-m", "Regenerate library indexes after merge", "--", g.rel)


def _conflict_report(g, lib, unresolved, clash_ids, base, upstream):
    rows = lib.rows()
    names = {r["AssetFolder"]: f"{r['Manufacturer']} {r['MPN']}".strip() for r in rows if r.get("AssetFolder")}
    by_id = {r["ID"]: f"{r['Manufacturer']} {r['MPN']}".strip() for r in rows}
    parts = {by_id.get(i, i) for i in clash_ids}
    parts |= {_part_label(g.lib_path(p) or "", names) for p in unresolved if g.lib_path(p) != CATALOG}
    parts = sorted(x for x in parts if x) or unresolved
    log = g.out("log", "--format=%an%x09%ae%x09%h%x09%s", f"{base}..{upstream}", "--", *unresolved)
    authors = {}
    for line in log.splitlines():
        name, email, sha, subject = (line.split("\t") + ["", "", "", ""])[:4]
        authors.setdefault(email, dict(name=name, email=email, commits=[]))["commits"].append(f"{sha} {subject}")
    return dict(ok=False, conflict=True, parts=parts, files=unresolved, authors=list(authors.values()),
                message="Someone else changed the same part(s) since you last pulled. Your work is saved "
                        "locally as a commit; nothing was lost. Contact them to agree which version to keep.")
