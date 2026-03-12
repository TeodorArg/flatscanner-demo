# Glossary

## Durable Context

Documentation that should stay valid across many features and pull requests.

## Feature Spec

A scoped artifact under `specs/<feature-id>/` describing one concrete unit of work.

## ADR

Architecture Decision Record documenting a durable technical choice and its rationale.

## Listing Adapter

A source-specific ingestion component that knows how to collect and normalize listing data from one platform such as Airbnb or a future aggregator.

## Normalized Listing

A platform-agnostic representation of a rental listing after raw source data has been mapped into shared fields.

## Enrichment

Additional signals collected after parsing the listing, such as transport access, nearby places, Street View context, and public safety indicators.

## Price Fairness

An explainable assessment of whether the listing price appears reasonable for the observed conditions, amenities, and surrounding context.
