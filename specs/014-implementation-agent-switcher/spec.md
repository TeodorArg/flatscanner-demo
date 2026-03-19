# Spec 014: Manual Implementation Agent Switcher

## Status

Active

## Problem

The repository has two capable code-writing agents (Claude and Codex) and two reviewers
(Claude and Codex). There is no lightweight, explicit way to choose which agent writes code
and which agent reviews a PR. Past attempts introduced quota logic, failover, and capacity
thresholds — complexity that is not required.

## Goal

A single manual switch that sets both the local code-writing agent and the repo reviewer at
the same time, with no automation beyond that act.

## Scope

- Two selectable implementation agents: `claude` and `codex`.
- Two selectable reviewers: `claude` and `codex`.
- Default implementation agent: `claude`.
- Default reviewer: `claude`.
- Choosing `codex` at task start switches both implementation agent and reviewer to `codex`.
- Choosing `claude` resets both to `claude`.

## Out of Scope

- Automatic failover between agents.
- Quota or capacity logic.
- Authentication or credential management.
- Restore or rollback logic beyond re-running the switch script.
- Any orchestration framework beyond a launcher script.

## Requirements

1. `scripts/set-implementation-agent.ps1 -Agent <claude|codex>` must:
   - Accept only `claude` or `codex`; reject anything else.
   - Write the chosen agent to `.codex/implementation-agent`.
   - Set the GitHub repo variable `AI_REVIEW_AGENT` to the same value via `gh variable set`.
   - Print what was set.

2. `scripts/start-implementation-worker.ps1` must:
   - Read `.codex/implementation-agent` (default `claude` when absent).
   - Forward all parameters to either `start-claude-worker.ps1` or `start-codex-worker.ps1`.

3. `scripts/start-codex-worker.ps1` must:
   - Mirror the parameter surface of `start-claude-worker.ps1`.
   - Use `.github/codex/prompts/implementation-worker.md` as the prompt template.
   - Launch `codex exec` in the assigned worktree.

4. A test script must verify agent-file-to-launcher dispatch for both `claude` and `codex`.

## Acceptance Criteria

- `set-implementation-agent.ps1 -Agent codex` writes `codex` to `.codex/implementation-agent`
  and calls `gh variable set AI_REVIEW_AGENT --body codex`.
- `set-implementation-agent.ps1 -Agent claude` writes `claude` and calls
  `gh variable set AI_REVIEW_AGENT --body claude`.
- `set-implementation-agent.ps1 -Agent invalid` exits non-zero without writing anything.
- `start-implementation-worker.ps1` dispatches to the correct launcher based on the agent file.
- Test script passes with no failures.
