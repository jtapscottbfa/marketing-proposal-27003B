"""scripts/pursuit/b592_data.py

Single source of truth for the B592 Dust Collection Delegated Design Peer
Review pursuit (G Force / FBSG -> BFA). Consumed by build_b592_package.py.

All values here are DRAFT and derived from:
  - 00_admin/rfp_intake/original_rfp/Re_ Request for quote - Phila Navy yard.msg
  - 00_admin/rfp_intake/attachments/Attachment+A+-+1808017_DWG_01of01 9.pdf
  - 00_admin/rfp_intake/attachments/Attachment+B+-+1808017_SPC_01of01 8.pdf
"""

PROJECT = {
    "short": "B592",
    "title": "FY26 Special Project Bldg 592 Renovations, RM16-1405",
    "location": "Bldg 592, Naval Foundry & Propeller Center (NFPC), Philadelphia Navy Yard Annex, Philadelphia, PA",
    "owner": "NAVFAC Mid-Atlantic (AOPS North)",
    "contract": "N40085-24-D-0009 (NAVFAC MACC)",
    "work_order": "1808017 (drawings, file names) / 1808024 (spec cover) - discrepancy",
    "eor": "Whitman, Requardt & Associates (WRA), Baltimore MD; MEP: Summer Consultants (SCI), Newark DE",
    "prime": "G Force Construction (an FBSG Inc. company) - 8(a), HUBZone, EDWOSB, WOSB, SDB",
    "client_poc": "Ennio Bruno, Director / Federal Operations, ebruno@fbsginc.com, 610.470.8279 (c) / 610.241.8552",
    "client_cc": "Ben M. Gallo (bgallo@fbsginc.com); Cindy Gallo (cgallo@fbsginc.com)",
    "bfa_poc": "Jonathan Tapscott, Director of Technology & Business Development, 757-226-8245",
    "bfa_role": "Contractor's Delegated Design Professional Engineer (PA) - peer review, verification, and seal of the dust collection / explosion protection delegated design",
    "docs_dates": "Drawings dated 24 SEP 2026 / plotted 06-09 OCT 2026 (179 sheets); Specs approved 23 OCT 2026 (1,550 pp)",
    "proposal_due": "Not stated - BFA target 2026-11-13 12:00 ET (ASSUMED)",
}

CORRESPONDENCE = [
    ("2026-10-27", "NAVFAC (F. Caruso) -> bidders", "Amendment 0003, N4008526R0275 B408 South Bay Demolition; proposals due 2026-11-12.", "Different solicitation. NOT this project."),
    ("2026-10-28", "E. Bruno -> J. Tapscott", "G Force passing on B408 (contractor risk).", "Context only."),
    ("2026-10-29", "E. Bruno -> J. Tapscott", "Asked if BFA is interested in Philadelphia Navy Yard work.", "Relationship."),
    ("2026-10-30", "J. Tapscott -> E. Bruno", "Yes; BFA already working at PNY on B3 RTUs.", "Win theme: PNY presence."),
    ("2026-11-02", "E. Bruno -> J. Tapscott (cc B. Gallo, C. Gallo)", "RFQ: quote for attached Phila project (Att. A drawings, Att. B specs).", "RFQ received."),
    ("2026-11-04", "J. Tapscott -> E. Bruno", "No design aspect apparent; requested scope; docs dated Oct 2026.", "Clarification request."),
    ("2026-11-04", "E. Bruno -> J. Tapscott", "Full package; BFA team for peer review on the mechanical calculations needed.", "Scope basis: mechanical calc peer review."),
]

