# Parts library ↔ Notion sync

`anteater_sync.py` keeps Notion in step with the repo. It runs in GitHub Actions (`.github/workflows/parts-library-sync.yml`) on every push that touches a schematic or the library, every night, and on demand.

**The git library is the source of truth.** Notion is a view of it, plus the planning and assignment columns (Key Specs, Person, Verifier, Notes...) that only live in Notion.

## What it does

| Source (repo) | Notion result |
| --- | --- |
| Each part in `Anteater Parts` | Its PCB Wiki row gets MPN, Manufacturer, Datasheet, Package/Footprint, **Category** (from the part's folder, mapped in `config.json` › `categories`), Library ID, and Library Status = *In library (un-verified)*. A Verifier sets *Done (added to KiCad library)* in Notion. The sync never overrides that, unless the part's catalog entry or CAD files change afterwards: then it goes back to un-verified and the Verifier is @mentioned. If no row matches, a row is created. |
| A part removed from the library | Library Status goes back to *Missing* and the row's Person is @mentioned. |
| Every `*.kicad_pro` in a season folder (`26-27/`, `25-26 Archive/`, later `27-28/`...) | One **Boards** page per board per season |
| Each board's schematic, exported with `kicad-cli` and expanded with connector accessories | **BOM Lines**: board × part × qty × refs |

### How a library part finds its PCB Wiki row (first match wins)

1. The row's **Library ID** column equals the part ID. The sync writes this once the two are linked.
2. The part's **Notes** in the Library Manager contain `Notion: <Component Name>;` or `Notion: <page link>;`. The Mini-Fit header uses `Notion: Connector (Internal);`.
3. The part's component folder name equals the row's *Component Name*.
4. The row's **MPN** matches the part's MPN. Lists like `Buck: TPS561201DDCR, LDO: MIC5528-3.3YMT-TR` work too.
5. Otherwise a new row is created, except for accessories (housings and contacts), which only appear in BOM Lines.

### Conflicts

- **Notion side:** someone edits a synced column (MPN, Manufacturer, Datasheet, Package/Footprint, Category) of a linked row to something other than the library value. The sync restores the library value and posts a **comment on the row @mentioning the row's Person, Verifier and whoever last edited it**, showing both values. The sync stores the last synced values in a hidden *Library Sync* column, so it can tell this apart from a normal library update, which is not flagged. The nightly run catches Notion edits made between pushes.
- **GitHub side:** two people change the same part. The **Publish** page in the Library Manager handles it:
  - Different fields, or different parts: merged automatically, and the generated database is rebuilt.
  - The same field: the intern sees the other person's name and commit, gets a one-click email, then picks *Keep my version* or *Keep their version*. Their work is committed locally first, so nothing is lost.
- **Sync failure** (bad schematic, Notion outage): the workflow opens a GitHub issue assigned to the pusher. A board whose schematic fails to export keeps its last good BOM and shows the error in its *BOM Error* column.

### Year to year

Boards are keyed by **season + path inside the season folder**, so renaming `26-27` to `26-27 Archive` keeps the same Board pages. They are marked *Archived* instead of duplicated. A new `27-28/` folder creates new Board pages with Season = 27-28, and filtered views keep each year separate. A board whose project is deleted is marked *Removed*. Its BOM lines are archived, which is restorable from Notion's trash.

## Proposed Notion schema (not applied yet; awaiting your review)

**PCB Wiki** (existing). Existing columns are unchanged. New columns:

| Column | Type | Notes |
| --- | --- | --- |
| Library ID | Text | Written by the sync, or typed by hand to force a link |
| Library Sync | Text | Sync bookkeeping (last synced values). Hide it in views. |
| BOM Lines | Relation → BOM Lines | Two-way, paired with BOM Lines › Part |
| Used On | Rollup: BOM Lines › Board Name, show unique | e.g. "FOCB 26-27, LATCH 25-26" |
| Total Qty | Rollup: BOM Lines › Qty, sum | Across all boards and seasons |

**Boards** (new, under Electrical Wiki):

| Column | Type |
| --- | --- |
| Board | Title (e.g. FOCB) |
| Key | Text, e.g. `26-27/FOC/FOCB.kicad_pro` (sync identity) |
| Season | Select (25-26, 26-27, ...) |
| Status | Select: Active / Archived / Removed |
| Project | Text, repo path |
| GitHub | URL |
| Part Count | Number (placed parts incl. accessories) |
| BOM Error | Text |
| Last Synced | Date |
| BOM Lines | Relation → BOM Lines, paired with BOM Lines › Board |

**BOM Lines** (new, under Electrical Wiki):

| Column | Type |
| --- | --- |
| Line | Title, e.g. "FOCB · 1724470004" |
| Key | Text (sync identity) |
| Board | Relation → Boards |
| Board Name | Text, e.g. "FOCB 26-27" (feeds the Used On rollup) |
| Season | Select |
| Part | Relation → PCB Wiki (empty if the part isn't a standard part) |
| MPN, Manufacturer, Description | Text |
| Qty | Number |
| Refs | Text, e.g. "J1; J4" |
| Type | Select: Library part / Accessory / Not in library |

**Views:**
- **Boards › This season:** table filtered by Season = current, with BOM Lines shown on each board page. Open a board to see its components and quantities.
- **BOM Lines › By board:** grouped by Board and filtered by Season. Sum Qty is shown per group.
- **BOM Lines › Not in library:** Type = *Not in library*, for current-season boards. This is the to-do list of parts to add.
- **PCB Wiki › Standard Parts Library:** add the Used On and Total Qty columns.

The existing *Relevant Boards* select stays as it is. *Used On* is its automatic replacement, and you can delete *Relevant Boards* whenever you like.

## One-time setup (library owner)

1. **Notion integration:** at https://www.notion.so/profile/integrations create an internal integration called "Parts Library Sync" for the Anteater Electric Racing workspace. Capabilities: read content, update content, insert content, read comments, insert comments, and read user information without email. Copy its token.
2. **Share the databases with it:** on PCB Wiki, Boards and BOM Lines, open ••• › Connections › add "Parts Library Sync".
3. **GitHub secret:** in the repo, go to Settings › Secrets and variables › Actions › New repository secret. Name it `NOTION_TOKEN` and paste the token.
4. Put the Boards and BOM Lines database IDs into `config.json` (`boards_db`, `bom_lines_db`) and push.
5. **First run:** go to Actions › *Parts library → Notion sync* › Run workflow, and tick **Dry run**. Check the planned writes in the log, then run it again without dry run.

## Running locally

```bash
cd "26-27/Standard Parts Library/sync"
python anteater_sync.py --no-notion --season 26-27
NOTION_TOKEN=secret_xxx python anteater_sync.py --dry-run
```

`--no-notion` prints every board's BOM using your local kicad-cli. `--dry-run` reads Notion and lists what it would change.

## Categories

The library's folders under `components/` mirror Notion's *Category* options one-to-one (see `config.json` › `categories`). The Library Manager only accepts existing folders, so interns can't invent new categories. To add a category: add the option in Notion, create the folder (with a `.gitkeep`), add the mapping line, and publish. `/` isn't allowed in folder names, so the option is named *Comparator - Op-Amp*.
