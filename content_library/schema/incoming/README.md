# Schema Specification — Incoming Draft

**Status:** DRAFT. Reconciled against v0.0.x codebase 2026-05-04 (D-017 through D-022). NOT authoritative until pressure-tested against three real projects.
**Generated:** May 4, 2026
**Source:** Multi-turn design session, conducted in chat
**Target version:** Schema v0.1.0 (project entity only)

---

## What this directory contains

A draft schema specification for the BFA content library, produced as part of
v0.0.2 build work. The directory was placed under `incoming/` deliberately to
signal that the contents are NOT yet authoritative repo artifacts.

```
content_library/schema/incoming/
├── README.md                           # this file
├── SPEC.md                             # main structural specification
└── vocabularies/
    ├── README.md                       # vocabulary conventions and standards posture
    ├── client_type.yaml                # 27 entries, NAICS-informed
    ├── program_type.yaml               # 115 entries, three-level, TWT-original
    ├── discipline.yaml                 # 26 entries, SF330 Section E
    ├── sub_discipline.yaml             # 66 entries, TWT-original under SF330 parents
    ├── building_systems.yaml           # 79 entries, TWT-original (UniFormat migration noted)
    ├── construction_scope.yaml         # 62 entries, TWT-original (MasterFormat migration noted)
    ├── delivery_method.yaml            # 12 entries, single-select
    ├── contract_vehicle.yaml           # 26 entries
    ├── procurement_type.yaml           # 28 entries, FAR-derived
    ├── award_type.yaml                 # 11 entries, single-select
    ├── project_status.yaml             # 14 entries, single-select
    ├── change_order_reason.yaml        # 16 entries
    ├── role_on_project.yaml            # 12 entries
    └── aliases/
        └── tag_aliases.yaml            # 37 starter aliases for tenant freeform tags
```

Total: 521 controlled vocabulary entries plus 37 starter aliases.

## Why this is in `incoming/` and not in `schema/` directly

The SPEC.md was drafted ahead of the existing v0.0.x codebase, on the working
assumption that an extraction pipeline existed and that the spec needed to be
reconciled against it. The reconciliation pass (2026-05-04) found that **no
extractor code exists in the repo.** The v0.0.x repo ships a CSV-based content
library (`content_library/*.csv`) and a form-population pipeline
(`scripts/populate_ae_forms.py`) that are architecturally *parallel* — not a
precursor — to the JSON record architecture described here.

The spec's design decisions held up against the multi-tenancy and
proposal-type-agnostic checks that surfaced during reconciliation, with one
in-session reversal (Virginia-named SWaM → generic
`socioeconomic_participation` block). All reconciliation outcomes landed in
`docs/decisions/2026-05-schema-design.md` as D-017 through D-022:

- **D-017** — Proposal-type-agnostic project entity. Schema captures facts;
  populators (DGS-AE, SF330, design-build, etc.) render facts into
  form-specific outputs.
- **D-018** — Additive CSV→JSON migration. JSON canonical; CSVs become a
  generated/derived view; `populate_ae_forms.py` unchanged at v0.0.3; full
  retirement of CSVs at v0.1.0+.
- **D-019** — `project_id` is the tenant's internal code; primary key is the
  composite `(tenant_id, project_id)`. Sunsets the engine-imposed DGS-prefix
  slug convention.
- **D-020** — Generic `socioeconomic_participation` block; certification
  scheme as a controlled vocabulary that ships with `va_swam` at v0.1.0 and
  expands as new tenants/jurisdictions land.
- **D-021** — DGS-AE5-specific rendering logic (codes_used → checkbox-token
  mapping, etc.) stays in `populate_ae_forms.py`; most v0.0.2 CSV columns
  absorb cleanly into the agnostic project entity.
- **D-022** — Multi-tenancy survival check as a design gate: every
  tenant-coupling decision must fold cleanly when tenant #2 signs.

The vocabulary YAML files are closer to ready-to-use because they're anchored
on industry standards (SF330, NAICS, FAR, Brooks Act) or are TWT-original at
a level not coupled to code structure. One new vocabulary file
(`certification_scheme.yaml` per D-020) needs to ship before the spec leaves
`incoming/`.

Promotion path: `incoming/v0.0.2-draft/` → `schema/` after pressure-test.

