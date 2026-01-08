## Schematic & PCB Rules Check

THIS IS A DRAFT!!!!

Use this checklist before handoff or generating fabrication outputs. Mark items off as you verify them.

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
- Upload to shared drive with date/revision; notify stakeholders.

