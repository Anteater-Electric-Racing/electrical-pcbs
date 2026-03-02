from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from formatter import export_to_csv, export_to_markdown, print_to_console
from logic import query_rules


def default_rules_db_path() -> Path:
    """
    Return the default location of the verified rules database.
    """
    base = Path(__file__).resolve().parent
    return base / "data" / "rules_db.json"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "FSAE EV PCB Rule Checker\n\n"
            "Workflow:\n"
            "  1) Run pdf_scraper.py to generate data/staging_db.json\n"
            "  2) Manually review staging_db.json and save as data/rules_db.json\n"
            "  3) Use this CLI to filter rules per PCB and export checklists"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--pcb",
        required=True,
        help="Target PCB identifier (e.g., BSPD, BMS, TSAL)",
    )
    parser.add_argument(
        "--domain",
        required=False,
        help="Optional hardware domain filter (e.g., pcb_specific)",
    )
    parser.add_argument(
        "--format",
        choices=["console", "md", "csv"],
        default="console",
        help="Output format: console (default), md, or csv",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    rules_path = default_rules_db_path()
    if not rules_path.exists():
        raise SystemExit(
            f"rules_db.json not found at {rules_path}. "
            "Run pdf_scraper.py to generate staging_db.json, "
            "review it manually, and save as rules_db.json."
        )

    result = query_rules(rules_path, target_pcb=args.pcb, domain_filter=args.domain)

    if args.format == "console":
        print_to_console(result.rules)
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.format == "md":
        filename = output_dir / f"fsae_rules_{result.pcb}_{result.domain_filter or 'all'}_{timestamp}.md"
        out_path = export_to_markdown(result.rules, filename)
        print(f"Wrote Markdown checklist to: {out_path}")
    elif args.format == "csv":
        filename = output_dir / f"fsae_rules_{result.pcb}_{result.domain_filter or 'all'}_{timestamp}.csv"
        out_path = export_to_csv(result.rules, filename)
        print(f"Wrote CSV checklist to: {out_path}")


if __name__ == "__main__":
    main()

