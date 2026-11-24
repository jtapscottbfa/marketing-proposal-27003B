---
schema_version: 0.1.0
status: draft
scope: project entity (BFA content library v1)
last_updated: 2026-05-04
applies_to: TWT GovCon Solutions content library
---

# Content Library Schema Specification

## Project Entity (v0.1.0)

### Purpose

This specification defines the structure of project records in the TWT content
library. It governs how the extractor produces JSON, how downstream gates query
the library, and how human reviewers edit records.

The schema is the product. Firm-specific data is tenant data. This separation is
enforced by structure, not by convention — every record carries `tenant_id`,
controlled vocabularies are versioned product artifacts, and free-text content
lives in tenant-scoped Markdown files referenced from JSON.

This v0.1.0 specification covers the **project entity only**. Personnel, past
performance (as a distinct entity from project records), capability statements,
and corporate facts are out of scope and will be specified in subsequent passes.

### Design principles

1. **Three categories of fields, three sets of rules.**
   - **Facts** are extracted with quote-or-null discipline and inline provenance.
   - **Taxonomy fields** are validated against controlled vocabularies in
     `vocabularies/`.
   - **Free-text content** lives in linked Markdown files, not in JSON.

2. **Multi-select is the default.** Every taxonomy field is an array of enum
   values. Single-value cases are arrays of length one. Single-select is the
   special case and must be explicitly noted in the field definition below.

