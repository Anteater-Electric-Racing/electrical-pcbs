# Anteater Racing Standard Parts Library

Approved parts for our PCB designs. **Check here before adding a new part.**

Parts are managed with the [KiCad Library Manager](https://github.com/TheGabem42/kicad-library-manager) (used with permission from its author). Each part's symbol, footprint, 3D model and connector accessories (housings, crimp contacts) are stored together, and they appear in KiCad under **Anteater Parts**.

| Folder / file | What it is |
| --- | --- |
| `Setup (run once).bat` / `.command` | One-time setup for each computer (`.bat` on Windows, `.command` on Mac) |
| `Open Library Manager.bat` / `.command` | Opens the app (or use the desktop shortcut that Setup creates) |
| `Anteater Parts/` | The library itself. Edit it only through the app. |
| `Library Manager/` | The app. Don't edit. |

## First time on a new PC (about 10 minutes)

You need **Windows**, **GitHub Desktop** (or git) with this repo cloned, and an internet connection.

1. Save your work and **close KiCad**.
2. Double-click **`Setup (run once).bat`** in this folder and follow the prompts. It will:
   - install Python and KiCad 10 if they're missing (answer **Y**)
   - open a download page for the **SQLite ODBC driver** if it's missing: download `sqliteodbc_w64.exe`, run it with the defaults, then press Enter in the setup window
   - connect the library to KiCad
   - put an **Anteater Parts Library** shortcut on your desktop
3. Open KiCad. In the schematic editor, press **A** (Add Symbol) and search for a part, for example `1724470004`. Parts are listed under **Anteater Parts**.

### On a Mac

Same steps, using the `.command` files. Double-click **`Setup (run once).command`**. It installs what's missing with [Homebrew](https://brew.sh) (install Homebrew first if you don't have it) and puts an **Anteater Parts Library** shortcut on your Desktop. The first time, macOS may say the file "can't be opened": right-click it › **Open** › **Open**. Quit KiCad with Cmd+Q when Setup asks.

## Finding and using a part

In KiCad, press **A** and search by part number, manufacturer or description. The footprint and 3D model are attached automatically, so you don't need to pick a footprint.

## Adding a new part

1. Find the part's row in the Notion **PCB Wiki** (Standard Parts Library view), for example *Connector (Internal)*. If there's no row, ask the library owner whether one should be added.
2. Double-click **Anteater Parts Library** on your desktop. The app opens in your browser. Keep the black window open while you work.
3. Click **Add component**.
4. Drag in the part's files: a ZIP from SnapEDA, Ultra Librarian or the manufacturer, or a `.kicad_sym`, a `.kicad_mod` and a `.step`.
5. Under **What are you adding?**, click the part's category (Regulator, MOSFET, LED...). It's the same list as the Notion PCB Wiki *Category*, and the app picks the right import mode for you. Tip: if you set **Component folder name** to the Notion row's *Component Name* (e.g. `TVS Diode - CAN`), the part links to that row automatically.
6. Fill in **Manufacturer**, **Part number** (MPN), **Description** and **Online datasheet**. Pasting a DigiKey/Mouser URL usually fails because those sites block it, so type the details in.
   In **Notes**, start with `Notion: <Component Name>;` using the row name from step 1, for example `Notion: Connector (Internal);`. This links the part to that row. You can skip it if the Notion row already has the same MPN.
7. Check the **Footprint**, **Symbol** and **3D alignment** tabs. In 3D alignment, use the **Top** and **Side** views and the Move/Rotate controls until the model sits on the pads, with pins in the holes and the body flat on the board.
8. For connectors, add the mating **housing and crimp contacts** as accessories at the bottom, so they appear on the BOM.
9. Click **Save**.
10. Open **Publish to GitHub** in the left sidebar, check the description, and click **Publish**. A few minutes later the Notion row turns **In library (un-verified)** and its MPN, manufacturer, datasheet, package and category are filled in. Then click **Quit manager**.
11. The row's **Verifier** checks the part (symbol, footprint, 3D alignment) and sets the status to **Done (approved and in library)** in Notion. If the part is changed in the library later, it goes back to *In library (un-verified)* and the Verifier gets a comment to re-check it.

