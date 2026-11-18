<!-- full.md — long form narrative, 1-2 pages, entire project -->

# Raw Water No. 2 Treatment Plant Electrical Coordination Study

## Project Overview

The Raw Water No. 2 Treatment Plant Electrical Coordination Study is a completed engineering study addressing the electrical distribution system at a raw-water pump station in Gloucester, Virginia. The study was delivered in May 2024 as a standalone technical deliverable. The facility is identified in project documentation as "Raw Water No. 2 Treatment Plant – Gloucester, VA," and serves a water treatment function for the county's water utility. No separate construction contract or design phase was associated with this engagement; the deliverable is the study report itself.

The study was conducted under the scope requirements of ANSI/NEMA MTS-2019, the recognized standard governing electrical coordination study methodology for systems of this type.

## Scope

The scope of the study encompassed four discrete technical tasks:

1. **Field survey.** A field inventory of the existing pump electrical distribution system serving Pumps No. 2, 3, and 4, documenting installed equipment ratings, breaker types, and system topology.
2. **System modeling.** Development of a system model using SKM Power Tools power analysis software, incorporating the field-surveyed equipment data and a utility contribution assumption of 3-phase 100 MVA and single-line-ground (SLG) 30 MVA per the project input data.
3. **Short-circuit study.** Analysis of available fault currents at each protective device location within the pump electrical distribution system.
4. **Protective device coordination.** Evaluation and coordination of the tripping characteristics of the overcurrent protective devices (OCPDs) protecting the pumping circuits, using time-current curve (TCC) analysis.

The existing distribution topology consists of three pole-mounted 50 kVA transformers forming a transformer bank with a 480 V secondary. The transformer bank feeds a low-voltage automatic transfer switch (ATS) equipped with a 200 A main circuit breaker (Square D type JGL-36200T) with adjustable instantaneous trip. Pump branch circuits downstream of the ATS are protected by 50 A circuit breakers (GE type TED13050, fixed setting) for Pumps No. 2 and 3, and a 100 A circuit breaker (GE type TED13100, fixed setting) for Pump No. 4.

## Role on Project

The engineering team served as the sole study author and technical authority on the engagement. Services included field investigation, analytical modeling, TCC analysis, Equipment Evaluation Report preparation, and development of system modification recommendations. No design drawings, specifications, or construction-phase services were within scope.

## Key Challenges and Resolutions

### Selective Coordination Not Achievable with Existing Devices

The central technical challenge was the inherent mismatch between the trip characteristics of the installed 200 A MCB and the downstream 50 A and 100 A pump branch breakers. The TCC analysis demonstrated that the pump branch circuit breakers cannot be selectively coordinated with the 200 A MCB at any operating point. The instantaneous trip region of the MCB overlaps with the branch breakers' operating curves, meaning a fault on a pump branch will potentially trip the MCB rather than isolating only the faulted branch — a loss of selectivity that would interrupt all pumping service rather than only the affected pump.

This finding is a characteristic limitation of the installed device family and cannot be resolved by settings adjustments alone within the existing MCB. The study applied the ANSI/NEMA MTS-2019 framework for "compromised coordination" — a defined standard acceptance criterion for systems where full selectivity is not achievable — to establish the best attainable protection performance with the existing equipment.

### Equipment Ratings Confirmed Within Fault-Current Limits

A parallel finding of the short-circuit study was that all installed equipment operates within its rated interrupting and withstand capacity for the available fault currents at each bus. The Equipment Evaluation Report found no equipment requiring replacement solely on the basis of fault-current ratings. This narrows the remediation scope: the coordination issue is a selectivity problem, not an equipment adequacy problem.

## Outcomes

The study produced two prioritized recommendations:

**Near-term (settings-based).** Set the 200 A MCB instantaneous trip to the High (maximum) position. This adjustment moves the MCB's instantaneous trip threshold as far as possible from the branch breaker curves, achieving the best compromised coordination attainable with the installed device.

**Longer-term (equipment upgrade).** Replace the existing 200 A MCB with a 200 A MCB model that includes an adjustable or static instantaneous trip. A device with a higher adjustable instantaneous threshold — or a truly static (non-instantaneous) trip characteristic in the overlapping range — would achieve a near-coordinated system, substantially improving selectivity while remaining within the 200 A rating required by the ATS.

<!-- INTERNAL: Contract value, client entity, procurement method, and team roster were not available in the sole source document (the study report itself). These fields remain missing in the JSON record. A project summary memo or transmittal letter would be needed to source engagement-level metadata. -->

The study provides the facility owner with a documented basis for immediate protective device settings, a clear explanation of system limitations under current equipment, and a defined upgrade path. No major corroboration conflicts were found; the single source document is internally consistent.
