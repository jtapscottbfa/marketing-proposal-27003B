# color_team_reviews.md — finding record schema

`00_admin/color_team_reviews.md` is the structured log of every color-team
finding for a pursuit. The Pink / Red / Gold / Blue Hat / Black Hat sections
each contain a `### Findings` block; inside that block, every finding is a
**YAML frontmatter record followed by a markdown body**, separated by blank
lines.

This schema is the contract between the review scripts in `scripts/review/`
and the reviewable artifact. Both producers (`color_team_review.sh`) and
consumers (`review_triage.sh`, the publish gate) parse against this format.

## Record format

```markdown
---
id: "PT-01"
gate: "pink"
priority: "H"
status: "open"
owner: "Proposal Manager"
target_docs:
  - "06_technical_approach/technical_approach.md"
dependencies: []
created: "2026-04-20"
locked_at: null
---

**Finding:** Win Theme WT-3 has no assigned section in the technical narrative —
evaluators cannot score a discriminator they cannot find.

**Notes:** [populated by PM before --remediate; provides verified facts that
let Claude generate a targeted fix.]

**Resolution:** [populated when status moves to resolved or accepted; states
exactly what changed, when, and where. Once written, locked_at is set and
the finding cannot be re-opened without --reopen <id> "<reason>".]
```

## Field reference

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Sequential within gate. Prefix encodes gate (see below). |
| `gate` | enum | yes | `pink` / `red` / `gold` / `blue_hat` / `black_hat` |
| `priority` | enum | yes | `H` (will cost evaluation points) / `M` (fix before next gate) / `L` (improve if time allows) |
| `status` | enum | yes | `open` / `resolved` / `accepted` / `reopened` |
| `owner` | string | yes | Role accountable for closure: `Proposal Manager` / `Tech Lead` / `PM Lead` / `Pricing Lead` / etc. |
| `target_docs` | list[string] | yes | Repo-relative paths to the document(s) the finding implicates. Empty list `[]` allowed for cross-cutting findings. Drives DISC-13 doc-touch tracking. |
| `dependencies` | list[string] | yes | Other finding IDs that must close first. Empty list `[]` if independent. |
| `created` | date | yes | ISO date the finding was first written. |
| `locked_at` | date \| null | yes | ISO date when status became `resolved` or `accepted`. `null` while `open`. Reset to `null` on `--reopen`. |

## ID prefix → gate

| Prefix | Gate |
|---|---|
| `PT-` | Pink Team |
| `RT-` | Red Team |
| `BL-` | Blue Hat |
| `BK-` | Black Hat |
| `GT-` | Gold Team |

Prefixes are stable. A Pink Team finding stays `PT-NN` even if it is later
re-validated in Red Team — Red Team gets its own `RT-NN` finding instead.

## Status state machine

```text
                ┌──────────────────────────┐
                │                          │
                ▼                          │
  (created) → open ──┬──→ resolved (locked_at set)
                     │       │
                     │       └──→ reopened (via --reopen) → open
                     │
                     └──→ accepted (locked_at set, with reason)
                             │
                             └──→ reopened (via --reopen) → open
```

- `resolved` and `accepted` both set `locked_at` to today's date. The
  finding is then **closure-locked**: `review_triage.sh` will reject any
  state change unless invoked as `--reopen <id> "<reason>"`. Reopening
  clears `locked_at` and appends the reason to **Notes**.
- This closes GAP-49 (during the VT pursuit, several Pink Team findings
  silently re-opened during Pink-2; closure lock prevents that).

## Gate ordering

Reviews advance Pink → Red → Blue Hat → Black Hat → Gold by default. Each
gate refuses to run while the prior gate has unresolved `H`-priority
findings (configurable; opt out per-run with `--force` once
`scripts/review/color_team_review.sh` is implemented).

Blue Hat / Black Hat are optional — skipping them does not block Gold, but
is logged.

## Authoring rules

- **Findings are appended, never deleted.** Marking accepted is the path
  for "we acknowledge but won't fix."
- **One sentence per `**Finding:**` line.** No softening, no hedging — this
  is an internal review.
- **`target_docs` paths must exist** in the repo at the time of writing.
  The script validates and fails loudly when they don't.
- **`dependencies` are checked at gate close.** A finding cannot close
  while any dependency is still `open`.
