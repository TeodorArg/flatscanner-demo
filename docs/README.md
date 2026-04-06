# Project Docs

`docs/` stores durable repository memory that should outlive any single feature
or agent session.

## Use `docs/` For

- product framing
- stable architecture and stack decisions
- ADRs and glossary terms
- durable workflow and operations guidance
- repository-memory rules that apply across many features

## Do Not Use `docs/` For

- active feature execution state
- one-off implementation checklists
- transient branch-level notes

Those belong in `specs/<feature-id>/`.

## Memory Taxonomy

- `docs/` = durable docs
- `specs/<feature-id>/` = feature memory
- `.specify/` = process memory and templates
- clearly marked archives = optional historical artifacts

## Recommended Reading Order

1. `project-idea.md`
2. `project/frontend/frontend-docs.md`
3. `project/backend/backend-docs.md`
4. `adr/*.md`
5. `context-policy.md`
6. `../README_PROCESS_RU.md`
7. `../PROCESS_OVERVIEW_EN.md`
8. `../DELIVERY_FLOW_RU.md`
9. `ai-pr-workflow.md`
10. `lightrag-local-pilot.md`
11. `local-memory-sync.md`
12. `glossary.md`

Concrete vendor-specific worker docs may exist in this repository, but they are
implementation examples rather than the generic process contract.
