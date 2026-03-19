# Plan 014: Manual Implementation Agent Switcher

## Approach

Minimal: one switch script, one generic launcher, one codex worker launcher, one test.

No new framework, no state machine, no config file beyond a single one-line agent file.

## Local Agent State

`.codex/implementation-agent` — a plain text file containing either `claude` or `codex`.

- Absent or empty → treated as `claude` (no change to current default behaviour).
- This file is local-only (gitignored via `.codex/` entry in `.gitignore`).
- The switch script is the only writer; launcher scripts are read-only consumers.

## Reviewer State

`AI_REVIEW_AGENT` is an existing GitHub Actions repo variable consumed by
`scripts/run-ai-pr-review.ps1`. The switch script updates it via `gh variable set`.

## Files Changed / Added

| Path | Change |
|---|---|
| `specs/014-implementation-agent-switcher/spec.md` | new |
| `specs/014-implementation-agent-switcher/plan.md` | new |
| `specs/014-implementation-agent-switcher/tasks.md` | new |
| `scripts/set-implementation-agent.ps1` | new — manual switch |
| `scripts/start-implementation-worker.ps1` | new — generic dispatcher |
| `scripts/start-codex-worker.ps1` | new — codex implementation worker |
| `scripts/test-implementation-agent-switcher.ps1` | new — validation |
| `.github/codex/prompts/implementation-worker.md` | new — codex worker prompt |
| `.gitignore` | new — ignore `.codex/implementation-agent` |
| `docs/claude-worker-orchestration.md` | update — mention agent switcher |

## Risks

- `gh variable set` requires the `gh` CLI to be authenticated; the script prints a clear
  error if it fails but does not attempt any fallback.
- `codex exec` must be installed and in PATH for the codex worker to run.
- Both are operator prerequisites, not things the scripts try to fix silently.
