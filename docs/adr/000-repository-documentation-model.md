# ADR 000: Repository Documentation Model

## Status

Accepted

## Context

The project needs a documentation approach that works well for AI agents without duplicating the same information across every feature spec.

## Decision

Use a two-layer model:

- `docs/` for durable product and architecture context
- `specs/` for feature-specific requirements, planning, and execution

The `spec-kit` process and templates remain under `.specify/`.

## Consequences

- Agents get a stable read order before working on features
- Feature specs stay smaller and more focused
- Architectural changes must be recorded in a durable location
