"""Anteater Racing addition: which boards each part is on (board, refs, quantity).

Stored in appdata/boards.json inside the library, so it is shared through Publish:
    {"version": 1,
     "boards": {"26-27/HVB": {"name": "HVB", "season": "26-27"}},      # boards added by hand
     "usage": {"<part ID>": {"26-27/FOCB": {"refs": "R1-R4, R7", "qty": 5, "source": "manual"}}}}

Boards with a KiCad project in a season folder (26-27/, 25-26 Archive/, ...) are
discovered automatically, keyed by season + name so next year's boards stay separate.
"""
import json
import re
import subprocess
import tempfile
from pathlib import Path

from .anteater_git import ensure_git
from .storage import APPDATA, json_bytes

FILE = APPDATA + "/boards.json"
SEASON = re.compile(r"^(\d\d-\d\d)")
SKIP = {".history", "Standard Parts Library", "node_modules"}


def load(lib):
    path = lib.root / FILE
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    data.setdefault("version", 1)
    data.setdefault("boards", {})
    data.setdefault("usage", {})
    return data


def aliases(lib):
    """Tags made on a folder-only board (e.g. 26-27/DASH) follow the KiCad project later
    created inside that folder (e.g. 26-27/DASHB)."""
    found = discover(lib)
    out = {}
    for b in found.values():
        old = f"{b['season']}/{b.get('folder_name', '')}"
        if b["project"] and b.get("folder_name") and old != b["key"] and old not in found:
            out[old] = b["key"]
    return out


def migrate(lib, data):
    alias = aliases(lib)
    if alias:
        for pid, per_part in data["usage"].items():
            data["usage"][pid] = {alias.get(k, k): v for k, v in per_part.items()}
        data["boards"] = {k: v for k, v in data["boards"].items() if k not in alias}
    return data


def save(lib, data):
    migrate(lib, data)
    data["usage"] = {p: b for p, b in sorted(data["usage"].items()) if b}
    lib.transaction({FILE: json_bytes(data)}, lib.revision())


def repo_root(lib):
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=lib.root,
                       capture_output=True, text=True) if ensure_git() else None
    return Path(r.stdout.strip()) if r and r.returncode == 0 else lib.root.parents[2]


def discover(lib):
    """KiCad projects in season folders -> {key: board}."""
    boards = {}
    root = repo_root(lib)
    for season_dir in sorted(p for p in root.iterdir() if p.is_dir() and SEASON.match(p.name)):
        season = SEASON.match(season_dir.name).group(1)
        for pro in sorted(season_dir.rglob("*.kicad_pro")):
            rel = pro.relative_to(season_dir).parts
            if any(d in SKIP or d.startswith("_") for d in rel[:-1]):
                continue
            key = f"{season}/{pro.stem}"
            if key in boards:  # same project name twice in a season: qualify with its folder
                key = f"{season}/{pro.stem} ({rel[0]})"
            boards[key] = dict(key=key, name=key.split("/", 1)[1], season=season,
                               project=pro.relative_to(root).as_posix(), folder_name=rel[0] if len(rel) > 1 else "",
                               archived="archive" in season_dir.name.lower())
        # A board folder created for this season but with no KiCad project yet (e.g. 26-27/DASH)
        if "archive" not in season_dir.name.lower():
            for folder in sorted(p for p in season_dir.iterdir() if p.is_dir()):
                if folder.name in SKIP or folder.name.startswith((".", "_")):
                    continue
                if not any(".history" not in q.parts for q in folder.rglob("*.kicad_pro")):
                    boards.setdefault(f"{season}/{folder.name}", dict(
                        key=f"{season}/{folder.name}", name=folder.name, season=season,
                        project="", folder=folder.relative_to(root).as_posix(), archived=False))
    return boards


def all_boards(lib, data=None):
    data = data or load(lib)
    boards = discover(lib)
    for key, b in data["boards"].items():
        boards.setdefault(key, dict(key=key, name=b["name"], season=b["season"], project="", archived=False))
    for per_part in data["usage"].values():  # boards only referenced by tags (e.g. project deleted)
        for key in per_part:
            season, _, name = key.partition("/")
            boards.setdefault(key, dict(key=key, name=name, season=season, project="", archived=True))
    return sorted(boards.values(), key=lambda b: (-int(b["season"][:2]), b["name"].lower()))


