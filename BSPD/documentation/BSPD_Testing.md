# BSPD Testing & Verification

This document defines a repeatable bench test and verification procedure for the BSPD (Brake System Plausibility Device) board.

For full BSPD design and signal descriptions, see `BSPD_documentation.md`. For the authoritative FSAE rule text that the BSPD must satisfy, see **Appendix A – FSAE Rule Checklist** at the end of this document and the official ruleset.

---

## 1. Test Environment & Equipment

**Required equipment**

- Adjustable GLV bench supply (e.g., 10–15 V) with current limit
- Multimeter (voltage, resistance, and current measurement)
- Oscilloscope (2+ channels) with probes and ground leads
- Signal sources for BRAKE and CURRENT channels:
  - Potentiometer fixtures or function generator
- Jumper wires / clip leads for simulating opens/shorts and test-point access
- Datasheets / schematics and latest BSPD BoM
- BSPD board under test

**Safety**

- Perform all tests with the Tractive System disabled and the BSPD isolated from any motor power stage.
- Follow team HV/LV safety procedures and PPE requirements when integrating into the vehicle.

---

## 2. Pre‑Power Hardware Checklist

Complete this section **before** applying power to the board.

### 2.1 Visual Inspection & Orientation

- [ ] All ICs (`U1–U6`, `Q1`) have correct orientation (pin 1 markers aligned with silkscreen, notch direction correct).
- [ ] Diodes and polarized components (electrolytic capacitors, LEDs) match silkscreen polarity.
- [ ] Connectors `J1` and `J2` are the correct part numbers and oriented per drawing (keying and latch direction).
- [ ] No visible solder bridges, tombstoned parts, or missing components in critical signal paths (comparators, logic ICs, MOSFET).

### 2.2 Part Pinout Verification

- [ ] Cross-check pinout for `J2` (primary harness connector) against the table in `BSPD_documentation.md`:
  - [ ] Pin 2 is GND, Pin 3 is +12 V, Pins 4/6 are `B_IN` and `C_IN`, Pin 5 is `BSPD_FAULT`.
- [ ] Cross-check pinout for `J1` (board-to-board connector) against documentation.

### 2.3 Continuity & Power Net Checks

- [ ] Verify continuity of **GND**:
  - [ ] GND pins between `J1`, `J2`, and representative GND test points show low resistance (near 0 Ω).
- [ ] Verify continuity of **VDD / +12 V**:
  - [ ] +12 V pins between `J1`, `J2`, and decoupling capacitors near logic ICs show low resistance along the rail.
- [ ] Check for shorts:
  - [ ] Resistance between +12 V and GND at the connector is **high** (no direct short).
  - [ ] No unintended short between sensor inputs and supply rails.

---

## 3. Power‑Up & Electrical Verification

These tests verify basic power behavior, current draw, and noise margins before functional testing.

### 3.1 Initial Power‑Up Sanity Check

1. Set bench supply to 12 V with a conservative current limit (100 mA).
2. Connect +12 V and GND to `J2` (or `J1`) per pinout; leave `B_IN` and `C_IN` at 0 V (or disconnected with appropriate pulldowns).
3. Enable the supply and observe:
   - [ ] Board powers without exceeding current limit.
   - [ ] No unexpected heating, smoke, or abnormal smell.
4. Measure **idle supply current** at 12 V and log it:
   - [ ] Idle current is within expected range

### 3.2 Supply Voltage Verification (Current/Voltage Verification)

- [ ] Measure voltage at +12 V pins on `J1`/`J2` relative to GND; confirm within system tolerance (11.5 V to 12.5 V).
- [ ] Verify supply voltage at key IC VDD pins (comparators, logic ICs) is within the same range.
- [ ] Confirm `BSPD_FAULT` output node is at the correct default level (defined in `BSPD_documentation.md`) with no applied inputs.

### 3.3 Power Measurement at Test Conditions (Current/Voltage Power Measurement)

1. With 12 V applied, exercise representative high-activity states:
   - Brake applied only.
   - Current-channel applied only.
   - Both channels applied (plausibility fault condition).
2. For each condition, record:
   - [ ] Supply voltage at the board.
   - [ ] Supply current drawn by the BSPD.
3. Confirm total power consumption (V × I) remains within the design envelope and connector / wiring ratings.

### 3.4 Noise & Stability Test

