---
title: "Technical Narrative: Delegated Design Peer Review, Dust Collection and Explosion Protection"
subtitle: "Bldg 592 Renovations (RM16-1405), Philadelphia Navy Yard Annex | NAVFAC N40085-24-D-0009 | WO 1808017"
author: "Bowman, Foster & Associates, Inc. for G Force Construction (an FBSG Inc. company)"
date: "DRAFT v01, 9 November 2026"
---

# 1. Scope Understanding

## 1.1 Project

| Item | Basis |
|---|---|
| Facility | Bldg 592, Naval Foundry & Propeller Center (NFPC), Philadelphia Navy Yard Annex, PA. Occupied and operational during construction. |
| Owner / Contract | NAVFAC Mid-Atlantic; MACC N40085-24-D-0009; WO 1808017 |
| Designer of Record | WRA (Baltimore, MD); MEP by Summer Consultants (Newark, DE) |
| Prime Contractor | G Force Construction (FBSG Inc.) |
| Contract Documents | Drawings dated 24 SEP 2026 (179 sheets); Specifications approved 23 OCT 2026 |
| BFA Scope Driver | Spec 01 11 00 §1.1.1.b: HVAC and dust exhaust system upgrades, mezzanine pattern shop |

## 1.2 System Under Review

| Component | Design Data (M-601 / 23 51 43) |
|---|---|
| Dust collector DCS-01 | Welded-steel reverse-air / rotary-arm fabric filter baghouse; 156 bags x 8 ft; involute scroll inlet (cyclonic pre-separation); 60-degree hopper; exterior; 145 x 125 x 390 in.; 9,000 lb |
| Airflow | 9,000 CFM (M-601) / 10,000 CFM (spec). To be resolved at kickoff. |
| Media | Air-to-cloth 6.2:1 nominal, 6.5:1 max; >= 1,600 sf; can velocity ~200 fpm (<= 250) |
| Exhauster EF-MEZZ-DC | Radial; 16.0 in. TSP; 1,385 RPM; 38.6 BHP; 50 HP, 460/3/60, VFD; 18 ga silencer |
| Housing / duct pressure | Housing -20.0 in. w.g.; dust duct class -24 in. w.g. (M-602); outlet-to-stack -10 / +30 in. w.c. transient |
| Duct velocity | Mains 4,000 fpm (3,500 min); runouts 5,000 fpm (4,000 min) |
| Cleaning | 3 HP positive-displacement blower, ~48-50 SCFM at 5 psig; rotating arm, TEFC |
| Discharge isolation | Rotary airlock (NFPA 69): tip clearance <= 0.0079 in.; zero-speed switch interlock |
| Deflagration venting | NFPA 68 vent panels; Pred <= 20 in. w.g.; Kst >= 200 bar-m/s; Pmax >= 8.5 bar; deflectors where required |
| Inlet isolation | Passive flow-actuated flap valve (NFPA 69, ATEX-certified) at Lmin-Lmax; microswitch fan shutdown |
| Suppression / detection | Fike HRD 20L sodium bicarbonate suppressor (or equal); spark detection; duct sprinkler nozzles |
| Emissions | <= 0.005 gr/dscf; >= 99.9% removal |
| Supports | IBC 2018 Risk Category II wind / seismic / snow; duct hangers sized for 50% dust fallout |

## 1.3 Contract Requirement for BFA Role

- 23 51 43.00 20 §1.3.1.1: the Contractor engages a Pennsylvania-licensed PE to provide a complete delegated engineering design for dust collection, ductwork, and explosion protection.
- The same delegated-design note appears on M-102, M-401, M-503, M-601, M-703, and the FA/FX/E sheets.
- All shop drawings, design calculations, SD-02, and SD-03 are signed and sealed by the Contractor's PE. The seal certifies NFPA 68, 69, 70, 72, 91, 654, and 664 compliance.
- The PE witnesses the duct leakage and smoke test (23 30 00 §3.9; SD-06).
- The PE performs a post-installation site visit and issues a sealed Certification of Compliance (SD-11).
- G Force request (2026-11-04): "peer review on the mechanical calculations needed."

