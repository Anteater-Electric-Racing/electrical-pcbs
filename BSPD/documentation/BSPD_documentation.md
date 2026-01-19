# BSPD (Brake System Plausibility Device) Documentation

## Overview

The Brake System Plausibility Device (BSPD) is a safety-critical circuit required by Formula SAE rules. It monitors the brake pedal and accelerator pedal positions to detect implausible driving conditions where both pedals are pressed simultaneously with significant motor power being applied. When a fault condition is detected, the BSPD opens the shutdown circuit to disable the tractive system.

## Version Information

- **Version:** 2026.1
- **Design Tool:** KiCad 9.0

---

## Functional Description

### Purpose

The BSPD ensures vehicle safety by:
1. Detecting simultaneous hard braking and accelerator pedal application
2. Monitoring for sensor open circuit faults
3. Monitoring for sensor short circuit faults

The output to latch board then ensures that:
4. Latching fault conditions until a manual reset is performed

### Operating Principle

The circuit continuously monitors two analog signals:
- **BRAKE** - Brake pedal position sensor signal
- **PEDAL** - Accelerator pedal position sensor signal

These signals are compared against configurable threshold voltages to determine:
- `BRAKE_APPLIED` - Brake pedal is pressed beyond threshold
- `PEDAL_APPLIED` - Accelerator pedal is pressed beyond threshold

When both conditions are true simultaneously (`BOTH_ON`), a fault is triggered. A fault may also be triggered due to short or open circuit.

---

## Circuit Architecture

### Major Functional Blocks

1. **Input Conditioning**
   - Signal filtering and buffering for BRAKE and PEDAL inputs
   - Protection against transients and noise

2. **Threshold Comparators**
   - `BRAKE_THRESHOLD` - Reference voltage for brake detection
   - `PEDAL_THRESHOLD` - Reference voltage for accelerator detection
   - LM393 dual comparators (U3, U4, U6) for signal comparison
   - PTD901 potentiometers (VR1-VR4) for threshold adjustment

3. **Fault Detection Logic**
   - **Open Circuit Detection** (`OPEN_CIRCUIT`)
     - `BRAKE_OPEN` - Detects brake sensor open circuit
     - `PEDAL_OPEN` - Detects pedal sensor open circuit
   - **Short Circuit Detection** (`SHORT_CIRCUIT`)
     - `BRAKE_SHORT` - Detects brake sensor short to ground/supply
     - `PEDAL_SHORT` - Detects pedal sensor short to ground/supply
   - **Plausibility Detection** (`BOTH_ON`)
     - Detects simultaneous brake and accelerator application

4. **Error Aggregation**
   - `BRAKE_ERROR` - Combined brake fault signal
   - `PEDAL_ERROR` - Combined pedal fault signal
   - `FAULT_SENSED` - Any fault condition detected

5. **Output Latch**
   - `BSPD_FAULT` - Latched fault output to shutdown circuit
   - Implemented using Schmitt trigger inverters (40106), which can be bypassed if needed.

6. **Logic Gates**
   - 4081 Quad AND gates - Combines fault conditions
   - 4071 Quad OR gates - Aggregates multiple fault sources

---

## Key Components

### Integrated Circuits

| Reference | Value | Description | Package |
|-----------|-------|-------------|---------|
| U1 | 40106 | Hex Schmitt Trigger Inverter | DIP-14 Socket |
| U2 | 4081 | Quad 2-Input AND Gate | DIP-14 Socket |
| U3, U4, U6 | LM393 | Dual Comparator | DIP-8 Socket |
| U5 | 4071 | Quad 2-Input OR Gate | DIP-14 Socket |

### Potentiometers

| Reference | Value | Description | Qty |
|-----------|-------|-------------|-----|
| VR1, VR2, VR3, VR4 | PTD901-1015F-B203 | Threshold Adjustment Pots | 4 |

### Transistors

| Reference | Value | Description | Package |
|-----------|-------|-------------|---------|
| Q1 | IRLIZ44N | N-Channel MOSFET | TO-220F |

### Capacitors

| Reference | Value | Footprint | Qty |
|-----------|-------|-----------|-----|
| C1 | 10µF | 0603 SMD | 1 |
| C2, C3 | 1nF | 0603 SMD | 2 |
| C4 | 3.3µF | 0603 SMD | 1 |
| C5, C6, C7, C8, C9, C10 | 0.1µF | 0603 SMD | 6 |

### Resistors

| Reference | Value | Footprint | Qty |
|-----------|-------|-----------|-----|
| R1, R2, R17 | 1kΩ | 0603 SMD | 3 |
| R3, R4, R5, R6, R7, R8, R9, R10, R11 | 10kΩ | 0603 SMD | 9 |
| R12, R13, R14, R15, R18, R19 | 20kΩ | 0603 SMD | 6 |
| R16 | 120kΩ | 0603 SMD | 1 |
| R_Bypass1, R_Bypass2 | 0Ω | 0603 SMD | 2 |

### Diodes

| Reference | Value | Footprint | Qty |
|-----------|-------|-----------|-----|
| D1, D2 | Diode | 0603 SMD | 2 |

### Connectors

| Reference | Value | Description | Qty |
|-----------|-------|-------------|-----|
| J1, J2, J3, J4 | Conn_01x02 | Molex CLIK-Mate 2-pin (P1.25mm) | 4 |

### Test Points