**Getting teammates' new parts:** opening the app pulls them automatically. If the app is already open, click **Refresh** on All components (or **Get latest** on the Publish page). If you have unpublished changes, it tells you to **Publish** instead, which merges theirs and yours. Never pull the library in GitHub Desktop.

### If Publish says someone else changed the same part
The app shows who it was and has an **Email** button. Agree with them which version is right, then click **Keep my version** or **Keep their version**. Your work is never lost. Edits to *different* parts or different fields are merged automatically, so you won't see this for them.

### Tagging parts with boards

- **Tag a part:** click it › **Used on boards** › **Add board**. Pick the board, type its refs (e.g. `R1-R4, R7`), and click **Save board tags**. Qty fills in from the refs; type a number to override it. Then **Publish**.
- **See a board's parts:** open **Boards** in the sidebar and click the board's card, for refs, quantities, a total and **Export CSV**. Or, on **All components**, click a board in the **Board** filter row. The **Category** row filters the same way, and the two combine.
- **Boards appear automatically:** any KiCad project in a season folder (`26-27/...`), and any board folder in the current season even before it has a project (e.g. `26-27/DASH`). New ones show up when you switch back to the app; boards made on someone else's PC show up after you pull. Tags on a folder-only board move to its KiCad project once one is created inside it. **Update from schematic** fills in that board's tags from the actual schematic, replacing its manual tags. Add a board with no schematic yet with the **+** next to BOARDS. If a board folder has a `kicad/` subfolder (e.g. `26-27/DCDC/kicad`), only the projects inside it count, so docs, test boards and other projects elsewhere in that folder are ignored.
- **`26-27/VCU` is a link (git submodule) to the [OTA-pcb-testing](https://github.com/Anteater-Electric-Racing/OTA-pcb-testing) repo.** The launcher downloads its files, or run `git submodule update --init` yourself. To change the VCU board, commit in the OTA-pcb-testing repo (GitHub Desktop lists it as its own repository). Then, to make `electrical-pcbs` point at the new version, run `git submodule update --remote 26-27/VCU` and commit the updated link.
- Only the current season shows by default. Use **Show older seasons** on the Boards page, or **Older seasons…** in the filter row.

### Who added a part, and what it replaces

Click a part and scroll to **History (from Notion)** at the bottom. It shows the PCB Wiki row's **Person** (added by) and **Previous Component** (what it replaces), plus **Relevant Boards** and **Verifier** when they're set, with a link to the row. To change these, edit the row in Notion. The sync copies them into the library (`appdata/notion-info.json`), so they show up after the next sync and Refresh.

### Changing or deleting a part

- **To fix details or files:** click the part › **Edit component**, change it, **Save**, then **Publish**.
- **To remove it:** click the part › **Delete component** and confirm. This removes its symbol, footprint, 3D model, and any housings/contacts only it used. Then **Publish**: its Notion row goes back to *Missing*, so it can be re-done (e.g. a different MPN chosen in Notion).
- You can't delete a part another connector uses as an accessory. Remove it from that connector's accessory list first.
- Deleted by mistake? Before publishing, ask the library owner. After publishing, it's still in git history.

Resistors and capacitors in standard sizes (0402/0603/0805...) share one model. Use the Resistor/Capacitor view, not a new folder.

## Rules

- **You can keep KiCad open** while adding parts, publishing and getting teammates' parts. Each PC builds its own parts database (`appdata/parts.sqlite`, not in git), so git never has to replace the file KiCad keeps open. Restart KiCad, or reopen the symbol chooser, to see new parts.
- **Publish right after you save.** Don't leave changes sitting on your PC.
- **The library is the source of truth.** In Notion, edit only the planning columns (Key Specs, Person, Verifier, Notes...). The sync overwrites MPN, Manufacturer, Datasheet and Package/Footprint from the library, and comments on the row to tell you when it does. To change those values, edit the part in the app and publish.
- Only change the library through the app. Don't rename or move files inside `Anteater Parts/` by hand. You may move a *whole* component folder to another category, then click **Refresh** in the app.
- Don't rename the `Anteater Parts` folder. KiCad uses its name to find parts.
- Every part needs a correct MPN and manufacturer, and a 3D model that is checked in **3D alignment**.

## Boards and BOMs in Notion

You don't need to do anything for these. Every time a schematic in a season folder (`26-27/...`) is pushed, GitHub reads it with KiCad and updates Notion:

- **Boards:** one page per board per season. Open a board to see every component with its quantity and reference designators, connector housings and contacts included.
- **BOM Lines › Not in library:** components placed on current boards that aren't library parts yet. This is the to-do list for adding parts.
- **PCB Wiki › Used On / Total Qty:** which boards use each standard part, and how many.

Next season, put the new boards in a `27-28/` folder. Last year's boards stay in Notion, marked with their season.

## BOM export (CSV from KiCad)

In the app, open **BOM export** and copy the generator command. In KiCad's schematic editor, go to **Tools > Generate Legacy Bill of Materials**, add the command as a new generator, and run it. You get purchasing, PCB and accessory CSVs. The accessory CSV includes the connector housings and contacts. The command contains paths on your PC, so each person adds it on their own machine.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Setup keeps offering to install KiCad, but it's installed | Setup searches Program Files, Documents, Desktop, Downloads and AppData. If KiCad is somewhere else, drag `kicad.exe` (Mac: `KiCad.app`) into the setup window when it asks. It must be KiCad **10**. |
| "The footprint has N pads the symbol doesn't" | Common with SnapEDA/Ultra Librarian files: thermal/exposed pads get their own numbers. Look up what they connect to in the datasheet's pin table (usually GND), pick that pin in the panel (or **Set all to**), then **Apply and save**. The app renumbers the pads for you, so you don't need to edit the footprint in KiCad. |
| Parts don't show up in KiCad | Close KiCad and run `Setup (run once).bat` again. |
| "Close KiCad before connecting" | Close every KiCad window, including PCB Editor and Schematic Editor. |
| A part was added but you can't see it | Pull, then restart KiCad. |
| The app window closes immediately | Run Setup again. If it still fails, open `Open Library Manager.bat` from a terminal and send the error to the library owner. |
| "Git is not installed" but GitHub Desktop is | Update this folder (GitHub Desktop › Fetch/Pull once), then reopen the app. Newer versions use GitHub Desktop's built-in git. |
| Publish says "Git doesn't know who you are" | GitHub Desktop › File › Options › Git: set your name and email. |
| Publish says push failed | Sign in to GitHub in GitHub Desktop, then try again. |
| Notion row didn't turn Done | Check the GitHub **Actions** tab for a failed *Parts library → Notion sync* run, or check that your Notes have `Notion: <exact Component Name>;`. |

## Maintainers

- App source: `Library Manager/`, copied from upstream commit `bad570eb`. The `web/` folder is the prebuilt UI, so interns don't need Node.
- To update the app: clone upstream, run `npm ci` then `npm run build`, and copy everything except `node_modules/`, `.git/` and `tests/` over `Library Manager/`. Keep `setup.ps1` and `anteater_setup.py`, which are our additions.
- Local fix in `manager/kicad.py`: it handles KiCad's `"vars": null` in `kicad_common.json`, which is the default on Windows when there are no path variables. Re-apply it after updating unless upstream has fixed it.
- Notion sync, schema and one-time setup: `sync/README.md`. Publish logic: `Library Manager/manager/anteater_publish.py` and `ui/Publish.tsx`. After changing the UI, rebuild it (`npm ci`, `npm run build`) and copy `web/` in.
- Library format, KiCad and ODBC details: `Library Manager/docs/ARCHITECTURE.md` and `Library Manager/docs/SETUP.md`.
