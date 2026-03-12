# ADR 001: Backend MVP Architecture

## Status

Accepted

## Context

The project now has a clear product direction: a user submits a rental listing URL through Telegram, the system collects source listing data, enriches it with external context, and returns an AI-assisted summary with scoring and price fairness analysis.

The repository previously had no chosen backend stack, which left future implementation decisions too open-ended.

## Decision

Adopt the following backend defaults for the first implementation phase:

- Python as the application language
- FastAPI for HTTP services and orchestration endpoints
- PostgreSQL as the primary durable store
- Redis for queue and cache support
- Telegram as the primary user interface for the first release
- OpenRouter as the model gateway for pluggable AI models
- Apify as the default initial listing extraction provider

The application architecture should remain platform-agnostic above the ingestion boundary:

- listing adapters handle source-specific collection
- normalized listing schemas feed shared enrichment logic
- AI analysis and scoring operate on normalized and enriched data

## Consequences

- The codebase can start implementation without revisiting fundamental stack choices
- Airbnb can be implemented first without locking the system to a single listing source
- Long-running analysis work should be designed as background jobs rather than synchronous request handling
- Price fairness should not rely only on LLM output; implementation should preserve structured signals for explainability
- Future architecture changes should update this ADR or add a newer one
