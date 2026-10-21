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
5. Choose the type: **Connector**, **IC**, **Resistor**, **Capacitor** or **Other**. Then set **Category** to the part's Notion *Category* (Regulator, MOSFET, LED...). The categories are the same list as the Notion PCB Wiki. Tip: if you set **Component folder name** to the Notion row's *Component Name* (e.g. `TVS Diode - CAN`), the part links to that row automatically.
6. Fill in **Manufacturer**, **Part number** (MPN), **Description** and **Online datasheet**. Pasting a DigiKey/Mouser URL usually fails because those sites block it, so type the details in.
   In **Notes**, start with `Notion: <Component Name>;` using the row name from step 1, for example `Notion: Connector (Internal);`. This links the part to that row. You can skip it if the Notion row already has the same MPN.
7. Check the **Footprint**, **Symbol** and **3D alignment** tabs. In 3D alignment, use the **Top** and **Side** views and the Move/Rotate controls until the model sits on the pads, with pins in the holes and the body flat on the board.
8. For connectors, add the mating **housing and crimp contacts** as accessories at the bottom, so they appear on the BOM.
9. Click **Save**.
10. Open **Publish to GitHub** in the left sidebar, check the description, and click **Publish**. A few minutes later the Notion row turns *Done (added to KiCad library)* and its MPN, manufacturer, datasheet and package are filled in. Then click **Quit manager**.

### If Publish says someone else changed the same part
The app shows who it was and has an **Email** button. Agree with them which version is right, then click **Keep my version** or **Keep their version**. Your work is never lost. Edits to *different* parts or different fields are merged automatically, so you won't see this for them.

### Changing or deleting a part

- **To fix details or files:** click the part › **Edit component**, change it, **Save**, then **Publish**.
- **To remove it:** click the part › **Delete component** and confirm. This removes its symbol, footprint, 3D model, and any housings/contacts only it used. Then **Publish**: its Notion row goes back to *Missing*, so it can be re-done (e.g. a different MPN chosen in Notion).
- You can't delete a part another connector uses as an accessory. Remove it from that connector's accessory list first.
- Deleted by mistake? Before publishing, ask the library owner. After publishing, it's still in git history.

Resistors and capacitors in standard sizes (0402/0603/0805...) share one model. Use the Resistor/Capacitor view, not a new folder.

## Rules

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
| Parts don't show up in KiCad | Close KiCad and run `Setup (run once).bat` again. |
| "Close KiCad before connecting" | Close every KiCad window, including PCB Editor and Schematic Editor. |
| A part was added but you can't see it | Pull, then restart KiCad. |
| The app window closes immediately | Run Setup again. If it still fails, open `Open Library Manager.bat` from a terminal and send the error to the library owner. |
| Publish says "Git doesn't know who you are" | GitHub Desktop › File › Options › Git: set your name and email. |
| Publish says push failed | Sign in to GitHub in GitHub Desktop, then try again. |
| Notion row didn't turn Done | Check the GitHub **Actions** tab for a failed *Parts library → Notion sync* run, or check that your Notes have `Notion: <exact Component Name>;`. |

## Maintainers

- App source: `Library Manager/`, copied from upstream commit `bad570eb`. The `web/` folder is the prebuilt UI, so interns don't need Node.
- To update the app: clone upstream, run `npm ci` then `npm run build`, and copy everything except `node_modules/`, `.git/` and `tests/` over `Library Manager/`. Keep `setup.ps1` and `anteater_setup.py`, which are our additions.
- Local fix in `manager/kicad.py`: it handles KiCad's `"vars": null` in `kicad_common.json`, which is the default on Windows when there are no path variables. Re-apply it after updating unless upstream has fixed it.
- Notion sync, schema and one-time setup: `sync/README.md`. Publish logic: `Library Manager/manager/anteater_publish.py` and `ui/Publish.tsx`. After changing the UI, rebuild it (`npm ci`, `npm run build`) and copy `web/` in.
- Library format, KiCad and ODBC details: `Library Manager/docs/ARCHITECTURE.md` and `Library Manager/docs/SETUP.md`.
