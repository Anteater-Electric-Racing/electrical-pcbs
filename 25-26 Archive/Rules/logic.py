from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set

from models import FSAERule, load_rules_file


# Example inheritance map for PCB tags. Keys inherit all tags listed in their value.
PCB_GROUPS: Dict[str, List[str]] = {
    # GLV / general PCBs
    "BSOD": ["ALL_GLV", "ALL"],
    "LATCH": ["ALL_GLV", "ALL"],
    "PDB": ["ALL_GLV", "ALL"],
    "BSPD": ["ALL_GLV", "ALL"],

    # HV PCBs
    "TSRTM": ["ALL_HV", "ALL"],
    "CCM": ["ALL_HV", "ALL"],
    "PCC": ["ALL_HV", "ALL"],
    "BMS": ["ALL_HV", "ALL"],
    "IMD": ["ALL_HV", "ALL"],

    # Group chaining examples
    "ALL_GLV": ["ALL"],
    "ALL_HV": ["ALL"],
}


def resolve_tags(target_pcb: str, groups: Dict[str, List[str]] | None = None) -> Set[str]:
    """
    Resolve the full set of tags that should be considered when filtering rules
    for a given PCB. This includes the PCB itself, any direct group tags, and
    any nested group expansions in PCB_GROUPS.
    """
    effective_groups = groups or PCB_GROUPS
    visited: Set[str] = set()
    to_visit: List[str] = [target_pcb]

    while to_visit:
        current = to_visit.pop()
        if current in visited:
            continue
        visited.add(current)

        for child in effective_groups.get(current, []):
            if child not in visited:
                to_visit.append(child)

    return visited


def load_rules(filepath: str | Path) -> List[FSAERule]:
    """
    Load rules_db.json (or similar) into a list of FSAERule objects.
    """
    return load_rules_file(filepath)


def get_rules_for_pcb(
    rules_list: Iterable[FSAERule],
    target_pcb: str,
    domain_filter: str | None = None,
) -> List[FSAERule]:
    """
    Filter the given rules for a specific PCB.

    Rules are included if:
      * any of the PCB's resolved tags appear in rule.applicable_pcbs
      * rule.is_mechanical is False
      * (optional) rule.hardware_domain == domain_filter, when domain_filter is provided
    """
    resolved = resolve_tags(target_pcb)
    filtered: List[FSAERule] = []

    for rule in rules_list:
        if rule.is_mechanical:
            continue

        if domain_filter is not None and rule.hardware_domain != domain_filter:
            continue

        if not rule.applicable_pcbs:
            continue

        if resolved.intersection(rule.applicable_pcbs):
            filtered.append(rule)

    # Stable, predictable ordering
    filtered.sort(key=lambda r: (r.functional_category or "", r.rule_id))
    return filtered


@dataclass
class RuleQueryResult:
    """
    Convenience wrapper when calling from other code paths or tests.
    """

    pcb: str
    domain_filter: str | None
    rules: List[FSAERule]


def query_rules(
    rules_path: str | Path,
    target_pcb: str,
    domain_filter: str | None = None,
) -> RuleQueryResult:
    """
    Load rules from disk and apply PCB and optional domain filtering in one step.
    """
    path = Path(rules_path)
    rules = load_rules(path)
    filtered = get_rules_for_pcb(rules, target_pcb, domain_filter)
    return RuleQueryResult(pcb=target_pcb, domain_filter=domain_filter, rules=filtered)

