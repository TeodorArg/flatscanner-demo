# Tasks 014: Manual Implementation Agent Switcher

## Checklist

- [x] Write `specs/014-implementation-agent-switcher/spec.md`
- [x] Write `specs/014-implementation-agent-switcher/plan.md`
- [x] Write `specs/014-implementation-agent-switcher/tasks.md`
- [x] Create `scripts/set-implementation-agent.ps1`
- [x] Create `scripts/start-implementation-worker.ps1`
- [x] Create `scripts/start-codex-worker.ps1`
- [x] Create `scripts/test-implementation-agent-switcher.ps1`
- [x] Create `.github/codex/prompts/implementation-worker.md`
- [x] Add `.gitignore` with `.codex/implementation-agent`
- [x] Update `docs/claude-worker-orchestration.md`
- [x] Run `test-implementation-agent-switcher.ps1` — passes
- [x] Commit on branch `codex/claude-014-manual-agent-switcher`

## Follow-up Fixes (post-initial commit)

- [x] `set-implementation-agent.ps1`: add optional `-Repo` parameter; pass `--repo` to `gh variable set` when provided
- [x] `start-implementation-worker.ps1`: resolve agent file from target `-WorktreePath` via `git -C $WorktreePath rev-parse --show-toplevel`, not caller checkout
- [x] `docs/ai-pr-workflow.md`: narrow wording so Claude is not implied as always the only implementation writer
- [x] Re-run `test-implementation-agent-switcher.ps1` — passes
- [x] Commit follow-up on branch `codex/claude-014-manual-agent-switcher`
