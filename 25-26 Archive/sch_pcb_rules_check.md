## Schematic & PCB Rules Check
Step-by-step instructions for schematic/PCB review. I/O = inputs and outputs

### Part 1: Schematic and BOM review

### 1. Familiarize yourself with the intended purpose of circuit
Learn what the schematic is meant to do by:
    - Reading FSAE rules applicable to circuit
    - Reading documentation created by circuit designer
        ASK: Does the circuit design goals match FSAE rules? 

### 2. Jot down I/O of circuit
Annotate what are the circuits inputs and outputs: sensors, signals, supply voltage, GND, etc. 
    WRITE: What is the voltage range (analog)? What is the signal made up of (digital)? Input current range? NOTE: if IO includes off-the-shelf components, check component datasheet.
        EX: Input includes an analog sensor, read its datasheet to find the analog sensor's voltage and current range. 
    ASK: When the I/O interphases with other boards, collaborate with team to make sure everyone is on the same page on I/O requirements of each board. 

### 3. Analyze the logic of circuit 
Using your knowledge of basic circuit components (gates, transistors, diodes, etc), trace & annotate the logic of the schematic. For IC's, read through its datasheet to find its logic. If you have any doubts on a components' function (basic or IC), ALWAYS read the datasheet throughouly or use reputable sources (NOT chatgpt).
    ASK: Does the logic on the schematic contradict my findings in step 1? Why? How can we improve it?

### 4. Component Choice Validity 
Go through each component's datasheet and look for voltage/current minimums and maximums, and any parameters it must abide by. (This is where your notes from step 2 come in). Go through each pin. 
    ASK: 
        -Are there any contradictions between the component's parameters and its I/O in the schematic?
            EX: 
                -IC chip has a maximum supply voltage of 5V. In the schematic, the supply voltage is connected to a 12V line. Action: Find replacement with 12V supply voltage capability or consider implementing a voltage regulator or step down DC converter. For-drop in replacements, pick a part with the same footprint. 
                - Two 10 ohm 1/10W SMD resistors form a voltage divider using 12V; the voltage divider is connected to an op-amp (high impedance pin).Power across resistors: 12V/20Ohm = 0.6A ; 0.6A*12V = 7.2W. Because these resistors are only rated for 1/10W, they would fry. Action: Increase resistance until less than 1/10W is across the line (Remember, 1/10W is the limit, realistically you want considerably less than 1/10W). In cases where a low resistance/high power is required, change to higher rated power resistors. 
        -Is the component chosen obsolete, low stock, or not recommended for new designs (NRND)? Search online for part availability, status, and pricing (octopart.com, digikey, mouser, etc).
        -Could I replace this component with a part from the Shared Parts List?
        -If expensive ($10+), could there be a cheaper alternative?


### Part 2: PCB Review

### 1. Schematic to PCB accuracy 
Verify that the schematic and PCB connections are the same. Mismatches can happen!

### 2. Traces
Go through each net and check trace dimensions and geometry. 
    ASK:
    -Are the traces the correct thickness/depth for its voltage, current, power, and/or signal demands? Generally, power traces are thicker than signal traces. 
        IMPORTANT!!!!!!!!!!!!!!!!!!!!!!: Differential signals (data signals consisting of 2 wires, EX: CANBUS) must be impedance matched. I.e. an impedance across both signals must be maintained, the impedance value depends on the signal type. EX: CANBUS requires 120Ohm differential impedance (this is why they are twisted + need 120 ohm termination resistor). There are online/software tools you can use to adjust traces for this purpose. 
    -Are signal paths isolated? Power lines can interfere with signal lines. 
    -Are there sharp (~90deg) turns on the traces? Sharp trace turns not recommended (reflection). 

### 3. Footprint Validity
Verify that each component's footprint matches the one described in its datasheet. Look for pad dimensions and pin locations. 

### 4. Practical Geometry
Verify that all components are reasonably spaced and easy-to-install. EX: previous PDB versions had its connectors too close together, making some mating connectors impossible/difficult to install. Remember: we want as small as possible but practical!


### General ChatGPT suggestions, review and use as applicable. 
### Project Hygiene
- Version control clean; backup archives up to date.
- All symbols/footprints from versioned libraries; no temporary local edits.
- Title block filled (rev, date, author, P/N); board stackup documented.
- Global annotations/refs updated; no duplicate references.

### Schematic Checklist
- Power flags placed; PWR/GND nets consistent and named clearly.
- Net labels used instead of long wires; buses have harness definitions where needed.
- Inputs have defined pull-ups/downs or drive sources; unused pins terminated per datasheet.
- Decoupling placed per IC requirements (value, voltage rating, count).
- Protection: TVS/clamps/fuses where required; polarity and orientation noted.
- Differential pairs defined and polarity labeled (+/–) consistently across pages.
- Analog vs digital domains isolated and nets named accordingly.
- Design rules: voltage/current ratings meet margins; resistor wattage checked.
- Simulation/validation notes captured (key calculations/assumptions).

### PCB Checklist
- Board outline closed; layer stack matches fab notes; origin set.
- Net classes set (clearance/width/via sizes); matched to fabrication capability.
- Critical nets (diff pairs, clocks, sense) length tuned and impedance-controlled as required.
- Return paths solid; stitching vias added; no split-plane crossings for high-speed.
- Decoupling capacitors as close as possible to IC pins with short loops.
- Thermal relief: power devices have copper area, vias to planes, keepouts respected.
- Clearance checks around high-voltage/creepage nets; slots or keepouts added if needed.
- Mechanical: mounting holes plated/non-plated as intended; courtyard violations resolved.
- Silkscreen legible; polarity/orientation marks clear; testpoints labeled and accessible.
- Fiducials placed for assembly; panelization notes recorded if required.

### ERC/DRC/Outputs
- ERC warnings reviewed and resolved or waived with justification.
- DRC run with board-specific constraints; zero unresolved errors.
- 3D view pass for component orientation/interference; keepout violations cleared.
- Gerbers/ODB++/IPC-2581, drill, IPC-D-356, pick-and-place, and BOM generated and spot-checked.
- Fab/assembly drawing includes stackup, drill table, notes, and critical dimensions.

### Handoff
- Release package includes: source files, fabrication/assembly outputs, readme with revision history.
- Upload to shared drive with date/revision
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