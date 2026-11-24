# drawing_set_and_spec_baseline.md — calibration and construction procedure

`00_admin/drawing_set_and_spec_baseline.md` is the internal estimating basis and
level-of-effort model for a pursuit. This document is the procedure an agent
follows to build one, and the calibration record against which the numbers in it
are judged.

Read this before writing a baseline. Copy
`00_admin/drawing_set_and_spec_baseline.md.template` to start the artifact, and
log the issued result in `00_admin/drawing_set_calibration_ledger.md` when the
set actually goes out.

---

## Provenance and authority

Every rule below carries a marker. The marker states where the rule comes from,
so a reviewer can tell a contractual constraint from a house convention from a
guess.

| Marker | Meaning |
|---|---|
| **[C]** | **Canon.** Stated in the source methodology, `00_admin/reference_proposals/BFA_Drawing_Set_Methodology_INTERNAL.docx`, or in an RFP paragraph it cites. Do not deviate without recording why. |
| **[I]** | **Inferred.** Derived by structural analysis of the reference set, not stated in it. The source document flags its own inferences the same way. Deviate with reason. |
| **[N]** | **New.** Established after the reference pursuit, on 26040A or later. Weakest authority. Least calibration behind it. |

The source methodology was written for one pursuit — N4008526R0202, Replace Fire
Alarm System, Bldg 529, NAS Oceana — and states on its face that it is "written
for the ae-proposal-engine developer as a candidate for generalisation." This
document is that generalisation. Where the two disagree, the source is canon for
NAVFAC and UFC-governed work; this document governs everything else.

---

## 0. When to run this

Build a baseline when **all** of the following hold:

- BFA will produce sealed drawings (not a study, not a report, not a review).
- A fee has to be named or defended before the design exists.
- The sheet count is not dictated to us by the client or prime.

Do **not** build one for study-only, calculation-only, or plan-review scopes.
The artifact is an estimating model for drafting effort; with no drafting, it
models nothing and its presence invites the reader to assume drawings are
included.

---

## 1. Invariants

These hold in every baseline regardless of project type. A baseline that
violates one is wrong, not merely unusual.

1. **Two tables, two jobs. [C]** A deterministic sheet list answering "what will
   exist," kept separate from a probabilistic low/expected/high count answering
   "how wrong might we be, and about what." One table attempting both collapses
   into false precision or uselessly wide ranges. This is described in the
   source as "the single most transferable idea in the section."
2. **Seal-holder is a first-class property of every sheet. [C]** It is not a
   label. It sets the floor on sheet count, because sheets cannot mix
   disciplines to reduce the total.
3. **Every sheet row carries a justification naming what forces it into
   existence. [C]** Strip that column and the table is a wish list. Keep it and
   it is an estimating model defensible line by line.
4. **The range is traceable to named drivers, each tied to a numbered open
   item. [C]** A range without named drivers cannot be narrowed as information
   arrives; it can only be guessed at again.
5. **The MEP/FP flag is carried per series. [C]** Fee is often negotiated
   against the MEP subtotal rather than the total, so the subtotal must fall out
   of the table rather than be recomputed by hand under time pressure.
6. **The sheet list and count tables are internal.** Client-facing narrative
   states the total, the MEP split, and the documentation approach — nothing
   lower. **[C]**
7. **Ranges and justifications are written by a person, not generated. [C]**
   See §8.

---

## 2. Inputs required before starting

| Input | Why it is needed | If missing |
|---|---|---|
| Scope of work or RFP scope paragraphs | Source of forcing constraints | Stop. Without it every justification is invented. |
| Governing code or contract vehicle (UFC/UFGS, IBC, USBC, VRC…) | Determines mandated sheets and the spec tier model | Stop. |
| Seal roster — which PE seals which discipline | Sets the count floor (§3.1) | Stop. Ask. Do not assume one seal covers M, P, and E. |
| Set ownership boundary — who draws what | Determines whether BFA issues G/A series | Assume BFA issues MEP only; flag the assumption. |
| Building area and floor count | Drives plan-sheet multiplication | Estimate from the RFP and flag as a range driver. |
| Architectural plan scale, if a consultant | The single largest range driver on residential and fit-out work | **Make it range driver #1 and escalate.** See §6.3. |
| Number of floors / distinct areas | Trailing-digit assignment in the numbering grammar | Assume one plan sheet per floor per series; flag. |