3. **Three-state null handling.**
   - `present_with_value` — field has a value extracted from sources.
   - `present_with_null` — source explicitly stated absence (e.g., "no change
     orders to date"). Encoded as `null` with provenance attached.
   - `missing` — sources did not address this field. Encoded by field absence
     from the JSON, OR by `{"value": null, "status": "missing"}` for fields
     where presence/absence matters downstream.

4. **Inline provenance, not parallel block.** Every fact field carries its
   source quote and anchor inline with the value, so copying a field copies its
   provenance. See `Provenance format` below.

5. **Multi-tenancy by design, single-tenant by implementation.** Every record
   carries `tenant_id`. Today it always equals `"bfa"`. The schema and
   extractor never assume single-tenant operation.

6. **Versioning on every record.** Every record carries `schema_version`,
   `extractor_version`, and `extracted_at`. Re-extraction bumps `extractor_version`
   and `extracted_at`; schema changes bump `schema_version`.

---

## Top-level project record structure

```yaml
# Identity and provenance (always present, all records)
tenant_id: bfa
schema_version: 0.1.0
extractor_version: 0.1.0
extracted_at: 2026-05-04T15:30:00Z
project_id: 23-1047                    # BFA internal project number; primary key
project_slug: matoaka-renovation       # human-readable secondary identifier

# Source documents (always present)
source_documents:
  - path: //bfa-staging/projects/23-1047/01_BOD_Final.pdf
    type: bod
    sha256: a3f8c9d2e1b4...
    page_count: 24
    included: true
  - path: //bfa-staging/projects/23-1047/SOW_Rev3.docx
    type: sow
    sha256: 7c2e5d4a9f1b...
    included: true
  # ...

# Completeness profile (always present; derived from manifest pass)
completeness:
  has_bod: true
  has_sow: true
  has_specs: true
  has_drawings: true              # files present, but extraction may be deferred
  has_narrative_documents: false
  completeness_tier: full         # full | partial | sparse
  drawing_extraction_status: deferred   # deferred | attempted | complete

# Facts section — quote-or-null discipline applies to all fields here
facts:
  project_name:
    value: "Matoaka Elementary School Renovation"
    source: "BOD p.1"
    quote: "Matoaka Elementary School Renovation"
  client_name:
    value: "Williamsburg-James City County Public Schools"
    source: "SOW §1.1"
    quote: "the Owner, Williamsburg-James City County Public Schools (WJCC)"
  owner_name:
    # Often same as client; separate field because they diverge on federal
    # projects (e.g., contracting agency vs. using agency)
    value: "Williamsburg-James City County Public Schools"
    source: "SOW §1.1"
    quote: "the Owner, Williamsburg-James City County Public Schools (WJCC)"
  location:
    city: "Williamsburg"
    state: "VA"
    country: "US"
    facility_address: "7800 Richmond Rd, Williamsburg VA 23188"
    source: "BOD p.1"
    quote: "Project Location: 7800 Richmond Rd, Williamsburg VA 23188"
  project_number_internal:
    value: "23-1047"
    source: "BFA internal records"
    quote: null               # internal data, not source-document-derived
  project_number_client:
    value: "WJCC-2023-014"
    source: "SOW p.1"
    quote: "WJCC Project No. WJCC-2023-014"
  contract_number:
    value: null
    status: missing
  task_order_number:
    value: null
    status: missing
  square_footage:
    value: 45000
    unit: gsf                 # gsf | nsf | rsf
    source: "BOD p.3"
    quote: "approximately 45,000 GSF of renovated space"
  program_budget:
    value: 8500000
    currency: USD
    source: "BOD p.4"
    quote: "Total Program Budget: $8.5M"

# Phased structure — design and construction tracked independently
# Either phase may be absent if BFA scope didn't include it
phases:
  design:
    contract_value:
      value: 425000
      currency: USD
      source: "Contract §3.1"
      quote: "Design Fee: $425,000 lump sum"
    awarded_date:
      value: "2023-03-15"
      source: "Contract signature page"
      quote: "Executed this 15th day of March, 2023"
    started_date:
      value: "2023-03-20"
      source: "BFA project records"
      quote: null
    completion_date:
      value: "2023-11-30"
      source: "Design submittal log"
      quote: "Final design submitted 2023-11-30"
    contractual_duration_days:
      value: 260
      source: "Contract §4.2"
      quote: "Design phase shall not exceed 260 calendar days"
    change_orders:
      - co_number: "D-CO-001"
        value: 18500
        currency: USD
        date: "2023-06-12"
        reason: scope_addition          # vocab: change_order_reason
        description: "Added geotechnical investigation per Owner request"
        source: "CO log"
        quote: null
    actual_value:
      value: 443500
      currency: USD
      source: "computed"
      quote: null
  construction:
    contract_value:
      value: 7800000
      currency: USD
      source: "GC contract §2.1"
      quote: "Construction Contract Sum: $7,800,000"
    awarded_date:
      value: "2024-02-01"
      source: "NTP letter"
      quote: "Notice to Proceed effective 2024-02-01"
    started_date:
      value: "2024-02-15"
      source: "Construction schedule"
      quote: null
    completion_date:
      value: null
      status: missing                   # project may still be in construction
    contractual_duration_days:
      value: 540
      source: "GC contract §3.1"
      quote: "Substantial Completion within 540 calendar days of NTP"
    change_orders: []
    actual_value:
      value: null
      status: missing

# Taxonomy section — every field validated against vocabularies/
taxonomy:
  client_type:                          # vocab: client_type
    - state_local
  program_type:                         # vocab: program_type
    - education_k12
  program_subtype:                      # vocab: program_type (subtype level)
    - education_k12_elementary
  disciplines:                          # vocab: discipline
    - mechanical_engineering
    - electrical_engineering
    - plumbing_engineering
    - fire_protection_engineering
  sub_disciplines:                      # vocab: sub_discipline
    - hvac_design
    - electrical_power_distribution
    - electrical_lighting
    - plumbing_domestic_water
    - plumbing_sanitary
  building_systems:                     # vocab: building_systems
    - hvac_air_distribution
    - hvac_chilled_water
    - electrical_service
    - electrical_lighting_interior
  construction_scope:                   # vocab: construction_scope
    - mechanical_hvac
    - electrical_power
    - electrical_lighting
    - plumbing_systems
    - fire_protection
  delivery_method:                      # vocab: delivery_method (single-select)
    - design_bid_build
  contract_vehicle:                     # vocab: contract_vehicle
    - standalone_project
  procurement_type:                     # vocab: procurement_type
    - state_local_competitive
  award_type:                           # vocab: award_type
    - qualifications_based
  project_status:                       # vocab: project_status (single-select)
    - in_construction
  bfa_role:                             # vocab: role_on_project
    - prime_consultant

# Tenant freeform tags — uncontrolled, governance via aliases
tenant_freeform_tags:
  - hampton_roads
  - wjcc_schools
  - elementary_renovation

# Personnel references — forward declaration, populated when personnel library exists
key_personnel: []                       # populated v0.2+
key_personnel_pending:                  # v1 placeholder, free-text names
  - name: "John Williams"
    role_on_project: "principal_in_charge"
  - name: "Sarah Osbourne"
    role_on_project: "project_manager"

# Narrative file references — content lives in linked .md files
# Pass 2 v2 shape (2026-05-07): short summary + long full + one short per discipline
narratives:
  summary: narratives/summary.md        # short form summary, ~150-300 words
  full: narratives/full.md              # long form, entire project, 1-2 pages
  disciplines:                          # one entry per taxonomy.disciplines[]
    mechanical_engineering: narratives/disciplines/mechanical_engineering.md
    electrical_engineering: narratives/disciplines/electrical_engineering.md
    plumbing_engineering: narratives/disciplines/plumbing_engineering.md
    fire_protection_engineering: narratives/disciplines/fire_protection_engineering.md
  aspects:
    schedule: null                      # optional, not yet generated
    technical: null
    teaming: null
```

---

## Provenance format

Every fact field follows this shape:

```yaml
field_name:
  value: <extracted value, or null>
  status: present | missing             # only present when value is null
  source: "<document-section reference>"
  quote: "<verbatim source text, or null if value derived non-textually>"
```

Rules:

- **Quote-or-null is enforced at extraction time.** The extractor MUST return
  either a verbatim source quote OR null. It must NOT paraphrase or summarize
  source text into the `quote` field.
- **`source` references a location in the source document.** Format:
  `"<document_short_name> <section_or_page>"` (e.g., `"BOD p.3"`,
  `"SOW §1.1"`, `"Contract Schedule A"`).
- **`status` distinguishes the three null cases.** When `value` is null:
  - `status: missing` — sources did not address this field.
  - `status: explicit_null` — source explicitly stated absence.
  - `status` is omitted when the value derives from non-source-document
    sources (e.g., BFA internal numbering systems), and `quote` is null.
- **Computed fields** (e.g., `actual_value` = `contract_value` + sum of change
  orders) carry `source: "computed"` and `quote: null`.

---

## Three-state null handling — examples

| Situation | Encoding |
|---|---|
| Source says project is 45,000 GSF | `value: 45000, source: "...", quote: "..."` |
| Source says "no change orders to date" | `value: [], status: explicit_null, source: "...", quote: "..."` |
| Sources don't mention change orders at all | `value: [], status: missing` (or field absent) |
| BFA internal data, not in source documents | `value: "23-1047", source: "BFA internal records", quote: null` |
| Computed from other fields | `value: 443500, source: "computed", quote: null` |

Downstream gate code MUST handle all four cases. Treating `missing` as
equivalent to `explicit_null` is a bug.

---

## Source document types

The `type` field on each `source_documents[]` entry uses this controlled list:

- `bod` — Basis of Design
- `sow` — Scope of Work
- `contract` — Executed contract document
- `spec_book` — Project Manual / Specifications
- `drawing_set` — Drawing Set (PDF render of CAD/Revit output)
- `narrative` — Narrative writeup (project description, capability statement)
- `correspondence` — Project correspondence (letters, emails, memos)
- `submittal` — Design or construction submittal
- `report` — Investigation, study, or analysis report
- `schedule` — Project schedule, milestone tracker
- `cost_estimate` — Cost estimate, budget document
- `change_order` — Executed change order document
- `meeting_minutes` — Meeting minutes
- `unknown` — Classifier could not determine; flag_for_human_review = true

---

## Vocabularies

All taxonomy fields validate against controlled vocabularies in
`vocabularies/`. See `vocabularies/README.md` for the full list and standards
posture.

| Field | Vocabulary | Standards anchor |
|---|---|---|
| `client_type` | `client_type.yaml` | NAICS-informed (public) |
| `program_type` | `program_type.yaml` | TWT-original |
| `program_subtype` | `program_type.yaml` (subtype level) | TWT-original |
| `disciplines` | `discipline.yaml` | SF330 Section E (public) |
| `sub_disciplines` | `sub_discipline.yaml` | TWT-original, SF330-informed |
| `building_systems` | `building_systems.yaml` | TWT-original (UniFormat-informed; future Option A) |
| `construction_scope` | `construction_scope.yaml` | TWT-original (MasterFormat-informed; future Option A) |
| `delivery_method` | `delivery_method.yaml` | AIA/ACEC contract document categories (public reference) |
| `contract_vehicle` | `contract_vehicle.yaml` | Federal + state/local + commercial common usage |
| `procurement_type` | `procurement_type.yaml` | FAR-derived (public) |
| `award_type` | `award_type.yaml` | Brooks Act + common usage |
| `project_status` | `project_status.yaml` | TWT-original |
| `bfa_role` / `role_on_project` | `role_on_project.yaml` | TWT-original |
| change order `reason` | `change_order_reason.yaml` | TWT-original |

**Standards posture for v0.1.0:** TWT-original where CSI MasterFormat or
UniFormat would otherwise apply, pending CSI Dynamic Standards data licensing
acquisition planned for v1.0 product gate. See `vocabularies/README.md` for
migration path.

---

## Multi-select and single-select fields

By default, every taxonomy field is multi-select (an array of enum values).

The following fields are explicitly **single-select** (must be array of length one):

- `delivery_method` — a project has one delivery method
- `project_status` — a project is in one lifecycle state
- `award_type` — a project was awarded one way

All other taxonomy fields are multi-select. A K-12 project on a federal base is
both `client_type: [federal]` and `program_type: [education_k12]`. A multi-use
civic building can have `program_type: [civic, office, education_higher_ed]`.

---

## Tenant freeform tags

Freeform tags are uncontrolled at write time. Governance is via the alias map
in `vocabularies/aliases/tag_aliases.yaml`.

Rules:

- Freeform tags are tenant-scoped (the field is `tenant_freeform_tags`, not
  `freeform_tags`). They do not propagate across tenants.
- The alias map normalizes known variants at write time (`VDOT` →
  `virginia_department_of_transportation`).
- Per the v0.0.2 build digest, freeform tags are reviewed monthly. Useful tags
  promote to controlled vocabulary; noise drops.
- Query logic that depends on freeform tag consistency is forbidden until the
  alias map matures. Filtering on freeform tags is best-effort, not authoritative.

---

## Identifier conventions

- **`project_id`** — BFA's internal project number, treated as authoritative.
  Format: as BFA assigns (typically `YY-NNNN`). Used as primary key, directory
  name, JSON filename, and cross-reference key.
- **`project_slug`** — human-readable secondary identifier derived from project
  name. Format: `kebab-case-slug`. Used in display contexts; not used as a key.
- **Personnel IDs** — to be defined in personnel library spec. Project records
  reference personnel by ID once that library exists.

For the v1 ingestion of historical projects, `project_id` may be assigned via
CSV round-trip: extractor proposes `suggested_id`; human reviewer assigns
`corrected_id`; reconciliation script updates JSON files in place. This is a
one-shot bootstrap pattern, not a general edit interface.

---

## Versioning policy

- `schema_version` — bumped on any change to this specification or to field
  definitions. Records carry the version under which they were extracted.
  Migrations are written when records cross versions.
- `extractor_version` — semver of the extraction engine. Re-extraction bumps it.
- Vocabulary files carry their own `vocabulary_version` independent of schema
  version. A vocabulary may bump (e.g., `client_type.yaml v1.0.0 → v1.1.0` adds
  a new entry) without bumping `schema_version`. Records reference the
  vocabulary version in effect at extraction time.

---

## Reproducibility

A given project record at extraction time is fully described by:

- `tenant_id`
- `project_id`
- `schema_version`
- `extractor_version`
- vocabulary versions (per-field, in record metadata)
- `source_documents[].sha256` for every source

Re-running the same extractor version against the same source hashes MUST
produce equivalent output (modulo non-determinism inherent to LLM calls,
mitigated by `temperature: 0` in extraction prompts).

---

## What this spec does NOT cover (out of scope for v0.1.0)

- Personnel library structure
- Past performance entity (as distinct from project record)
- Capability statements
- Corporate facts library
- Rate schedules
- Teaming partner records
- Win/loss outcomes (will reference project records when added)
- Gate retrieval API surface
- Index files for personnel matrix, rate schedule, past performance index

These will be added in subsequent spec passes after the project entity
stabilizes against the first three projects.

---

## Pressure-test deferred

This v0.1.0 specification is derived from industry-standard taxonomies and
common AE practice. It has NOT yet been pressure-tested against actual BFA
projects. The pressure-test pass is a separate activity scheduled after this
spec is reviewable, in which:

1. The schema is walked through against three first-projects on paper
2. Every scope element on each project is mapped to schema fields and
   vocabulary entries
3. Gaps are identified — fields the schema lacks or vocabulary entries missing
4. The spec bumps to v0.1.1 with pressure-test-driven corrections

Until the pressure-test pass is complete, this spec is provisional.