# (ID, Source ref, Requirement (condensed, verbatim intent), BFA role, Trade, BFA deliverable)
REQUIREMENTS = [
    ("TECH-01", "23 51 43.00 20 §1.3.1.1; M-102/M-401/M-601 notes", "Contractor engages a PE licensed in Pennsylvania to provide a complete delegated engineering design for the dust collection, ductwork, and explosion protection systems.", "Delegated Design PE - review, verify, seal", "Mechanical", "D11"),
    ("TECH-02", "23 51 43.00 20 §1.3.1.1", "Duct aerodynamic calculations: node-by-node static pressure loss, sizing, flow balancing; minimum transport velocity at woodworking runouts per ACGIH and NFPA 664.", "Verify and seal", "Mechanical", "D02"),
    ("TECH-03", "23 51 43.00 20 §1.3.1.1", "Structural, wind and seismic anchorage: point loads and anchoring for collector legs, support stand, access platform/ladder, fan base, exterior exhaust stack per ASCE 7 / IBC.", "Verify and seal", "Structural", "D07"),
    ("TECH-04", "23 51 43.00 20 §1.3.1.1, §2.6", "NFPA 68 deflagration venting: vent area (Av) from vessel volume, Pred <= 20 in. w.g., Kst >= 200 bar-m/s, Pmax >= 8.5 bar; reaction force for vent deflectors.", "Verify and seal", "Mechanical", "D03"),
    ("TECH-05", "23 51 43.00 20 §1.3.1.1; 23 35 19.00 20 §3.1.5", "NFPA 69 isolation: Lmin/Lmax placement of passive flow-actuated flap valve from collector scroll inlet, based on manufacturer ATEX/NFPA test certificate.", "Verify and seal", "Mechanical", "D04"),
    ("TECH-06", "23 51 43.00 20 §1.3.1.1", "NFPA 664: if exhaust air is recirculated, provide high-speed abort gate design and return-air monitoring.", "Determination memo", "Mechanical", "D05"),
    ("TECH-07", "23 51 43.00 20 §1.3.1.1", "Delegated package covers dust collector, industrial exhaust fan, HRD explosion suppression, passive flap isolation valves, and spark detection integration.", "Verify and seal", "Mechanical / FP", "D04, D09"),
    ("TECH-08", "23 51 43.00 20 §1.3.1.1", "Electrical and control logic integration for rotary-blower reverse-air cleaning system and spark/explosion suppression systems.", "Review", "Electrical", "D08"),
    ("TECH-09", "23 51 43.00 20 §1.3.1.1", "All shop drawings, design calculations, SD-02 and SD-03 signed and sealed by Contractor's PE; seal certifies compliance with NFPA 68, 69, 70, 72, 91, 654, 664 and local codes.", "Seal", "Mechanical", "D11"),
    ("TECH-10", "23 51 43.00 20 §1.3.1.1", "PE site visit after installation; signed and sealed Certification of Compliance (installation, HRD, vents, flap valves, CFM/static, cleaning cycle, interlock shutdown) as SD-11.", "Site visit + sealed certificate", "Mechanical", "D15"),
    ("TECH-11", "23 30 00 SD-02", "Shop drawings, layouts, structural hanger calcs, and explosion protection placements for dust collection ductwork sealed by Contractor's delegated PE registered in project jurisdiction.", "Verify and seal", "Mechanical / Structural", "D07, D11"),
    ("TECH-12", "23 30 00 §3.2.5", "Dust duct supports/hangers engineered for duct dead weight at 50% full of wood dust fallout plus seismic and wind loads.", "Verify and seal", "Structural", "D07"),
    ("TECH-13", "23 30 00 §3.9", "Duct leakage test (SMACNA Class 3, < 1% of 10,000 CFM) and smoke test witnessed by the Delegated Design PE; report as SD-06 before final balancing.", "Witness", "Mechanical", "D14"),
    ("TECH-14", "23 30 00 §2.x (flexible hose / runouts)", "Runouts min 4,000 FPM; runout size and airflow adjustments permitted via delegated-design shop drawings.", "Verify", "Mechanical", "D02"),
    ("TECH-15", "23 35 19.00 20 §3.1.5", "Flap valve between Lmin and Lmax as sealed by DD PE; rigid supports and seismic restraint both sides; microswitch fail-safe exhaust fan shutdown; manual trip test before acceptance.", "Verify / observe", "Mech / Struct / Elec", "D04, D07, D08, D15"),
    ("TECH-16", "23 51 43.00 20 §2.5.1", "Emissions <= 0.005 gr/dscf; DD Engineer verifies compliance with local air quality permits and EPA standards.", "Verify manufacturer data only (permitting excluded)", "Mechanical", "D06"),
    ("TECH-17", "23 51 43.00 20 §2.5.1, §2.6", "Gross air-to-cloth <= 6.5:1 at 10,000 CFM (>= 1,600 sf media); steady-state dP 2.0-5.0 in. w.g.; can velocity ~200 fpm (<= 250).", "Verify", "Mechanical", "D06"),
    ("TECH-18", "23 51 43.00 20 §2.5.2", "Duct velocity 4,000 FPM mains (3,500 min), 5,000 FPM runouts (4,000 min); outlet-to-stack duct rated -10 to +30 in. w.c. transient without permanent deformation.", "Verify", "Mechanical", "D02, D06"),
    ("TECH-19", "23 51 43.00 20 §2.6", "Rotary airlock as NFPA 69 isolation barrier: <= 0.0079 in. tip clearance, zero-speed switch interlock.", "Verify", "Mechanical / Electrical", "D04, D08"),
    ("TECH-20", "23 51 43.00 20 §2.6", "Support structures per IBC 2018 Risk Category II wind, seismic, snow.", "Verify and seal", "Structural", "D07"),
    ("TECH-21", "23 51 43.00 20 §1.3.2, SD-05", "Hanger load calculations and equipment foundation design loading (loading plan with base loads).", "Verify and seal", "Structural", "D07"),
    ("TECH-22", "M-601 Dust Collection Schedule", "DCS-01: radial fan 9,000 CFM, 16.0 in. TSP, 38.6 BHP / 50 HP, 460/3/60; 156 bags; housing -20.0 in. w.g.; 145x125x390 in.; 9,000 lb; exterior; spark detection, silencer, explosion vent, 3 HP cleaning air, 2 HP rotary valve.", "Basis of review", "Mechanical", "D01"),
    ("TECH-23", "FX sheets; GI004", "Fike HRD 20L sodium bicarbonate high-rate-discharge suppressor (or equal); dust collector gets unique alarm and sprinkler protection per UFC/NFPA.", "Interface review", "Fire Protection", "D09"),
    ("TECH-24", "M-102 keynotes 5, 8-12", "Duct sprinkler nozzles; flexible clean-up arms; floor sweeps; blast gates; industrial backdraft dampers; runout sizes verified per delegated design.", "Verify", "Mechanical / FP", "D02, D09"),
    ("TECH-25", "M-401 keynotes 3-4, 6", "Flow-actuated flap valve; vertical deflection shield if required by delegated design; structural duct supports per delegated design.", "Verify", "Mechanical / Structural", "D03, D07"),
    ("TECH-26", "M-602 Ductwork Classification", "Dust collection ductwork pressure class -24 in. w.g.; SMACNA Round Industrial Duct 2013, NFPA 654, NFPA 68.", "Verify", "Mechanical", "D06"),
    ("TECH-27", "E-602 equipment schedule", "EF-MEZZ-DC 50 HP 460V VFD; AC-MEZZ-DC 3 HP 460V; cleaning mechanism 1/3 HP 200V; rotary valve 2 HP 200V.", "Interface review", "Electrical", "D08"),
    ("TECH-28", "P-601; M-601 note F", "Cleaning air: AC-MEZZ-DC 3 HP, 50 SCFM @ 5 psig (dust collector). Shop air AC-01 15 HP, 50 SCFM @ 125 psig (separate).", "Interface coordination", "Plumbing", "D10"),
    ("TECH-29", "01 33 00 §1.11", "Government review: 20 working days (CO approval); 30 working days where Government fire protection engineer reviews; resubmittals same duration.", "Schedule input", "PM", "Schedule"),
    ("TECH-30", "01 14 00 §1.3", "All personnel U.S. citizens; SECNAV 5512/1 submitted >= 2 weeks before site work; NFPC remains operational.", "Comply (site visits)", "PM", "D16"),
    ("TECH-31", "23 51 43.00 20 §1.4.1", "Collector manufacturer >= 5 operating installations >= 10,000 CFM wood dust in past 5 years.", "Check in submittal review", "Mechanical", "D11"),
    ("TECH-32", "S-001 Delegated Design list", "Structural delegated items (e.g., cold-formed framing, scaffolding, temp loads on existing structure) by Contractor's PE.", "Not in BFA scope", "Structural", "Excluded"),
]

