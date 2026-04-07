# Tasks: Repo-Memory Platform with `LightRAG`

## Status

- [x] Feature folder created
- [x] Canonical `spec.md` created
- [x] Canonical `plan.md` created
- [x] Canonical `tasks.md` created

## Phase 1. Product Reframing

- [x] Rewrite `README.md` for repo-memory platform positioning
- [x] Rewrite `README_PROCESS_RU.md` for the new product
- [x] Rewrite `PROCESS_OVERVIEW_EN.md` for the new product
- [x] Rewrite `DELIVERY_FLOW_RU.md` for the new product
- [x] Rewrite `docs/project-idea.md`

## Phase 2. Process Neutralization

- [x] Rewrite `AGENTS.md` to remove Claude-only coupling
- [x] Rewrite `.specify/memory/constitution.md` to remove Claude-specific role binding
- [x] Review workflow/process docs for vendor-specific language

## Phase 3. Retrieval Boundaries

- [x] Define mandatory context set
- [x] Define retrieve-on-demand set
- [x] Fix pilot corpus file list
- [x] Explicitly exclude legacy `flatscanner` artifacts from pilot corpus

## Phase 4. Local LightRAG Stack

- [x] Lock local stack to `Ollama + qwen2.5:1.5b + nomic-embed-text`
- [x] Decide pilot interface: CLI, script, or local API
- [x] Add local setup notes for the pilot stack
- [x] Define local memory mirror policy for `in_memory/memory.jsonl` and MCP
      sync
- [x] Add repository-local manual memory sync helper
- [x] Add remove-observation and delete-entity support to the manual helper

## Phase 5. Ingestion MVP

- [x] Define Markdown chunking rules for pilot docs
- [x] Define metadata schema for chunks
- [x] Implement pilot ingestion prototype
- [x] Validate indexing on pilot corpus

## Phase 6. Retrieval MVP

- [x] Implement policy-driven retrieval prototype
- [x] Test `hybrid` mode
- [x] Test `mix` mode
- [x] Verify mandatory docs are always added

## Phase 7. Evaluation

- [x] Run 3-5 engineering retrieval questions
- [x] Review retrieval relevance manually
- [x] Compare pilot retrieval vs full manual read order
- [x] Record gaps and follow-up decisions

## Phase 8. Legacy Cleanup

- [x] Remove `flatscanner` narrative from rewritten docs
- [ ] Confirm pilot no longer depends on legacy artifacts
- [ ] Delete legacy Telegram/rental code after pilot success
- [ ] Delete legacy domain tests after pilot success
- [ ] Delete old domain-specific specs/docs after pilot success

## Completion Criteria

- [x] Top-level docs describe the new product coherently
- [x] Process docs are vendor-neutral
- [x] LightRAG pilot runs locally on the chosen stack
- [x] Pilot retrieval returns relevant process-memory context
- [x] Mandatory docs are preserved by policy
- [ ] Legacy `flatscanner` artifacts are removed only after pilot success
