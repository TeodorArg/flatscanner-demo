"""Web delivery channel package.

Provides the HTTP API layer for the web delivery channel:

- ``models`` — channel-neutral read models for submit/status/result
- ``stubs`` — no-op ``ProgressSink`` and ``AnalysisResultPresenter`` used while
  the web result-storage backend is not yet implemented
- ``router`` — FastAPI router exposing the web API endpoints
"""