| Reference | Signal | Description |
|-----------|--------|-------------|
| TP1 | BRAKE | Brake sensor input |
| TP2 | PEDAL | Pedal sensor input |
| TP3 | SC | Short Circuit detection |
| TP4 | OC | Open Circuit detection |
| TP5 | BRAKE_TH | Brake threshold reference |
| TP6 | PEDAL_TH | Pedal threshold reference |
| TP7 | B_APPLIED | Brake applied signal |
| TP8 | P_APPLIED | Pedal applied signal |
| TP9 | BOTH_ON | Both pedals active |
| TP10 | B_SHORT | Brake short circuit |
| TP11 | B_OPEN | Brake open circuit |
| TP12 | P_SHORT | Pedal short circuit |
| TP13 | P_OPEN | Pedal open circuit |
| TP14 | B_ERROR | Brake error aggregate |
| TP15 | P_ERROR | Pedal error aggregate |
| TP16 | FAULT_SENSED | Any fault detected |
| TP17 | BSPD_FAULT | Final fault output |

### Mechanical

| Reference | Description | Qty |
|-----------|-------------|-----|
| H1, H2, H3, H4 | 3mm Mounting Holes | 4 |

---

## Signal Definitions

### Input Signals

| Signal | Description | Range |
|--------|-------------|-------|
| BRAKE | Brake pedal position sensor | 0-5V analog |
| PEDAL | Accelerator pedal position sensor | 0-5V analog |

### Internal Signals

| Signal | Description | Active Level |
|--------|-------------|--------------|
| BRAKE_APPLIED | Brake pressed above threshold | HIGH |
| PEDAL_APPLIED | Accelerator pressed above threshold | HIGH |
| BRAKE_THRESHOLD | Brake comparator reference | - |
| PEDAL_THRESHOLD | Accelerator comparator reference | - |
| BOTH_ON | Both pedals simultaneously active | HIGH |
| BRAKE_OPEN | Brake sensor open circuit detected | HIGH |
| BRAKE_SHORT | Brake sensor short circuit detected | HIGH |
| PEDAL_OPEN | Accelerator sensor open circuit detected | HIGH |
| PEDAL_SHORT | Accelerator sensor short circuit detected | HIGH |
| BRAKE_ERROR | Any brake sensor fault | HIGH |
| PEDAL_ERROR | Any accelerator sensor fault | HIGH |
| OPEN_CIRCUIT | Open circuit fault threshold | - |
| SHORT_CIRCUIT | Short short circuit fault threshold | - |
| FAULT_SENSED | Any fault condition detected | HIGH |

### Output Signals

| Signal | Description | Levels |
|--------|-------------|--------------|
| BSPD_FAULT | Fault output to latch circuit | GND when FAULT_SENSED, 12V otherwise |

---

## Power Supply

- **Main Supply:** +12V (vehicle power bus)
- **Bulk Capacitance:** C1 (10µF)
- **Decoupling:** C5-C10 (0.1µF ceramic)
- **Filtering:** C2, C3 (1nF)
- **Footprint:** All capacitors 0603 SMD

---

## PCB Information

### Design Specifications

- **Schematic File:** `bspd.kicad_sch`
- **PCB File:** `bspd.kicad_pcb`

### Component Footprints

- Resistors: 0603 SMD
- Capacitors: 0603 SMD
- Diodes: 0603 SMD
- Logic ICs (40106, 4081, 4071): DIP-14 with sockets
- Comparators (LM393): DIP-8 with sockets
- MOSFET (IRLIZ44N): TO-220F THT
- Potentiometers: PTD901 THT
- Connectors: Molex CLIK-Mate 2-pin vertical
- Mounting Holes: 3mm

---

---

## Calibration & Setup

### Threshold Adjustment

The brake and pedal thresholds can be adjusted via four PTD901-1015F-B203 potentiometers:
- **VR1, VR2** - Brake threshold adjustment
- **VR3, VR4** - Pedal threshold adjustment

### Recommended Threshold Settings

| Parameter | Recommended Value | Notes |
|-----------|-------------------|-------|
| Brake Threshold | ~10% travel | Match intended sensor |
| Pedal Threshold | ~25% travel | Match intended sensor |
| Fault Delay | <500ms | Timer circuit |

---

## Testing Procedures

### Functional Verification

1. **Brake Input Test**
   - Apply brake gradually
   - Verify `BRAKE_APPLIED` activates at threshold
   - Verify no fault when accelerator is released

2. **Pedal Input Test**
   - Apply accelerator gradually
   - Verify `PEDAL_APPLIED` activates at threshold
   - Verify no fault when brake is released

3. **Plausibility Test**
   - Apply both pedals simultaneously above thresholds
   - Verify `BSPD_FAULT` activates
   - Verify fault latches (stays active after releasing pedals)
   - Verify manual reset clears fault

4. **Open Circuit Test**
   - Disconnect brake sensor
   - Verify `BRAKE_OPEN` and `BSPD_FAULT` activate
   - Repeat for accelerator sensor

5. **Short Circuit Test**
   - Short brake sensor to GND
   - Verify `BRAKE_SHORT` and `BSPD_FAULT` activate
   - Repeat for accelerator sensor

---

## Troubleshooting

| Symptom | Possible Cause | Solution |
|---------|----------------|----------|
| Constant fault | Sensor wiring issue | Check sensor connections |
| No fault detection | Threshold too high | Adjust threshold potentiometer |
| Intermittent faults | Noise on sensor lines | Add or remove filtering capacitors |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2026.1 | Jan 2026 | Albert | Initial design |

---

## References

- KiCad Project Files: `/electrical-pcbs/BSPD/2026.1/bspd_2026/`
- Component Datasheets: Located in respective `LIB_*` folders