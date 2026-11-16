# content_library/narratives/

Reusable markdown narrative patterns. Drop new patterns in here as they
emerge in pursuits.

## Naming convention

`{topic-slug}.md` — lowercased, hyphenated. Examples:

- `responsible-charge-unlicensed-pe.md`
- `foreign-trained-engineer-credentialing.md`
- `dual-role-pm-and-design.md`

## File format

Each narrative file should start with a YAML frontmatter block describing
when to reach for it:

```yaml
---
title: Responsible Charge with Unlicensed Senior PE
discipline: any
when_to_use: Senior staff member is technically expert but lacks U.S. PE license; PE-of-record is a different person
relevance_tags: foreign-trained;dual-role;responsible-charge
---
```

Followed by the narrative body in markdown.

## `[VERIFY]` markers

Use `[VERIFY]` for any pursuit-specific facts (project names, dates, agency
contacts) that need to be re-verified in the new context. The
`sanity_check.py` publish gate refuses to ship a docx containing
`[VERIFY]`.

## What this directory contains at v0.0.x

Currently empty. Patterns get added per pursuit as they prove reusable.
