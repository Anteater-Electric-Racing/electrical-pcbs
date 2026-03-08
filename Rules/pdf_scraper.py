from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Tuple

import pdfplumber

from models import FSAERule, save_rules_file


# Match EV/IN rule identifiers at the start of a heading line.
# Allows top-level rules like EV.2 as well as deeper ones like EV.10.1.2.
EV_IN_RULE_PATTERN = re.compile(r"^(EV|IN)\.\d+(?:\.\d+){0,3}\b")

# Match EV/IN identifiers that appear inline at the *end* of a line in heading form,
# e.g. '... Tractive System EV.2 DOCUMENTATION'.
INLINE_HEADING_PATTERN = re.compile(
    r"\b(EV|IN)\.\d+(?:\.\d+){0,3}\b\s+[A-Z][A-Z0-9 \-/]*$"
)


def normalize_description(lines: list[str]) -> str:
    """
    Convert a list of raw PDF lines into a single cleaned description string.

    Strategy:
      - Join lines with newlines.
      - Strip leading/trailing whitespace.
      - Collapse internal line breaks into single spaces so JSON has
        human-readable sentences instead of hard-wrapped lines.
    """
    if not lines:
        return ""
    raw = "\n".join(lines).strip()
    return " ".join(raw.splitlines())


def iter_pdf_lines(pdf_path: Path) -> Iterable[Tuple[int, str]]:
    """
    Yield (page_index, line_text) tuples for every line of text in the PDF.
    Page index is zero-based.
    """
    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                yield page_index, line


def split_heading(line: str) -> Tuple[str, str]:
    """
    Split a heading line into (rule_id, title) components.
    If no explicit title exists on the heading line, the title is returned
    as an empty string and can be filled from the following content.
    """
    match = EV_IN_RULE_PATTERN.match(line)
    if not match:
        raise ValueError(f"Line does not start with rule id: {line!r}")
    rule_id = match.group(0)
    remainder = line[len(rule_id) :].strip()
    return rule_id, remainder


def _rule_sort_key(rule: FSAERule) -> tuple:
    """
    Sort EV/IN rule IDs in numeric order so EV.2 comes after EV.1.7,
    not after EV.10.*

    Examples of desired ordering:
      EV.1, EV.1.1, EV.1.2, ..., EV.2, EV.2.1, ...
      IN.1, IN.1.1, ...
    """
    m = re.match(r"^(EV|IN)\.(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?", rule.rule_id)
    if not m:
        # Fallback: plain string sort for unexpected IDs
        return (2, rule.rule_id)

    prefix = 0 if m.group(1) == "EV" else 1
    nums: List[int] = []
    for part in m.groups()[1:]:
        if part is None:
            nums.append(-1)
        else:
            try:
                nums.append(int(part))
            except ValueError:
                nums.append(-1)
    return (prefix, *nums)


def extract_rules_from_pdf(pdf_path: Path) -> List[FSAERule]:
    """
    Parse the FSAE rules PDF and extract fine-grained EV/IN clauses into
    FSAERule objects suitable for manual review.
    """
    rules: List[FSAERule] = []

    current_rule_id: str | None = None
    current_title: str = ""
    collected_lines: List[str] = []

    for _page_index, raw_line in iter_pdf_lines(pdf_path):
        line = raw_line

        # If a heading like 'EV.2 DOCUMENTATION' was fused onto the end of the
        # previous description line, split it out so we can treat it as a new rule
        # while retaining the leading text as part of the old description.
        inline_match = INLINE_HEADING_PATTERN.search(line)
        if inline_match and inline_match.start() > 0:
            prefix = line[: inline_match.start()].rstrip()
            heading_part = line[inline_match.start() :].strip()

            # Prefix text still belongs to the current rule's body, if any.
            if prefix and current_rule_id is not None:
                if not current_title:
                    current_title = prefix
                else:
                    collected_lines.append(prefix)

            line = heading_part
        if EV_IN_RULE_PATTERN.match(line):
            # Flush any currently accumulated rule before starting a new one
            if current_rule_id is not None:
                description = normalize_description(collected_lines)
                rules.append(
                    FSAERule(
                        rule_id=current_rule_id,
                        title=current_title.strip(),
                        description=description,
                        functional_category="",
                        hardware_domain="",
                        applicable_pcbs=[],
                        inspection_criteria="",
                        is_mechanical=False,
                    )
                )

            current_rule_id, heading_title = split_heading(line)
            current_title = heading_title
            collected_lines = []
            continue

        # Non-heading line: treat as part of the body for the current rule.
        if current_rule_id is not None:
            if not current_title and line:
                # Use the first non-empty body line as a fallback title if the
                # heading line did not contain one.
                current_title = line
            else:
                collected_lines.append(line)

    # Flush final rule if any
    if current_rule_id is not None:
        description = normalize_description(collected_lines)
        rules.append(
            FSAERule(
                rule_id=current_rule_id,
                title=current_title.strip(),
                description=description,
                functional_category="",
                hardware_domain="",
                applicable_pcbs=[],
                inspection_criteria="",
                is_mechanical=False,
            )
        )

    # Sort deterministically (numeric-aware) for easier human review
    rules.sort(key=_rule_sort_key)
    return rules


def default_paths() -> Tuple[Path, Path]:
    """
    Return (pdf_path, staging_json_path) using paths relative to this file.
    """
    base = Path(__file__).resolve().parent
    pdf_path = base / "data" / "FSAE_Rules_2026_V1.pdf"
    staging_path = base / "data" / "staging_db.json"
    return pdf_path, staging_path


def run(pdf_override: str | None = None, output_override: str | None = None) -> Path:
    """
    Execute the extraction pipeline and return the path to the written JSON file.
    """
    pdf_path, staging_path = default_paths()

    if pdf_override is not None:
        pdf_path = Path(pdf_override)
    if output_override is not None:
        staging_path = Path(output_override)

    rules = extract_rules_from_pdf(pdf_path)
    save_rules_file(staging_path, rules)
    return staging_path


def main() -> None:
    """
    Simple CLI entry point:
      python pdf_scraper.py [--pdf path] [--out path]
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract EV/IN rules from the FSAE 2026 rulebook into staging_db.json"
    )
    parser.add_argument(
        "--pdf",
        dest="pdf_path",
        metavar="PATH",
        help="Path to FSAE_Rules_2026_V1.pdf (defaults to ./data/FSAE_Rules_2026_V1.pdf)",
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        metavar="PATH",
        help="Path to write staging_db.json (defaults to ./data/staging_db.json)",
    )

    args = parser.parse_args()
    written_path = run(args.pdf_path, args.out_path)
    print(f"Wrote staging rules to: {written_path}")


if __name__ == "__main__":
    main()

