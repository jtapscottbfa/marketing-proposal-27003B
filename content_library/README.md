# content_library/

Firm-level reference data shared across pursuits. The engine ships the
**schema and structure** of this library; **content is populated per
pursuit** — when a new project, person, or subconsultant becomes relevant,
add it here so the next pursuit doesn't re-encode it inline.

This file documents the schemas. The CSV files in this directory ship
with header rows only; pursuit-specific data is added as it gets
verified.

## Files

| File | Purpose | Schema below |
|---|---|---|
| `projects.csv` | Past projects available for AE-5 / project-selector matching | §1 |
| `personnel.csv` | Firm personnel for AE-4 key-personnel population and staffing plans | §2 |
| `firms.csv` | Subconsultant firms with cert numbers and contact data for AE-3 | §3 |
| `past_performance.csv` | CPARS / PPQ scores keyed to project IDs (full ingest is ARCH-14) | §4 |
| `personnel_projects.csv` | Links a person × a past project with their role on it (drives AE-4 project tables) | §5 |
| `project_contacts.csv` | Per-project owner-admin and construction-prime POCs (drives AE-5 Section 2 contact rows) | §6 |
| `project_designers.csv` | Per-project design team list (drives AE-5 Section 4 designer rows) | §7 |
| `narratives/` | Reusable markdown narrative assets | §8 |

Firm-level metadata that is invariant across pursuits (firm legal name,
address, FEIN, SCC ID, ownership classifications, principal POCs) lives in
**`~/.bfa/firm_profile.yml`** per ARCH-11. A template is provided at
`00_admin/firm_profile.yml.example`. **Do not duplicate firm-level data
into `proposal_config.yml`** — that file is per-pursuit; the firm profile
is per-firm.

---

## §1 — projects.csv

One row per past project that the firm has done (or is doing) and might
cite as past performance in a future pursuit. Used by the project-selector
and AE-5 form population.

| Column | Type | Required | Description |
|---|---|---|---|
| `id` | slug | ✓ | Stable code. BFA convention follows DGS prefixes (`S` = state/local, `V` = veterans/VA, `N` = Navy/NAVFAC, `F` = federal-other, `H` = higher-ed) but other firms may adopt their own scheme. Once assigned, never rename — `past_performance.csv` references this. |
| `name` | string | ✓ | Full project title as it should appear in proposals |
| `client` | string | ✓ | Owner / client organization name |
| `agency_type` | enum | ✓ | One of: `federal`, `state`, `local`, `higher_ed`, `private` |
| `location` | string | ✓ | City, state |
| `firm_role` | string | ✓ | The firm's contractual role (e.g., `Prime A/E`, `Sub to <prime>`) |
| `eor_disciplines` | semicolon-list |  | Disciplines the firm was Engineer-of-Record for (e.g., `mechanical;electrical`) |
| `start_date` | YYYY-MM-DD or `Ongoing` | ✓ | Construction / contract start date |
| `complete_date` | YYYY-MM-DD or `In Progress` | ✓ | Completion date or status |
| `contract_value` | int (USD) |  | Total construction value or fee — pick the most relevant number for proposal comparisons |
| `gross_sf` | int |  | Building gross square footage. Leave **blank** for non-building projects (do NOT enter `N/A`; form-populator handles empty correctly). |
| `scope_summary` | string | ✓ | One- to two-sentence project description for narrative use |
| `relevance_tags` | semicolon-list |  | Win-theme tags for project-selector matching (e.g., `hvac;k-12;chiller;controls`) |
| `project_type` | string |  | AE-5 cell J9 — full descriptive type (e.g., `K-12 HVAC Replacement / MEP Term Contract Task Order`) |
| `building_type` | string |  | AE-5 cell I41 — short DGS category (e.g., `Educational`, `Office`, `Healthcare`) |
| `design_start_date` | YYYY-MM-DD |  | AE-5 cell AF42 — when design phase started |
| `design_complete_date` | YYYY-MM-DD |  | AE-5 cell AK42 — when design phase ended |
| `num_floors` | int |  | AE-5 cell N44 — building floor count |
| `owner_budget` | int (USD) |  | AE-5 cell K45 — owner's design-not-to-exceed budget |
| `ae_estimate` | int (USD) |  | AE-5 cell K46 — engineer's CD-phase estimate |
| `low_bid` | int (USD) |  | AE-5 cell K47 — actual low bid received |
| `num_change_orders` | int |  | AE-5 cell AH45 — count of design-attributable change orders |
| `cost_change_orders` | int (USD) |  | AE-5 cell AH46 — total cost of change orders |
| `substantial_completion` | YYYY-MM-DD |  | AE-5 cell AH47 — substantial completion date |
| `codes_used` | semicolon-list |  | Building codes used. Tokens mapped to AE-5 Section 5 checkboxes: `VUSBC`→C30, `IBC`→H30, `life_safety`→L30, `ASAD`→S30, `ADAAG`→X30. Other tokens are ignored unless also listed in `codes_other`. |
| `codes_other` | string |  | AE-5 cell AI30 — free-text "other" codes (e.g., `NFPA 101`) |
| `swam_proposed_pct` | int (0-100) |  | AE-5 cell L50 — proposed SWaM participation |
| `swam_final_pct` | int (0-100) |  | AE-5 cell Z50 — final SWaM participation |
| `swam_description` | string |  | AE-5 cell C51 — narrative description of SWaM participation |

