# Feature Spec: Telegram Listing Analysis MVP

## Context

Deliver the first end-to-end user flow for `flatscanner`: a user sends a rental listing URL in Telegram and receives a structured analysis generated from parsed listing data and selected external signals.

This feature should establish the reusable vertical slice for future source platforms, even if Airbnb is the first supported provider.

## Scope

- Accept listing URLs from Telegram
- Detect the listing platform and route through a source adapter interface
- Implement the first working adapter for Airbnb
- Normalize parsed listing data into a shared schema
- Run an analysis job through the backend pipeline
- Produce an AI-assisted result summary for Telegram
- Persist request, normalized listing data, and analysis results

## Out Of Scope

- Full multi-platform implementation beyond the first adapter
- Production-grade billing, quotas, or account management
- Advanced web frontend
- A final production-calibrated price model for every market

## Requirements

- Telegram must be the primary interface for initiating the analysis
- The ingestion design must support additional listing providers without changing shared downstream logic
- The system must store a normalized listing representation separate from raw provider payloads
- The analysis result must include a concise summary, notable risks, and a price fairness assessment
- The system must tolerate partial enrichments when some external sources are unavailable
- The result must make clear which findings came from source listing data versus derived analysis

## Acceptance Criteria

- A Telegram message containing an Airbnb URL creates an analysis job
- The backend parses the Airbnb listing through the adapter layer and stores a normalized listing record
- The system returns a Telegram response with summary text, strengths, risks, and a price fairness verdict
- The architecture leaves a defined extension point for future providers such as Booking or other aggregators
- Automated tests cover the URL routing, normalization, and result formatting paths for the implemented slice

## Open Questions

- Which enrichment sources are reliable enough for the very first MVP response
- How detailed the initial Telegram report should be before the message becomes too long
- Whether the first version should return a single final message or incremental status updates during analysis
