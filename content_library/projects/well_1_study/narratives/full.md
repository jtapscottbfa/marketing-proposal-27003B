# Gloucester County Well No. 1 Electrical Coordination Study

## Project Overview

The Gloucester County Well No. 1 Electrical Coordination Study is a technical engineering study performed for Gloucester County, Virginia, in June 2024. The subject facility is Well Pump No. 1 at the Raw Water No. 2 Treatment Plant in Gloucester, VA — a municipal water infrastructure asset supplying raw water to the county's treatment process. The electrical distribution system studied serves the well pump as its primary load, with ancillary loads fed from the same switchboard. The work was performed as a prime consulting engagement, with a single study report as the primary deliverable.

The study was conducted in compliance with ANSI/NEMA MTS-2019, the governing standard for the scope and methodology of coordination studies, and interpreted against NEC 2023 provisions for overcurrent protection coordination requirements.

## Scope of Services

The scope of the coordination study comprised four integrated technical tasks:

**Field Survey and System Modeling.** A field survey of Well Pump No. 1 was conducted to document the existing electrical distribution system configuration. Survey data was used to build a computational model in SKM Power Tools, a power systems analysis software, capturing the system topology from the utility service point through to the well pump load.

**Short Circuit Study.** A short circuit analysis of the modeled system was performed to quantify available fault currents at each bus in the distribution system. The utility service provides a three-phase short circuit contribution of 2,528 amperes and a single-line-to-ground (SLG) contribution of 2,114 amperes. Calculated bus fault currents ranged from 27,545 amperes (three-phase) at the main switchboard to 1,989 amperes (three-phase) at Panel LP3 on the 208 V branch.

**Equipment Evaluation.** Each protective device in the distribution system was evaluated against the ANSI Fault Analysis criteria, which requires that calculated available fault current not exceed 90 percent of the device's rated interrupting capacity. The evaluation covered the following system components: a 1,500 kVA, 34,500–480Y/277 V utility transformer; a 3,000-ampere, 480/277 V main switchboard (EATON HKD-type circuit breaker at 400 A); a 600-ampere, 480/277 V Panel DP-1 (EATON HLD-type main circuit breaker at 600 A); a 30 kVA step-down transformer branch serving Panel LP3 at 208/120 V; and a 100 HP, 460 V well pump motor with associated starter circuit. An emergency generator feeds the system through a transfer switch, providing backup to the distribution system in loss-of-utility events.

**Time Current Curve Development and Protective Device Coordination.** Time current curves (TCCs) were developed for the distribution system using the SKM model. TCC analysis identified the coordination relationships between protective devices and established the recommended instantaneous trip settings for each circuit breaker in the system.

## Role on Project

The firm served as prime consultant for the study, with full responsibility for the field survey, system modeling, analysis, and written study deliverable. No subconsultants were engaged. The client was Gloucester County.

## Key Challenges and Resolutions

**Selective Coordination Limitation.** The central technical challenge of the study was that full selective coordination — the preferred protection coordination outcome, in which only the protective device nearest a fault operates while all upstream devices remain closed — cannot be fully achieved for this system configuration. Two 600-ampere circuit breakers are present in series in the distribution path (the main circuit breaker of Panel DP-1 and the overcurrent protective device for the well pump circuit), and their overlapping time-current characteristics prevent full selectivity.

The resolution applied was compromised coordination, the achievable alternative recognized under ANSI/NEMA MTS-2019. Under compromised coordination, the protective devices are set to minimize the zone of outage while accepting some degree of overlap in operating characteristics. The recommended instantaneous trip settings documented in the TCC Setting Report achieve this outcome within the constraints of the installed equipment. Separately, NEC 2023 paragraph 620.62 Exception No. 2 provides an explicit regulatory allowance for the two 600-ampere circuit breakers in series, which are not required to be selectively coordinated under that code provision, reinforcing the technical and regulatory basis for the compromised-coordination recommendation.

**Single-Source Documentation.** The study report is the only project document available in the project record — no contract, basis of design, or specifications exist in the record. All quantitative facts (equipment ratings, fault currents, voltage drop results) were sourced from within the report itself, cross-referenced between the introductory narrative, the study input data section, and the embedded one-line diagrams (sheets E-601 through E-604). Financial and procurement data are entirely absent from the available record.

## Outcomes

All protective devices in the distribution system passed the ANSI Fault Analysis equipment evaluation — no equipment was found to have failed the evaluation, meaning no protective device upgrades were required as a prerequisite to implementing the coordination recommendations. The study concluded with a set of recommended instantaneous trip settings, documented in a TCC Setting Report, that achieve compromised coordination for the system in its current configuration. Voltage drop results were documented across the distribution system: 0.4% at the main switchboard, 1.3% at Panel DP-1, and 3.1% at Panel LP3.

The study provides Gloucester County with a quantitative, code-compliant basis for configuring protective device settings at Well Pump No. 1, reducing risk of cascading outages from a fault at the well pump while operating within the physical constraints of the installed distribution equipment. The study was completed in June 2024.
