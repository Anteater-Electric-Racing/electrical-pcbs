"""Sync the Anteater parts library and board schematics to Notion.

The git library is the source of truth. For every library part this keeps the
matching PCB Wiki row up to date, and when someone has edited a synced field in
Notion to something different, it restores the library value and comments on
the page @mentioning the people involved. For every KiCad project in a season
folder (26-27, 25-26 Archive, ...) it exports the schematic BOM with kicad-cli
and mirrors it into the Boards and BOM Lines databases.

Usage:
  python anteater_sync.py                 # needs NOTION_TOKEN; writes to Notion
  python anteater_sync.py --dry-run       # reads Notion, prints planned writes
  python anteater_sync.py --boards-only --no-notion   # just print board BOMs
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import notion_api as N

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(HERE.parent / "Library Manager"))
from manager.bom import expand, read_design  # noqa: E402
from manager.storage import Library  # noqa: E402

# Library column -> PCB Wiki property. Library wins on every one of these.
SYNCED = {
    "MPN": "MPN",
    "Manufacturer": "Manufacturer",
    "Datasheet": "Datasheet",
    "Package": "Package/Footprint",
    "NotionCategory": "Category",
}
URL_PROPS = {"Datasheet"}
SELECT_PROPS = {"Category"}


def prop_value(prop, value):
    if prop in URL_PROPS:
        return N.url(value)
    if prop in SELECT_PROPS:
        return N.select(value)
    return N.text(value)


def norm(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


def mpn_tokens(s):
    """'Buck: TPS561201DDCR, LDO: MIC5528' -> {'TPS561201DDCR', 'MIC5528'}"""
    out = set()
    # a "/" inside an MPN (MCP2518FDT-E/SL) is part of it; " / " separates alternatives
    for tok in re.split(r"[,;\n]|\s/\s", s or ""):
        tok = re.sub(r"^[^:]*:", "", tok).strip()
        if norm(tok):
            out.add(norm(tok))
    return out


def git(*args):
    r = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


# ---- library -----------------------------------------------------------------
def library_parts(lib):
    parts = {}
    for row in lib.rows():
        pkg = row.get("Package") or row.get("Footprint", "").split(":")[-1]
        folder = row.get("Category", "").split("/")[1] if row.get("Category", "").count("/") else ""
        notion_cat = CFG["categories"].get(folder, "")  # accessories/unknown folders: leave Notion alone
        parts[row["ID"]] = dict(row, Package=pkg, NotionCategory=notion_cat)
    return parts


def explicit_link(row):
    """Library Notes may contain 'Notion: <page url or Component Name>'."""
    m = re.search(r"Notion:\s*([^;\n]+)", row.get("Notes", ""))
    return m.group(1).strip().strip('"') if m else ""


# ---- boards ------------------------------------------------------------------
def discover_boards():
    rx = re.compile(CFG["season_folder_regex"])
    boards = []
    for season_dir in sorted(p for p in REPO.iterdir() if p.is_dir() and rx.match(p.name)):
        season = rx.match(season_dir.name).group(1)
        for pro in sorted(season_dir.rglob("*.kicad_pro")):
            rel_parts = pro.relative_to(season_dir).parts
            if any(d in CFG["skip_dirs"] or d.startswith(tuple(CFG["skip_dir_prefixes"])) for d in rel_parts[:-1]):
                continue
            rel = "/".join(rel_parts)
            boards.append(dict(
                key=f"{season}/{rel}",  # stable when "26-27" is renamed to "26-27 Archive"
                name=pro.stem,
                season=season,
                archived="archive" in season_dir.name.lower(),
                project=pro,
                schematic=pro.with_suffix(".kicad_sch"),
                repo_path=pro.relative_to(REPO).as_posix(),
            ))
    stems = {}
    for b in boards:
        stems.setdefault((b["season"], b["name"]), []).append(b)
    for group in stems.values():
        if len(group) > 1:  # e.g. two BSPD projects in one season
            for b in group:
                b["name"] = f"{b['name']} ({b['repo_path'].split('/')[1]})"
    return boards


def kicad_cli():
    for c in (os.environ.get("KICAD_CLI"), shutil.which("kicad-cli"),
              r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe",
              "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"):
        if c and Path(c).exists():
            return c
    raise RuntimeError("kicad-cli not found; set KICAD_CLI")


def board_bom(board, lib, cli):
    if not board["schematic"].exists():
        return [], "No root schematic next to the .kicad_pro"
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "bom.xml"
        r = subprocess.run([cli, "sch", "export", "python-bom", str(board["schematic"]), "-o", str(xml)],
                           capture_output=True, text=True)
        if r.returncode != 0 or not xml.exists():
            return [], "kicad-cli failed: " + (r.stderr or r.stdout)[-400:]
        instances, _ = read_design(xml)
    try:
        return expand(lib, instances)["purchasing"], ""
    except ValueError as e:
        return [], str(e)


# ---- Notion sync -------------------------------------------------------------
class Sync:
    def __init__(self, notion, lib, parts, author, commit):
        self.n, self.lib, self.parts = notion, lib, parts
        self.author, self.commit = author, commit
        self.report = {"linked": 0, "created": 0, "updated": 0, "conflicts": [], "removed": 0,
                       "boards": [], "lines_created": 0, "lines_updated": 0, "lines_archived": 0}
        self.part_page = {}  # library ID -> Notion page id

    def notify(self, page, people, message):
        rich = [N.mention(p) for p in dict.fromkeys(people)]
        rich.append(N.plain_rt((" " if rich else "") + message))
        self.n.comment(page["id"], rich, label=N.read(page, "Component Name") or page["id"])

    def people(self, page):
        ids = (N.read(page, "Person") or []) + (N.read(page, "Verifier") or [])
        editor = page.get("last_edited_by", {})
        if editor.get("object") == "user" and editor.get("type", "person") == "person":
            ids.append(editor["id"])
        return ids

    def sync_parts(self):
        db = CFG["notion"]["parts_db"]
        pages = self.n.query(db)
        by_libid = {N.read(p, "Library ID"): p for p in pages if N.read(p, "Library ID")}
        # rows with no Component Name (blank rows) must never match anything by name
        by_name = {name: p for p in pages if (name := (N.read(p, "Component Name") or "").strip().lower())}
        by_id = {p["id"].replace("-", ""): p for p in pages}
        unlinked_by_mpn = {}
        for p in pages:
            if not N.read(p, "Library ID"):
                for t in mpn_tokens(N.read(p, "MPN")):
                    unlinked_by_mpn.setdefault(t, p)
        claimed = set()

        for pid, row in sorted(self.parts.items()):
            page = by_libid.get(pid)
            if not page:
                link = explicit_link(row)
                hexid = re.search(r"[0-9a-f]{32}", link.replace("-", ""))
                page = (by_id.get(hexid.group(0)) if hexid else None) or (by_name.get(link.lower()) if link else None)
                if not page and row.get("AssetFolder"):  # folder named after the Notion row
                    page = by_name.get(row["AssetFolder"].rsplit("/", 1)[-1].strip().lower())
                if page and N.read(page, "Library ID"):
                    page = None  # already linked to a different part
            if not page:
                page = unlinked_by_mpn.get(norm(row["MPN"]))
            if page and page["id"] in claimed:
                page = None
            if not page:
                if row.get("Type") == "accessory":
                    continue  # housings/contacts only appear as BOM lines
                props = {
                    "Component Name": N.title(f"{row['Manufacturer']} {row['MPN']}".strip()),
                    "Library ID": N.text(pid),
                    "Library Status": N.status(CFG["uploaded_status"]),
                    "Key Specs": N.text(row.get("Description", "")),
                    "Library Sync": N.text(self.snapshot(row)),
                    **{prop: prop_value(prop, row[col]) for col, prop in SYNCED.items() if row[col]},
                }
                res = self.n.create(db, props, label=f"{row['Manufacturer']} {row['MPN']}")
                self.part_page[pid] = res["id"]
                self.report["created"] += 1
                continue
            claimed.add(page["id"])
            self.part_page[pid] = page["id"]
            self.reconcile(page, pid, row)

        for libid, page in by_libid.items():
            if libid not in self.parts:
                self.n.update(page["id"], {"Library ID": N.text(""), "Library Sync": N.text(""),
                                           "Library Status": N.status(CFG["removed_status"])},
                              label=N.read(page, "Component Name"))
                self.notify(page, self.people(page),
                            f"Part {libid} was removed from the KiCad library by {self.author} "
                            f"({self.commit}). Library Status was set back to {CFG['removed_status']}.")
                self.report["removed"] += 1
        return pages

    def snapshot(self, row):
        return json.dumps({**{c: row.get(c, "") for c in SYNCED}, "_rev": self.revision(row)},
                          separators=(",", ":"))

    def revision(self, row):
        """Fingerprint of the part's catalog entry and CAD files: changes when it needs re-verifying."""
        import hashlib
        h = hashlib.sha256(json.dumps({k: v for k, v in sorted(row.items()) if k not in
                                       ("UpdatedUTC", "NotionCategory")}).encode())
        folder = self.lib.root / row["AssetFolder"] if row.get("AssetFolder") else None
        if folder and folder.is_dir():
            for f in sorted(folder.rglob("*")):
                if f.is_file():
                    h.update(f.relative_to(folder).as_posix().encode())
                    h.update(f.read_bytes())
        return h.hexdigest()[:16]

    def reconcile(self, page, pid, row):
        try:
            last = json.loads(N.read(page, "Library Sync") or "")
        except ValueError:
            last = None
        props, conflicts = {}, []
        newly_linked = N.read(page, "Library ID") != pid
        for col, prop in SYNCED.items():
            lib_v = (row.get(col) or "").strip()
            if not lib_v:
                continue  # a blank library field never erases what someone entered in Notion
            if col == "MPN" and norm(lib_v) == norm(N.read(page, prop) or ""):
                continue  # same part number, punctuation only (library folders can't contain "/")
            cur = (N.read(page, prop) or "").strip()
            if cur == lib_v:
                continue
            props[prop] = prop_value(prop, lib_v)
            notion_edited = last is None or cur != (last.get(col) or "").strip()
            if cur and notion_edited:
                conflicts.append(f"• {prop}: Notion had \"{cur}\", library has \"{lib_v}\"")
        # In library -> "In library (un-verified)" until a Verifier sets Done in Notion.
        # A verified part that later changes in the library goes back to un-verified.
        status = N.read(page, "Library Status")
        changed_since_verified = (status == CFG["done_status"] and last is not None
                                  and last.get("_rev") not in (None, self.revision(row)))
        if status not in (CFG["done_status"], CFG["uploaded_status"]) or changed_since_verified:
            props["Library Status"] = N.status(CFG["uploaded_status"])
        if changed_since_verified:
            self.report.setdefault("reverify", []).append(N.read(page, "Component Name"))
            verifiers = N.read(page, "Verifier") or []
            self.notify(page, verifiers + (N.read(page, "Person") or []),
                        f"This part changed in the KiCad library after it was verified ({self.author}, "
                        f"{self.commit}), so its status is back to {CFG['uploaded_status']}. "
                        "Please re-check it in the Library Manager and set it to Done again.")
        snap = self.snapshot(row)
        if newly_linked:
            props["Library ID"] = N.text(pid)
            self.report["linked"] += 1
        if props or (N.read(page, "Library Sync") or "") != snap:
            props["Library Sync"] = N.text(snap)
            self.n.update(page["id"], props, label=N.read(page, "Component Name"))
            self.report["updated"] += 1
        if conflicts:
            name = N.read(page, "Component Name")
            self.report["conflicts"].append((name, conflicts))
            self.notify(page, self.people(page),
                        "The KiCad parts library is the source of truth, so these Notion edits were "
                        f"replaced with the library values (sync of {self.author}'s commit {self.commit}):\n"
                        + "\n".join(conflicts)
                        + "\nIf the Notion value was right, fix the part in the Library Manager and Publish.")

    def sync_boards(self, boards, boms, part_pages):
        bdb, ldb = CFG["notion"]["boards_db"], CFG["notion"]["bom_lines_db"]
        if not (bdb and ldb):
            print("Boards/BOM Lines database IDs not set in config.json; skipping board sync.")
            return
        mpn_to_page = {}
        for p in part_pages:
            for t in mpn_tokens(N.read(p, "MPN")):
                mpn_to_page.setdefault(t, p["id"])
        existing_boards = {N.read(p, "Key"): p for p in self.n.query(bdb)}
        existing_lines = {}
        for p in self.n.query(ldb):
            existing_lines[N.read(p, "Key")] = p
        seen_boards, seen_lines = set(), set()
        gh = f"https://github.com/{CFG['github_repo']}/tree/main/"
        for b in boards:
            lines, error = boms[b["key"]]
            props = {
                "Board": N.title(b["name"]),
                "Key": N.text(b["key"]),
                "Season": N.select(b["season"]),
                "Status": N.select("Archived" if b["archived"] else "Active"),
                "Project": N.text(b["repo_path"]),
                "GitHub": N.url(gh + "/".join(b["repo_path"].split("/")[:-1]).replace(" ", "%20")),
                "Part Count": N.number(sum(int(l["Quantity"]) for l in lines)),
                "BOM Error": N.text(error),
                "Last Synced": N.date(now()),
            }
            page = existing_boards.get(b["key"])
            board_id = (self.n.update(page["id"], props, label=b["name"]) and page["id"]) if page \
                else self.n.create(bdb, props, label=b["name"])["id"]
            seen_boards.add(b["key"])
            self.report["boards"].append((b["name"], b["season"], len(lines), error))
            if error:
                # keep the last good BOM lines rather than wiping them on a broken schematic
                seen_lines.update(k for k in existing_lines if k and k.startswith(b["key"] + "|"))
                continue
            for l in lines:
                ident = l["PartID"] or f"mpn:{norm(l['MPN'])}:{norm(l['Manufacturer'])}"
                key = f"{b['key']}|{ident}"
                seen_lines.add(key)
                row = self.parts.get(l["PartID"])
                kind = ("Accessory" if row and row.get("Type") == "accessory" else
                        "Library part" if row else "Not in library")
                part = self.part_page.get(l["PartID"]) or mpn_to_page.get(norm(l["MPN"]))
                want = {
                    "Line": N.title(f"{b['name']} · {l['MPN'] or l['Description']}"),
                    "Key": N.text(key),
                    "Board": N.relation([board_id]),
                    "Board Name": N.text(f"{b['name']} {b['season']}"),
                    "Season": N.select(b["season"]),
                    "Part": N.relation([part] if part else []),
                    "MPN": N.text(l["MPN"]),
                    "Manufacturer": N.text(l["Manufacturer"]),
                    "Description": N.text(l["Description"]),
                    "Qty": N.number(int(l["Quantity"])),
                    "Refs": N.text(l["Reference"]),
                    "Type": N.select(kind),
                }
                old = existing_lines.get(key)
                if not old:
                    self.n.create(ldb, want, label=key)
                    self.report["lines_created"] += 1
                elif any(N.read(old, k) != N.read({"properties": {k: {"type": next(iter(v)), **v}}}, k)
                         for k, v in want.items() if k not in ("Board", "Part")) \
                        or N.read(old, "Part") != ([part] if part else []):
                    self.n.update(old["id"], want, label=key)
                    self.report["lines_updated"] += 1
        for key, page in existing_lines.items():
            if key not in seen_lines:
                self.n.archive(page["id"], label=key)
                self.report["lines_archived"] += 1
        for key, page in existing_boards.items():
            if key not in seen_boards and N.read(page, "Status") != "Removed":
                self.n.update(page["id"], {"Status": N.select("Removed")}, label=key)


