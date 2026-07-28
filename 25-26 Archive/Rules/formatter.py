from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Iterable, List

from colorama import Fore, Style, init as colorama_init

from models import FSAERule


def _group_by_category(rules: Iterable[FSAERule]) -> dict[str, List[FSAERule]]:
    groups: dict[str, List[FSAERule]] = defaultdict(list)
    for rule in rules:
        key = rule.functional_category or "Uncategorized"
        groups[key].append(rule)
    for key in groups:
        groups[key].sort(key=lambda r: r.rule_id)
    return dict(sorted(groups.items(), key=lambda kv: kv[0].lower()))


def print_to_console(filtered_rules: Iterable[FSAERule]) -> None:
    """
    Pretty-print rules to the terminal, grouped by functional_category.
    """
    colorama_init(autoreset=True)
    groups = _group_by_category(filtered_rules)

    if not groups:
        print(Fore.YELLOW + "No rules matched the given filters.")
        return

    for category, rules in groups.items():
        header = f"[{category}]"
        print(Fore.CYAN + Style.BRIGHT + header)
        for rule in rules:
            title = rule.title or "(no title)"
            print(
                f"  {Fore.GREEN}{rule.rule_id}{Style.RESET_ALL} "
                f"- {Style.BRIGHT}{title}{Style.RESET_ALL}"
            )
            if rule.inspection_criteria:
                print(f"      Criteria: {rule.inspection_criteria}")
            elif rule.description:
                print(f"      Desc: {rule.description.splitlines()[0]}")
        print()


def export_to_markdown(filtered_rules: Iterable[FSAERule], filename: str | Path) -> Path:
    """
    Write a Markdown checklist file with grouped FSAE rules.
    """
    path = Path(filename)
    groups = _group_by_category(filtered_rules)

    lines: List[str] = []
    lines.append("# FSAE EV PCB Rule Checklist")
    lines.append("")

    for category, rules in groups.items():
        lines.append(f"## {category}")
        lines.append("")
        for rule in rules:
            title = rule.title or ""
            criteria_or_desc = rule.inspection_criteria or rule.description
            extra = f" - {criteria_or_desc}" if criteria_or_desc else ""
            lines.append(f"- [ ] `{rule.rule_id}` **{title}**{extra}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def export_to_csv(filtered_rules: Iterable[FSAERule], filename: str | Path) -> Path:
    """
    Export rules to CSV with a consistent, ESF-friendly column order.
    """
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "rule_id",
        "title",
        "description",
        "functional_category",
        "hardware_domain",
        "applicable_pcbs",
        "inspection_criteria",
        "is_mechanical",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rule in filtered_rules:
            writer.writerow(
                {
                    "rule_id": rule.rule_id,
                    "title": rule.title,
                    "description": rule.description,
                    "functional_category": rule.functional_category,
                    "hardware_domain": rule.hardware_domain,
                    "applicable_pcbs": ";".join(rule.applicable_pcbs),
                    "inspection_criteria": rule.inspection_criteria,
                    "is_mechanical": "TRUE" if rule.is_mechanical else "FALSE",
                }
            )

    return path

