# Project Idea: repo-memory platform

## Problem

AI-assisted development becomes brittle when important context lives only in
chat history, private notes, or human memory.

As repositories grow, agents and humans need a stable way to answer questions
such as:

- what is the current product or process contract
- which feature memory is active
- which architectural decisions already constrain the change
- which documents are always mandatory before implementation

## Solution

Build a reusable repo-memory platform where:

- Markdown files remain the canonical source of truth
- `docs/` stores durable repository memory
- `specs/<feature-id>/` stores feature memory
- `.specify/` stores governing process rules and templates
- pull requests and checks remain the unit of completion
- retrieval tooling such as `LightRAG` can index repository memory without
  replacing it

## Core Value

- faster onboarding for humans and agents
- lower context loss between sessions
- clearer architectural and process continuity
- safer multi-agent collaboration through explicit repository artifacts
- smaller, more relevant context packs for planning and review

## High-Level Flow

1. A human requester or orchestrator identifies a task
2. Repository memory is read from canonical files
3. The active feature is formalized in `spec.md`, `plan.md`, and `tasks.md`
4. Implementation happens in an isolated branch/worktree
5. Checks and AI review validate the pull request
6. Durable decisions are written back into repository memory
7. Optional retrieval tooling accelerates future context assembly

## Target Users

- developers setting up a reusable AI-assisted delivery repository
- orchestrators and planners who need reliable repository context
- implementation and review agents that need scoped context packs

## Product Direction

- keep repository truth in files and in a Light-RAG database
- separate durable memory from feature memory
- preserve explicit review and merge gates
- add retrieval as a derivative helper layer only after the file model is clear
- keep the platform vendor-neutral at the role and process level
