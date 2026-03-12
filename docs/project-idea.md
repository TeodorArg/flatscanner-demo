# Project Idea: flatscanner

## Problem

People evaluating rentals often need to combine fragmented listing details, map context, safety signals, transport access, and price reasonableness by hand. The repository needs a clear product and technical baseline so AI agents can make consistent implementation decisions without rebuilding context in every session.

## Solution

Build a universal rental listing analysis service. A user sends a listing URL to Telegram, the backend collects listing data from the source platform, enriches it with external public signals, and generates an AI summary with a quality score and a price fairness assessment.

Maintain a lightweight durable documentation layer for the product and architecture, then drive each concrete change through feature specs under `specs/`.

## Core Value

- Faster, more informed rental decisions for end users
- One comparable analysis flow across multiple listing platforms
- Clear explanation of risks, tradeoffs, and price fairness
- Faster onboarding for AI agents and humans
- Less drift between sessions and pull requests
- Clear separation between durable context and active feature work

## High-Level Flow

1. User sends a listing URL in Telegram
2. The backend detects the source platform and selects the matching adapter
3. Listing data is collected from the platform through Apify or another source-specific connector
4. The system enriches the listing with external location and context data
5. AI models summarize findings, score the listing, and estimate price fairness
6. Telegram returns a structured result with key strengths, risks, and recommendations
7. Durable project context stays in `docs/`, and each implementation slice is tracked in `specs/`

## Target Audience

- End users who want a fast, reliable evaluation of a rental listing
- Developers and AI agents collaborating on the `flatscanner` codebase

## Product Direction

- The service should support multiple listing aggregators over time, even if early implementation starts with Airbnb
- Telegram is the primary user interface for the first release
- The backend should keep platform-specific ingestion separate from shared analysis and scoring logic
- AI output should be explainable, not just a black-box score
