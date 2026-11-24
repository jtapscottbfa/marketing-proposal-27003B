# Building 340 Replace Closed Circuit Evaporative Cooler — Full Project Narrative

**Client:** Naval Facilities Engineering Systems Command (NAVFAC) Mid-Atlantic, PWD Oceana FEAD  
**Location:** Naval Air Station Oceana, Virginia Beach, Virginia  
**BFA Role:** Designer of Record (DOR), subconsultant to SYNCON LLC (design-build prime)  
**Contract Vehicle:** Federal design-build task order (eProjects WO# 1655654)  
**BFA Project No.:** 22-044  
**Design Submittal:** Final Interim Submittal, April 7, 2023

---

## Project Overview

Building 340 at Naval Air Station Oceana houses a water-source heat pump (WSHP) system — a multi-unit geothermal cooling and heating plant serving approximately 30 heat pumps distributed across five occupied floors. The heat rejection leg of this system relies on a closed-circuit evaporative cooler (CC-1) mounted on an exterior concrete pad on the northeast side of the building. By 2022, the existing EVAPCO unit (Model ESW-102-33H, installed circa the 2009 energy conservation measures project) had deteriorated to an unusable state, rendering the building's condenser water system unreliable.

NAVFAC Mid-Atlantic procured the replacement through its design-build delivery platform, issuing a Request for Proposal (eProjects WO# 1655654) developed by PWD Oceana FEAD and approved by Design Engineering Branch Manager Christopher B. Morris, P.E. SYNCON LLC was awarded the design-build contract as prime contractor; BFA served as the licensed Designer of Record, providing full engineering design for all disciplines required to complete the replacement within the constraints of the active installation and the occupied building.

A critical operational constraint governed the entire project: Building 340 was required to remain in operation throughout construction. All utility outages — electrical, HVAC, and plumbing — required coordination and after-hours scheduling. The existing geothermal well field system was to serve as the primary heat exchanger during the construction period.

---

## Scope of Work

### Mechanical

BFA designed the removal of the existing CC-1 unit and all associated exterior condenser water piping, controls, and equipment supports, and the installation of a new EVAPCO ESW4 9-43G18-SP-R closed-circuit evaporative cooler. The new unit is an induced-draft, vertical-discharge, all-stainless-steel cooler rated at 524.8 GPM with 25% propylene glycol solution, entering water temperature (EWT) of 100°F, leaving water temperature (LWT) of 90°F at a design wet-bulb temperature of 80°F — achieving approximately 168 tons (2,524 MBH) of heat rejection capacity. Key equipment features designed per the NAVFAC RFP requirements include electric sump heaters (2 × 6 kW), a low-sound fan option with inverter-duty motors and VFD control, electric water level control, an external service platform with ladder and motor davit, and a NEMA 4X stainless steel VFD control panel with single-point 460V/3-phase power connection.

New condenser water piping was designed with insulation, metallic jacket, and heat tracing for all exterior piping subject to freezing, integrated with the existing geothermal/condenser water system. Mechanical room scope included replacement of the existing floor drain with a new 12" × 36" trench drain system discharging to sanitary sewer in Room 166, and a new chemical water treatment system with Neptune filter feeder for spray water quality management.

DDC integration required modification and expansion of the existing Trane Tracer DDC control system to accept the new cooler via BACnet communications, including control points for fan start/stop, spray pump start/stop, VFD speed, condenser water supply and return temperatures, and make-up water flow metering. A new standalone wall-mounted LED temperature sensor in a NEMA 4X enclosure provided direct reading of condenser water supply temperature independent of the DDC system.

### Structural

The structural design addressed the substantial weight and dynamic loading of the new cooler unit. The EVAPCO ESW4 9-43G18-SP-R weighs approximately 26,450 lbs operating (plus 1,020 lbs for the external service platform), with plan dimensions of approximately 8'-5.5" wide by 18'-0" long. BFA designed a new 2'-6" thick reinforced concrete mat foundation — reinforced with #6 bars at 12" o.c. at the top mat and #8 bars at 12" o.c. at the bottom mat — located approximately 3 feet from the existing building wall to avoid imposing load on existing building foundations. The foundation is elevated 6 inches above surrounding grade to achieve positive drainage.

A two-level structural steel support frame of W12 sections raises the bottom of the cooler to +2'-0" above the concrete foundation, providing access for drain and piping connections and meeting the RFP requirement that the cooler discharge elevation exceed the adjacent main building exterior wall height to prevent recirculation. Three-quarter inch diameter anchor bolts resist lateral forces from wind (design wind speed 124 mph Vult, Exposure Category C, Risk Category II; Wind Base Shear Vx = 13.2 kips, Vy = 6.5 kips) and seismic loading (Design Spectral Response Acceleration Sms = 0.124g; Design Base Shear 3.38 kips). Special inspections were specified under Broyles and Associates, P.C. Geotechnical bearing capacity was assumed at 1,500 PSF pending contractor-provided geotechnical confirmation prior to concrete placement.

### Civil

Civil site work was confined to a limit of disturbance (LOD) of approximately 750 SF on the northeast side of Building 340. The scope included demolition of the existing cooling unit, concrete walk pavement, and surrounding gated wood fence enclosure; installation of the new elevated concrete equipment pad/foundation; site grading with positive drainage away from the building; a new 50 LF, 7-foot high pressure-treated wood fence enclosure; and Bermuda grass sod restoration of disturbed areas. Erosion and sediment control was provided via silt fence. The land disturbance did not exceed 10,000 SF, and additional impervious surface did not exceed 5,000 SF; no DEQ permit and no LID calculations were required.

### Electrical

The electrical design addressed demolition of all existing CC-1 power and control circuits back to their source, and provision of a new 40A circuit from the existing 480Y/277V, 3-phase, 4-wire panelboard in Room 165 ("LA" or "HC") to the new VFD control panel, including a new 60A 3-phase NEMA 4X fused disconnect switch and new 60/3 circuit breaker in the panelboard. A new GFCI duplex receptacle was provided in the cooler equipment yard. All conductors were specified as copper THHN/THWN, minimum #12 AWG for power and #14 AWG for control, with voltage drop limits not exceeding 2% for feeders and 3% for branch circuits. The electrical scope also included removal, re-lamping, cleaning, and reinstallation of six fluorescent lighting fixtures in the mechanical equipment room to support ceiling access for mechanical and electrical work.

### Architectural

Architectural work was provided in support of the mechanical scope. The scope included removal of the existing acoustical ceiling system in Room 166 to provide ceiling access for the mechanical and electrical work, with storage, cleaning, and reinstallation following completion. All existing wall openings remaining from Plumbing, Mechanical, and Electrical work not reused for new work were filled, patched, and painted to match adjacent construction. All new and reused pipe and conduit wall penetrations were sealed and flashed.

---

## Key Challenges and Design Approach

**Occupied facility continuity.** The building remained in full operation throughout the project, requiring careful sequencing of all mechanical and electrical outages to occur after hours, on weekends, or on federal holidays. BFA's design addressed this by clearly delineating existing systems to remain and providing detailed sequencing guidance.

**Glycol system coordination.** The existing geothermal/condenser water system contained glycol of unknown type and concentration. The RFP required that the contractor coordinate with the NAS Oceana Water Program Manager prior to any discharge, with detailed water sampling and testing protocols before disposal. BFA's mechanical design specified flushing and refilling the system with 25% propylene glycol per UFC/UFGS criteria.

**Cooler elevation and discharge recirculation.** The RFP required the new cooler's top discharge to be at or above the adjacent building wall to prevent discharge air recirculation. BFA's structural design resolved this through the combination of the elevated foundation and the two-level W12 steel support frame, raising the cooler body sufficiently to meet this requirement while maintaining manufacturer-required service clearances.

**Foundation proximity to existing structure.** The new mat foundation was designed with a 3-foot setback from the existing building wall to avoid imposing bearing loads on the existing building foundations — a conservative but necessary approach given the absence of geotechnical borings required by the RFP (allowable bearing capacity assumed at 1,500 PSF, pending contractor-provided geotechnical confirmation).

---

## Outcomes

BFA completed the Final Interim Design Submittal on April 7, 2023, providing a complete, professionally signed and sealed design package in compliance with NAVFAC's FC 1-300-09N design procedures and all applicable UFC criteria. The design addressed all disciplines required to support SYNCON LLC's construction of the cooler replacement — delivering a technically complete, installation-ready design that maintained the operational continuity requirements of the active naval air station.
