# Tasks: Dual Review Runner Init Selection

## Status

- [x] Feature folder created
- [x] Canonical `spec.md` created
- [x] Canonical `plan.md` created
- [x] Canonical `tasks.md` created

## Scope Confirmation

- [x] Confirm both supported runner strategies: Windows and macOS
- [x] Confirm where runner-strategy choice is recorded during project init
- [x] Confirm which workflow/docs/scripts are in scope

## Implementation

- [x] Define the initialization-time runner selection mechanism
- [x] Add a canonical init script that sets the runner-strategy repo variable
- [x] Make AI review workflow runner targeting follow the selected strategy
- [x] Make Claude fix workflow runner targeting follow the selected strategy
- [x] Update setup docs for Windows and macOS runner paths
- [x] Keep reviewer selection independent from runner selection

## Validation

- [x] Verify docs and workflow targeting are aligned
- [x] Verify dynamic runs-on preserves the stable `AI Review` check name
- [ ] Prepare implementation loop notes / PR summary
