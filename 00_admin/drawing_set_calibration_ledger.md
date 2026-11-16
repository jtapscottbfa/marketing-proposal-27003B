# Drawing Set Calibration Ledger

<!-- INTERNAL. Estimating accuracy record. Not for client or design-team
     transmittal. This file exists to make the next estimate better than the
     last one; it also documents, in public view, every time BFA was wrong. -->

**Internal document.** Estimating accuracy record across pursuits. Not for
client or design-team transmittal.

The only sanctioned source of sheet-count anchors. Built and consumed per
`00_admin/drawing_set_and_spec_baseline.SCHEMA.md` §10.

---

## Why this file exists

A low/expected/high range is only an estimate if someone eventually checks it
against what issued. Without that check the method reproduces its own priors
indefinitely and calls the result experience.

**The content library cannot substitute for this.**
`content_library/projects/*/record.json` carries a `drawings.sheets[]` block —
143 records, 72 populated, 440 sheets as of 2026-08-10 — but those rows are
extractions from whatever PDFs were on hand, not issued sets. Median extraction
on records flagged `drawing_extraction_status: complete` is **4 sheets**, against
real sets an order of magnitude larger. Using library counts as anchors would
bake in a severe low bias. The library calibrates naming, numbering, and
discipline mix. It does not calibrate counts.

## Logging rule

Log a row when the set **issues** — permit submission, bid set, or final
delivery, whichever is the first sealed issue. Not at award, not at DD.

Logging is a required close-out step. Every issued set that is not logged is
calibration permanently lost, and it is lost silently.

If a pursuit is lost or cancelled before issue, log it anyway with
`Actual = n/a` and a note. The estimate itself is still evidence about how the
method behaves on that project type.

---

## Row schema

| Field | Notes |
|---|---|
| `Pursuit` | Project number and short name |
| `Type` | Project type — residential / fit-out / industrial / federal / institutional |
| `Vehicle` | Governing code or contract vehicle |
| `Area` | Gross SF, or `n/a` |
| `Seals` | Count of distinct seal holders (the count floor) |
| `Specs` | `volume` / `on-drawing` / `none` — the largest non-comparability driver |
| `Low / Exp / High` | The baseline range as first issued |
| `Actual` | Sheets in the issued set, BFA-authored only |
| `Err` | `Actual − Exp` |
| `In band?` | Whether `Low ≤ Actual ≤ High` |
| `Dominant driver` | The RD- that carried the most spread, and how it actually resolved |

---

## Ledger

| Pursuit | Type | Vehicle | Area | Seals | Specs | Low | Exp | High | Actual | Err | In band? | Dominant driver — actual resolution |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N4008526R0202 — Bldg 529 FA replacement, NAS Oceana | Federal, replacement in occupied building | NAVFAC / UFC / UFGS | n/a | 4+ (Lead DOR, RA, FP DOR, Mech PE, Elec PE) | volume | 16 | 21 | 28 | *not recorded* | — | — | Area smoke detection extent (OI-12); plan fit at 1/8" — resolution not recorded |
| 26040A — Waltz Residence, Virginia Beach | Residential, new construction | Virginia USBC / VRC | 6,500 SF | 2 | none | 13 | 18 | 29 | *pending issue* | — | — | RD-4 plan scale — **unresolved at baseline**; settle on scoping call |

<!-- Two rows, neither with an actual. This is not calibration yet. Any baseline
     written before this table has depth must say so in its own text: the range
     is judgement-led, not data-led. -->

---

## Derived metrics

Recompute when a row gains an actual. Do not report a metric on fewer than five
closed rows; state the count alongside any figure quoted elsewhere.

| Metric | Definition | Current | n |
|---|---|---|---|
| Band hit rate | Share of closed rows where `Low ≤ Actual ≤ High` | — | 0 |
| Median signed error | Median of `Actual − Exp` — detects systematic optimism | — | 0 |
| Median absolute error | Median of absolute `Actual − Exp` | — | 0 |
| Mean spread ratio | Mean of `High ÷ Low` at baseline | 1.98× | 2 |
| Spread efficiency | Band hit rate ÷ mean spread ratio — rewards being right *and* tight | — | 0 |

**Target once n ≥ 5:** band hit rate ≥ 80% with mean spread ratio ≤ 2.0×. A
100% hit rate with a 3× spread is not accuracy; it is a range wide enough to be
unfalsifiable.

---

## Driver post-mortem

One row per range driver that materially moved, across all pursuits. This is
where the driver catalog in the SCHEMA earns or loses its priors.

| Pursuit | Driver | Predicted swing | Actual swing | Note |
|---|---|---|---|---|
| — | — | — | — | *first entry lands when 26040A issues* |

<!-- Watch specifically for: (1) whether plan scale really is the dominant
     driver on consultant-to-architect work, or whether 26040A was atypical;
     (2) whether the -11x reassignment to second-pass plans survives contact
     with production, or gets folded back onto the -10x plans. -->

---

## Change log

| Date | Change |
|---|---|
| 2026-08-10 | Ledger created. Seeded with the reference NAVFAC pursuit and 26040A, neither yet closed. Content-library limitation recorded. |
