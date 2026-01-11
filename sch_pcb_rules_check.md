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

