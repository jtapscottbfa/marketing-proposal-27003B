# Git Scripts

Proposal-specific Git helpers for version control and milestone management.

---

## Setup

```bash
# Load aliases for the current session
source scripts/git/proposal-aliases.sh

# Install pre-commit hook (run once after cloning)
bash scripts/git/hooks/install_hooks.sh
```

To load aliases automatically in every terminal session, add to your shell profile:

```bash
echo 'source /path/to/your/proposal/scripts/git/proposal-aliases.sh' >> ~/.bashrc
# or for zsh:
echo 'source /path/to/your/proposal/scripts/git/proposal-aliases.sh' >> ~/.zshrc
```

---

## Alias Reference

| Command | Description |
|---|---|
| `prop-save "message"` | Stage all changes and commit |
| `prop-checkpoint` | Commit with auto-timestamped message |
| `prop-tag <name> ["msg"]` | Create annotated tag for a review gate |
| `prop-tags` | List all milestone tags with dates |
| `prop-diff [file]` | Word-level diff (much more readable for prose) |
| `prop-diff-tag <t1> <t2>` | Word diff between two milestone tags |
| `prop-log` | Clean one-line commit history |
| `prop-log-files` | Commit history with file stats |
| `prop-status` | Repo status summary |
| `prop-wc` | Word count per volume |
| `prop-pages` | Estimated page count per volume |
| `prop-undo` | Undo last commit, keep changes staged |
| `prop-discard` | Discard all unstaged changes (asks to confirm) |
| `prop-help` | Print this reference |

---

## Recommended Save Discipline

Save frequently. Each meaningful chunk of work gets its own commit:

```bash
prop-save "draft: executive summary opening paragraph"
prop-save "draft: technical approach phases 1-2"
prop-save "fix: red team RT-05 — strengthen management approach §3.2"
prop-save "compliance: update compliance matrix for REQ-012 through REQ-018"
```

Tag every review gate package before distributing to reviewers:

```bash
prop-tag v0.2-pink-team "Pink Team package — distributed 2025-09-15"
git push origin --tags
```

---

## Pre-Commit Hook

The hook at `scripts/git/hooks/pre-commit` warns (but does not block) on:

- Unfilled `PLACEHOLDER` tokens in narrative volumes
- Markdown files with no body content
- Unchecked rows in `compliance_matrix.md`

To bypass (e.g., early draft work-in-progress):

```bash
git commit --no-verify -m "wip: early draft technical approach"
```
