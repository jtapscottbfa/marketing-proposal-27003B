# docs/ — Engine Dev Process

This folder is **engine-internal**. It documents the development process of
`ae-proposal-engine` itself — not any specific pursuit.

## What lives here

- `retrospectives/` — post-mortems of real pursuits that seeded the engine
  backlog. These explain the *why* behind specific backlog items, issues, and
  architectural decisions.
- Future: architecture notes, roadmap, decision records.

## What does **not** live here

- Per-pursuit content — that belongs in a scaffolded child proposal repo,
  specifically in `00_admin/`, `01_*` through `06_*` volumes, and the
  root-level `retrospectives/` folder of the child repo (for that pursuit's
  own post-mortem).

## If you cloned this engine via GitHub "Use this template"

Delete this folder in your new proposal repo — it is engine history, not
part of your pursuit:

```bash
rm -rf docs/
git add -A && git commit -m "chore: remove engine-internal docs/"
```

Scaffolding via `scripts/scaffold/new_proposal.sh` does not copy this folder,
so you only need this step for the GitHub-template path.