RED_FLAGS = [
    ("RF-01", "High", "Scope term mismatch", "G Force asked for a 'peer review' of mechanical calcs. The spec requires a complete PA-sealed delegated design plus a sealed field Certification of Compliance. Base fee covers verifying and sealing the manufacturer-prepared design; a full independent design is Option 1."),
    ("RF-02", "High", "Liability / seal", "Sealing explosion-protection design (NFPA 68/69) carries engineer-of-record-level liability. Limit BFA to verifying manufacturer-engineered components; confirm E&O coverage and limitation of liability in the subcontract."),
    ("RF-03", "High", "PA licensure", "Needs a Pennsylvania-licensed mechanical PE (and a structural PE for anchorage). Confirm BFA's PA licenses and any firm-registration requirement before quoting."),
    ("RF-04", "High", "No due date", "No GC due date or solicitation number provided. The 12 Nov 2026 date in the thread is B408 (N4008526R0275), which G Force declined."),
    ("RF-05", "Med", "Airflow basis", "M-601 DCS-01 = 9,000 CFM; 23 51 43 and 23 30 00 = 10,000 CFM (air-to-cloth, leakage test basis)."),
    ("RF-06", "Med", "Pressure basis", "M-602 dust duct class -24 in. w.g.; housing -20.0 in. w.g.; fan TSP 16.0 in.; outlet-to-stack -10/+30 in. w.c. transient. Confirm design pressures."),
    ("RF-07", "Med", "Cleaning air", "Spec: 3 HP blower, 48 SCFM @ 5 psig. M-601: 'air compressor' AC-MEZZ-DC 3 HP, 50 SCFM @ 5 psig. E-602 shows extra motors (1/3 HP cleaning, 2 HP rotary valve, marked 'SEE PLUMBING')."),
    ("RF-08", "Med", "Dust characteristics", "Kst >= 200 bar-m/s (St-2) is specified as 'verified'. Confirm whether dust explosibility testing is required (excluded; see Option 6) or the spec values govern."),
    ("RF-09", "Med", "Code editions", "Spec cites NFPA 664 (2020) and IBC 2018. NFPA 660 (2025) now consolidates the combustible dust standards. Confirm the governing editions with the UFC 1-200-01 basis."),
    ("RF-10", "Low", "Work order no.", "Spec cover reads WO 1808024; drawings, title blocks, and file names read 1808017."),
    ("RF-11", "Low", "Carryover text", "01 14 00 §1.2 e/f covers Building 20 concrete repair phasing, which does not apply to B592."),
    ("RF-12", "Low", "DHA", "No Dust Hazard Analysis (NFPA 652/660) is referenced. Not BFA scope; recommend that the Government confirm an existing DHA."),
    ("RF-13", "Low", "Recirculation", "HV-M01 is 100% OA and the collector exhausts outdoors, so no abort gate is presumed. To be confirmed in D05."),
    ("RF-14", "Low", "Air permit", "The 0.005 gr/dscf verification includes local air permit compliance. BFA verifies the manufacturer's data only; permitting is excluded."),
]