- [ ] Attach an oscilloscope probe to +12 V near the BSPD (for example, decoupling capacitor pad) and to GND.
- [ ] While sweeping `B_IN` and `C_IN` through thresholds and toggling fault conditions:
  - [ ] Confirm supply ripple and transient spikes remain within acceptable bounds for the GLV system.
  - [ ] Confirm outputs (`BSPD_FAULT`, `BOTH_ON`) transition cleanly without repeated chatter or oscillation.

If significant ringing or oscillation is observed, consult the \"Delay and Fall-Time Network\" and grounding sections in `BSPD_documentation.md` before proceeding.

### 3.5 Threshold Margin & Voltage Sweep Logging

Use this section to quantify threshold margins and switching behavior across GLV supply variation.

1. For each supply level (11.5 V, 12.0 V, 12.5 V), repeat the relevant parts of Sections 3.1–3.3 and 4.1–4.3.
2. At each supply level, record measured values in the table below (fill in cells during testing):

| Parameter                                | Test Condition / Notes                     | 11.5 V | 12.0 V | 12.5 V |
|------------------------------------------|--------------------------------------------|--------|--------|--------|
| VDD–GND resistance (unpowered)          | Measured at connector before power‑up      |        |        |        |
| Idle power consumption                  | No inputs asserted                         |        |        |        |
| Brake threshold voltage                 | `B_IN` at which `B_APPLIED` asserts        |        |        |        |
| Brake margin to false‑trip              | Headroom between normal max and threshold  |        |        |        |
| Current‑channel threshold voltage       | `C_IN` at which `P_APPLIED` asserts        |        |        |        |
| Current‑channel margin to false‑trip    | Headroom between normal max and threshold  |        |        |        |
| BSPD fault trip delay                   | Time from BOTH_ON to `BSPD_FAULT`          |        |        |        |
| Additional observation / measurement #1 |                                            |        |        |        |
| Additional observation / measurement #2 |                                            |        |        |        |

---

## 4. Functional Test Procedures

These tests validate BSPD behavior against FSAE rules EV.7.7.1–EV.7.7.4 and related shutdown requirements. Whenever possible, correlate observations with test points documented in `BSPD_documentation.md`.

### 4.1 Brake Input Test

**Objective:** Verify brake channel threshold behavior without generating a fault when the current channel is inactive. (Supports EV.7.7.1.)

**Procedure**

1. Ensure `C_IN` (CURRENT channel) is held below its threshold.
2. Slowly ramp `B_IN` from 0 V to its maximum test value.
3. Observe:
   - [ ] `B_APPLIED` asserts when `B_IN` crosses the configured brake threshold.
   - [ ] No fault outputs (`BSPD_FAULT`, `B_ERROR`, `P_ERROR`, `BOTH_ON`) assert while only the brake channel is above threshold.

### 4.2 Current‑Channel Input Test

**Objective:** Verify current-channel threshold behavior without generating a fault when the brake channel is inactive. (Supports EV.7.7.1.)

**Procedure**

1. Ensure `B_IN` is held below its threshold.
2. Slowly ramp `C_IN` (CURRENT channel) from 0 V to its maximum test value.
3. Observe:
   - [ ] `P_APPLIED` asserts when `C_IN` crosses the configured current-channel threshold.
   - [ ] No fault outputs assert while only the current channel is above threshold.

### 4.3 Plausibility Test (Simultaneous Application)

**Objective:** Verify that simultaneous brake and current-channel application triggers a BSPD fault with the required timing behavior. (Directly validates EV.7.7.2.)

**Procedure**

1. Set both `B_IN` and `C_IN` below thresholds.
2. Step or ramp `B_IN` and `C_IN` above their thresholds so that both `B_APPLIED` and `P_APPLIED` are true.
3. Observe:
   - [ ] `BOTH_ON` asserts once both channels exceed thresholds.
   - [ ] `BSPD_FAULT` asserts after the designed delay (see calibration targets; must be < 500 ms).
   - [ ] Fault remains latched until the system reset path is exercised (per latch-board / system integration).

### 4.4 Open‑Circuit Detection Test

**Objective:** Verify detection of open-circuit conditions on each sensor input. (Supports EV.7.7.3.)

**Procedure**

1. Apply nominal sensor-level voltage on `B_IN`, then disconnect the signal to simulate an open (or use a fixture that lifts the connection).
2. Observe:
   - [ ] `B_OPEN` asserts.
   - [ ] BSPD transitions to a faulted state (`BSPD_FAULT` asserted, appropriate error LED on).
3. Repeat for the CURRENT channel by opening `C_IN`:
   - [ ] `P_OPEN` asserts and BSPD enters fault state.

### 4.5 Short‑Circuit Detection Test

