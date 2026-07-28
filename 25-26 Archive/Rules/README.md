## FSAE EV PCB Rule Checker

This folder contains tools for generating rule checklists for FSAE EV PCBs from a curated rules database.

The main entry point is `fsae_checker.py`, which filters rules for a specific PCB and outputs a checklist in console, Markdown, or CSV format.

### Prerequisites

- **Python**: 3.9+ recommended
- **Working directory**: you can run the script from anywhere; outputs are always written under this `Rules` folder.
- **Rules database**: `data/rules_db.json` must exist and contain the verified rules.
  - Typical workflow (summarized from the script description):
    1. Run `pdf_scraper.py` to generate `data/staging_db.json`.
    2. Manually review `staging_db.json`. Note: latest manual verification was performed by Albert March 1st. If there are any errors, notify Albert.
    3. Save the verified result as `data/rules_db.json`.

### Basic usage

From the `Rules` directory:

```bash
cd electrical-pcbs/Rules
python fsae_checker.py --pcb BSPD
```

- **`--pcb`** (required): Target PCB identifier, e.g. `BSPD`, `BMS`, `TSAL`.
- **`--domain`** (optional): Hardware domain filter, e.g. `pcb_specific`.
- **`--format`** (optional): `console` (default), `md`, or `csv`.

### Output location

When `--format` is:

- **`console`**: Rules are printed directly in the terminal.
- **`md`**: A Markdown checklist is written under:

  - `electrical-pcbs/Rules/output/fsae_rules_<PCB>_<DOMAIN_OR_ALL>_<TIMESTAMP>.md`

- **`csv`**: A CSV checklist is written under:

  - `electrical-pcbs/Rules/output/fsae_rules_<PCB>_<DOMAIN_OR_ALL>_<TIMESTAMP>.csv`

The `output` directory is created automatically if it does not already exist.

### Example commands

Console output for BSPD rules (all domains):

```bash
python fsae_checker.py --pcb BSPD
```

Markdown checklist for BSPD, PCB-specific domain:

```bash
python fsae_checker.py --pcb BSPD --domain pcb_specific --format md
```

CSV checklist for BMS rules (all domains):

```bash
python fsae_checker.py --pcb BMS --format csv
```