QUESTIONS = [
    ("Q1", "What is G Force's proposal due date to NAVFAC, the solicitation / task order number, and the date you need BFA's quote?"),
    ("Q2", "Confirm BFA's role: (a) Contractor's Delegated Design PE that seals the package and certifies the field installation (per 23 51 43), or (b) a non-sealing third-party peer review only."),
    ("Q3", "Has a dust collector manufacturer or explosion-protection vendor been selected? Will they furnish engineered calcs (duct SP, NFPA 68 venting, NFPA 69 isolation, support stand)?"),
    ("Q4", "Who provides structural anchorage and hanger calcs: BFA, the manufacturer, or G Force's structural delegated engineer (S-001)?"),
    ("Q5", "Design airflow basis: 9,000 CFM (M-601) or 10,000 CFM (spec)?"),
    ("Q6", "Is any recirculation of collector exhaust intended (abort gate per NFPA 664)?"),
    ("Q7", "Is dust explosibility testing (Kst/Pmax) expected, or do the spec values govern?"),
    ("Q8", "What is the anticipated construction duration, and in which months will installation, leakage testing, and final inspection occur?"),
    ("Q9", "Fee format (lump sum vs T&M NTE) and subcontract terms (insurance, limitation of liability, payment)?"),
    ("Q10", "Have any amendments been issued after the 23 Oct 2026 specification?"),
    ("Q11", "Confirm that the sprinkler, spark detection, and HRD system design is by G Force's FP subcontractor/QFPE, with BFA reviewing only the interface."),
]

