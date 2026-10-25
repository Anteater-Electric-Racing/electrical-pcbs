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
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from manager.anteater_publish import Git, _rebuild, _resolve  # noqa: E402
from manager.storage import Library  # noqa: E402


def main():
    lib = Library(sys.argv[1])
    g = Git(lib)
    git_dir = Path(g.out("rev-parse", "--git-dir"))
    git_dir = git_dir if git_dir.is_absolute() else g.top / git_dir
    merging = (git_dir / "MERGE_HEAD").exists()
    rebasing = (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists()
    unmerged = g.out("diff", "--name-only", "--diff-filter=U").splitlines()
    if not (merging or rebasing):
        if unmerged:
            print("Some files are marked as conflicted but no merge is in progress. Message the library owner.")
            return 1
        return 0  # the normal case: nothing to repair

    what = "merge" if merging else "rebase"
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
