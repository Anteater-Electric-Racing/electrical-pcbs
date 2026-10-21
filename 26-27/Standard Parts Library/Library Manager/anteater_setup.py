"""Anteater Racing helper for Setup.bat: connect the shared library to KiCad and check ODBC.

Usage: python anteater_setup.py <library folder> [--switch]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from manager import kicad  # noqa: E402
from manager.anteater_guard import check as check_conflicts  # noqa: E402
from manager.odbc import check_odbc  # noqa: E402
from manager.storage import Library  # noqa: E402


def main():
    try:
        check_conflicts(sys.argv[1])
    except ValueError as exc:
        print("ERROR:", exc)
        return 1
    lib = Library(sys.argv[1])
    switch = "--switch" in sys.argv
    status = kicad.setup_status(lib)
    if status["connected"]:
        print("KiCad is already connected to", lib.root)
    else:
        try:
            kicad.connect(lib, switch=switch)
        except ValueError as exc:
            print("ERROR:", exc)
            return 2 if "Another library is active" in str(exc) else 1
        print("Connected KiCad to", lib.root, "(old KiCad settings backed up as *.bak)")
    # Try the ODBC manager KiCad uses first. On a Mac, KiCad's bundled libodbc can only be
    # loaded by KiCad itself (missing @rpath), so fall back to Homebrew's unixODBC.
    managers = [None, "/opt/homebrew/lib/libodbc.2.dylib", "/usr/local/lib/libodbc.2.dylib"]
    load_errors = []
    for manager in managers:
        if manager and not Path(manager).exists():
            continue
        try:
            print("Database check:", check_odbc(lib.appdata, manager=manager))
            return 0
        except OSError as exc:  # this ODBC manager couldn't be loaded; try the next one
            load_errors.append(str(exc).splitlines()[0])
        except Exception as exc:  # loaded, but the database itself isn't reachable: a real problem
            print("WARNING: database check failed:", exc)
            return 3
    print("NOTE: couldn't load an ODBC manager to double-check the database from here:")
    for e in load_errors:
        print("   ", e)
    print("KiCad is connected; confirm by pressing A in KiCad's schematic editor and searching for a part.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
