# Interior Renovations for 120 Dorset Avenue — Full Narrative

## Project Overview

Bowman Foster & Associates provided full mechanical, electrical, and plumbing (MEP) engineering design services for the interior renovation of a single-story industrial building located at 120 Dorset Avenue, Virginia Beach, Virginia 23462. Construction documents were issued as final on September 28, 2020 under Bowman Foster project number 20-066, with Wylie R. Cooke Design, LLC (Norfolk, VA) serving as engineer of record. The project title as stated in every drawing title block is "Interior Renovations for 120 Dorset Avenue."

The facility is an active industrial manufacturing and fabrication building. Panelboard schedules and drawing annotations reference powder coat booths, welding outlets (50A circuits), a sinter oven (SINTER-2), an overhead lift, a compactor, a cord reel station, and a compressed air system with an existing compressor — confirming a machine shop or industrial fabrication use. The renovation introduced a dedicated clean work area requiring critical power (UPS-backed), refreshed the employee restroom and utility areas, upgraded HVAC throughout, replaced all lighting with LED, and extended compressed air distribution. A new emergency power system (generator and ATS) was installed to serve the clean work area.

## Scope of Work

### Mechanical / HVAC

The mechanical scope began with a complete demolition of existing HVAC equipment in the affected areas: the existing heat pump and AHU were removed (heat pump turned over to the customer per demo notes), all associated ductwork, diffusers, grilles, and hangers were removed, and thermostat wiring was reset. One existing AHU was noted to remain.

New HVAC installed for the clean work area consisted of:

- **AHU-1**: 840 CFM, 100% outside air, 1 HP motor, R-410a refrigerant, 7.5 kW electric heating coil, 208V/1-phase, 38A MCA. Entering air conditions 77°F DB/65°F WB; leaving air conditions 54.5°F DB (cooling), 89.1°F DB (heating). Mounted on a steel platform with auxiliary drain pan.
- **HP-1**: Air-cooled condensing unit paired with AHU-1, R-410a, 208V/1-phase, 26.3A MCA, 45A MOCP.
- **EF-1**: Inline exhaust fan, 900 CFM, 1.5 HP, 115V/1-phase, direct drive.
- **EF-2**: Inline exhaust fan, 150 CFM, 0.5 HP, 115V/1-phase, direct drive.

New rectangular galvanized ductwork was routed to serve the clean work area with 24×24 supply diffusers and 12×12 exhaust grilles; perimeter supply registers were sized at 14/10, 16/14, and 20/25 inches. Manual volume dampers and a 7-day programmable thermostat were specified. Duct insulation per Section 230713 (2-inch mineral fiber blanket) and refrigerant piping insulation per Section 230719 were specified throughout. The existing gas meter equipment was retained. Compressed air distribution was extended from the existing compressor, with new 1-inch CA mains throughout the industrial floor and 3/4-inch drops with quick disconnects at 12 inches AFF.

### Plumbing

The plumbing scope included complete demolition and replacement of all plumbing fixtures, piping, and the water heater in the restroom and utility areas. Existing 4-inch waste and 2-inch cold water mains were retained at the connection points; new piping was roughed in from those points. The existing air compressor piping and drops were retained.

New plumbing fixtures per the fixture connection schedule included: floor-mounted flush-tank water closets (P-1, 1.1 GPF, handicap accessible); counter-mounted lavatories (P-2, 0.35 GPM, HC); floor-mounted mop sink (P-3); floor-mounted shower (P-4); counter-mounted kitchen sink (P-5); floor-mounted stackable washer/dryer with utility box (P-6); and wall-mounted urinal (P-7, 0.5 GPF).

A new electric water heater (EWH-1) with dual 4500W elements, expansion tank, and T&P relief valve was specified, with a 2-inch deep drain pan piped to waste. Domestic water piping was ASTM B88 Type L copper; sanitary waste was cast iron or PVC per Section 221316. All plumbing piping insulation per Section 220719 (1-inch flexible elastomeric or mineral fiber). ADA-accessible piping protection was specified at accessible lavatories and sinks.

### Electrical

