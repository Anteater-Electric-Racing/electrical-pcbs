"""Anteater Racing addition: find part files that were put in the library without importing.

Someone can drop vendor downloads straight into components/<Category>/... (for example
through GitHub's website). Those folders have no catalog entry, so the parts are
invisible in KiCad and the folders show up as fake categories. This finds them so the
app can offer to import each one, and removes the raw folder once it has been imported.
"""
from pathlib import Path

from .storage import inside

CAD = {".kicad_sym", ".kicad_mod", ".step", ".stp", ".wrl", ".zip"}
LEGACY = {".lib", ".mod", ".dcm"}            # KiCad 5 formats the importer can't use
JUNK = {".htm", ".html", ".txt", ".md", ".pdf", ".url", ".ini"}
RESERVED = {"generic_models", "logos"}


def find(lib):
    """Folders under components/ that hold CAD files but belong to no catalog part."""
    owned = {r["AssetFolder"] for r in lib.rows() if r["AssetFolder"]}
    comps = lib.root / "components"
    found = []
    for folder in sorted(p for p in comps.rglob("*") if p.is_dir()):
        rel = folder.relative_to(lib.root).as_posix()
        parts = folder.relative_to(comps).parts
        if parts[0] in RESERVED or (folder / "component.json").exists():
            continue
        if any(rel == o or rel.startswith(o + "/") for o in owned):
            continue  # inside an imported part's own folder
        files = sorted(f for f in folder.iterdir() if f.is_file())
        if not any(f.suffix.lower() in CAD for f in files):
            continue
        found.append(dict(
            folder=rel,
            category="components/" + parts[0],
            name=folder.name,
            files=[f.name for f in files if f.suffix.lower() in CAD],
            legacy=[f.name for f in files if f.suffix.lower() in LEGACY],
            other=[f.name for f in files if f.suffix.lower() not in CAD | LEGACY],
        ))
    return found


def read_file(lib, folder, name):
    entry = next((f for f in find(lib) if f["folder"] == folder), None)
    if not entry or name not in entry["files"]:
        raise ValueError("That file isn't in an un-imported part folder")
    return inside(lib.root, folder + "/" + name).read_bytes()


def remove(lib, folder):
    """Delete an un-imported folder (after its part was imported). Backed up by the transaction."""
    entry = next((f for f in find(lib) if f["folder"] == folder), None)
    if not entry:
        raise ValueError("That folder isn't an un-imported part folder")
    root = inside(lib.root, folder)
    files = [p.relative_to(lib.root).as_posix() for p in root.rglob("*") if p.is_file()]
    # a README.md left next to it (GitHub's "Create README.md") goes too if it's the only thing left
    lib.transaction({}, lib.revision(), deletes=files)
    for d in sorted((x for x in [root, *root.rglob("*")] if x.is_dir()), key=lambda x: -len(x.parts)):
        if d.exists() and not any(d.iterdir()):
            d.rmdir()
    parent = root.parent
    while parent != lib.root / "components" and parent.exists():
        leftovers = [p for p in parent.iterdir()]
        if leftovers and all(p.is_file() and p.name.lower() == "readme.md" for p in leftovers):
            for p in leftovers:
                lib.transaction({}, lib.revision(), deletes=[p.relative_to(lib.root).as_posix()])
        if parent.exists() and not any(parent.iterdir()) and parent.parent != lib.root / "components":
            parent.rmdir()
        parent = parent.parent
    return dict(removed=folder, files=len(files))
