from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any

import json


@dataclass
class FSAERule:
    """
    Canonical representation of a single FSAE rule that is relevant to
    the EV electrical system and inspection workflow.
    """

    rule_id: str
    title: str
    description: str
    functional_category: str
    hardware_domain: str
    applicable_pcbs: List[str]
    inspection_criteria: str
    is_mechanical: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FSAERule":
        """
        Construct an FSAERule from a plain dictionary, applying defaults for
        any missing optional-like fields so older JSON remains compatible.
        """
        return cls(
            rule_id=str(data.get("rule_id", "")),
            title=str(data.get("title", "")),
            description=str(data.get("description", "")),
            functional_category=str(data.get("functional_category", "")),
            hardware_domain=str(data.get("hardware_domain", "")),
            applicable_pcbs=list(data.get("applicable_pcbs", [])),
            inspection_criteria=str(data.get("inspection_criteria", "")),
            is_mechanical=bool(data.get("is_mechanical", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this rule into a JSON-serializable dictionary.
        """
        data = asdict(self)
        # Ensure list types are always plain lists for JSON encoding
        data["applicable_pcbs"] = list(self.applicable_pcbs)
        return data


def rules_from_list(raw: List[Dict[str, Any]]) -> List[FSAERule]:
    """
    Convert a list of plain dictionaries into FSAERule objects.
    """
    return [FSAERule.from_dict(item) for item in raw]


def rules_to_list(rules: List[FSAERule]) -> List[Dict[str, Any]]:
    """
    Convert a list of FSAERule objects into JSON-serializable dictionaries.
    """
    return [rule.to_dict() for rule in rules]


def load_rules_file(path: str | Path) -> List[FSAERule]:
    """
    Load a JSON file containing an array of rule dictionaries and return
    a list of FSAERule objects.
    """
    json_path = Path(path)
    with json_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        raise ValueError(f"Expected a list of rules in {json_path}, got {type(raw)}")
    return rules_from_list(raw)


def save_rules_file(path: str | Path, rules: List[FSAERule]) -> None:
    """
    Persist a list of FSAERule objects as a JSON array to disk.
    """
    json_path = Path(path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(rules_to_list(rules), f, indent=2, ensure_ascii=False, sort_keys=False)