## 1.4 Delivery Model

- Manufacturer and vendors prepare the engineered system: collector, fan, explosion protection, flap valve, support stand, duct layout.
- BFA independently verifies each calculation set, issues comments, confirms compliance, and seals as the Delegated Design PE.
- If the manufacturer does not furnish engineered calculations, BFA prepares them (Option 1).

# 2. Technical Approach by Discipline

## 2.1 Mechanical (Lead Discipline; PA PE in Responsible Charge)

### Criteria and references

- UFGS 23 51 43.00 20, 23 35 19.00 20, 23 30 00, 23 09 13, 23 05 93
- NFPA 664, 68, 69, 91, 654 (plus NFPA 660 alignment check); ACGIH Industrial Ventilation Manual; SMACNA Round Industrial Duct Construction
- UFC 3-410-01; UFC 1-200-01; UFC 3-600-01 (interface)

### D01: Basis of Review

- Reconcile design basis: 9,000 vs 10,000 CFM; pressure classes; cleaning-air source; code editions.
- Issue a Basis-of-Review criteria memo: acceptance criteria, calc methods, required inputs list for the manufacturer.

### D02: Duct Aerodynamic Verification

- Independent node-by-node static pressure check (velocity-pressure method): hood/runout entry losses, branch entries, elbows, blast gates, backdraft dampers, flex hose, collector dP (2.0-5.0 in.), silencer, stack.
- Verify transport velocity at every node: mains >= 3,500 fpm, runouts >= 4,000 fpm; check balance at design (static pressure balance, no reliance on blast-gate throttling).
- Check fan selection against system curve at clean and dirty filter conditions; VFD range.
- Verify intermittent outlets (floor sweeps, clean-up arms) with industrial backdraft dampers per M-102 keynote 11.
- Verify runout sizing changes permitted by 23 30 00 against equipment connection sizes.

### D03: NFPA 68 Deflagration Venting

- Verify vessel volume (V), L/D, and Pred against manufacturer vessel strength.
- Recalculate vent area (Av) with Kst >= 200 bar-m/s and Pmax >= 8.5 bar; include panel inertia/efficiency (Ef) and partial-volume corrections where applied.
- Verify reaction force and deflector design; fireball and discharge hazard zone vs personnel paths, building openings, and adjacent equipment; vertical deflection shield need (M-401 keynote 4).

### D04: NFPA 69 Isolation and Suppression

- Verify flap valve Lmin/Lmax from the scroll inlet per the manufacturer's test certificate (duct diameter, velocity range, Pred, Kst limits).
- Verify supports and seismic restraint on both sides of the valve body; position monitoring; fail-safe fan shutdown.
- Verify rotary airlock as an isolation device: tip clearance, rotor vanes, zero-speed interlock.
- Verify HRD suppressor placement, detector response time, and container sizing vs system volume (coordinated with Fire Protection).

### D05: Recirculation / Abort Gate

- Confirm exhaust-to-atmosphere configuration (HV-M01 100% OA; exterior collector). Document that no abort gate is required, or define abort-gate and return-air monitoring requirements if recirculation is proposed.

### D06: Equipment and Pressure Integrity

- Verify air-to-cloth, can velocity, media, filtration efficiency, emission data (<= 0.005 gr/dscf).
- Verify duct gauge / pressure class for -24 in. w.g. and the -10 / +30 in. w.c. transient (outlet to stack); stack and silencer construction; outdoor coatings.
- Verify leakage acceptance basis (SMACNA Class 3, < 1% of design CFM).

### D11 / D12: Submittal Review and Seal

- Review SD-02 / SD-03 / SD-05 packages for compliance; issue a consolidated comment log.
- Verify manufacturer experience certification (>= 5 installations >= 10,000 CFM wood dust).
- Seal calculations and delegated-design shop drawings; respond to one round of Government comments.

### D14 / D15: Field Verification

