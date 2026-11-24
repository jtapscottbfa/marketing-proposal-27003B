# Color Team Review Log

> **Opportunity:** `[RFP Title]`
> Track all review gates here. Each gate produces structured findings that must
> be remediated or risk-accepted before the next gate.
>
> **Schema:** See [color_team_reviews.SCHEMA.md](color_team_reviews.SCHEMA.md)
> for the finding record structure (YAML frontmatter + markdown body) and
> the gate-ordering / closure-lock rules that `scripts/review/` enforces.

---

## Pink Team — Storyboard / Outline Review

**Date:** `PLACEHOLDER: YYYY-MM-DD`
**Review Lead:** `PLACEHOLDER: Name`
**Reviewers:** `PLACEHOLDER: Name, Name, Name`
**Focus:** Are win themes visible? Is the compliance matrix addressed? Are sections structured correctly?

### Findings

<!-- Findings inserted by `scripts/review/color_team_review.sh --pink`.
     Each finding is a YAML frontmatter block followed by a markdown body,
     separated by blank lines. Format:

---
id: "PT-01"
gate: "pink"
priority: "H"            # H | M | L
status: "open"           # open | resolved | accepted | reopened
owner: "Proposal Manager"
target_docs:
  - "PLACEHOLDER/path/to/file.md"
dependencies: []         # other finding IDs that must close first
created: "YYYY-MM-DD"
locked_at: null          # ISO date when status moved to resolved/accepted
---

**Finding:** [one direct sentence — what is missing, weak, or misaligned.]

**Notes:** [working triage notes — populate before --remediate]

**Resolution:** [populated when status: resolved or accepted]

-->

**Overall Assessment:** `PLACEHOLDER: Pass / Conditional Pass / Fail`

---

## Red Team — Full Draft Review

**Date:** `PLACEHOLDER: YYYY-MM-DD`
**Review Lead:** `PLACEHOLDER: Name`
**Reviewers:** `PLACEHOLDER: Name, Name, Name`
**Focus:** Evaluator-perspective scoring. Does every Section M criterion have a compelling response?

### Three Evaluator Questions

| Question | Answer | Confidence |
|---|---|---|
| Can they do the work? | `PLACEHOLDER` | High / Medium / Low |
| Will they do what they say? | `PLACEHOLDER` | High / Medium / Low |
| Is it worth the price? | `PLACEHOLDER` | High / Medium / Low |

### Scoring (mirror Section M evaluation criteria)

| Evaluation Factor | Evaluator Score | Our Target | Gap |
|---|---|---|---|
| `PLACEHOLDER: e.g., Technical Approach` | `PLACEHOLDER` | Outstanding | `PLACEHOLDER` |

### Findings

<!-- Findings inserted by `scripts/review/color_team_review.sh --red`.
     Same YAML frontmatter schema as Pink Team — see schema doc.
     IDs use prefix `RT-`. -->

**Overall Assessment:** `PLACEHOLDER: Pass / Conditional Pass / Fail` — `PLACEHOLDER: one paragraph`

---

## Blue Hat — Competitive Ghosting Review

> **Stub.** Implementation lands in a later PR (issue #7, AC #6). Blue Hat
> reviews the proposal *as if you were the customer reading it next to your
> top competitor's response* — flags every "me-too" claim a competitor could
> copy verbatim, and every place a competitor's discriminator goes
> unanswered. Findings prefix: `BL-`.

**Date:** `PLACEHOLDER: YYYY-MM-DD`
**Review Lead:** `PLACEHOLDER: Name`
**Focus:** Discriminator strength relative to known competitors; ghost-theme coverage; me-too statement detection.

### Findings

<!-- Findings inserted by `scripts/review/color_team_review.sh --blue-hat`.
     Same YAML frontmatter schema as Pink Team. IDs use prefix `BL-`. -->

**Overall Assessment:** `PLACEHOLDER: Pass / Conditional Pass / Fail`

---

## Black Hat — Competitor Red-Team

> **Stub.** Implementation lands in a later PR (issue #7, AC #6). Black Hat
> role-plays the *competitor* writing their proposal — surfaces every
> argument a competitor will use against us, every weakness in our story
> they'll exploit, and every claim of theirs we have not pre-rebutted.
> Findings prefix: `BK-`.

**Date:** `PLACEHOLDER: YYYY-MM-DD`
**Review Lead:** `PLACEHOLDER: Name`
**Focus:** Adversarial competitor simulation — what will the other firms argue, and what's our pre-rebuttal?

### Findings

<!-- Findings inserted by `scripts/review/color_team_review.sh --black-hat`.
     Same YAML frontmatter schema as Pink Team. IDs use prefix `BK-`. -->

**Overall Assessment:** `PLACEHOLDER: Pass / Conditional Pass / Fail`

---

## Gold Team — Final Approval

**Date:** `PLACEHOLDER: YYYY-MM-DD`
**Approver:** `PLACEHOLDER: Executive Sponsor Name`
**Reviewers:** `PLACEHOLDER: Name, Name`
**Focus:** Price competitiveness, risk, final messaging, compliance with all format requirements.

### Executive Questions

| Question | Answer | Status |
|---|---|---|
| Is the submission fully compliant? | `PLACEHOLDER` | ✅ / ⚠ / ❌ |
| Is our pricing competitive? | `PLACEHOLDER` | ✅ / ⚠ / ❌ |
| Will we win? (P(win) estimate) | `PLACEHOLDER` | ✅ / ⚠ / ❌ |

### Final Checklist

- [ ] All Pink Team findings resolved or risk-accepted
- [ ] All Red Team findings resolved or risk-accepted
- [ ] Blue Hat / Black Hat findings reviewed
- [ ] Compliance matrix 100% addressed
- [ ] Page limits verified for all volumes
- [ ] File naming / submission format confirmed
- [ ] Executive Sponsor sign-off obtained
- [ ] Submission logistics confirmed
- [ ] Addendum pre-flight clean (latest addendum reflected in `rfp_shred`)

### Findings

<!-- Findings inserted by `scripts/review/color_team_review.sh --gold`.
     Same YAML frontmatter schema as Pink Team. IDs use prefix `GT-`.
     Gold Team findings are blockers only — submission risks. -->

**Decision:** ☐ APPROVED TO SUBMIT &nbsp;&nbsp; ☐ CONDITIONAL (see below)

**Conditions:** `PLACEHOLDER`