`[VERIFY]` in any cell means the value needs human verification before use
in a delivered proposal. The `sanity_check.py` script (ARCH-05) refuses to
publish a pursuit that draws on a `[VERIFY]`-tagged row.

## §2 — personnel.csv

One row per firm staff member. Used by AE-4 key-personnel population and
the staffing plan.

| Column | Type | Required | Description |
|---|---|---|---|
| `id` | slug | ✓ | Stable identifier (last name lowercased, no punctuation: `williams`, `ogrady`). Once assigned, never rename. |
| `name` | string | ✓ | Full name with credentials (e.g., `Jane Doe, PE`) |
| `title` | string | ✓ | Job title |
| `office` | string | ✓ | Office location (city, state) |
| `years_total` | int | ✓ | Total years of professional experience |
| `years_firm` | int | ✓ | Years with this firm |
| `education` | string | ✓ | Degree(s), institution(s), year(s); credentials |
| `discipline` | enum | ✓ | One of: `electrical`, `mechanical`, `plumbing`, `controls`, `pm`, `cadd`, `other` |
| `license_type` | enum |  | One of: `PE`, `EIT`, `CPD`, `none`. Empty = unlicensed. |
| `license_state` | string |  | State of licensure (e.g., `Virginia`). Empty if unlicensed. |
| `license_number` | string |  | License number (use exactly as it appears on the license) |
| `license_year` | YYYY |  | Year first licensed |
| `cpsm_status` | enum |  | One of: `Yes`, `No`. Whether CPSM-certified for DGS work. |
| `cpsm_date` | YYYY-MM-DD |  | Date of CPSM certification if applicable |
| `registration_line` | string |  | Optional override of AE-4 cell C33 (Registration line). When present, used verbatim. When absent, populator derives a default from `license_*` fields (e.g., `"2011 / Virginia / Professional Electrical Engineer"`). Use the override for non-standard cases: foreign credentials, EITs with notable scopes, CPDs, unlicensed senior staff with explanatory text. |
| `notes` | string |  | Special situations (e.g., responsible-charge pattern, foreign credentials, unique role assignments) |

## §3 — firms.csv

One row per subconsultant firm in the prime's ecosystem. Used by AE-3
firm-data population and subconsultant intake.