## Remaining work to do

Before any file in this directory becomes authoritative:

1. **Add `certification_scheme.yaml` vocabulary** with `va_swam` as the only
   entry at v0.1.0 (per D-020). Multi-tenant-ready shape; minimal seed
   content.

2. **Pressure-test against three real projects.** Per the v0.0.2 build
   digest, the spec needs to be walked through against three real BFA
   pursuits before v0.1.0 is locked. Suggested: one HRPDC, one WSSC, one
   state/local TBD. Each project's scope elements get mapped to schema
   fields and vocabulary entries; gaps are recorded as v0.1.1 corrections.

3. **Apply pressure-test corrections.** Spec bumps to v0.1.1 to reflect any
   field additions, vocabulary entries, or rule changes surfaced by the
   pressure-test pass.

4. **Move to final location.** After pressure-test, files move from
   `content_library/schema/incoming/` to `content_library/schema/`.

5. **Archive this directory.** Once promoted, the `incoming/v0.0.2-draft/`
   directory can be deleted or archived to `docs/archive/` for historical
   reference.

6. **Implement the CSV→JSON bridge** (`scripts/lib/csv_from_json.py`) per
   D-018, alongside the v0.0.3 spec promotion. The engine repo ships
   header-only CSVs; bridge work mostly affects BFA's working pursuit repos.

## Key design decisions baked into these files

Documented in detail in `docs/decisions/2026-05-schema-design.md`. Summary:

- **Project entity only** in v0.1.0. Personnel, past performance (as a
  separate entity), capability statements, and corporate facts are deferred
  to subsequent spec passes.
- **Three categories of fields**: facts (quote-or-null), taxonomy (controlled
  vocabularies), free text (linked Markdown files).
- **Multi-tenancy by design, single-tenant by implementation.** Every record
  carries `tenant_id` from day one even though it always equals `"bfa"` today.
- **Multi-select default** for taxonomy fields. Single-select is the explicit
  exception (delivery_method, project_status, award_type).
- **Three-state null handling**: `present_with_value`, `present_with_null`
  (source explicitly stated absence), `missing` (sources didn't address it).
- **Inline provenance**, not parallel block. Every fact field carries source
  reference and verbatim quote inline.
- **Phased financial structure**: design phase and construction phase tracked
  independently. Change orders are records, not scalars.
- **Drawing extraction deferred** to v1.1. v1 is text-only.
- **Source documents preserved**, not purged after ingestion.
- **CSI standards posture**: TWT-original taxonomies for v0.0.2 (Option B),
  with documented future migration to licensed CSI MasterFormat / UniFormat
  at v1.0 product gate (Option A). See `vocabularies/README.md` for migration
  paths.

## Charter-related items surfaced during this work

The following items need to be folded into the BFA license update for charter
v1.1, captured here so they're not lost:

1. **API/IP confidentiality acknowledgment.** BFA's Anthropic API account
   carries TWT prompts which are TWT confidential information per Article 10
   of the BFA license. Charter language needs to acknowledge this.
2. **Third-party IP carve-out clause.** Future v1.0 will license CSI Dynamic
   Standards. The BFA license needs a clause clarifying that Platform
   vocabularies may incorporate third-party industry standards under separate
   license, and such incorporation does not affect BFA's rights provided BFA
   maintains a current Platform subscription.

These are attorney-review items, not v0.0.2 blockers.

## Source materials

- **Design transcript:** `/mnt/transcripts/2026-05-04-15-37-29-bfa-content-library-schema-design.txt`
  (approximately 6 hours of multi-turn design discussion, including pushback
  and decision rationale)
- **Decision log:** `docs/decisions/2026-05-schema-design.md` (sanitized
  summary of design decisions and rationale, derived from transcript)
- **Build digest:** `v0_0_2-build-digest.md` in repo root or project docs.
  Architectural principles and goals that this spec implements.

## Generated by

This draft was produced through interactive design work, with deliberate
pushback on several initial assumptions. The transcript shows where the
direction reversed (drawing extraction deferred, source documents preserved,
CSV bootstrap reframed as one-shot). Read the decision log before making
substantive changes — many design choices have explicit rationale that
shouldn't be re-litigated without reading the source.
