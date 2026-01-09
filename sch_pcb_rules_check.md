## Schematic & PCB Rules Check
Use this checklist before handoff or generating fabrication outputs. Mark items off as you verify them.

### 1. Familiarize yourself with the intended purpose of circuit
Learn what the schematic is meant to do by:
    - Reading FSAE rules applicable to circuit
    - Reading documentation created by circuit designer
        ASK: Does the circuit design goals match FSAE rules? 

### 2. Jot down I/O of circuit
Annotate what are the circuits inputs and outputs; sensors, signals, supply voltage, GND, etc. 
    WRITE: What is the voltage range (analog)? What is the signal made up of (digital)? Input current?

### 3. Analyze the logic of circuit 
Using your knowledge of basic circuit components (gates, transistors, diodes, etc), trace & annotate the logic of the schematic. For IC's, read through its datasheet to find its logic. If you have any doubts on any components function (basic or IC), ALWAYS read the datasheet throughouly or use reputable sources (NOT chatgpt alone).
    ASK: Does the logic on the schematic contradict my findings in step 1? Why? How can we improve it?

### 4. Component Choice Validity 
Go through each component's datasheet and look for voltage/current minimums and maximums, and any parameters it must abide by. (This is where your notes from step 2 come in). 
    ASK: Are there any contradictions between the component's parameters and its I/O in the schematic? 


### ChatGPT suggestions, use as applicable. 
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

