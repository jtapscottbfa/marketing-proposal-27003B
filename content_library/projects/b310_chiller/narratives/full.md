# Building 310 Chiller Replacement — NAS Oceana Dam Neck Annex
## Full Project Narrative

### Project Overview

The Building 310 Chiller Replacement project was a NAVFAC Mid-Atlantic design-build project executed at the Paraloft addition of Building 310, Naval Air Station Oceana, Dam Neck Annex, Virginia Beach, Virginia (eProjects WO# 1732054). Both of the building's nominal 40-ton air-cooled chillers—Trane Model CGAFC40EARA1000DEGH00N00000W00S units—had become non-functional and were beyond repair following years of exposure to the salt-laden marine environment at Dam Neck. The facility user, a DEVGRU tenant, required a reliable chilled water source to support year-round operations in the Paraloft addition, which houses air handling units AHU-1, AHU-2, and AHU-3 and could not tolerate extended loss of cooling.

Prior to contract award, Naval Station Oceana Facilities Maintenance & Shops (FM&S) had installed a temporary rental chiller to maintain chilled water service. The design-build contract required this temporary solution to remain in service to the maximum extent possible while the permanent replacement was designed and constructed.

### Scope of Work

The project scope encompassed the full replacement of the chilled water generation system at Building 310's exterior mechanical area:

**Demolition:** Remove two existing inoperable air-cooled chillers (CH-1 and CH-2) and their associated exterior chilled water supply and return piping from the mechanical room connection outward to each chiller. Demolish existing chiller housekeeping pads (92" × 92" × 7" each), electric heat trace and associated controls, and associated DDC control wiring back to the Johnson Controls Metasys panel.

**New Chiller Installation:** Furnish and install two new nominal ARI-certified 40-ton scroll air-cooled chillers with galvanized steel frames, epoxy electrodeposition-coated condenser coils for the salt-air environment, dual refrigerant circuits, four-stage capacity control, low-ambient capability to 0°F, factory-installed BACnet interfaces, and integral NEMA 4X disconnects. Chillers are piped in series, with the downstream chiller (CH-2) controlling to 41°F supply and CH-1 controlling to 49°F, consistent with the original system design from the 2006 Paraloft construction contract.

**Chilled Water Piping:** Install new Type L copper chilled water piping connecting the new chillers to the existing exterior supply and return piping at a point outside the mechanical room. The piping arrangement incorporates manually operated bypass valves at each chiller for single-chiller servicing, and emergency connection flanges with blind flanges to allow future temporary rental chiller hookup. All exterior piping is insulated with flexible elastomeric cellular insulation with an aluminum jacket and is protected by a new 5W/ft self-regulating electric heat trace system—one circuit for supply, one for return—fed from the existing Panelboard SP2.

**DDC Controls Integration:** The new chillers are integrated into the facility's existing Johnson Controls Metasys DDC system, which operates on an MS/TP BACnet FC Bus network served by an NAE-5512 controller located in Building P301-1. The existing FEC/IOM controller serving the chilled water system (address 4 on the CHWS trunk) communicates chiller enable/disable commands, chiller alarm and status monitoring, chilled water pump control, and chilled water supply and return temperature monitoring. The BACnet-capable microprocessor controls integral to the new chillers communicate directly into this existing JCI architecture. System TAB was required for the complete chilled water loop, including existing AHU-1, AHU-2, AHU-3, CWP-1, and CWP-2.

**Housekeeping Pads:** New reinforced concrete housekeeping pads are provided at each new chiller location, sized to the selected equipment with dowel connections to the existing slab-on-grade, coordinated with chiller service clearances, new piping routing, and pad elevation relative to the new piping connections.

**Construction Sequencing:** Due to anticipated long lead times for the chillers, construction sequencing required that all material and equipment submittals be approved and equipment in hand before commencing work, to minimize the duration of chilled water outage. During the cooling season, the DEVGRU tenant agreed to accept a maximum two-week period without chilled water service, and temporary chiller arrangements were specified to bridge any gap.

### Site and Security Context

Building 310 is a Controlled Access Area (CAA) within the NSWDG compound at NAS Oceana Dam Neck Annex. All contractor personnel, subcontractors, and suppliers required formal DEVGRU escort for all movements within and around the building. Escort requests were due NLT close-of-business each Wednesday for the following work week; failure to submit on time would result in lost access for the entire following week. Work hours were restricted to 0800–1600 Monday through Friday. All contractor personnel required background screening through the Defense Biometrics Identification System (DBIDS) and confirmation of U.S. citizenship. These security constraints formed a material schedule risk throughout the project and required disciplined coordination between the design-build contractor, the activity security officer, and NAVFAC's contracting officer representative.

The coastal location also imposed environmental requirements: all water drained from the chilled water system had to be captured, containerized, and sampled before discharge, with results submitted to the NAS Oceana Wastewater Manager.

### BFA's Role

BFA served as the Electrical Designer of Record (DOR) as a subconsultant to the design-build prime contractor. BFA's scope was limited to the electrical discipline: power distribution for the new chillers, demolition of existing chiller power circuits, new heat trace circuit wiring, and all associated panelboard coordination.

BFA produced a four-sheet electrical For-Sale Submission (FSS) drawing set under BFA project number 23-053, dated June 10, 2024:

- **E-001:** Legend, Abbreviations, and General Notes — electrical symbols and one-line legend; NAVFAC drawing number N40085-1909195 assigned.
- **ED101:** Electrical Demolition Floor Plan – Power — 1/2"=1'-0" scale plan of the mechanical room showing existing chillers CH-1 and CH-2 (dashed/demo) with associated panelboard circuits to be removed, including 208V chiller feeds and 120V heat trace and brazed plate heater circuits.
- **E-101:** Electrical New Work Floor Plan – Power — 1/2"=1'-0" scale plan showing new chiller power feeds: each new chiller served by a new 3-#3/0 AWG + 1-#6 AWG GND circuit in 2" conduit from existing Panelboard SP1 (800A MLO, 208Y/120V), through a new NEMA 4X integral disconnect (200A-3P, non-fused), at 194 MCA per chiller. Heat trace and brazed plate heater circuits extended from existing SP2.
- **E-601:** Panelboard Schedule and One-Line Riser Diagram — updated panelboard schedules for SP1 and SP2 and a one-line riser diagram confirming connection to the building's existing 2000A main switchboard.

The electrical FSS drawings were signed and sealed by Felix A. Pessig, PE, Virginia PE License No. 048025, and prepared under NAVFAC MILCON project 12901782.

### Key Technical Challenges

**Salt-environment corrosion failure:** The root cause of both chiller failures was the salt-laden marine environment at Dam Neck. The replacement specification required condenser coils with factory-applied epoxy electrodeposition coating on all coil surface areas—applied at the manufacturer's facility, not in the field—and galvanized steel frames and panels with louvered protective panels over the condenser coil face. Electric heat trace on exterior copper piping addresses the freeze protection concern identified in the original Paraloft construction.

**Operational continuity:** The Paraloft addition remained occupied and operationally active throughout construction. The construction sequencing plan required pre-coordination of the temporary rental chiller's removal (or relocation) with FM&S, because the temporary equipment occupied the work area and limited access to the chiller yard. A two-week maximum outage during the cooling season represented the activity's operational tolerance.

**DDC integration complexity:** The existing Johnson Controls Metasys system had been installed in 2009 under a separate JCI maintenance contract. Maintaining the existing control sequences—lead/lag pump selection by lowest runtime, series-chiller staging with distinct supply setpoints—while integrating new BACnet-capable chillers into an older FEC/IOM architecture required careful factory start-up and BACnet configuration by the chiller manufacturer's commissioning team, coordinated with JCI and the Oceana DDC Branch.

### Outcomes

The project resulted in restoration of permanent chilled water service to the Paraloft addition of Building 310, replacing two corrosion-failed chillers with new equipment selected and specified for the salt-air coastal environment. BFA's electrical FSS drawings addressed the FSS milestone for BFA design deliverables in June 2024, with the project proceeding toward construction completion. BFA project 23-053 is classified as complete.