MECH_SHEETS = [
    ("M-001", "Symbols and abbreviations"), ("MD101-MD104, MD401", "Mechanical demolition (existing dust collector removal)"),
    ("M-101", "First floor mechanical plan"), ("M-102", "Mezzanine mechanical plan (dust duct, runouts, keynotes 1-12)"),
    ("M-103 / M-104", "Second floor / roof mechanical plans"), ("M-401", "Enlarged first floor - dust collector (keynotes 1-7)"),
    ("M-402 to M-404", "Enlarged mezzanine / 2nd floor / Mech Rm 207"), ("M-501 to M-505", "Details (M-503 dust collector sections)"),
    ("M-601 / M-602", "Schedules: DCS-01, AHU, HV, fans, louvers, design conditions, duct classification"),
    ("M-701 to M-704", "Controls (M-703 dust collection controls)"), ("C-101, C-103, S-004 B4", "Dust collector site plan / foundation"),
    ("FA/FX sheets", "Spark detection, HRD suppressor, sprinkler protection"), ("E-602", "Dust collection electrical equipment schedule"),
]

SPEC_SECTIONS = [
    ("23 51 43.00 20", "Dust and Fabric Filter Type", "PRIMARY: delegated design, NFPA 68/69/664, certification"),
    ("23 35 19.00 20", "Industrial Ventilation and Exhaust", "Flap valve install, NFPA 664/91"),
    ("23 30 00", "HVAC Air Distribution", "Dust duct shop drawings sealed; hangers at 50% fallout; leakage test witness"),
    ("23 09 13", "Testing Industrial Ventilation Systems", "Performance testing (Option 4)"),
    ("23 05 93", "Testing, Adjusting, and Balancing", "TAB (Option 4)"),
    ("23 03 00", "Basic Mechanical Materials and Methods", "General"),
    ("21 13 13 / 21 13 16", "Wet / Dry Pipe Sprinkler", "QFPE design by others; interface"),
    ("28 31 70", "Interior Fire Alarm, Addressable", "Spark/explosion detection I/O"),
    ("26 20 00", "Interior Distribution System", "Applies to 23 51 43"),
    ("01 33 00", "Submittal Procedures", "Review durations"),
    ("01 14 00", "Work Restrictions", "Access, badging, citizenship"),
]

# ---------------------------------------------------------------- schedule
# (date, start HH:MM or None for all-day, duration_min, title, owner, notes, in_ics)
SCHEDULE = [
    ("2026-10-23", None, 0, "Specifications approved (NAVFAC)", "NAVFAC", "Spec cover approval date.", False),
    ("2026-11-02", None, 0, "RFQ received from G Force (E. Bruno)", "G Force", "Drawings + specs via SharePoint links.", False),
    ("2026-11-04", None, 0, "Scope clarified: peer review of mechanical calcs", "G Force", "Email 10:54 ET.", False),
    ("2026-11-09", None, 0, "RFP shred, schedule, narrative, fee draft issued (v01)", "BFA / Claude", "This package.", False),
    ("2026-11-09", "15:00", 60, "BFA internal review of B592 draft package (v01)", "J. Tapscott", "Review shred, fee, narrative; mark up for v02. Files: output/published/.", True),
    ("2026-11-10", "09:00", 30, "Send clarification questions Q1-Q11 to G Force", "J. Tapscott", "Due date, BFA role (seal vs non-seal), vendor calcs, structural responsibility, CFM basis.", True),
    ("2026-11-10", "14:00", 60, "PA mechanical PE scope and hours validation", "Mech EOR (PA PE)", "Confirm PA licensure, hours D01-D16, rates.", True),
    ("2026-11-11", None, 0, "Veterans Day (federal holiday): Gov offices closed", "-", "G Force may still be working; plan around it.", True),
    ("2026-11-12", "10:00", 60, "Pricing approval / Gold review (Principal)", "Principal", "Approve base fee, options, terms.", True),
    ("2026-11-12", "16:00", 30, "Final QC: quote letter, scope, fee sheet", "J. Tapscott", "Clear visible markers; confirm v-latest.", True),
    ("2026-11-13", "12:00", 30, "TARGET: Submit fee proposal to G Force (ASSUMED)", "J. Tapscott", "ASSUMED date; reset when G Force answers Q1.", True),
    ("2026-11-17", "10:00", 15, "Follow up with G Force on quote / GC bid status", "J. Tapscott", "Check questions, award timing.", True),
    ("2027-02-11", None, 0, "Quote validity expires (90 days from 2026-11-13)", "J. Tapscott", "Re-confirm pricing if no award.", True),
]

