#!/usr/bin/env python3
"""Desktop entry point and KiCad external BOM command."""

import os
import subprocess
import sys

# Anteater Racing: KiCad files are UTF-8, but Windows Python reads text as cp1252 by
# default, garbling symbols with characters like Omega or micro. Re-run in UTF-8 mode.
if os.name == "nt" and not sys.flags.utf8_mode and __name__ == "__main__":
    sys.exit(subprocess.call([sys.executable, "-X", "utf8", *sys.argv]))

import argparse
import json


def main():
    parser = argparse.ArgumentParser(description="Portable KiCad Library Manager")
    sub = parser.add_subparsers(dest="command")
    bom = sub.add_parser(
        "bom", help="Expand a KiCad XML BOM with connector accessories"
    )
    bom.add_argument("--library", required=True)
    bom.add_argument("--input", required=True)
    bom.add_argument("--output", required=True)
    parser.add_argument("--library", help="Explicit portable library directory")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--desktop", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--parent-pid", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.command == "bom":
        from manager.storage import Library
        from manager.bom import export

        print(
            json.dumps(export(Library(args.library), args.input, args.output), indent=2)
        )
    else:
        if args.library:  # Anteater Racing: explain a conflicted library instead of a blank page
            from manager.anteater_guard import check

            check(args.library)
        from manager.server import run

        run(args.library, args.port, not args.no_browser, desktop=args.desktop, parent_pid=args.parent_pid)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc))
