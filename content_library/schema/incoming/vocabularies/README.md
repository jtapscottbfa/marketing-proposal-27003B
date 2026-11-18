---
last_updated: 2026-05-04
applies_to: TWT GovCon Solutions content library, vocabulary files
---

# Vocabularies

This directory contains controlled vocabularies referenced by `SPEC.md`. Each
vocabulary is a separate YAML file, independently versioned.

## File structure

Every vocabulary file is a single YAML document with metadata fields at the
top level alongside an `entries` (or `aliases`) array. Files do NOT use
Markdown-style `---` frontmatter — they are pure YAML, parseable in one pass
with `yaml.safe_load()`.

```yaml
vocabulary_id: <snake_case_id>
vocabulary_version: 1.0.0
last_updated: <YYYY-MM-DD>
anchor_standard: <standard reference or "twt-original">
anchor_standard_version: <version of standard if applicable>
hierarchy: <flat | two_level | three_level>
multi_select: <true | false>
governance_notes: |
  <free text on how the vocabulary is maintained>
future_migration: <null or reference to planned future anchor>

entries:
  - canonical_id: <snake_case_stable_id>
    display_name: <human-readable name>
    definition: <one-sentence definition>
    standard_reference: <citation if applicable>
    parent_id: <null or canonical_id of parent>     # for hierarchical vocabs
    aliases:                                         # known variants
      - <variant string>
    notes: <optional free text>
```

The alias map (`aliases/tag_aliases.yaml`) follows the same single-document
pattern with an `aliases:` array instead of `entries:`.

## Standards posture (v0.1.0)

### Public standards — used directly
- **SF330** (Architect-Engineer Qualifications) — Section E discipline list,
  Section F project type categories. Federal form, freely usable.
  - Used in: `discipline.yaml`, indirectly in `program_type.yaml`
- **NAICS** (North American Industry Classification System) — sector codes for
  client/contract matching. US Census, freely usable.
  - Used in: `client_type.yaml` (informed, not numbered)
- **FAR / DFARS** (Federal Acquisition Regulation) — set-aside categories,
  procurement methods. Public.
  - Used in: `procurement_type.yaml`
- **Brooks Act** (40 USC §1101–1104) — qualifications-based selection for
  federal A/E services. Public.
  - Used in: `award_type.yaml`
- **AIA / ACEC contract document categories** — referenced for delivery method
  taxonomy. Names and concepts used as public reference; AIA-specific document
  numbers (B101, A201, etc.) not embedded.
  - Used in: `delivery_method.yaml`

### TWT-original — placeholder for future licensed standards
- **`building_systems.yaml`** — TWT-original system/element taxonomy.
  Functionally informed by UniFormat structure but uses TWT-original
  category names. Slated for replacement with UniFormat under CSI Dynamic
  Standards license at v1.0 product gate.
- **`construction_scope.yaml`** — TWT-original scope-of-work taxonomy.
  Functionally informed by MasterFormat divisional structure but uses
  TWT-original category names. Slated for replacement with MasterFormat
  under CSI Dynamic Standards license at v1.0 product gate.

### TWT-original — fully original
- **`program_type.yaml`** — building/sector taxonomy. No clean public standard
  exists at the granularity needed; TWT-original.
- **`sub_discipline.yaml`** — engineering sub-disciplines. SF330-informed but
  TWT-original at the granularity used.
- **`change_order_reason.yaml`** — change order reason categories. TWT-original.
- **`project_status.yaml`** — project lifecycle states. TWT-original.
- **`role_on_project.yaml`** — prime/sub/JV/teaming roles. TWT-original.
- **`contract_vehicle.yaml`** — vehicle types span federal + state/local +
  commercial; TWT-aggregated from common usage.

## Future migration paths

When CSI Dynamic Standards licensing is acquired (v1.0 product gate):

1. **`building_systems.yaml` → UniFormat-aligned**
   - New file `building_systems_uniformat.yaml` with UniFormat element codes
     and titles
   - Crosswalk file `crosswalks/building_systems_twt_to_uniformat.yaml` maps
     every TWT-original entry to UniFormat equivalent
   - Migration script re-tags all existing project records
   - Schema version bumps to 1.0.0 (breaking vocabulary change)

2. **`construction_scope.yaml` → MasterFormat-aligned**
   - New file `construction_scope_masterformat.yaml` with MasterFormat division
     numbers and titles
   - Crosswalk file `crosswalks/construction_scope_twt_to_masterformat.yaml`
   - Same migration pattern

The current TWT-original files include `future_migration` references in their
frontmatter pointing to the planned future anchor.

## Hierarchy levels

- **Flat** — entries are independent, no parent-child relationships.
  Examples: `delivery_method`, `award_type`, `project_status`.
- **Two-level** — entries have an optional `parent_id`; one level of nesting.
  Examples: `client_type`, `discipline`, `sub_discipline`.
- **Three-level** — entries chain through two parents.
  Examples: `program_type` (top → subtype → specialization).

## Multi-select default

Per `SPEC.md`, taxonomy fields are multi-select unless explicitly noted
otherwise. Single-select vocabularies are flagged in their frontmatter:
`multi_select: false`.

## Aliases and governance

Variant terms ("VDOT" vs "Virginia Department of Transportation") are handled
in two places:

1. **Within a vocabulary** — each entry's `aliases` field captures known
   variants. The extractor maps incoming text to canonical_id via this list.
2. **Across vocabularies and freeform** — `aliases/tag_aliases.yaml` is a
   global alias map for the tenant freeform tag space and for cross-vocabulary
   normalization.

Per the v0.0.2 build digest: freeform tags reviewed monthly. Useful tags
promote into a controlled vocabulary with canonical form and aliases. Noise
drops.

## Pressure-test deferred

These vocabularies have not yet been pressure-tested against actual BFA
projects. The first three project ingestions are the test cases. Vocabularies
will bump to v1.1.0 after pressure-test corrections.

## File index (v0.1.0)

| File | Hierarchy | Multi-select | Anchor |
|---|---|---|---|
| `client_type.yaml` | Two-level | True | NAICS-informed |
| `program_type.yaml` | Three-level | True | TWT-original |
| `discipline.yaml` | Flat | True | SF330 Section E |
| `sub_discipline.yaml` | Two-level | True | TWT-original, SF330-informed |
| `building_systems.yaml` | Two-level | True | TWT-original (→ UniFormat) |
| `construction_scope.yaml` | Two-level | True | TWT-original (→ MasterFormat) |
| `delivery_method.yaml` | Flat | False | AIA/ACEC concepts |
| `contract_vehicle.yaml` | Two-level | True | TWT-aggregated |
| `procurement_type.yaml` | Two-level | True | FAR-derived |
| `award_type.yaml` | Flat | False | Brooks Act + common usage |
| `project_status.yaml` | Flat | False | TWT-original |
| `change_order_reason.yaml` | Flat | True | TWT-original |
| `role_on_project.yaml` | Flat | True | TWT-original |