**Objective:** Verify detection of short-to-rail or short-to-ground conditions on each sensor input. (Supports EV.7.7.3.)

**Procedure**

1. Using a safe series resistor or fixture, simulate a short on the brake input (for example, brake signal forced hard to GND or +V beyond valid range).
2. Observe:
   - [ ] `B_SHORT` asserts.
   - [ ] BSPD enters fault state; `BSPD_FAULT` and the appropriate error LED assert.
3. Repeat for the CURRENT channel:
   - [ ] `P_SHORT` asserts and BSPD enters fault state.

### 4.6 Debug LED Confirmation (v2026.3)

**Objective:** Verify that debug LEDs correctly indicate fault categories for bench diagnostics. (Supports EV.7.7.4 test demonstration readiness.)

- [ ] Induce a brake-side fault (open or short) and confirm `B_ERROR` LED1 illuminates.
- [ ] Induce a current-channel fault and confirm `P_ERROR` LED2 illuminates.
- [ ] Induce a plausibility fault (both channels above threshold) and confirm `BOTH_ON` LED3 illuminates.

---

## 5. BSPD Bring‑Up & Verification Checklist

Use this condensed checklist as a final gate before vehicle integration or competition.

### 5.4 Documentation & Rule Compliance

- [ ] Calibration values (thresholds, fault delay) recorded and stored with the vehicle documentation.
- [ ] BSPD behavior reviewed against FSAE rules EV.7.7.1–EV.7.7.4 and related shutdown rules.
- [ ] FSAE rule checklist in Appendix A reviewed and confirmed for the BSPD implementation.

---

## Appendix A – FSAE Rule Checklist

### Technical Inspection – EV

