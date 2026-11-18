# Full Narrative — B2185, B2187, B2855 Replace DDC Controls, NAS Patuxent River

## Project Overview

This project replaced and modernized the Direct Digital Control (DDC) systems — the core building automation infrastructure — across three occupied federal facilities at Naval Air Station Patuxent River, Maryland. The client was the Naval Facilities Engineering Command (NAVFAC), with the Naval Air Station and the Department of the Navy as the building owner. The project was structured as a design-build contract with the Designer of Record serving as a subconsultant to the general contractor prime, responsible for engineering the DDC replacement systems across all three buildings.

The three facilities collectively encompass approximately 785,000 square feet of active federal use. Building 2187 is a 467,530 SF research and development facility comprising open-plan and private offices, an atrium, raised-floor computer rooms, high-bay laboratories, secure facilities, and support spaces. Building 2185 is a 268,000 SF office building with open-plan workspace, secure facilities, and support functions. Building 2855 is a 49,464 SF office building with open-plan offices, private offices, and support spaces. All three buildings remained occupied and fully operational throughout construction, a defining constraint on scheduling, sequencing, and system cutover planning.

## Scope

The project was organized into three contract line items, each corresponding to a building with its own existing-conditions baseline, scope of DDC replacement, and commissioning requirements.

**Building 2187 (CLIN 001)** required replacement and upgrade of an existing JCI Metasys DDC installation serving a large and technically complex mechanical plant: three 650-ton water-cooled centrifugal chillers, three cooling towers, four gas-fired low-pressure hot-water boilers, fifteen variable-speed cooling-only air handling units, twenty-seven constant-volume makeup AHUs, fifty-six computer room air conditioning units with chilled-water and hot-water coils, and 442 VAV terminal units. New DDC controllers were provided throughout, existing wiring reused where adequate. The scope also required integration of the building's CRAC units into the new DDC system, correction of existing nuisance alarm conditions, implementation of energy savings control sequences (outdoor-air resets, economizer control, scheduling, chiller and boiler optimization), connection to the base-wide Unified Monitoring and Control System (UMCS) network via Niagara 4.x, and installation of a government-furnished Facility Point of Connection (FPOC) panel.

**Building 2185 (CLIN 002)** required complete replacement of an aging Automated Logic DDC system that was approaching obsolescence. Scope included new DDC controllers serving three chillers, four boilers, twenty-four AHUs, 225 VAV terminal units, and ninety computer room units, along with scheduling and optimization controls and maintenance of existing base-wide network connectivity.

**Building 2855 (CLIN 003)** required upgrade of an existing JCI Metasys DDC installation to meet current Unified Facilities Criteria (UFC) standards. Scope included replacement of CO₂, outdoor-air, and humidity sensors; cleaning of heat-exchange coils in rooftop units and VAV boxes; testing, adjusting, and balancing (TAB) of the complete HVAC system per NEBB/AABC standards; and commissioning of new and existing HVAC systems.

All three CLINs required BACnet-compliant controllers per ASHRAE Standard 135, a BACnet/IP backbone with MS/TP field networks, and cybersecurity implementation per UFC 4-010-06, UFGS 25 05 11, NIST 800-82, and the DoD Risk Management Framework. Network access controls included IEEE 802.1x and PIV credential integration. Contractor personnel required DoD DBIDS access authorization throughout construction.

## Role on the Project

The engineering team served as the Designer of Record under the design-build prime contractor, responsible for all DDC system engineering, specification, shop drawing review, and construction support across the three facilities. Design standards included UFC 3-410-01, UFC 3-410-02 (Direct Digital Control for HVAC), and the full UFGS suite for instrumentation, BACnet DDC, cybersecurity, and UMCS front-end integration (UFGS 23 09 00, 23 09 13, 23 09 23.02, 25 05 11, 25 10 10). An independent Commissioning Authority was required per UFGS 01 91 00.15 Total Building Commissioning.

<!-- INTERNAL: bfa_role is recorded as prime_consultant but DOR-under-GC relationship not confirmed from source documents; verify from project files -->

## Key Challenges and Resolutions

**Occupied-facility sequencing across a complex existing plant.** Building 2187 in particular presented a high-complexity sequencing challenge: a large chiller plant, multi-zone VAV system, and 56 CRAC units in active computer room and laboratory spaces, all requiring cutover without disruption to research operations. DDC replacement in occupied conditions required careful controller-by-controller cutover planning, with existing wiring reused where conditions allowed.

**Multi-manufacturer DDC ecosystem.** The three buildings had three different legacy DDC platforms — JCI Metasys in B2187 and B2855, Automated Logic in B2185 — each with its own network topology, field device wiring, and software environment. The replacement design standardized all three buildings on an open BACnet protocol, eliminating proprietary vendor lock-in and enabling integration to the base-wide Niagara 4.x UMCS.

**DoD cybersecurity requirements for facility control systems.** The project incorporated a full cybersecurity scope under UFGS 25 05 11 and UFC 4-010-06, addressing the DoD Risk Management Framework for Operational Technology (OT) networks. Requirements included STIG compliance, password management protocols, physical security of IP network components, IEEE 802.1x network access control, and PIV credential integration. This level of cybersecurity integration is increasingly standard on NAVFAC projects and required close coordination between the controls design, IT/network, and commissioning scopes.

**Base-wide UMCS integration.** Connection to the base Niagara 4.x UMCS (installed and managed by a separate contractor) required the design team to provide complete DDC system information to government integrators while maintaining construction schedules. The FPOC panels for B2187 and B2855 were government-furnished equipment installed by the contractor, requiring careful coordination with government-furnished material delivery and commissioning sequences.

## Outcomes

The project delivered open-protocol BACnet DDC systems in all three buildings, replacing end-of-life proprietary controls and connecting the buildings to the base-wide UMCS for centralized monitoring and management. Energy savings control sequences — outdoor-air resets, economizer operation, scheduling, chiller and boiler staging optimization — were implemented across the three facilities, replacing basic on/off control with sequence-based optimization. Nuisance alarm conditions in Building 2187 were identified and corrected as part of the DDC replacement. Building 2855 received a full HVAC testing, adjusting, and balancing pass alongside its DDC upgrade, improving system performance concurrent with the controls modernization. All systems were commissioned per UFGS 01 91 00.15 and government-witnessed Performance Verification Testing was completed per UFGS 23 09 00 requirements.
