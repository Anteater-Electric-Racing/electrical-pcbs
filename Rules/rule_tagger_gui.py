from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from models import FSAERule, load_rules_file, save_rules_file


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STAGING_PATH = DATA_DIR / "staging_db.json"
RULES_DB_PATH = DATA_DIR / "rules_db.json"
PRESETS_PATH = DATA_DIR / "tag_presets.json"


DEFAULT_PRESETS: Dict[str, List[str]] = {
    "functional_category": [
        "Shutdown System",
        "Accumulator / Tractive Battery",
        "LV Power & GLV",
        "TSAL / HV Indicators",
        "TSM / IMD / Insulation",
        "Harness & Wiring",
        "Charger / Charging System",
        "Technical Inspection – EV",
    ],
    "hardware_domain": [
        "pcb_specific",
        "wire_integration",
        "enclosure_mechanical",
        "safety_labeling",
        "test_procedure",
    ],
    "applicable_pcbs": [
        "CCM",
        "LATCH",
        "PCC",
        "PDB",
        "TSRTM",
        "TSSI",
        "BMS",
        "IMD",
        "ALL_GLV",
        "ALL_HV",
        "ALL",
    ],
}


def load_presets() -> Dict[str, List[str]]:
    if not PRESETS_PATH.exists():
        return json.loads(json.dumps(DEFAULT_PRESETS))
    try:
        with PRESETS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        presets: Dict[str, List[str]] = {}
        for key, default_vals in DEFAULT_PRESETS.items():
            raw_vals = data.get(key, [])
            if not isinstance(raw_vals, list):
                raw_vals = []
            # De-duplicate while preserving order
            seen = set()
            merged: List[str] = []
            for val in list(default_vals) + list(raw_vals):
                if not isinstance(val, str):
                    continue
                if val in seen:
                    continue
                seen.add(val)
                merged.append(val)
            presets[key] = merged
        return presets
    except Exception:
        # Fall back to defaults on any error
        return json.loads(json.dumps(DEFAULT_PRESETS))


