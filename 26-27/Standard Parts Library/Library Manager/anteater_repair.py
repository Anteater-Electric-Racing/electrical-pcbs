"""Anteater Racing: finish (or safely undo) a git merge/rebase that stopped on library files.

GitHub Desktop pulls with a plain git merge, which can't merge the library's catalog
and generated KiCad files, so it stops halfway with conflict text in them and every
later pull is refused ("you have unmerged files"). The launchers run this first:

  * conflicts only in library files, different parts edited -> merged like Publish
    does (catalog rows by part ID, KiCad files regenerated) and the merge finished;
  * the same part edited on both sides -> the merge is undone; the intern's own
    work stays in their local commit, and Publish offers keep-mine / keep-theirs;
  * conflicts in non-library files (e.g. a board schematic) -> left alone, with a message.

Usage: python anteater_repair.py "<library folder>"     (exit 0 = nothing to do or repaired)
       python anteater_repair.py "<library folder>" --check-generated
           after pulling: regenerate KiCad's files (parts.sqlite, lib tables) if a bad
           merge deleted them or left them out of date. Writes only when needed.
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from manager.anteater_publish import Git, _rebuild, _resolve  # noqa: E402
from manager.storage import Library  # noqa: E402


def touches_locked_files(g, frm, to):
    """Files KiCad keeps open (Windows can't replace them while it runs) that an update would change."""
    from manager.anteater_publish import KICAD_LOCKED

    changed = g.out("diff", "--name-only", frm, to).splitlines()
    return [p for p in changed if g.lib_path(p) in KICAD_LOCKED]


def safe_pull(lib):
    """Launcher pull: get teammates' parts, even with KiCad open, unless the update would
    have to replace a file KiCad holds open (then skip it rather than half-pull)."""
    g = Git(lib)
    if not g.run("rev-parse", "--abbrev-ref", "@{u}", check=False).stdout.strip():
        return 0
    print("Getting the latest parts from GitHub...")
    if g.run("fetch", "--quiet", check=False).returncode:
        print("  Couldn't reach GitHub; opening the library as it is.")
        return 0
    if g.out("rev-list", "--count", "HEAD..@{u}") == "0":
        print("  Already up to date.")
        return check_generated(Library(lib.root))
    from manager import kicad

    if os.name == "nt" and kicad.running() and touches_locked_files(g, "HEAD", "@{u}"):
        print("  KiCad is open, and this update changes the parts database file KiCad keeps open.")
        print("  Close KiCad and reopen this to get it. Opening the library as it is...")
        return 0
    r = g.run("pull", "--ff-only", "--quiet", check=False)
    if r.returncode:
        print("  Could not update automatically. Use Publish in the app (it merges for you).")
        return 0
    check_generated(Library(lib.root))  # rebuild the local parts database for the new parts
    print("  Updated.")
    return 0


def check_generated(lib):
    from manager.anteater_guard import conflicted_files
    from manager.anteater_publish import _same

    if conflicted_files(lib.root):
        return 0  # the app's own guard explains this case
    writes = lib.compiled(lib.rows())
    stale = [k for k, v in writes.items() if not _same(lib.root / k, v)]
    if stale:
        lib.transaction(writes, lib.revision())
        print("Regenerated KiCad's library files (" + ", ".join(Path(k).name for k in stale) + ").")
    return 0


def repair_stash_pop(g, lib, unmerged):
    """GitHub Desktop stashes unsaved work, pulls, then re-applies it; if that clashes,
    files are left conflicted with no merge in progress (the stash is kept as a backup)."""
    outside = [p for p in unmerged if g.lib_path(p) is None]
    if outside:
        print("Your saved work clashed with files outside the parts library:")
        for p in outside:
            print("  -", p)
        print("Resolve those in GitHub Desktop (or ask the board's owner), then open this again.")
        return 1
    print("GitHub Desktop couldn't put your unpublished library changes back after pulling. Repairing it...")
    unresolved, clash_ids = _resolve(g)  # stage 2 = what was pulled, stage 3 = your changes
    if unresolved:
        print("Two people changed the same part (" + ", ".join(sorted(set(clash_ids))) + ").")
        print("Nothing is lost (GitHub Desktop kept your changes in a stash), but this needs the")
        print("library owner. Don't commit in GitHub Desktop; send them a screenshot of this window.")
        return 1
    g.run("reset", "-q", check=False)  # back to ordinary uncommitted changes, ready for Publish
    check_generated(Library(lib.root))
    print("Repaired: your new parts and everyone else's are both kept. Don't commit in GitHub Desktop;")
    print("open 'Publish to GitHub' in the app and click Publish. (GitHub Desktop's stash is a")
    print("leftover backup and can be deleted later.)")
    return 0


def main():
    lib = Library(sys.argv[1])
    if "--check-generated" in sys.argv:
        return check_generated(lib)
    if "--pull" in sys.argv:
        return safe_pull(lib)
    g = Git(lib)
    git_dir = Path(g.out("rev-parse", "--git-dir"))
    git_dir = git_dir if git_dir.is_absolute() else g.top / git_dir
    merging = (git_dir / "MERGE_HEAD").exists()
    rebasing = (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists()
    unmerged = g.out("diff", "--name-only", "--diff-filter=U").splitlines()
    if not (merging or rebasing):
        if not unmerged:
            return 0  # the normal case: nothing to repair
        return repair_stash_pop(g, lib, unmerged)

    what = "merge" if merging else "rebase"
    from manager import kicad

    if os.name == "nt" and kicad.running():  # macOS can replace open files
        print(f"A git {what} needs repairing, but KiCad is open and locks the parts database.")
        print("Close all KiCad windows, then open this again.")
        return 1
    outside = [p for p in unmerged if g.lib_path(p) is None]
    if outside:
        print(f"A git {what} stopped on files outside the parts library:")
        for p in outside:
            print("  -", p)
        print("Resolve those in GitHub Desktop (or ask the board's owner), then open this again.")
        return 1

    print(f"A git {what} stopped on parts-library files. Repairing it...")
    env = {"GIT_EDITOR": "true"}
    for _ in range(50):  # a rebase may stop once per local commit
        unresolved, clash_ids = _resolve(g)
        if unresolved:
            g.run(what, "--abort", check=False)
            print("Two people changed the same part, so the merge was undone instead (nothing is lost:")
            print("your parts are still in your local commit). Open the Library Manager, go to")
            print("'Publish to GitHub' and click Publish; it will ask which version to keep.")
            return 0
        if merging:
            r = g.run("commit", "--no-edit", check=False, env=env)
            if r.returncode and "nothing to commit" not in (r.stdout + r.stderr):
                print("Couldn't finish the merge:", (r.stderr or r.stdout).strip()[-300:])
                return 1
            break
        r = g.run("-c", "core.editor=true", "rebase", "--continue", check=False, env=env)
        if r.returncode == 0:
            break
        if not g.out("diff", "--name-only", "--diff-filter=U"):
            # nothing left to apply in this step (e.g. already upstream): skip it
            r = g.run("rebase", "--skip", check=False, env=env)
            if r.returncode == 0 and not (git_dir / "rebase-merge").exists():
                break
    else:
        g.run(what, "--abort", check=False)
        print("Couldn't finish automatically; undid it instead. Message the library owner.")
        return 1
    _rebuild(g, Library(sys.argv[1]))  # regenerate KiCad's files from the merged catalog
    print("Repaired. Your parts and everyone else's are kept. Click 'Publish to GitHub' in the app to share them.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never block the launcher on the repair itself
        print("Automatic repair didn't run:", exc)
        sys.exit(1)