Do not defer starting because an input is missing. Record the gap as a range
driver and proceed. That is what the range is for.

---

## 3. Procedure

### Step 1 — Establish the seal floor

List every discipline in scope and the licensed individual who will seal it.
Collapse disciplines that share a seal holder into one merge group.

**The floor on sheet count is the number of distinct seal holders, not the
number of disciplines. [I]**

On NAVFAC and UFC work the constraint is contractual — the reference cites Part 2
¶1.3.d, requiring each drawing to be sealed only by the Designer of Record
registered in the discipline depicted. **[C]** Elsewhere the constraint is
professional rather than contractual: a sheet is sealed by the engineer
competent in the work depicted. **[N]**

Record the merge groups explicitly, because they are what fee negotiation will
push against:

| Series | Seal holder | Merge permitted with |
|---|---|---|
| M | (name, license #) | P — same seal holder |
| P | (name, license #) | M — same seal holder |
| E | (different name, license #) | none |

Then state, in one sentence, whether disciplines are kept separate because a
rule forbids merging or because legibility at this building size argues against
it. Those are different positions under pressure, and the difference must be on
the page before the call, not improvised during it.

### Step 2 — Establish the set ownership boundary

Name every series in the eventual permit or bid set, and mark who issues it.

If BFA issues no G and no A series, state the consequence explicitly: **the MEP
subtotal equals the total, so any per-sheet fee discussion is a discussion about
the entire deliverable — there is no non-MEP ballast in the set to absorb a
reduction. [N]**

The reference set carried G and A and reported 16 MEP/FP of 21 total, so a
proportional fee cut landed partly on sheets BFA was not drawing. A consultant-
only set has no such cushion. This asymmetry is the most commercially important
adaptation made on 26040A and should be checked on every consultant engagement.

### Step 3 — Generate sheets from forcing constraints

Do not start from a sheet list and justify backwards. Start from constraints and
let sheets fall out. For each discipline, walk these in order:

1. **Vehicle-mandated.** What does the contract vehicle or code require to exist
   regardless of design? (Code analysis sheet, demolition sheet where any
   demolition occurs, calculation summary where the code names a calculation
   method.)
2. **Scope-mandated.** What does a named scope element force? (Generator in
   scope forces a one-line and a transfer detail. Gas service forces a gas plan.)
3. **Design-implied.** What does a design decision force, which would move if the
   decision moved? (Conduit-only distribution forces a raceway section. A sealed
   crawlspace forces under-floor distribution plans.)

These three justification types are canon from the specification model **[C]**
and apply equally to sheets **[I]**. They must be distinguished because **they
behave differently under change**: vehicle-mandated cannot be removed;
scope-mandated falls away only if that scope falls away; design-implied moves
when the design decision moves. Tag each sheet row with its type so that a scope
change can be costed by filtering rather than by re-reading.

Every discipline gets, at minimum:

- one legend / general notes / schedule sheet (`-001`)
- one plan sheet per floor (`-101`, `-102`, …)
- details where a non-standard installation exists (`-501`)

Anything beyond that must be forced by one of the three types above.

### Step 4 — Number the sheets

Apply the grammar in §4. Do not invent numbers. If a sheet does not fit a block,
that is a signal the sheet is mis-scoped, not that the grammar needs extending.

### Step 5 — Write the justification column

One clause per sheet, naming the constraint. Cite the paragraph, code section,
or scope element by number where one exists.

Good: `VRC M1401.3 Manual J/S/D summary; M1505.4.3 whole-house rate`
Good: `Six transmitter zones mapped` (the RFP prescribes exactly six)
Bad: `Required for coordination`
Bad: `Standard practice`

A justification that would read identically on any project is not a
justification. It is filler, and it is exactly what §8 forbids generating.

### Step 6 — Set the range

Assign low / expected / high per series, then total. Rules in §6.

### Step 7 — Name the range drivers

Every unit of spread between low and high must be attributable to a named
driver. Build the table:

| ID | Driver | Affects | Resolved by | Swing |
|---|---|---|---|---|

- **ID** — sequential `RD-n`.
- **Driver** — the uncertainty, stated as a question with two answers.
- **Affects** — the specific sheets that move. Not "all plans" unless literally
  all plans.
- **Resolved by** — a numbered open item in the client-facing narrative, or the
  words "production judgement" where no client input can settle it.
- **Swing** — signed sheet delta.

**Cross-check:** the sum of the positive swings must approximately reconcile to
`high − expected`, and the negative swings to `expected − low`. If they do not
reconcile, either a driver is missing or the range was set by feel. Both are
defects. **[N]**

Then name the dominant driver in prose beneath the table, state what it would
cost, and say when it must be settled. On 26040A that paragraph is what turned a
sheet count into a scoping-call agenda item.

### Step 8 — Build the specification model

Tier by **who holds the discretion**, which is the useful distinction: **[C]**

| Tier | Content | Discretion |
|---|---|---|
| Front-end (Div 0 / 1) | Enumerated by the vehicle | None — treat as a lookup keyed to the contract vehicle, not authored content |
| Technical | Derived from scope | Engineering judgement |
| Package components | Cover, TOC, proprietary packages, submittal register | Fixed checklist |

Capture the constraints that shape the whole package and carry hours: native
source format (e.g. SpecsIntact with generated submittal register is a tooling
requirement with real hours behind it, not a format preference), MasterFormat,
prescriptive sections incorporated without modification, and whether **on-drawing
specifications are accepted**. **[C]**

That last one is a level-of-effort switch, not a formatting note:

- **Not accepted** (typical NAVFAC): the specification effort must be priced
  separately. Removes the common shortcut of pushing short specs onto drawings.
- **No specification volume required** (typical residential permit path under a
  residential code): requirements ride in drawing notes, schedules, and details.
  The specification tier contributes **zero hours**. **[N]**

State which applies in one sentence, because it is the largest single driver of
non-comparability between sets of equal sheet count. An 18-sheet residential set
and an 18-sheet NAVFAC set are not the same job.

### Step 9 — Write the client-facing summary separately

See §7. Write it as its own block, in its own file or its own clearly bounded
section. Do not produce it by deleting columns from the internal tables.

### Step 10 — Run the acceptance gate

The baseline is not done until every line passes:

- [ ] Sheet list and count table are separate tables.
- [ ] Every sheet row has a seal holder.
- [ ] Every sheet row has a justification citing a specific constraint.
- [ ] Every sheet row is tagged vehicle-mandated / scope-mandated / design-implied.
- [ ] Every sheet number conforms to the §4 grammar.
- [ ] MEP flag present per series; subtotal stated.
- [ ] Low ≤ expected ≤ high on every row and on the total.
- [ ] Range drivers reconcile to the spread (Step 7 cross-check).
- [ ] Every driver names either an open-item number or "production judgement."
- [ ] Spread ratio is inside the §6.2 band, or the excursion is explained.
- [ ] Specification tier model present, including the on-drawing-specs switch.
- [ ] Client-facing summary states total, MEP split, and approach — and nothing
      lower.
- [ ] Document opens with an internal-only marker in an HTML comment **and** in
      visible text.
- [ ] Any conditional sheet is marked conditional and linked to its driver.

---

## 4. Sheet numbering grammar

Standard A/E practice; **[I]** in the source, which derived it from twenty-one
sheet numbers and found it held without exception.

| Block | Meaning |
|---|---|
| `-001`, `-002` | Legends, general notes, symbols, abbreviations, schedules |
| `-101`, `-102` | Primary plans. **Trailing digit = area or floor.** |
| `-111`, `-112` | Parallel second-pass plans over the *same* areas as `-10x` |
| `-201`, `-202` | Diagrams and schedules — riser, one-line, point-to-point |
| `-501` | Details |
| `-601` | Calculation summaries and device schedules |

Series prefix is the discipline: `G` general, `A` architectural, `M` mechanical,
`P` plumbing, `E` electrical, `FA` fire alarm and mass notification, `FP` fire
suppression.

### 4.1 The `-10x` / `-11x` pairing

In the reference, `-10x` was demolition and `-11x` was new work, on **matching
area splits**, so a reviewer can set `FA-101` beside `FA-111` and read the same
area before and after. On a replacement-in-an-occupied-building project, the
source notes, "that pairing is the whole story." **[C]**

**On new construction the `-11x` block is free.** Reassign it to a second pass
over the same areas — on 26040A, lighting circuiting parallel to the `-10x`
power plans. This preserves the convention's intent (same area, parallel sheet
family, readable side by side) while dropping its demolition-specific meaning.
**[N]**

Do not reassign `-11x` to an unrelated purpose. If the second family does not
cover the same areas as `-10x`, it belongs in a different block.

---

## 5. Justification taxonomy

Tag every sheet and every technical specification section:

| Tag | Definition | Behaviour under change |
|---|---|---|
| `vehicle_mandated` | Required by the contract vehicle or governing code irrespective of design | Cannot be removed |
| `scope_mandated` | Required by a named scope element | Falls away only if that scope falls away |
| `design_implied` | Follows from a design decision | Moves if the decision moves |

**[C]** — stated in the source for specification sections; extended to sheets
here **[I]**.

The practical value: when a scope element is cut during negotiation, filter on
`scope_mandated` + that element to get the exact sheet delta, instead of
re-deriving the set.

---

## 6. Range-setting rules

### 6.1 What the range means

Low, expected, and high are **not** best/likely/worst case on drafting hours.
They are the count of sheets that will exist under the plausible resolutions of
the named drivers. Expected is the count under the most likely resolution of
every driver simultaneously; low and high are the count under favourable and
unfavourable resolution of the drivers that actually move sheets.

### 6.2 Spread band

**[N] — prior, weakly calibrated. Two data points. Correct this from
`drawing_set_calibration_ledger.md` as sets issue.**

| Spread (high ÷ low) | Reading |
|---|---|
| < 1.5× before DD | Likely false precision. Check that plan-scale and area-split risk has actually been considered. |
| 1.7× – 2.3× | Normal at scoping stage before a DD set is in hand. |
| > 2.5× | A driver is unresolved to the point that the estimate is not yet an estimate. Escalate the driver; do not price around it. |

Observed to date: reference NAVFAC set 16/21/28 = **1.75×**. 26040A residential
set 13/18/29 = **2.2×**, the wider figure driven almost entirely by unresolved
plan scale.

Expect the band to tighten on receipt of the DD set. State the tightening
trigger in the document.

### 6.3 The plan-scale driver

**[N].** On any project where BFA draws over an architect's backgrounds, ask
before anything else: *does the floor plate fit at the architect's plan scale on
one sheet per floor?*

If it does not, BFA must either match the scale and split every plan sheet, or
diverge from the architectural set. Matching scale is normally correct for
coordination, which means the high column must assume the split.

This driver is uniquely dangerous because it **multiplies across every plan
sheet in every series simultaneously**. On 26040A it alone accounts for +6
sheets of a +11 total spread. Make it `RD-1` or close to it, and put it on the
scoping-call agenda in writing.

### 6.4 Conditional sheets

A sheet that exists only under one resolution of a driver is marked
**Conditional** in the sheet list, in bold, with a pointer to its driver ID. It
counts in expected only if its driver's likely resolution creates it.

---

## 7. The client-facing firewall

**Internal, always:** the sheet list, the count table, the range, and the range
drivers.

**Publishable:** the sheet total, the MEP split, the documentation approach, and
the seal count.

The reasoning is commercial, not stylistic. **[C]** These tables are the
estimating basis. Publishing them before the design exists invites line-item
negotiation against sheets that have not been drawn. The risk is sharper on a
consultant-only set, where every sheet is an MEP sheet and there is no non-MEP
ballast to absorb a reduction.

**This is the rule most easily broken.** On 26040A a full sheet list was
published to the architect and had to be pulled back to a summary.

### 7.1 Enforcement status — open gap

The reference pursuit enforced the split **programmatically**, via
`scripts/publish/build_dropin_narrative.py`, which sourced client prose from a
separate `narrative_summary.md` rather than filtering the detailed volume, so
the tables could not leak by accident. **[C]**

**No equivalent script exists in this repository.** The separation here is
convention only, and depends on the author not pasting a table into the
narrative. Until that script is ported, Step 9 is the only control, and an agent
must treat it as a hard step rather than a formatting preference.

---

## 8. What must not be automated

Canon, stated directly in the source. **[C]**

- **Ranges are engineering judgement.** How much fits at 1/8" = 1'-0" is not
  derivable from a schema. The engine should **store and aggregate** ranges, not
  generate them.
- **Justifications must be written by a person who read the requirement.** "A
  generated justification would look identical and mean nothing."

What an agent *may* do without judgement: aggregate counts per series from the
sheet list, compute the MEP subtotal by filtering the flag, run the Step 7
reconciliation arithmetic, run the Step 10 gate, and follow
`range_drivers[].affects` to report impact when an open item resolves.

An agent proposing a range must present it as a proposal for the engineer to
overwrite, and must say so in the document.

---

## 9. Data model

Carried from the source's §4.2 suggested model **[C]**, extended with
`justification_type` **[I]** and `conditional` **[N]**.

```yaml
sheet_series:
  - code: E
    discipline: Electrical
    seal: elec_pe              # constrains merging; see §3.1
    mep_fp: true
    count: { low: 5, expected: 7, high: 11 }
    sheets:
      - number: E-111
        title: First floor lighting circuiting plan
        role: second_pass      # legend | plan | second_pass | diagram | detail | calc
        area: floor_1
        justification: Circuits the architect's fixture layout
        justification_type: scope_mandated   # vehicle_mandated | scope_mandated | design_implied
        conditional: false
range_drivers:
  - id: RD-3
    description: Whether lighting circuiting overlays the power plans
    affects: [E-111, E-112]
    resolved_by: "narrative §5 item 1"
    swing: -2
spec_sections:
  front_end:                   # tier 1 — lookup by contract vehicle, no discretion
    - { section: "01 33 00", title: Submittal Procedures, source: "Pt. 2 ¶1.3.e.2" }
  technical:                   # tier 2 — derived from scope
    - section: "28 31 76"
      division: "28"
      title: Interior Fire Alarm and Mass Notification System
      justification_type: scope_mandated
      basis: Primary technical section
```

Three things fall out mechanically from this model that are otherwise manual:
the count table (aggregate sheets per series), the MEP subtotal (filter on the
flag), and impact analysis when an open item resolves (follow
`range_drivers[].affects`). **[C]**

---

## 10. Calibration data — what we have, and what it cannot tell us

### 10.1 The content library samples sheets; it does not count sets

`content_library/projects/*/record.json` carries a `drawings.sheets[]` block
with `sheet_number`, `title`, and `discipline`. As of 2026-08-10: **143 project
records, 72 with sheet data, 440 sheets total**, across a clean discipline
vocabulary (`electrical_engineering`, `mechanical_engineering`,
`plumbing_engineering`, `fire_protection_engineering`, `civil_engineering`,
`structural_engineering`, and others).

**These are not set totals and must never be used as count anchors.** The
records extract whatever PDFs were on hand, not issued sets. The median
extraction on records flagged `drawing_extraction_status: complete` is **4
sheets**, while individual extraction notes describe the real sets they came
from as far larger — the Kislak record's own note says its set "spans ~150+
sheets" against 6 extracted rows.

Calibrating a count model on that data would bake in an order-of-magnitude low
bias.

### 10.2 What the library *can* calibrate

- **Discipline vocabulary** — use the library's terms so a baseline joins to the
  rest of the content library.
- **Numbering and titling conventions** actually used on BFA and partner sets.
- **Discipline mix** — which series co-occur on which project types, as a check
  that a series has not been forgotten.

### 10.3 Count anchors come from the ledger

`00_admin/drawing_set_calibration_ledger.md` is the only sanctioned source of
count anchors. It starts nearly empty by design: two rows, one of them an
estimate not yet an actual. **Do not treat a two-row ledger as calibration.**
State in every baseline that the range is judgement-led until the ledger has
depth.

Logging a set into the ledger is a required close-out step, not an optional one.
Every issued set that is not logged is calibration permanently lost.

---

## 11. Worked derivation — 26040A, Waltz Residence

The full artifact is `00_admin/drawing_set_and_spec_baseline.md`. This is the
derivation, step by step, as a pattern to match.

**Project.** New-construction single-family residence, ~6,500 SF, two storeys,
Virginia Beach. BFA is MEP consultant to makeSHIFT (architect). Residential
permit set under the Virginia USBC / VRC.

**Step 1 — seal floor.** Two seals, not three disciplines: O'Grady seals M and
P; Williams seals E. M and P *could* legally merge. They were kept separate for
legibility at 6,500 SF, not because a rule forbids it — and the document says so
explicitly, so that fee negotiation meets a stated position rather than an
improvised one. E cannot merge with either.

**Step 2 — ownership boundary.** makeSHIFT holds cover, index, code analysis,
and all architectural sheets. BFA issues no G, no A. Consequence recorded: MEP
subtotal = total, 18 of 18, no ballast.

**Step 3 — forcing constraints.** VRC M1401.3 forces a Manual J/S/D summary
(`vehicle_mandated`). NEC Art. 220 forces a service-sizing load calculation
(`vehicle_mandated`). Generator and ATS in scope force a one-line and a pad
detail (`scope_mandated`). Gas service, if elected, forces a gas plan and
isometric (`design_implied`, and therefore conditional).

**Step 4 — numbering.** New construction, so no demolition series; the `-11x`
block was reassigned to lighting circuiting over the same areas as the `-10x`
power plans. Riser diagrams took `-201` because a two-storey set needs them for
plan-review legibility.

**Step 6 — range.** 13 / 18 / 29. Spread 2.2×, wider than the reference's 1.75×,
and the document says why in one sentence rather than leaving the reader to
infer competence or its absence.

**Step 7 — drivers.** Seven, RD-1 through RD-7. RD-4 (plan scale) alone swings
+6 by multiplying across every plan sheet in all three series, and is called out
in prose as the item to settle on the scoping call before fee issue.

**Step 8 — specifications.** The residential permit path inverts the reference:
no specification volume, requirements carried in drawing notes and schedules,
CSI-format specifications an explicit exclusion in the client narrative. The
specification tier contributes zero hours — recorded as "the single largest
structural difference between this pursuit and the reference."

**Step 9 — client-facing.** Four permitted statements enumerated; three
prohibited ones enumerated. Both lists written out, because the failure mode on
this pursuit was over-disclosure.

---

## 12. Change log

| Date | Change |
|---|---|
| 2026-08-10 | Initial generalisation from `BFA_Drawing_Set_Methodology_INTERNAL.docx` (N4008526R0202) plus the 26040A adaptations. Added: seal-floor framing, ownership-boundary step, justification taxonomy extended to sheets, spread band, plan-scale driver, acceptance gate, content-library calibration finding. |
