# Spec: Dual Review Runner Init Selection

## Feature ID

- `044-dual-review-runner-init-selection`

## Context

The current repository review workflow is blocked on machines that do not have
the exact self-hosted runner shape expected by `.github/workflows/ai-review.yml`.

Today the workflow requires:

- `self-hosted`
- `windows`
- `ai-runner`

The user only has a MacBook available, so the current project-initialization
story is incomplete for repositories that want to reuse this workflow but do
not plan to provision a Windows runner first.

At the same time, the repository must preserve the ability to use the existing
Windows review runner path. The goal is not to replace one runner with another;
it is to support both runner strategies and choose the intended one at project
initialization time.

This feature builds on prior decisions:

- spec `004-switchable-ai-reviewer`: reviewer choice comes from
  `AI_REVIEW_AGENT`
- spec `005-neutral-ai-runner-label`: workflows target the neutral custom label
  `ai-runner`

## Scope

This feature defines a reusable project-init decision for AI review runner
selection:

- preserve both Windows and macOS self-hosted runner options
- define how a project chooses its review-runner strategy during initialization
- align workflow targeting, docs, and setup guidance with that explicit choice
- keep one stable `AI Review` required check contract

## Out Of Scope

- replacing the reviewer-selection contract controlled by `AI_REVIEW_AGENT`
- changing the sticky review comment contract
- removing self-hosted review as a concept
- adding automatic runtime detection or failover between runner operating
  systems

## Requirements

- The repository must support both Windows and macOS self-hosted review runner
  strategies.
- Project initialization must include one explicit choice of review-runner
  strategy.
- The chosen runner strategy must be recorded explicitly rather than left
  implicit.
- The workflow runtime source for runner selection must be a GitHub repo
  variable.
- The canonical way to set that repo variable must be a repository init script,
  not manual GitHub UI editing as the normal path.
- Workflow targeting must match the selected runner strategy.
- The required check name must remain `AI Review`.
- Existing Windows runner support must remain valid after this feature.
- A macOS runner path must be documented using GitHub's self-hosted runner
  model and default label matching rules.

## Acceptance Criteria

- Feature memory defines the two supported runner strategies: Windows and
  macOS.
- Feature memory defines where runner-strategy choice is made during project
  initialization.
- Feature memory defines the preferred mechanism: init script writes the repo
  variable used by workflow runtime.
- Feature memory defines how workflow targeting changes based on that choice.
- The repository keeps one stable `AI Review` status-check name.
- The feature lists the concrete workflow/docs/scripts that must change in the
  implementation phase.

## Preferred Design

- Runner strategy is selected during project initialization.
- The initialization script writes one GitHub repo variable that represents the
  chosen runner strategy.
- GitHub Actions workflow runtime reads that repo variable to decide which
  runner label set to target.
- Reviewer selection remains a separate concern and continues to use
  `AI_REVIEW_AGENT`.

## Source Notes

- GitHub Actions routes self-hosted jobs only to runners that match all labels
  in `runs-on`.
- Self-hosted runners receive default labels including `self-hosted`, OS label
  (`windows`, `macOS`, `linux`), and architecture label.
- macOS self-hosted runners can be installed as a service after runner setup.

These points were verified against GitHub Actions documentation via Context7.