def save_presets(presets: Dict[str, List[str]]) -> None:
    PRESETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = PRESETS_PATH.with_suffix(PRESETS_PATH.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(presets, f, indent=2, ensure_ascii=False, sort_keys=True)
    tmp.replace(PRESETS_PATH)


def merge_rules(staging_rules: List[FSAERule], existing_rules: List[FSAERule]) -> List[FSAERule]:
    existing_by_id = {r.rule_id: r for r in existing_rules}
    merged: List[FSAERule] = []
    for rule in staging_rules:
        merged.append(existing_by_id.get(rule.rule_id, rule))
    return merged


def load_rules_with_merge() -> List[FSAERule]:
    if not STAGING_PATH.exists():
        raise FileNotFoundError(
            f"staging_db.json not found at {STAGING_PATH}. "
            "Run pdf_scraper.py first to generate it."
        )

    staging_rules = load_rules_file(STAGING_PATH)

    if RULES_DB_PATH.exists():
        existing_rules = load_rules_file(RULES_DB_PATH)
        rules = merge_rules(staging_rules, existing_rules)
    else:
        rules = staging_rules

    return rules


def find_first_untagged_index(rules: List[FSAERule]) -> int:
    for idx, rule in enumerate(rules):
        if not rule.functional_category or not rule.hardware_domain:
            return idx
    return 0


class RuleTaggerApp:
    AUTOSAVE_INTERVAL_MS = 15000

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("FSAE Rule Tagger")

        self.rules: List[FSAERule] = load_rules_with_merge()
        self.presets: Dict[str, List[str]] = load_presets()

        self.current_index: int = find_first_untagged_index(self.rules)
        self.dirty: bool = False

        self._build_widgets()
        self._load_rule_into_form(self.current_index)

        self.root.after(self.AUTOSAVE_INTERVAL_MS, self._autosave_tick)

    # GUI construction
    def _build_widgets(self) -> None:
        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=8, pady=4)

        self.position_label = ttk.Label(top, text="")
        self.position_label.pack(side="left")

        btn_prev = ttk.Button(top, text="Prev", command=self.prev_rule)
        btn_prev.pack(side="right", padx=2)
        btn_next = ttk.Button(top, text="Next", command=self.next_rule)
        btn_next.pack(side="right", padx=2)
        btn_jump_untagged = ttk.Button(
            top, text="Jump to First Untagged", command=self.jump_to_first_untagged
        )
        btn_jump_untagged.pack(side="right", padx=2)
        btn_jump_id = ttk.Button(top, text="Jump to ID...", command=self.jump_to_id)
        btn_jump_id.pack(side="right", padx=2)

        # Main panes
        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=8, pady=4)

        # Left: rule context
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 4))

        lbl_id = ttk.Label(left, text="Rule ID:")
        lbl_id.pack(anchor="w")
        self.rule_id_var = tk.StringVar()
        self.rule_id_entry = ttk.Entry(left, textvariable=self.rule_id_var)
        self.rule_id_entry.pack(fill="x", pady=(0, 4))
        self.rule_id_var.trace_add("write", self._on_field_changed)

        lbl_title = ttk.Label(left, text="Title:")
        lbl_title.pack(anchor="w")
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(left, textvariable=self.title_var)
        self.title_entry.pack(fill="x", pady=(0, 4))
        self.title_var.trace_add("write", self._on_field_changed)

        lbl_desc = ttk.Label(left, text="Description:")
        lbl_desc.pack(anchor="w")

        desc_frame = ttk.Frame(left)
        desc_frame.pack(fill="both", expand=True)
        self.desc_text = tk.Text(desc_frame, height=10, wrap="word")
        self.desc_text.pack(side="left", fill="both", expand=True)
        self.desc_text.bind("<KeyRelease>", self._on_field_changed)
        scroll_y = ttk.Scrollbar(desc_frame, orient="vertical", command=self.desc_text.yview)
        scroll_y.pack(side="right", fill="y")
        self.desc_text.configure(yscrollcommand=scroll_y.set)

        # Right: tagging controls
        right = ttk.Frame(main)
        right.pack(side="right", fill="y")

        # Functional category
        ttk.Label(right, text="Functional Category:").pack(anchor="w")
        fc_frame = ttk.Frame(right)
        fc_frame.pack(fill="x", pady=(0, 4))
        self.functional_category_var = tk.StringVar()
        self.functional_category_combo = ttk.Combobox(
            fc_frame,
            textvariable=self.functional_category_var,
            values=self.presets.get("functional_category", []),
            state="readonly",
        )
        self.functional_category_combo.pack(side="left", fill="x", expand=True)
        self.functional_category_combo.bind("<<ComboboxSelected>>", self._on_field_changed)
        btn_add_fc = ttk.Button(fc_frame, text="+", width=3, command=self.add_functional_category)
        btn_add_fc.pack(side="left", padx=2)

        # Hardware domain
        ttk.Label(right, text="Hardware Domain:").pack(anchor="w")
        hd_frame = ttk.Frame(right)
        hd_frame.pack(fill="x", pady=(0, 4))
        self.hardware_domain_var = tk.StringVar()
        self.hardware_domain_combo = ttk.Combobox(
            hd_frame,
            textvariable=self.hardware_domain_var,
            values=self.presets.get("hardware_domain", []),
            state="readonly",
        )
        self.hardware_domain_combo.pack(side="left", fill="x", expand=True)
        self.hardware_domain_combo.bind("<<ComboboxSelected>>", self._on_field_changed)
        btn_add_hd = ttk.Button(hd_frame, text="+", width=3, command=self.add_hardware_domain)
        btn_add_hd.pack(side="left", padx=2)

        # Applicable PCBs
        ttk.Label(right, text="Applicable PCBs:").pack(anchor="w")
        pcb_frame = ttk.Frame(right)
        pcb_frame.pack(fill="both", expand=False, pady=(0, 4))
        self.pcb_listbox = tk.Listbox(pcb_frame, selectmode="multiple", height=8)
        self.pcb_listbox.pack(side="left", fill="both", expand=True)
        self.pcb_listbox.bind("<<ListboxSelect>>", self._on_field_changed)
        pcb_scroll = ttk.Scrollbar(pcb_frame, orient="vertical", command=self.pcb_listbox.yview)
        pcb_scroll.pack(side="right", fill="y")
        self.pcb_listbox.configure(yscrollcommand=pcb_scroll.set)

        btn_add_pcb = ttk.Button(right, text="Add PCB Tag...", command=self.add_pcb_tag)
        btn_add_pcb.pack(anchor="e", pady=(0, 4))

        # Inspection criteria
        ttk.Label(right, text="Inspection Criteria:").pack(anchor="w")
        self.criteria_text = tk.Text(right, height=6, wrap="word")
        self.criteria_text.pack(fill="x", pady=(0, 4))
        self.criteria_text.bind("<KeyRelease>", self._on_field_changed)

        # Is mechanical
        self.is_mechanical_var = tk.BooleanVar(value=False)
        self.is_mechanical_check = ttk.Checkbutton(
            right,
            text="Mechanical-only rule (exclude from PCB checklists)",
            variable=self.is_mechanical_var,
            command=self._on_field_changed,
        )
        self.is_mechanical_check.pack(anchor="w", pady=(4, 4))

        # Bottom bar
        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", padx=8, pady=4)
        btn_quit = ttk.Button(bottom, text="Quit", command=self.on_quit)
        btn_quit.pack(side="right", padx=2)
        btn_save_next = ttk.Button(bottom, text="Save & Next", command=self.save_and_next)
        btn_save_next.pack(side="right", padx=2)
        btn_save = ttk.Button(bottom, text="Save", command=self.save_current)
        btn_save.pack(side="right", padx=2)
        btn_delete = ttk.Button(bottom, text="Delete Rule", command=self.delete_current_rule)
        btn_delete.pack(side="left", padx=2)

        self.root.bind("<Alt-Left>", lambda event: self.prev_rule())
        self.root.bind("<Alt-Right>", lambda event: self.next_rule())

    # Data <-> form
    def _load_rule_into_form(self, index: int) -> None:
        rule = self.rules[index]
        self.current_index = index
        self.position_label.config(text=f"Rule {index + 1} of {len(self.rules)}")

        self.rule_id_var.set(rule.rule_id)
        self.title_var.set(rule.title)

        self.desc_text.delete("1.0", tk.END)
        if rule.description:
            self.desc_text.insert("1.0", rule.description)

        # Tagging fields
        fc_values = self.presets.get("functional_category", [])
        if rule.functional_category and rule.functional_category not in fc_values:
            fc_values.append(rule.functional_category)
            self.presets["functional_category"] = fc_values
            save_presets(self.presets)
        self.functional_category_combo.configure(values=fc_values)
        self.functional_category_var.set(rule.functional_category)

        hd_values = self.presets.get("hardware_domain", [])
        if rule.hardware_domain and rule.hardware_domain not in hd_values:
            hd_values.append(rule.hardware_domain)
            self.presets["hardware_domain"] = hd_values
            save_presets(self.presets)
        self.hardware_domain_combo.configure(values=hd_values)
        self.hardware_domain_var.set(rule.hardware_domain)

        # Populate PCB listbox options
        self.pcb_listbox.delete(0, tk.END)
        pcb_values = self.presets.get("applicable_pcbs", [])
        current_pcbs = set(rule.applicable_pcbs)
        # Ensure all existing rule PCB tags are in presets
        for tag in current_pcbs:
            if tag and tag not in pcb_values:
                pcb_values.append(tag)
        self.presets["applicable_pcbs"] = pcb_values
        if pcb_values:
            save_presets(self.presets)
        for tag in pcb_values:
            self.pcb_listbox.insert(tk.END, tag)
        # Select those present in rule.applicable_pcbs
        for idx in range(self.pcb_listbox.size()):
            value = self.pcb_listbox.get(idx)
            if value in current_pcbs:
                self.pcb_listbox.selection_set(idx)
            else:
                self.pcb_listbox.selection_clear(idx)

        self.criteria_text.delete("1.0", tk.END)
        if rule.inspection_criteria:
            self.criteria_text.insert("1.0", rule.inspection_criteria)

        self.is_mechanical_var.set(bool(rule.is_mechanical))

        # Freshly loaded form is not dirty yet
        self.dirty = False

    def _update_rule_from_form(self) -> None:
        rule = self.rules[self.current_index]
        rule.rule_id = self.rule_id_var.get().strip()
        rule.title = self.title_var.get().strip()
        rule.description = self.desc_text.get("1.0", tk.END).strip()
        rule.functional_category = self.functional_category_var.get().strip()
        rule.hardware_domain = self.hardware_domain_var.get().strip()

        selected_pcbs: List[str] = []
        for idx in self.pcb_listbox.curselection():
            selected_pcbs.append(self.pcb_listbox.get(idx))
        rule.applicable_pcbs = selected_pcbs

        criteria = self.criteria_text.get("1.0", tk.END).strip()
        rule.inspection_criteria = criteria
        rule.is_mechanical = bool(self.is_mechanical_var.get())

    # Tag adding helpers
    def _add_tag_value(self, key: str, prompt: str) -> None:
        value = simpledialog.askstring("Add value", prompt, parent=self.root)
        if not value:
            return
        value = value.strip()
        if not value:
            return
        values = self.presets.setdefault(key, [])
        if value not in values:
            values.append(value)
            save_presets(self.presets)
        if key == "functional_category":
            self.functional_category_combo.configure(values=values)
            self.functional_category_var.set(value)
        elif key == "hardware_domain":
            self.hardware_domain_combo.configure(values=values)
            self.hardware_domain_var.set(value)
        elif key == "applicable_pcbs":
            self.pcb_listbox.insert(tk.END, value)
        self.dirty = True

    def add_functional_category(self) -> None:
        self._add_tag_value("functional_category", "New functional category:")

    def add_hardware_domain(self) -> None:
        self._add_tag_value("hardware_domain", "New hardware domain:")

    def add_pcb_tag(self) -> None:
        self._add_tag_value("applicable_pcbs", "New PCB tag (e.g., BSPD, BMS):")

    # Navigation and save
    def save_current(self) -> None:
        self._update_rule_from_form()
        self._write_rules_and_presets()
        self.dirty = False

    def save_and_next(self) -> None:
        self.save_current()
        self.next_rule()

    def prev_rule(self) -> None:
        if self.current_index > 0:
            self._maybe_commit_before_switch()
            self._load_rule_into_form(self.current_index - 1)

    def next_rule(self) -> None:
        if self.current_index < len(self.rules) - 1:
            self._maybe_commit_before_switch()
            self._load_rule_into_form(self.current_index + 1)

    def jump_to_first_untagged(self) -> None:
        idx = find_first_untagged_index(self.rules)
        self._maybe_commit_before_switch()
        self._load_rule_into_form(idx)

    def jump_to_id(self) -> None:
        target = simpledialog.askstring("Jump to ID", "Enter rule_id (e.g., EV.6.7.1):", parent=self.root)
        if not target:
            return
        target = target.strip()
        for idx, rule in enumerate(self.rules):
            if rule.rule_id == target:
                self._maybe_commit_before_switch()
                self._load_rule_into_form(idx)
                return
        messagebox.showinfo("Not found", f"No rule with id {target!r} found.")

    def _maybe_commit_before_switch(self) -> None:
        if self.dirty:
            self._update_rule_from_form()
            self._write_rules_and_presets()
            self.dirty = False

    def _write_rules_and_presets(self) -> None:
        # Atomic write for rules_db.json
        tmp_rules = RULES_DB_PATH.with_suffix(RULES_DB_PATH.suffix + ".tmp")
        save_rules_file(tmp_rules, self.rules)
        tmp_rules.replace(RULES_DB_PATH)
        # Presets already written incrementally, but ensure they exist
        save_presets(self.presets)

    def _autosave_tick(self) -> None:
        try:
            if self.dirty:
                self._update_rule_from_form()
                self._write_rules_and_presets()
                self.dirty = False
        finally:
            self.root.after(self.AUTOSAVE_INTERVAL_MS, self._autosave_tick)

    def _on_field_changed(self, *_args: Any) -> None:
        self.dirty = True

    def delete_current_rule(self) -> None:
        if not self.rules:
            return
        rule = self.rules[self.current_index]
        if not messagebox.askyesno(
            "Delete Rule",
            f"Permanently delete rule {rule.rule_id!r}?\nThis cannot be undone.",
            default=messagebox.NO,
        ):
            return
        self.rules.pop(self.current_index)
        self._write_rules_and_presets()
        if not self.rules:
            messagebox.showinfo("Empty", "No rules remaining.")
            self.root.destroy()
            return
        new_index = min(self.current_index, len(self.rules) - 1)
        self.dirty = False
        self._load_rule_into_form(new_index)

    def on_quit(self) -> None:
        if self.dirty:
            if not messagebox.askyesno(
                "Unsaved changes",
                "You have unsaved changes. Save before quitting?",
                default=messagebox.YES,
            ):
                self.root.destroy()
                return
            self._update_rule_from_form()
            self._write_rules_and_presets()
        self.root.destroy()


def main() -> None:
    try:
        root = tk.Tk()
        app = RuleTaggerApp(root)
        root.mainloop()
    except FileNotFoundError as exc:
        messagebox.showerror("Missing data", str(exc))


if __name__ == "__main__":
    main()

