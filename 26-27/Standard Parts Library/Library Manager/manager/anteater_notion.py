"""Anteater Racing addition: a part's PCB Wiki info (who added it, what it replaces).

The Notion sync writes appdata/notion-info.json with every named PCB Wiki row and the
rows it has linked to parts. The part's own 'Notion: <Component Name or page URL>' note
is followed here too, so a newly linked part shows its info as soon as it's saved,
before the next sync runs.
"""
import json
import re


def part_info(lib, part_id):
    f = lib.appdata / "notion-info.json"
    if not f.is_file():
        return None
    data = json.loads(f.read_text(encoding="utf-8"))
    rows = data.get("rows", {})
    row = next((r for r in lib.rows() if r["ID"] == part_id), None)
    if row:
        m = re.search(r"Notion:\s*([^;\n]+)", row.get("Notes", ""))
        link = m.group(1).strip().strip('"') if m else ""
        page = re.search(r"[0-9a-f]{32}", link.replace("-", ""))
        if page:
            match = next((r for r in rows.values() if page.group(0) in r.get("url", "").replace("-", "")), None)
            if match:
                return match
        elif link.lower() in rows:
            return rows[link.lower()]
    if part_id in data.get("parts", {}):
        return data["parts"][part_id]
    # a component folder named after the row also links it (same rule as the sync)
    folder = (row or {}).get("AssetFolder", "").rsplit("/", 1)[-1].strip().lower()
    return rows.get(folder) if folder else None
