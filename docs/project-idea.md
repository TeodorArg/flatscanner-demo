# Project Idea: flatscanner

## Problem

The repository needs a clear product and technical baseline so AI agents can make consistent implementation decisions without rebuilding context in every session.

## Solution

Maintain a lightweight durable documentation layer for the product and architecture, then drive each concrete change through feature specs under `specs/`.

## Core Value

- Faster onboarding for AI agents and humans
- Less drift between sessions and pull requests
- Clear separation between durable context and active feature work

## High-Level Flow

1. Define durable project context in `docs/`
2. Create or update an active feature in `specs/`
3. Plan with Codex
4. Implement with Claude Code
5. Validate through PR checks and review

## Target Audience

Developers and AI agents collaborating on the `flatscanner` codebase.