- Site Visit 1: witness the duct leakage test and the smoke test at clamped joints, wyes, blast gates, and access doors (SD-06).
- Site Visit 2: observe installation vs sealed design; verify vent and flap valve positions; observe flap manual trip and fan shutdown, cleaning cycle, measured CFM and static pressure; review spark/HRD interlock test records.
- Issue a sealed Certification of Compliance (SD-11).

## 2.2 Structural (PA PE)

- D07: verify manufacturer support calculations per ASCE 7 / IBC 2018, Risk Category II:
  - Collector legs and support stand: dead, operating, dust-full hopper, wind, seismic, snow.
  - Access platform, ladder, fall protection attachments.
  - Fan base and silencer supports; vibration isolation reactions.
  - Exterior exhaust stack; guy wires to lower structure (M-503 keynote 2).
  - Explosion vent reaction forces transferred to supports.
  - Duct hangers and supports at duct dead weight with 50% wood dust fallout plus seismic and wind (23 30 00 §3.2.5); rigid supports each side of the flap valve.
- Verify anchor design vs the foundation (S-004 detail B4 by EOR); post-installed anchors per 05 05 20 / ACI 318 Ch. 17.
- Provide the equipment foundation loading plan / hanger load summary (SD-05).
- Seal structural verification calculations within the delegated design package.

## 2.3 Electrical

- D08: review controls and power integration:
  - Interlock matrix: flap valve microswitch, rotary airlock zero-speed switch, spark detection, HRD discharge, high hopper level, filter dP, fan VFD, blower.
  - Fail-safe shutdown logic and restart permissives; dust collection enable push-button (M-703).
  - Hazardous (classified) location review for Class II dust areas per NFPA 70 / NFPA 499 / NFPA 664; equipment ratings for enclosures inside the collector and duct.
  - Bonding and grounding continuity of duct, flex hose helix, collector, and stack (NFPA 77 / 664).
  - Motor and disconnect data vs E-602 (EF-MEZZ-DC 50 HP VFD; AC-MEZZ-DC 3 HP; cleaning 1/3 HP; rotary valve 2 HP).
- Review wiring diagrams and schematic control diagrams (23 51 43 §1.3.1.3-1.3.1.4) for the delegated system.

## 2.4 Fire Protection

- D09: interface review only:
  - Spark detection and extinguishing (or diversion) location vs duct transit time.
  - HRD suppressor I/O to fire alarm (28 31 70); explosion detector to the FA input/output matrix (FA001).
  - Sprinkler protection nozzles in duct and collector taps (M-102 keynote 5; 23 51 43 §2.6); confirm the QFPE design is coordinated with the delegated design.
- Participate in D04 (HRD placement) and D11/D12 (seal package coordination).

## 2.5 Plumbing

- D10: verify the cleaning-air source and utility interface:
  - AC-MEZZ-DC (3 HP, 50 SCFM at 5 psig) vs spec blower (48 SCFM at 5 psig); confirm blower vs compressor.
  - Confirm independence from shop air AC-01 (15 HP, 125 psig).
- Sprinkler tap and drain coordination at the collector.

## 2.6 Quality Assurance / Quality Control

- Principal QA/QC review of the Basis-of-Review memo, the seal package, and the Certification of Compliance.
- Independent check by a second engineer of every sealed calculation set before seal.
- Comment log tracked to closure; version-controlled deliverables.

# 3. Deliverables

