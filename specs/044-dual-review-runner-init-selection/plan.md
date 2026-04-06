# Plan: Dual Review Runner Init Selection

## Summary

Add a project-initialization level choice for AI review runner strategy while
preserving both supported self-hosted paths:

- Windows self-hosted review runner
- macOS self-hosted review runner

The implementation should make the selected runner strategy explicit and use it
to align workflow targeting and setup guidance.

Preferred mechanism:

- canonical init script chooses the runner strategy
- init script writes a GitHub repo variable for workflow runtime
- workflow `runs-on` resolution follows that repo variable

## Files And Areas

- `.github/workflows/ai-review.yml`
- `.github/workflows/claude-fix-pr.yml`
- `docs/project/backend/self-hosted-runner.md`
- `docs/ai-pr-workflow.md`
- `docs/project/backend/backend-docs.md`
- `docs/adr/002-ai-development-workflow.md`
- `scripts/set-review-runner.ps1`
- `specs/044-dual-review-runner-init-selection/`

## Risks

- mixing reviewer choice and runner choice would create configuration
  confusion
- keeping one workflow with hard-coded OS labels would preserve the current
  blocker for some projects
- introducing runner flexibility without explicit initialization-time choice
  would make support paths ambiguous
- leaving Windows-specific shell/path usage in workflow steps would still break
  macOS execution even if runner labels became dynamic

## Validation

- confirm the design preserves both Windows and macOS runner strategies
- confirm the selected runner strategy can be expressed during project
  initialization
- confirm workflow targeting rules match GitHub's self-hosted label semantics
- confirm the `AI Review` required check name remains stable
- confirm workflow steps use cross-platform PowerShell invocation

## Notes

- This feature is about runner-strategy selection, not reviewer selection.
- Reviewer choice remains controlled by `AI_REVIEW_AGENT`.
- Runner label matching must respect GitHub's rule that all labels listed in
  `runs-on` must be present on the selected self-hosted runner.
- The preferred design is: init script sets repo variable, workflow reads repo
  variable, docs explain Windows and macOS runner setup separately.