def summary(report, boards):
    out = ["## Parts library → Notion sync", ""]
    out.append(f"Parts: {report['linked']} newly linked, {report['created']} created, "
               f"{report['updated']} updated, {report['removed']} removed from library")
    if report["conflicts"]:
        out += ["", "### Conflicts (Notion edits replaced by library values; authors notified in Notion)"]
        for name, items in report["conflicts"]:
            out.append(f"- **{name}**")
            out += [f"  - {i[2:]}" for i in items]
    out += ["", "### Boards", "", "| Board | Season | BOM lines | Problem |", "|---|---|---|---|"]
    for name, season, n, err in report["boards"] or [(b["name"], b["season"], "-", "") for b in boards]:
        out.append(f"| {name} | {season} | {n} | {err} |")
    out.append("")
    out.append(f"BOM lines: {report['lines_created']} created, {report['lines_updated']} updated, "
               f"{report['lines_archived']} archived")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="read Notion but make no changes")
    ap.add_argument("--no-notion", action="store_true", help="only extract and print board BOMs")
    ap.add_argument("--boards-only", action="store_true")
    ap.add_argument("--season", help="only boards from this season, e.g. 26-27")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    from manager.anteater_guard import check

    check(REPO / CFG["library"])  # fail loudly (and open an issue in CI) on a conflicted library
    lib = Library(REPO / CFG["library"])
    parts = library_parts(lib)
    boards = [b for b in discover_boards() if not args.season or b["season"] == args.season]
    cli = kicad_cli()
    boms = {b["key"]: board_bom(b, lib, cli) for b in boards}
    author = os.environ.get("SYNC_AUTHOR") or git("log", "-1", "--format=%an") or "unknown"
    commit = (os.environ.get("GITHUB_SHA") or git("rev-parse", "HEAD"))[:8]

    if args.no_notion:
        for b in boards:
            lines, err = boms[b["key"]]
            print(f"\n{b['name']} [{b['season']}] {b['repo_path']}  {err}")
            for l in lines:
                print(f"  {l['Quantity']:>3}  {l['MPN'][:30]:30} {l['Reference'][:60]}")
        return 0

    token = os.environ.get("NOTION_TOKEN")
    if not token:
        # Not configured yet (see sync/README.md): don't fail every push before setup is done.
        print("NOTION_TOKEN is not set; skipping the Notion sync. See sync/README.md for setup.")
        return 0
    # Only the databases listed in config.json "writable_databases" can be touched (PCB Wiki only).
    sync = Sync(N.Notion(token, dry_run=args.dry_run, writable_databases=CFG["writable_databases"]),
                lib, parts, author, commit)
    part_pages = sync.n.query(CFG["notion"]["parts_db"]) if args.boards_only else sync.sync_parts()
    if args.boards_only:
        sync.part_page = {N.read(p, "Library ID"): p["id"] for p in part_pages if N.read(p, "Library ID")}
    sync.sync_boards(boards, boms, part_pages)

    text = summary(sync.report, boards)
    print(text)
    if args.dry_run:
        print("\nPlanned Notion writes:")
        for action, label, _ in sync.n.writes:
            print(f"  {action:8} {label}")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        Path(os.environ["GITHUB_STEP_SUMMARY"]).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
