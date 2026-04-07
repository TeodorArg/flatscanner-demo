# Glossary

This glossary contains only stable repository-wide terms.

Update it when a term becomes canonical across multiple docs, features, or
process steps and needs one consistent meaning for the whole repository.

Do not update it for one-off task wording, temporary draft language, or
vendor-specific local conventions that are not part of the generic platform
model.

## Durable Docs

Repository documentation in `docs/` that should remain valid across many
features and pull requests.

## Feature Memory

The active feature-specific context stored under `specs/<feature-id>/`.

It is typically expressed through `spec.md`, `plan.md`, and `tasks.md`.

## Process Memory

Repository-level rules and templates that govern how work is planned,
implemented, reviewed, and merged.

This mainly lives in `.specify/`, `AGENTS.md`, and the core process docs.

## MCP Memory

A derivative machine memory layer used to retain repo-relevant facts across
sessions.

It may speed up recall and retrieval, but it does not replace canonical
repository files.

## Local Memory Mirror

A local file snapshot of selected MCP memory entities, currently stored in
`in_memory/memory.jsonl`.

It is derivative, repo-scoped, and subordinate to canonical files.

## Historical Artifacts

Older documents or closed feature records kept for traceability, but not used
as default canonical context for new work.

## Repository Context

The set of repository documents used to understand a task before changing code
or process.

## Mandatory Context

The documents that must always be included in a context pack before certain
types of work.

These are defined by policy and cannot be delegated entirely to retrieval.

## Retrieve-On-Demand Context

Documents that are not always loaded by default, but may be added through
search, retrieval, or explicit need for the current task.

## Context Pack

The final bundle of mandatory and retrieved documents used for planning,
implementation, or review on one task.

## Pilot Corpus

The intentionally limited set of canonical documents included in the initial
`LightRAG` indexing pilot.

## Orchestrator

The role responsible for reading repository memory, framing scope, maintaining
spec alignment, and driving the delivery loop.

## Implementation Agent

The role responsible for making scoped changes in an isolated branch/worktree
and updating the active feature state.

## Review Agent

The role responsible for evaluating pull requests and producing review
findings.

## ADR

Architecture Decision Record documenting a durable technical decision and its
rationale.

## Merge-Ready

The state where the current pull request head SHA has no blocking findings,
green required checks, no merge conflicts, and only human approval or final
merge remaining.