- [ ] `EV.4.5` **Accelerator Pedal Position Sensor - APPS** - Refer to T.4.2 for specific requirements of the APPS
- [ ] `EV.4.6` **Brake System Encoder - BSE** - Refer to T.4.3 for specific requirements of the BSE
- [ ] `EV.4.7.2` **APPS / Brake Pedal Plausibility Check Fault** - If the two conditions in EV.4.7.1 occur at the same time: a. Power to the Motor(s) must be immediately and completely shut down b. The Motor shut down must stay active until the APPS signals less than 5% Pedal Travel, with or without brake operation. The team must be able to demonstrate these actions at Technical Inspection
- [ ] `EV.5.2.1` **All Tractive System components must be rated for the maximum Tractive System voltage**
- [ ] `EV.5.2.4` **Soldering** - Soldering electrical connections in the high current path is prohibited. Soldering wires to cells for the voltage monitoring input of the BMS is permitted, these wires are not part of the high current path
- [ ] `EV.5.2.5` **Wiring** - Each wire used in a Tractive Battery Container, whether it is part of the GLV or Tractive System, must be rated to the maximum Tractive System voltage
- [ ] `EV.6.2.1` **Insulation material must:** - Insulation material must: a. Be appropriate for the expected surrounding temperatures b. Have a minimum temperature rating of 90°C
- [ ] `EV.6.2.2` **Insulating tape or paint may be part of the insulation, but must not be the only insulation**
- [ ] `EV.6.3.1` **Wire Size** - All wires and terminals and other conductors used in the Tractive System must be sized for the continuous current they will conduct
- [ ] `EV.6.3.2` **All Tractive System wiring must:** - All Tractive System wiring must: a. Be marked with wire gauge, temperature rating and insulation voltage rating A serial number or a norm printed on the wire is sufficient if this serial number or norm is clearly bound to the wire characteristics for example by a data sheet. b. Have temperature rating more than or equal to 90°C
- [ ] `EV.6.3.3` **Tractive System wiring must be:** - a. Done to professional standards with sufficient strain relief b. Protected from loosening due to vibration c. Protected against damage by rotating and / or moving parts d. Located out of the way of possible snagging or damage
- [ ] `EV.6.3.4` **Any Tractive System wiring that runs outside of electrical enclosures:** - Any Tractive System wiring that runs outside of electrical enclosures: a. Must meet one of the two: • Enclosed in separate orange nonconductive conduit • Use an orange shielded cable b. The conduit or shielded cable must be securely anchored at each end to let it withstand a force of 200 N without straining the cable end crimp c. Any shielded cable must have the shield grounded
- [ ] `EV.6.3.5` **Wiring that is not part of the Tractive System must not use orange wiring or conduit**
- [ ] `EV.6.5.1` **Separation of Tractive System and GLV System:** - The entire Tractive System and GLV System must be completely galvanically separated
- [ ] `EV.6.5.3` **Tractive System and GLV circuits must not be in the same conduit or connector** - Tractive System and GLV circuits must not be in the same conduit or connector except as permitted in in EV.7.8.4
- [ ] `EV.6.6.1` **Overcurrent Protection Required** - All electrical systems (Low Voltage and High Voltage) must have appropriate Overcurrent Protection/Fusing.
- [ ] `EV.6.6.2` **Overcurrent Protection devices** - Unless otherwise permitted in the Rules, all Overcurrent Protection devices must: a. Be rated for the highest voltage in the systems they protect Overcurrent Protection devices used for DC must be rated for DC and must carry a DC rating equal to or more than the system voltage b. Have a continuous current rating less than or equal to the continuous current rating of any electrical component that it protects c. Have an interrupt current rating higher than the theoretical short circuit current of the system that it protects
- [ ] `EV.6.6.6` **Splicing Cables** - If conductor ampacity is reduced below the ampacity of the upstream Overcurrent Protection, the reduced conductor longer than 150 mm must have additional Overcurrent Protection. This additional Overcurrent Protection must be: a. 150 mm or less from the source end of the reduced conductor b. On the positive and the negative conductors in the Tractive System c. On the positive conductor in the Grounded Low Voltage System
- [ ] `EV.7.1.3` **The BMS, IMD, and BSPD parts of the Shutdown Circuit must be Normally Open** - The BMS, IMD, and BSPD parts of the Shutdown Circuit must be Normally Open
- [ ] `EV.7.1.4` **The BMS, IMD and BSPD must have completely independent circuits** - The BMS, IMD and BSPD must have completely independent circuits to Open the Shutdown Circuit. The design of the respective circuits must make sure that a failure cannot result in electrical power being fed back into the Shutdown Circuit.
- [ ] `EV.7.7.1` **BSPD** - The vehicle must have a standalone nonprogrammable circuit to check for simultaneous braking and high power output. The BSPD must be provided in addition to the APPS / Brake Pedal Plausibility Check (EV.4.7)
- [ ] `EV.7.7.2` **BSPD Bahavior** - The BSPD must Open the Shutdown Circuit EV.7.2.2 when the two of these exist: • Demand for Hard Braking EV.4.6 • Tractive System current is at a level where 5 kW of electrical power in the DC circuit is delivered to the Motor(s) at the nominal battery voltage. The BSPD may delay opening the shutdown circuit up to 0.5 sec to prevent false trips.
- [ ] `EV.7.7.3` **BSPD Behavior** - The BSPD must Open the Shutdown Circuit EV.7.2.2 when there is an open or short circuit in any sensor input
- [ ] `EV.7.7.4` **The team must have a test to demonstrate BSPD operation at Electrical Technical Inspection.** - The team must have a test to demonstrate BSPD operation at Electrical Technical Inspection. a. Power must not be sent to the Motor(s) of the vehicle during the test b. The test must prove the function of the complete BSPD in the vehicle, including the current sensor. The suggested test would introduce a current by a separate wire from an external power supply simulating the Tractive System current while pressing the brake pedal.
- [ ] `IN.2.2.1` **Given dimensions are absolute, and do not have any tolerance unless specifically stated**
- [ ] `IN.2.2.3` **No allowance is given for measurement accuracy or error**
- [ ] `IN.2.3` **Visible Access** - All items on the Technical Inspection Form must be clearly visible to the technical inspectors without using instruments such as endoscopes or mirrors Methods to provide visible access include but are not limited to removable body panels, access panels, and other components
- [ ] `IN.5.1` **Inspection Items** - Bring these to Tractive Battery Pack and Charger Inspection: • Tractive Battery Pack mounted on the Hand Cart EV.4.10 • Spare Battery Pack(s) and Tractive Battery components (if applicable) EV.5.1.3 • Charger(s) for the Tractive Battery EV.8.1 • Tractive Battery Container samples (if applicable) F.10.2.1.c, F.10.2.2.c • Electrical Systems Form (ESF) and Component Data Sheets EV.2 • Electronic copies of any submitted Rules Questions with the received answer GR.7 These basic tools in good condition: • Insulated cable shears • Insulated screw drivers • Multimeter with protected probe tips • Insulated tools, if screwed connections are used in the Tractive System • Face Shield • HV insulating gloves which are 12 months or less from their test date • Two HV insulating blankets of minimum 0.83 m² each • Safety glasses with side shields for all team members that might work on the Tractive System or Battery Pack
