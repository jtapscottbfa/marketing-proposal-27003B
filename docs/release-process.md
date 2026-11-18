# Release Process

Step-by-step runbook for cutting a new release of `ae-proposal-engine`.
Reflects the conventions documented in the main `README.md` ("Branching,
Commits, and Versioning") and the format established with v0.0.1.

---

## Versioning rules ([SemVer](https://semver.org/))

Version format: `MAJOR.MINOR.PATCH`.

| Bump | When |
|---|---|
| `MAJOR` | Incompatible changes to scaffold presets, config schema, or build output structure. |
| `MINOR` | New backwards-compatible capability — typically a theme of related fixes consolidated from retrospectives. |
| `PATCH` | Backwards-compatible fix (bug fix, typo, dependency patch). |

Pre-1.0 (`0.x.y`) signals the API is still in flux — minor bumps may introduce
breaking changes. `1.0.0` will be declared when the engine runs an end-to-end
pursuit without manual intervention — **stability bar, not feature bar**.

---

## Pre-release checklist (before tagging)

1. **All work merged.** Every change for this release is on `main` via PR
   (squash merges per the trunk-based workflow).
2. **CI green** on the head of `main`.
3. **`package.json`** `"version"` field bumped to the new version.
4. **`CHANGELOG.md` updated:**
   - Move entries from `## [Unreleased]` under a new dated heading:
     `## [X.Y.Z] - YYYY-MM-DD`
   - For larger releases, group entries by theme (`#### Foundations`,
     `#### Repo hygiene`, etc.) — see v0.0.1 as a model
   - Add a new `[X.Y.Z]: https://github.com/<your-org>/ae-proposal-engine/releases/tag/vX.Y.Z`
     reference link at the bottom of the file
   - Update the `[Unreleased]` reference link to compare from the new tag
5. **No unresolved tokens** in source: `PLACEHOLDER`, `[VERIFY]`, `[INTERNAL]`,
   `[DRAFT]`, `*End of draft*` should not appear in committed `.md` files
   except in scaffold templates and CLAUDE.md (where they are documented examples).

---

## Cut the release

Replace `X.Y.Z` and `<tagline>` everywhere below.

### 1. Annotated tag

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z — <tagline>

<two-to-three sentence summary>

See CHANGELOG.md for full details."

git tag -n9 vX.Y.Z   # verify the annotation
```

Annotated tags (`-a`) carry a message, date, and tagger — they show up as
proper releases on GitHub. Lightweight tags (no flag) are just pointers
and don't.

### 2. Push the tag

```bash
git push origin vX.Y.Z
```

Tags are **not** pushed by `git push` by default — that's the most common
mistake. Push them explicitly.

### 3. Create the GitHub release

Preferred — `gh` CLI:

```bash
gh release create vX.Y.Z \
  --title "vX.Y.Z — <tagline>" \
  --prerelease \
  --notes "$(awk '/^## \[X.Y.Z\]/{flag=1} /^## \[/{if(flag && !/X\.Y\.Z/) exit} flag' CHANGELOG.md)"
```

Notes:

- **`--prerelease`** stays on for any `0.x.y` release. Drop it for `1.0.0`+.
- The **awk command** extracts only the `## [X.Y.Z]` section from `CHANGELOG.md`
  (stops at the next `## [` heading), so the release body shows only this
  version's notes — not Unreleased, not earlier versions.
- **Replace `X.Y.Z` in the awk pattern** with the literal version (e.g.
  `0\.0\.2`). The backslashes escape the dots for regex.

### 4. Web UI alternative

If `gh` fails or you prefer to click:

1. Visit `https://github.com/<your-org>/ae-proposal-engine/releases/new`
2. **Choose a tag** dropdown → select `vX.Y.Z`
3. **Target** → `main`
4. **Release title** → `vX.Y.Z — <tagline>`
5. **Describe this release** → from `CHANGELOG.md`:
   - **Start at** the descriptive paragraph below `## [X.Y.Z] - YYYY-MM-DD`
     (e.g. "Initial release. Production engine for...")
   - **End at** the last bullet of that version's `### Added` / `### Changed`
     / `### Fixed` / `### Removed` content
   - **Do not** copy the version heading itself — redundant with the release
     title GitHub renders at the top
   - **Do not** copy the `[X.Y.Z]: ...` reference links at the bottom of
     the file — those are CHANGELOG file plumbing, not user-facing content;
     they would render as literal text on the release page
6. ☑ **Set as a pre-release** for `0.x.y` (uncheck for `1.0.0`+)
7. Leave **Set as the latest release** checked
8. Click **Publish release**

---

## Post-release

1. **Verify** at `https://github.com/<your-org>/ae-proposal-engine/releases`
   — release notes render correctly, pre-release badge present (for 0.x).
2. **Verify** at `https://github.com/<your-org>/ae-proposal-engine/tags`
   — annotated tag (not just a hash, has a description).
3. Open the next PR with an empty `## [Unreleased]` placeholder restored
   to `CHANGELOG.md` (you'll start collecting entries for the next version).
4. Update memory / notes — what worked, what didn't, what to fix in the
   process for next time.

---

## Cheat-sheet — full sequence

```bash
# 0. Pre-release checks done (CHANGELOG, package.json, CI green)

# 1. Tag
git tag -a vX.Y.Z -m "Release vX.Y.Z — <tagline>

<summary>

See CHANGELOG.md for full details."

# 2. Push tag
git push origin vX.Y.Z

# 3. Release on GitHub
gh release create vX.Y.Z \
  --title "vX.Y.Z — <tagline>" \
  --prerelease \
  --notes "$(awk '/^## \[X.Y.Z\]/{flag=1} /^## \[/{if(flag && !/X\.Y\.Z/) exit} flag' CHANGELOG.md)"

# 4. Verify
gh release view vX.Y.Z
```

---

## Special tag types (do not confuse with releases)

The proposal aliases (`scripts/git/proposal-aliases.sh`) define **per-pursuit
milestone tags** for use inside scaffolded proposal repos:

```text
v1.0-pink-team       Pink Team review snapshot
v2.0-red-team        Red Team review snapshot
v3.0-gold-team       Gold Team approval snapshot
v3.1-submitted       Final submission marker
```

These are **not releases** of the engine. They live inside the per-pursuit
child repo and follow a different convention (Shipley gate names, not SemVer).
Don't confuse them with the engine's `v0.0.1` / `v0.1.0` / `v1.0.0` releases.