The electrical scope was the most extensive discipline on this project. The existing electrical distribution infrastructure was largely retained: the Cutler-Hammer 600V/400A, 3-phase safety switch and MDP (480Y/277V, 400A, MLO), two 75 kVA step-down transformers (480V→208Y/120V), and Panels A, B, C, and Office Panel 1 all remained in service. Notable existing loads from the retained panel schedules include fabrication training lights, beam outlets, welder outlets (50A each), the air compressor, lift, compactor, powder coat booth, cord reel, and the SINTER-2 oven.

New electrical work included:

- **Emergency Panel D** (new): 100A, 90A MCB, 208Y/120V, 3-phase, 4-wire, 22 KAIC, surface mount. Fed from Panel C under normal power, and from the generator via ATS under emergency. Serves the clean work area: cord reel receptacles, 220V clean work area receptacles, and the SINTER-2 oven (30A circuit).
- **25 kVA UPS**: 208Y/120V, 3-phase, online double-conversion, with bypass. Fed from Panel C; provides ride-through for clean work area loads during power anomalies. Specified per Section 263353 for continuous operation with 15-minute backup duration at full load.
- **20 kW/25 kVA generator**: 208Y/120V, 3-phase, diesel-engine driven, with automatic transfer switch (ATS). Generator feeds Emergency Panel D via ATS when normal power fails. Specified per Section 263600.
- **LED lighting replacement**: All existing lighting was replaced. New LED high-bay fixtures were installed on purlins in the industrial work area. Office and support areas received 2×4 direct/indirect LED troffers (36W, 41W, or 50.3W MVOLT) and surface LED wraparound fixtures (39W MVOLT). Exit signs (LED, 90-min battery backup) and LED emergency units (twin-head, 33W, 90-min battery, wall-mounted at 7'-6" AFF) were specified throughout per Section 265213.
- **Occupancy sensors**: New occupancy sensor switches (So type, dual-technology PIR/ultrasonic) installed to control lighting in office and support areas.
- **Branch circuit modifications**: Existing circuits in Panels A, B, C, and Office Panel 1 were modified to accommodate new loads. RFI #9 circuit noted on Panel C.
- **Arc flash warning labels**: Required at all distribution equipment per NEC 2020 110.16(A) and UFC 3-560-01.

The UFC 3-560-01 reference (a DoD arc flash specification) noted on sheet E6 is unusual for a private commercial industrial project and may indicate a DoD-adjacent customer or contractor preference, or it may reflect the engineer's standard practice.

## Key Challenges and Technical Considerations

**Critical power infrastructure for clean work area**: The project introduces a layered critical-power scheme — Panel C normal feed → Emergency Panel D + ATS → generator backup, with a parallel 25 kVA UPS path — suggesting the clean work area hosts sensitive processes or equipment (potentially a clean room environment, consistent with the "clean room" reference in key personnel notes and the project's freeform tags) that cannot tolerate power interruptions.

**Industrial hazard coordination**: The building contains inherently hazardous operations (welding, powder coat booth, sinter oven). The electrical design maintained all existing 50A welder outlets and heavy equipment circuits, while separating the clean work area (with its own Emergency Panel D) from the general industrial distribution. Panel C's 22 KAIC rating (versus Panels A and B at 10 KAIC) reflects the higher fault currents at the distribution panel serving this area.

**100% outside air AHU**: AHU-1 is specified as 100% outside air, which is atypical for general comfort conditioning and consistent with a clean room, laboratory, or specialty process environment — providing continuous dilution ventilation without recirculation.

**Incomplete document package**: The source documents provided are construction drawings and specifications only. No BOD, SOW, contract, or narrative documents are present, so client identity, contract value, project budget, and procurement details are unavailable from these sources.

## Project Role

Bowman Foster & Associates served as the prime MEP consultant. Wylie R. Cooke Design, LLC (Norfolk, VA) is stamped as engineer of record on all 11 drawing sheets (6 electrical, 5 mechanical/plumbing). The design team is the same firm operating under two names or in a principal-subconsultant relationship.

## Project Status and Completion

Construction documents are dated September 28, 2020, representing the final-issue construction document set. Project status is inferred as complete given the final CD issue date; no construction-phase or closeout documents are present to confirm.
