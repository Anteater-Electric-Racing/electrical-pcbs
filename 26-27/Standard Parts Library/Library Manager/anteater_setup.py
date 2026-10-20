"""Anteater Racing helper for Setup.bat: connect the shared library to KiCad and check ODBC.

Usage: python anteater_setup.py <library folder> [--switch]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from manager import kicad  # noqa: E402
from manager.odbc import check_odbc  # noqa: E402
from manager.storage import Library  # noqa: E402


def main():
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
    try:
        result = check_odbc(lib.appdata)
        print("Database check:", result)
    except Exception as exc:  # report, but the KiCad registration is already done
        print("WARNING: database check failed:", exc)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