| Column | Type | Required | Description |
|---|---|---|---|
| `id` | slug | ✓ | Short identifier (e.g., `jensen-hughes`, `bsg`) |
| `name` | string | ✓ | Full legal firm name |
| `addr1` | string |  | Street address line 1 |
| `addr2` | string |  | City, state, zip |
| `phone` | string |  | Main phone |
| `fax` | string |  | Main fax (AE-2 cell T12) |
| `fein` | string |  | Federal Employer Identification Number (`XX-XXXXXXX`) |
| `scc_id` | string |  | Virginia State Corporation Commission ID |
| `apelscidla` | string |  | Virginia APELSCIDLA professional registration number |
| `dsbsd_cert` | string |  | Virginia DSBSD certification number, or `N/A (Large Business)` for non-SWaM firms |
| `ownership_class` | enum | ✓ | One of: `large`, `small`, `micro`, `minority`, `women`, `veteran`, `service_disabled_veteran` |
| `legal_form` | string |  | Legal form (e.g., `Professional Corporation`, `LLC`) — used for AE-2 Section 4 legal-form checkbox |
| `other_names` | string |  | Other names firm has operated under (AE-2 cell AC10) |
| `primary_function` | string | ✓ | Discipline / service description (one to three sentences) |
| `parent_firm` | string |  | Parent entity name if applicable, blank otherwise |
| `years_in_practice` | int |  | Years operating under current name (AE-2 cell AR8) |
| `poc_name` | string | ✓ | Primary point of contact full name |
| `poc_title` | string | ✓ | POC title |
| `poc_email` | string | ✓ | POC email |
| `poc_phone` | string |  | POC phone |
| `insurance_status` | string |  | Insurance summary (carrier, limits) or `[VERIFY]` |
| `prior_projects_with_prime` | int |  | Count of prior joint projects with this prime |

## §4 — past_performance.csv

One row per project × evaluation. CPARS / PPQ scores keyed to a project
`id` in `projects.csv`. Schema only at v0.0.x; full ingest tooling is
ARCH-14.

| Column | Type | Required | Description |
|---|---|---|---|
| `project_id` | slug | ✓ | Foreign key to `projects.csv` `id` |
| `eval_type` | enum | ✓ | One of: `CPARS`, `PPQ`, `client_letter`, `internal` |
| `eval_period` | string | ✓ | Period covered (e.g., `2023-Q3`, `final`) |
| `score_overall` | enum | ✓ | One of: `Exceptional`, `Very Good`, `Satisfactory`, `Marginal`, `Unsatisfactory` |
| `score_quality` | enum |  | Quality sub-score (same enum) |
| `score_schedule` | enum |  | Schedule sub-score |
| `score_cost` | enum |  | Cost-control sub-score |
| `score_management` | enum |  | Management sub-score |
| `client_poc_name` | string |  | Client point of contact who completed the eval |
| `client_poc_phone` | string |  | Client POC phone |
| `client_poc_email` | string |  | Client POC email |
| `verification_status` | enum | ✓ | One of: `verified`, `unverified`, `[VERIFY]` |
| `notes` | string |  | Verbatim quotes, caveats, follow-ups |

## §5 — personnel_projects.csv

One row per (person × project) pair. Drives AE-4 Section 6's
"Specific Experience" table — six rows per AE-4 form, one form per
key person. Adding a row here means "this person worked on this
project in this role"; the populator looks up project name + completion
date from `projects.csv` and writes them into the AE-4 cells.

| Column | Type | Required | Description |
|---|---|---|---|
| `personnel_id` | slug | ✓ | Foreign key to `personnel.csv` `id` |
| `project_id` | slug | ✓ | Foreign key to `projects.csv` `id` |
| `role` | string | ✓ | This person's role on this project (e.g., `Mechanical Engineer of Record`, `Project Manager; client interface`) |
| `listing_order` | int |  | Sort key for AE-4 ordering when a person has more than 6 projects. Lower numbers list first; ties broken by project completion date desc. Default 0. |

The populator filters this table per-person, sorts by `listing_order`
then completion date, and takes the first six. Add the *same* project
row twice (once per person) when two people share a project — that
keeps each person's role text accurate without joins at populate time.

## §6 — project_contacts.csv

