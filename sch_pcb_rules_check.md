## Schematic & PCB Rules Check (KiCad v7/v8)

Use this tailored checklist before handoff or generating fabrication outputs. Mark items off as you verify them.

**Author:** [Your Name]  
**Project:** [Project Name]  
**Target:** [JLC, PCBWay]

---

## Phase 1: Schematic (Schematic Editor)

Goal: clean, error-free logical design that passes ERC.

### 1.1 Project & Library Hygiene
- [ ] Grid discipline (critical): symbol placement and wiring strictly on 50 mil (1.27 mm) grid. Changing to smaller grids for wiring breaks connectivity.
- [ ] Library tables: project-specific symbols saved in a local `.kicad_sym` (not cache). `.kicad_sym` must be committed/uploaded with the project. No rescued symbols in final schematic.
- [ ] Annotation: run Tools → Annotate Schematic (sort by Y or X). Ensure no duplicate designators.

### 1.2 Electrical Setup
- [ ] (optional but recommended) Power flags (`PWR_FLAG`) on the input source of every power net (e.g., connector VCC, regulator output) to avoid "pin not driven" errors. Add when ERC complains about undriven nets.
- [ ] Net classes (directives): Place → Add Net Class Directive on HV/high-current nets (e.g., `HV_Mains`, `50_Ohms`, `Power_2A`).
- [ ] Unused pins: mark with No Connect (x).
- [ ] Footprint assignment: run the Footprint Assignment tool and verify every part. Avoid generic sizes for power parts; spot-check in 3D viewer.

### 1.3 Electrical Rules Check (ERC)
- [ ] Run Inspect → Electrical Rules Checker.
- [ ] Review: "Pin not connected" (missing wire/NC?), "Input pin not driven" (missing PWR_FLAG/connection?), "Conflict between pins" (two outputs tied?).
- [ ] Deliverable: 0 errors, 0 warnings (or waivers with reason).

#### KiCad pitfalls (schematic)
- The grid trap: wiring on sub-50 mil grids looks connected but is not.
- Hidden pins: enable "show hidden pins" if using legacy symbols (e.g., 74xx).
- Global vs local labels: globals connect everywhere; locals only within sheet; hierarchical pins for sheet I/O.

---

## Phase 2: PCB Layout (PCB Editor)

Goal: physical board that meets fab capability and design intent.

### 2.1 Board Setup (first step)
- [ ] Board Setup: set min clearance/track/via to fab limits (e.g., JLC std 5 mil / 0.127 mm).
- [ ] Net classes: confirm imported classes and widths/clearances match constraints needed for power/HV/diff pairs.
- [ ] Update PCB (F8) from schematic; resolve any footprint/mapping errors.

### 2.2 Placement & Constraints
- [ ] Board outline: closed loop on `Edge.Cuts`.
- [ ] Mechanicals: at least four mounting holes placed.

### 2.3 Routing & Planes
- [ ] Create fill zones for GND/power; enable "Remove islands" with a sensible size limit to drop tiny copper remnants.
- [ ] Filled zones: press B to refill; ensure GND reaches all pads; confirm thermal relief settings (typ 10–20 mil spokes).
- [ ] (recommended) Via stitching to tie planes/returns, especially near edges or high-speed paths.

### 2.4 Design Rules Check (DRC)
- [ ] Run Inspect → Design Rules Checker.
- [ ] Must fix: clearance violations, unconnected items, courtyard overlaps, keepout violations.
- [ ] Board finish: silkscreen clear of pads; include board name and version on silk; label outputs/power pins (e.g., VDD, GND, signals) on-board in addition to connector labels (e.g., J1); add date/logo as needed.

#### KiCad pitfalls (PCB)
- Stale zones: always press B before DRC/exports.
- Edge cuts: overlapping/gapped outlines fail fab. Inspect corners.
- Mirrored text: bottom silk should read correctly when flipped (KiCad handles if using Flip).

---

## Phase 3: BOM (Manufacturing Prep)

Goal: complete sourcing-ready BOM.

- [ ] Generate BOM with every part including:
  - [ ] Link to distributor page (Digi-Key or Mouser).
  - [ ] Manufacturer name (MFN) and manufacturer part number (MPN).
  - [ ] Brief functional description.
  - [ ] PDF datasheet link.
- [ ] Export and review to ensure no refs missing and footprints align with chosen MPNs.

---

## Phase 4: Git Hygiene

Do **not** commit:
```
*-bak
*.kicad_prl
*.kicad_pcb-bak
fp-info-cache
/backups/
```

Do commit:
```
*.kicad_pro
*.kicad_sch
*.kicad_pcb
*.kicad_sym
*.kicad_dru
```