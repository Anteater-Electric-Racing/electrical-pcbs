# Anteater Racing Standard Parts Library

Approved parts for PCB designs. Check here before adding a new part.

## Layout

Matches the "Standard Parts" Notion tracker: folders are the Notion **Category**, part folders start with the Notion role name.

    Category / (Sub-type) / <Role> - <Description> /
        Symbols/      .kicad_sym
        Footprints/   .kicad_mod
        STEPS/        .stp
        Part Info.txt same fields as the Notion columns

Example: `Connector/Internal/Connector (Internal) - Mini-Fit Jr Header 4-Pos Vertical/`

## Naming parts

`<Notion role name> - <Series/Description> <Pin count/Value>`. MPN and manufacturer go in `Part Info.txt` and the symbol's Value field, not the folder name.
Good: `Connector (Internal) - Mini-Fit Jr Header 4-Pos Vertical`   Bad: `1724470004`

Symbol and STEP files use the part folder name; the footprint file uses the Package/Footprint value from Part Info.

## Library Status

`Missing` until the symbol, footprint and STEP are all present and checked, then `Complete`. Keep it in sync with Notion.

## Adding a part

1. Copy the example part folder into the right Category folder and rename it.
2. Drop in the symbol, footprint and STEP, renamed to the part name.
3. Fill in `Part Info.txt` (all Notion fields) and update Library Status.
4. Check the footprint name matches the symbol's Footprint property and the 3D model loads aligned.