One row per (project × contact-role) pair. Drives AE-5 Section 2 — the
client-administrator and construction-prime contact rows. Up to three
roles per project: `admin` (owner's project administrator), 
`construction_prime_pm` (construction GC's project manager), and
`construction_supt` (construction GC's superintendent). Missing roles
leave their cells blank.

| Column | Type | Required | Description |
|---|---|---|---|
| `project_id` | slug | ✓ | Foreign key to `projects.csv` `id` |
| `role` | enum | ✓ | One of: `admin`, `construction_prime_pm`, `construction_supt` |
| `firm` | string |  | Firm/agency name (used for construction prime; admin's firm is the owner from `projects.csv`) |
| `name` | string |  | Contact's full name |
| `title` | string |  | Contact's title (admin only — populator writes to AE5 AE11) |
| `addr` | string |  | Contact's mailing address (admin only — AE5 G12) |
| `email` | string |  | Contact's email |
| `phone` | string |  | Contact's phone |
| `fax` | string |  | Contact's fax |

The `admin` role is what AE-5 calls the "Owner's Administrator" — the
agency representative who can verify the project's particulars. The two
`construction_*` roles populate the GC's PM/Supt contact rows
separately so both names land at the right cells.

## §7 — project_designers.csv

One row per (project × designer-role) pair. Drives AE-5 Section 4 — the
seven-row design-team table. The form has fixed rows by discipline, so
each project ends up with at most seven entries (one per discipline used).
The populator orders them by the `discipline` enum's documented row map.

| Column | Type | Required | Description |
|---|---|---|---|
| `project_id` | slug | ✓ | Foreign key to `projects.csv` `id` |
| `discipline` | enum | ✓ | One of: `prime_ae`, `architectural`, `structural`, `mechanical`, `electrical`, `civil`, `other` (row 27, gets discipline label in col C) |
| `firm` | string | ✓ | Firm name (own firm or sub) |
| `individual` | string | ✓ | EOR / lead designer's full name |
| `role` | string | ✓ | Concise role description on the project |

Multiple rows with the same discipline on a project: only the
last-encountered wins (the form has one slot per discipline). Use the
`other` row for any non-standard discipline (e.g., `Plumbing`,
`Fire Protection`); the populator writes the `role` text into the
discipline-label cell.

## §8 — narratives/

Markdown files holding reusable narrative patterns (e.g., responsible-charge
with unlicensed senior PE, foreign-trained engineer credentialing). Drop
new patterns in here as they emerge in pursuits; reference from pursuit
volumes via include or copy-paste.

Naming convention: `{topic-slug}.md` (e.g., `responsible-charge-unlicensed-pe.md`).

Each narrative file should start with a YAML frontmatter block:

```yaml
---
title: Responsible Charge with Unlicensed Senior PE
discipline: any
when_to_use: Senior staff member is technically expert but lacks U.S. PE license; PE-of-record is a different person
relevance_tags: foreign-trained;dual-role;responsible-charge
---
```

Use `[VERIFY]` markers for any pursuit-specific facts (project names,
dates, agency contacts) that need to be re-verified in the new context.

---

## CSV editing conventions

- UTF-8, comma-separated, double-quote on fields containing commas or
  newlines (standard CSV).
- Use empty cells for "no data" — do **not** write `N/A` or `null`.
  Form-populators handle empty cells correctly; literal `N/A` leaks into
  rendered output as a string.
- `[VERIFY]` is the canonical marker for "this needs human review before
  it's safe to ship." `sanity_check.py` greps for it and refuses publish
  if any reach the rendered docx.
- **Stable IDs are forever.** Once `personnel.id = williams` exists, do
  not rename it — `past_performance` and other tables reference it. To
  deprecate a row, leave it in place and add a `notes` flag.

## What this directory does NOT contain at v0.0.x

- **Seed data** — every CSV ships header-only. Pursuits populate as
  they go.
- **A renderer helper** — the CSV→narrative renderer (e.g., for AE-3
  firm tables) lands as a follow-up alongside ARCH-02 (populate_ae_forms.py).