POST_AWARD = [
    ("NTP + 0", "Subcontract executed; kickoff (D01)", "BFA / G Force"),
    ("NTP + 10 WD", "Basis-of-Review criteria memo issued (D01)", "BFA"),
    ("Receipt + 10 WD", "Verification of complete manufacturer delegated-design package (D02-D10); comments issued", "BFA"),
    ("Comments + 5 WD", "Sealed SD-02/03/05 package to G Force QC (D11)", "BFA"),
    ("+ 20 to 30 WD", "Government review (20 WD CO approval; 30 WD if Gov FP engineer reviews)", "NAVFAC"),
    ("Gov comments + 5 WD", "Resubmittal / comment response (D12)", "BFA"),
    ("<= 60 CD after award", "Contractor mobilization (01 32 17)", "G Force"),
    ("Install complete", "Site Visit 1: duct leakage and smoke test witness (D14), 15 CD notice + badge", "BFA"),
    ("Pre-acceptance", "Site Visit 2: final inspection, interlock test observation (D15)", "BFA"),
    ("Visit 2 + 10 WD", "Sealed Certification of Compliance (SD-11) (D15)", "BFA"),
]

# ---------------------------------------------------------------- fee model
# Rates are ASSUMED placeholders: replace with BFA's current billing rate sheet.
ROLES = [
    # code, role, trade, rate
    ("PRIN", "Principal / QA-QC", "PM / QA-QC", 225),
    ("MEOR", "Sr. Mechanical PE (PA) - Delegated Design EOR", "Mechanical", 210),
    ("MPE", "Mechanical PE", "Mechanical", 180),
    ("MEIT", "Mechanical EIT / Designer", "Mechanical", 130),
    ("SPE", "Structural PE (PA)", "Structural", 195),
    ("SEIT", "Structural EIT", "Structural", 135),
    ("EPE", "Electrical PE", "Electrical", 185),
    ("FPE", "Fire Protection PE", "Fire Protection", 190),
    ("PPE", "Plumbing PE", "Plumbing", 170),
    ("ADM", "Project Coordinator / Admin", "PM / QA-QC", 95),
]
TRADES = ["Mechanical", "Structural", "Electrical", "Fire Protection", "Plumbing", "PM / QA-QC"]
PHASES = {
    "A": "A - Mobilization & Basis of Review",
    "B": "B - Calculation Verification",
    "C": "C - Submittal Review & Seal",
    "D": "D - Construction Phase",
    "E": "E - Project Management",
}
# id, phase, deliverable, spec ref, submittal type, hours{role:hrs}, trips, print_ship
DELIVERABLES = [
    ("D01", "A", "Kickoff, document review, Basis-of-Review criteria memo", "23 51 43 §1.3; M-601", "Memo",
     dict(PRIN=2, MEOR=4, MPE=6, MEIT=4, SPE=2, EPE=2, FPE=2, PPE=1, ADM=2), 0, 0),
    ("D02", "B", "Duct aerodynamic calc verification: node-by-node SP, transport velocity, runout sizing, balancing", "23 51 43 §1.3.1.1, §2.5.2; 23 30 00", "SD-05 (sealed)",
     dict(MEOR=3, MPE=10, MEIT=16), 0, 0),
    ("D03", "B", "NFPA 68 deflagration venting verification: Av, Pred, Kst/Pmax, reaction force, deflector, discharge zone", "23 51 43 §1.3.1.1, §2.6", "SD-05 (sealed)",
     dict(MEOR=4, MPE=8, MEIT=6), 0, 0),
    ("D04", "B", "NFPA 69 isolation and suppression verification: flap valve Lmin/Lmax, rotary airlock, HRD placement", "23 51 43 §2.6; 23 35 19 §3.1.5", "SD-05 (sealed)",
     dict(MEOR=4, MPE=6, MEIT=4, FPE=2), 0, 0),
    ("D05", "B", "NFPA 664 recirculation / abort gate determination memo", "23 51 43 §1.3.1.1", "Memo",
     dict(MEOR=2, MPE=3), 0, 0),
    ("D06", "B", "Collector performance, exhauster, silencer, stack, duct pressure-class and emission data review", "23 51 43 §2.5; M-602", "Review comments",
     dict(MEOR=2, MPE=5, MEIT=3), 0, 0),
    ("D07", "B", "Structural / wind / seismic anchorage and hanger verification (legs, stand, platform, fan base, stack, duct @ 50% fallout)", "23 51 43 §1.3.1.1, §1.3.2, §2.6; 23 30 00 §3.2.5", "SD-05 (sealed)",
     dict(MEOR=1, SPE=12, SEIT=14), 0, 0),
    ("D08", "B", "Electrical and controls integration review: interlocks, sequence, area classification, bonding/grounding, VFD", "23 51 43 §1.3.1.1; M-703; E-602", "Review comments",
     dict(MPE=2, EPE=10), 0, 0),
    ("D09", "B", "Fire alarm / spark detection / HRD and sprinkler-in-duct interface review", "FX/FA sheets; 28 31 70", "Review comments",
     dict(EPE=2, FPE=8), 0, 0),
    ("D10", "B", "Cleaning-air blower / compressed air utility interface coordination", "M-601 note F; P-601", "Review comments",
     dict(PPE=3), 0, 0),
    ("D11", "C", "Delegated design submittal (SD-02/03/05) review, comment, PE seal: initial", "23 51 43 §1.5; 23 30 00 SD-02", "SD-02/03/05 (sealed)",
     dict(PRIN=3, MEOR=6, MPE=8, MEIT=6, SPE=3, EPE=2, FPE=2, ADM=2), 0, 1),
    ("D12", "C", "Resubmittal and Government comment response: 1 round", "01 33 00 §1.11", "SD-02/03/05 (sealed)",
     dict(MEOR=2, MPE=5, MEIT=3, SPE=2, EPE=1, FPE=1, ADM=1), 0, 1),
    ("D13", "D", "Construction RFI / field question support: allowance", "-", "RFI responses",
     dict(MEOR=2, MPE=8, SPE=2, EPE=2), 0, 0),
    ("D14", "D", "Site Visit 1: ductwork leakage and smoke test witness", "23 30 00 §3.9", "SD-06 witness",
     dict(MPE=14, MEIT=2, ADM=1), 1, 0),
    ("D15", "D", "Site Visit 2: final inspection; sealed Certification of Compliance", "23 51 43 §1.3.1.1", "SD-11 (sealed)",
     dict(PRIN=1, MEOR=16, MPE=4, MEIT=4, EPE=2, FPE=1, ADM=1), 1, 1),
    ("D16", "E", "Project management, base access (SECNAV 5512/1), invoicing", "01 14 00 §1.3", "-",
     dict(PRIN=2, MEOR=4, ADM=8), 0, 0),
]
OPTIONS = [
    ("OPT-1", "Full independent delegated design calculations (if manufacturer does not furnish engineered calcs)",
     dict(MEOR=6, MPE=24, MEIT=32, SPE=8, SEIT=12), 0),
    ("OPT-2", "HVAC / plumbing non-delegated submittal pre-review for G Force QC (AHU-M01, AHU-201, HV-M01, EF/RF, CU, HP, AC-01)",
     dict(MPE=16, MEIT=8), 0),
    ("OPT-3", "Additional site visit (each)", dict(MPE=14, ADM=1), 1),
    ("OPT-4", "Dust collection TAB / performance test witness (23 05 93 / 23 09 13)", dict(MPE=14, MEIT=2, ADM=1), 1),
    ("OPT-5", "Additional resubmittal round (each)", dict(MEOR=2, MPE=5, MEIT=3, SPE=2, EPE=1, FPE=1, ADM=1), 0),
    ("OPT-6", "Coordinate dust explosibility (Kst/Pmax) lab testing: lab fee by others, pass-through", dict(MPE=4, ADM=1), 0),
]
# Expenses: per site trip (item, qty, unit, unit cost, basis)
TRIP_ITEMS = [
    ("Mileage, Hampton Roads VA - Philadelphia PA round trip", 560, "mi", 0.70, "ASSUMED 2026 IRS rate"),
    ("Lodging, Philadelphia", 1, "night", 250.00, "ASSUMED; verify GSA FY27 per diem"),
    ("Meals & incidentals (M&IE), travel days at 75%", 2, "day", 59.25, "ASSUMED GSA $79 x 75%"),
    ("Tolls / parking", 1, "trip", 60.00, "ASSUMED"),
]
PRINT_SHIP_UNIT = 75.00  # per sealed package (printing, PE seal, overnight)