| ID | Deliverable | Format | Timing |
|---|---|---|---|
| D01 | Basis-of-Review criteria memo; required-inputs list | PDF memo | NTP + 10 WD |
| D02 | Duct aerodynamic verification calculations | Sealed calc (PDF) | Receipt + 10 WD |
| D03 | NFPA 68 venting verification calculations | Sealed calc (PDF) | Receipt + 10 WD |
| D04 | NFPA 69 isolation / suppression verification | Sealed calc (PDF) | Receipt + 10 WD |
| D05 | Recirculation / abort gate determination | PDF memo | Receipt + 10 WD |
| D06 | Equipment and pressure integrity review comments | Comment log | Receipt + 10 WD |
| D07 | Structural anchorage / hanger verification; foundation loading plan | Sealed calc (PDF) | Receipt + 10 WD |
| D08 | Electrical / controls integration review comments | Comment log | Receipt + 10 WD |
| D09 | FA / spark / HRD / sprinkler interface review comments | Comment log | Receipt + 10 WD |
| D10 | Cleaning-air utility interface comments | Comment log | Receipt + 10 WD |
| D11 | Sealed delegated design package (SD-02 / SD-03 / SD-05) | Sealed PDF | Comments + 5 WD |
| D12 | Resubmittal and Government comment responses (1 round) | Sealed PDF + response matrix | Gov comments + 5 WD |
| D13 | RFI responses (allowance) | PDF | 3 WD per RFI |
| D14 | Duct leakage / smoke test witness record | Field report (SD-06) | Visit + 5 WD |
| D15 | Final inspection report; Certification of Compliance | Sealed certificate (SD-11) | Visit + 10 WD |
| D16 | Project management, badging, invoicing | - | Continuous |

**Optional services (priced separately):**

| ID | Option |
|---|---|
| OPT-1 | Full independent delegated design calculations |
| OPT-2 | Non-delegated HVAC / plumbing submittal pre-review for G Force QC |
| OPT-3 | Additional site visit (each) |
| OPT-4 | Dust collection TAB / performance test witness |
| OPT-5 | Additional resubmittal round (each) |
| OPT-6 | Dust explosibility lab testing coordination |

# 4. Assumptions

1. BFA is the Contractor's Delegated Design PE under a subcontract to G Force; no direct contract with NAVFAC.
2. The manufacturer and explosion-protection vendor furnish engineered calculations, shop drawings, and test certificates. BFA verifies, comments, and seals. Full independent design is OPT-1.
3. A Pennsylvania-licensed mechanical PE seals the mechanical calculations and the Certification of Compliance; a PA-licensed structural PE seals the anchorage calculations.
4. Design basis: drawings 24 SEP / 08 OCT 2026 and specifications 23 OCT 2026; no amendments.
5. One dust collection system (DCS-01) serving the mezzanine pattern shop; up to 25 branch drops / runouts.
6. Exhaust discharges to atmosphere; no recirculation; no abort gate.
7. Dust explosibility values per spec (Kst >= 200 bar-m/s; Pmax >= 8.5 bar); no lab testing.
8. One initial submittal and one resubmittal round.
9. Two site visits (leakage test witness; final inspection); one PE per visit; two travel days and one night each.
10. Submittals arrive complete through G Force QC. Turnaround: 10 WD initial, 5 WD resubmittal.
11. Deliverables are electronic, sealed PDFs.
12. Government review durations per 01 33 00 §1.11 (20 WD; 30 WD with Government FP engineer review) are outside BFA's turnaround.
13. BFA personnel meet the U.S. citizen and SECNAV 5512/1 access requirements; G Force sponsors base access.
14. Lump-sum fee by phase; expenses at cost; 90-day validity.

# 5. Exclusions

1. Design or review of non-dust-collection HVAC, plumbing, electrical, or fire protection systems by the EOR (WRA / SCI), except OPT-2.
2. Engineer-of-record responsibility for the contract documents.
3. Sprinkler / standpipe hydraulic calculations and QFPE seal (21 13 13 / 21 13 16); fire alarm shop drawings (28 31 70).
4. Dust Hazard Analysis (NFPA 652 / 660); process hazard analysis; combustible dust lab testing.
5. Air permitting, emissions or stack testing, agency submissions.
6. Building structural analysis beyond the dust collector and duct support load paths; foundation design (S-004); S-001 delegated items.
7. Power system studies (26 05 73); substation and distribution design.
8. Cybersecurity / RMF (25 05 11); controls programming.
9. Full-time inspection, special inspections, commissioning, TAB execution.
10. Hazardous materials survey or abatement design.
11. Means and methods, temporary works, rigging and lift plans, construction safety.
12. Cost estimating, NAS scheduling, eCMS data entry.
13. Site visits beyond two (OPT-3); resubmittal rounds beyond one (OPT-5).
