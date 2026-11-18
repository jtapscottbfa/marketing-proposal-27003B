---
name: Review Gate (Color Team)
about: Open a Pink / Red / Gold Team review gate
title: "[REVIEW] PLACEHOLDER: Pink/Red/Gold Team — YYYY-MM-DD"
labels: review-gate
assignees: ''
---

## Review Gate Details

| Field | Value |
|---|---|
| **Gate Type** | `☐ Pink Team` `☐ Red Team` `☐ Gold Team` |
| **Scheduled Date** | `PLACEHOLDER: YYYY-MM-DD` |
| **Review Lead** | `PLACEHOLDER: Name` |
| **Reviewers** | `PLACEHOLDER: Name, Name, Name` |
| **Volumes in Scope** | `PLACEHOLDER: All / Vol I / Vol II / etc.` |

## Pre-Review Checklist (author completes before review)

- [ ] All volumes built to `.docx` (`bash scripts/publish/build_docx.sh`)
- [ ] Compliance matrix updated
- [ ] Word count checked against RFP page limits (`prop-pages`)
- [ ] Remaining `PLACEHOLDER` tokens reviewed (`grep -r 'PLACEHOLDER' 0[1-5]_*/`)
- [ ] Win themes visible in each volume
- [ ] Review package distributed to reviewers

## Review Focus Areas

`PLACEHOLDER: List specific questions or areas to focus on for this review gate`

1. `PLACEHOLDER`
2. `PLACEHOLDER`

## Output

- [ ] Review findings logged in `00_admin/color_team_reviews.md`
- [ ] Action items created as individual issues (label: `action-item`)
- [ ] Gate result recorded: `☐ Pass` `☐ Conditional Pass` `☐ Fail`