ASSUMPTIONS = [
    "BFA serves as the Contractor's (G Force's) Delegated Design PE under a subcontract to G Force; no contract with NAVFAC.",
    "The dust collector manufacturer and explosion-protection vendor (e.g., Fike or equal) furnish engineered calcs, shop drawings, and test certificates. BFA verifies, comments, and seals. A full independent design is Option 1.",
    "A Pennsylvania-licensed mechanical PE seals the mechanical calcs and the Certification of Compliance; a PA-licensed structural PE seals the anchorage calcs.",
    "Design basis = the contract documents dated 24 SEP / 08 OCT 2026 (drawings) and 23 OCT 2026 (specs), with no amendments.",
    "One dust collection system (DCS-01, 9,000-10,000 CFM) serving the mezzanine pattern shop; up to 25 branch drops/runouts.",
    "No recirculation: collector exhaust discharges outdoors, so no abort gate is assumed (to be confirmed in D05).",
    "Dust explosibility values per spec (Kst >= 200 bar-m/s, Pmax >= 8.5 bar); no lab testing (Option 6).",
    "One initial submittal and one resubmittal; additional rounds are Option 5.",
    "Two site visits: (1) leakage test witness, (2) final inspection. Each visit = 1 PE, 2 travel days, 1 night.",
    "Submittals arrive as complete packages through G Force QC. BFA turnaround: 10 working days initial, 5 working days resubmittal.",
    "Electronic deliverables (PDF, sealed); hard copies only where noted.",
    "Labor rates are ASSUMED placeholders pending BFA's current rate sheet. Lump sum by phase; expenses at cost, no markup.",
    "BFA personnel meet the U.S. citizen and SECNAV 5512/1 access requirements.",
    "Quote valid 90 days.",
]
EXCLUSIONS = [
    "Design or review of non-dust-collection HVAC, plumbing, electrical, or fire protection systems designed by WRA/SCI (EOR), except Option 2.",
    "Engineer-of-record responsibility for the base contract design; responsibility for errors in EOR documents.",
    "Sprinkler / standpipe hydraulic calculations and QFPE seal (21 13 13 / 21 13 16) and fire alarm shop drawings (28 31 70); interface review only.",
    "Dust Hazard Analysis (NFPA 652/660), process hazard analysis, combustible dust lab testing.",
    "Air quality permitting, emissions testing, stack testing, or agency submissions.",
    "Building structural analysis beyond dust collector / duct support load paths; foundation design (S-004 by EOR); S-001 delegated items.",
    "Arc flash, short circuit, coordination studies (26 05 73); electrical design of the substation/distribution.",
    "Cybersecurity / RMF (25 05 11) and BACnet controls programming.",
    "Full-time inspection, special inspections, commissioning, TAB execution.",
    "Hazardous materials (asbestos, lead, PCB) survey or abatement design.",
    "Means and methods, temporary works, construction safety, rigging and crane lift plans.",
    "Construction cost estimating, scheduling (NAS), and eCMS data entry.",
    "Site visits beyond two (Option 3); additional resubmittal rounds (Option 5).",
]