def count_refs(refs):
    """'R1-R4, R7' -> 5 ; 'J1; J2' -> 2"""
    n = 0
    for tok in re.split(r"[,;\s]+", refs or ""):
        m = re.fullmatch(r"([A-Za-z#_]*)(\d+)-\1?(\d+)", tok)
        if m and int(m.group(3)) >= int(m.group(2)):
            n += int(m.group(3)) - int(m.group(2)) + 1
        elif tok:
            n += 1
    return n


def natural(ref):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", ref)]


def set_usage(lib, part_id, entries):
    if part_id not in {r["ID"] for r in lib.rows()}:
        raise ValueError("That component no longer exists; click Refresh")
    data = load(lib)
    usage = {}
    for e in entries:
        board = (e.get("board") or "").strip()
        if not board:
            continue
        refs = (e.get("refs") or "").strip()
        qty = int(e.get("qty") or 0) or count_refs(refs)
        if qty <= 0:
            raise ValueError(f"{board}: enter the reference designators or a quantity")
        usage[board] = dict(refs=refs, qty=qty, source="manual")
    data["usage"][part_id] = usage
    save(lib, data)
    return state(lib)


def add_board(lib, name, season):
    name, season = (name or "").strip(), (season or "").strip()
    if not name or not SEASON.fullmatch(season):
        raise ValueError("Give the board a name and a season like 26-27")
    data = load(lib)
    data["boards"][f"{season}/{name}"] = dict(name=name, season=season)
    save(lib, data)
    return state(lib)


def import_schematic(lib, board_key, kicad_cli):
    """Replace a board's tags with what its KiCad schematic actually contains."""
    from .bom import read_design

    board = next((b for b in all_boards(lib) if b["key"] == board_key), None)
    if not board or not board["project"]:
        raise ValueError("This board has no KiCad project in the repo yet")
    sch = (repo_root(lib) / board["project"]).with_suffix(".kicad_sch")
    if not sch.exists():
        raise ValueError(f"Schematic not found: {sch.name}")
    if not kicad_cli:
        raise ValueError("KiCad CLI was not found; install KiCad 10")
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "bom.xml"
        r = subprocess.run([kicad_cli, "sch", "export", "python-bom", str(sch), "-o", str(xml)],
                           capture_output=True, text=True)
        if r.returncode or not xml.exists():
            raise ValueError("KiCad couldn't read the schematic: " + (r.stderr or r.stdout)[-300:])
        instances, _ = read_design(xml)
    refs = {}
    for i in instances:
        if i["partID"] and i["libraryID"] == lib.id:
            refs.setdefault(i["partID"], []).append(i["ref"])
    known = {r["ID"] for r in lib.rows()}
    data = load(lib)
    for per_part in data["usage"].values():
        per_part.pop(board_key, None)
    for pid, rs in refs.items():
        if pid in known:
            rs.sort(key=natural)
            data["usage"].setdefault(pid, {})[board_key] = dict(refs=", ".join(rs), qty=len(rs), source="schematic")
    save(lib, data)
    others = sum(1 for i in instances if not (i["partID"] and i["libraryID"] == lib.id))
    return dict(state(lib), imported=sum(len(v) for v in refs.values()), notInLibrary=others)


def remove_part(data, part_id):
    data["usage"].pop(part_id, None)


def state(lib):
    data = migrate(lib, load(lib))
    return dict(boards=all_boards(lib, data), usage=data["usage"])


def merge(base, ours, theirs, prefer=None):
    """Three-way merge of boards.json for Publish (ours=upstream, theirs=local). None on a clash."""
    b, o, t = (json.loads(x) if x else {"boards": {}, "usage": {}} for x in (base, ours, theirs))
    out = {"version": 1, "boards": {**o.get("boards", {}), **t.get("boards", {})}, "usage": {}}
    clashes = []
    for pid in set(o.get("usage", {})) | set(t.get("usage", {})) | set(b.get("usage", {})):
        bu, ou, tu = (x.get("usage", {}).get(pid, {}) for x in (b, o, t))
        merged = {}
        for board in set(bu) | set(ou) | set(tu):
            bv, ov, tv = bu.get(board), ou.get(board), tu.get(board)
            if tv == bv or tv == ov:
                v = ov
            elif ov == bv:
                v = tv
            elif prefer:
                v = tv if prefer == "mine" else ov
            else:
                clashes.append(f"{pid} on {board}")
                continue
            if v:
                merged[board] = v
        out["usage"][pid] = merged
    if clashes:
        return None, clashes
    out["usage"] = {p: v for p, v in sorted(out["usage"].items()) if v}
    return json_bytes(out).decode("utf-8"), []
