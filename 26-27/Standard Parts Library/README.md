# Anteater Racing Standard Parts Library

Approved parts for our PCB designs. **Check here before adding a new part.**

Parts are managed with the [KiCad Library Manager](https://github.com/TheGabem42/kicad-library-manager) (used with permission from its author). Each part's symbol, footprint, 3D model and connector accessories (housings, crimp contacts) are stored together, and they appear in KiCad under **Anteater Parts**.

| Folder / file | What it is |
| --- | --- |
| `Setup (run once).bat` | One-time setup for each PC |
| `Open Library Manager.bat` | Opens the app (or use the desktop shortcut that Setup creates) |
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

## Finding and using a part

In KiCad, press **A** and search by part number, manufacturer or description. The footprint and 3D model are attached automatically, so you don't need to pick a footprint.

## Adding a new part

1. **Pull** in GitHub Desktop. The launcher also tries to pull for you.
2. Double-click **Anteater Parts Library** on your desktop. The app opens in your browser. Keep the black window open while you work.
3. Click **Add component**.
4. Drag in the part's files: a ZIP from SnapEDA, Ultra Librarian or the manufacturer, or a `.kicad_sym`, a `.kicad_mod` and a `.step`.
5. Choose the type: **Connector**, **IC**, **Resistor**, **Capacitor** or **Other**.
6. Fill in **Manufacturer**, **Part number** (MPN), **Description** and **Online datasheet**. Pasting a DigiKey/Mouser URL usually fails because those sites block it, so type the details in.
7. Check the **Footprint**, **Symbol** and **3D alignment** tabs. In 3D alignment, use the **Top** and **Side** views and the Move/Rotate controls until the model sits on the pads, with pins in the holes and the body flat on the board.
8. For connectors, add the mating **housing and crimp contacts** as accessories at the bottom, so they appear on the BOM.
9. Click **Save**, then click **Quit manager** in the app.
10. **Commit and push straight away** in GitHub Desktop, with a message like `Add Molex 1724470004`. Never leave library changes uncommitted.

Resistors and capacitors in standard sizes (0402/0603/0805...) share one model. Use the Resistor/Capacitor view, not a new folder.

## Rules

- **One person adds parts at a time.** Before you add a part, pull. After you save, commit and push right away. If two people edit at once, git will report a conflict in `Anteater Parts/appdata`. Ask the library owner rather than guessing.
- Only change the library through the app. Don't rename or move files inside `Anteater Parts/` by hand. You may move a *whole* component folder to another category, then click **Refresh** in the app.
- Don't rename the `Anteater Parts` folder. KiCad uses its name to find parts.
- Every part needs a correct MPN and manufacturer, and a 3D model that is checked in **3D alignment**.

## BOM export

In the app, open **BOM export** and copy the generator command. In KiCad's schematic editor, go to **Tools > Generate Legacy Bill of Materials**, add the command as a new generator, and run it. You get purchasing, PCB and accessory CSVs. The accessory CSV includes the connector housings and contacts. The command contains paths on your PC, so each person adds it on their own machine.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Parts don't show up in KiCad | Close KiCad and run `Setup (run once).bat` again. |
| "Close KiCad before connecting" | Close every KiCad window, including PCB Editor and Schematic Editor. |
| A part was added but you can't see it | Pull, then restart KiCad. |
| The app window closes immediately | Run Setup again. If it still fails, open `Open Library Manager.bat` from a terminal and send the error to the library owner. |
| Git conflict in `Anteater Parts/appdata` | Don't merge by hand. Ask the library owner. |

## Maintainers

- App source: `Library Manager/`, copied from upstream commit `bad570eb`. The `web/` folder is the prebuilt UI, so interns don't need Node.
- To update the app: clone upstream, run `npm ci` then `npm run build`, and copy everything except `node_modules/`, `.git/` and `tests/` over `Library Manager/`. Keep `setup.ps1` and `anteater_setup.py`, which are our additions.
- Local fix in `manager/kicad.py`: it handles KiCad's `"vars": null` in `kicad_common.json`, which is the default on Windows when there are no path variables. Re-apply it after updating unless upstream has fixed it.
- Library format, KiCad and ODBC details: `Library Manager/docs/ARCHITECTURE.md` and `Library Manager/docs/SETUP.md`.
