# LightRAG Local Pilot

This document fixes the local stack and the executable interface for the first
repository-memory `LightRAG` pilot.

## Purpose

The first pilot must be locally reproducible, small in scope, and aligned with
the repository context policy.

This phase does not introduce a production service. It defines the minimum
local setup needed to validate indexing and retrieval on the pilot corpus.

## Locked Local Stack

The Phase 4 pilot stack is fixed to:

- `Ollama`
- `qwen3:4b` for generation
- `nomic-embed-text` for embeddings
- `LightRAG` as the retrieval/indexing library

No alternate provider matrix is part of the MVP.

## Why This Stack

- `Ollama` keeps the pilot local and vendor-neutral.
- `qwen3:4b` is the fixed lightweight local LLM for first validation passes.
- `nomic-embed-text` is fixed before first indexing so retrieval results are
  comparable across runs.
- `LightRAG` remains a derivative retrieval layer over canonical Markdown files.

## Embedding Invariant

- The embedding model is chosen before the first real index build.
- If the embedding model changes, the pilot index must be rebuilt.
- Retrieval results from different embedding models must not be compared as one
  continuous baseline.

## Pilot Interface Decision

The canonical Phase 4 interface is a repository-local script.

### Chosen Interface

Use a script-first pilot that:

1. reads the fixed pilot corpus
2. builds or refreshes the local index
3. runs retrieval queries against that index
4. injects mandatory docs according to `docs/context-policy.md`

### Why Script-First

- The MVP acceptance criteria require a reproducible local scenario, not a
  long-running service.
- A repository-local script can encode repo-specific corpus rules and context
  policy directly.
- The official `LightRAG` library already supports direct programmatic usage
  with local `Ollama` models, so a script is the thinnest viable integration.
- A local API would add server lifecycle, port/config management, and a broader
  interface surface before the pilot proves useful.
- A pure manual CLI workflow is too loose for policy-driven context assembly and
  repeatable repo-specific validation.

## Non-Canonical Interfaces For MVP

- Local API server: allowed later, but not the Phase 4 baseline
- Ad hoc manual CLI commands: useful for debugging, but not the canonical pilot
  interface

If an API is added later, it must remain a wrapper around the same canonical
pilot corpus rules and mandatory-context policy.

## Local Setup Notes

### Required Local Services

- `Ollama` running locally
- `qwen3:4b` pulled into `Ollama`
- `nomic-embed-text` pulled into `Ollama`

On macOS, the expected way to start the local `Ollama` service for this pilot
is to launch the `Ollama.app` desktop application before running pilot
commands from the terminal.

### Local Runtime Topology

The pilot uses:

- local `Ollama` on the Mac host
- local `LightRAG` in the repository Python environment

Example local preparation:

```bash
ollama pull qwen3:4b
ollama pull nomic-embed-text
```

The expected local `Ollama` host for the pilot is `http://localhost:11434`
unless a later repo-specific script documents a different default.

### LightRAG Wiring Direction

The pilot implementation should use direct library wiring with `Ollama` for:

- generation via `qwen3:4b`
- embeddings via `nomic-embed-text`
- a repo-local working directory for index data

The implementation may later expose this through a CLI wrapper or local API,
but the Phase 4 baseline stays script-first.

### Local Storage For The Pilot

For the first local pilot, `LightRAG` uses its default local storage layer in a
repository-local `working_dir`.

Current default storage components from the `LightRAG` README:

- `kv_storage`: `JsonKVStorage`
- `vector_storage`: `NanoVectorDBStorage`
- `graph_storage`: `NetworkXStorage`
- `doc_status_storage`: `JsonDocStatusStorage`

For this pilot, index and document-status data are stored in the local
`working_dir` used by the repository script.

### Working Directory Shape

The repository script should use one fixed pilot working directory under the
repository root.

Recommended location:

- `.lightrag/`

Recommended contents at the pilot stage:

- `input/` for optional debug snapshots of the fixed pilot corpus
- `chunks/` for optional debug exports of prepared Markdown chunks
- `index/` for `LightRAG` local index/state files created under the chosen
  `working_dir`
- `logs/` for pilot run logs when debug output is persisted

The exact file names inside these folders may follow `LightRAG` defaults and
the repository script implementation, but the pilot should keep all runtime
artifacts inside one repo-local working area.

### Readiness Checklist

Before the first real pilot indexing run, confirm all of these are true:

- `Ollama` is installed on the Mac host
- the local `Ollama` service is running
- `qwen3:4b` is available in local `Ollama`
- `nomic-embed-text` is available in local `Ollama`
- `LightRAG` is installed in the repository Python environment
- the repository script can reach the expected local `Ollama` host
- the pilot `working_dir` exists or can be created by the repository script
- the fixed pilot corpus from `docs/context-policy.md` is readable from the
  repository root

Minimal readiness checks should confirm:

- `ollama --version` returns the local CLI version without crashing
- `ollama list` shows the required models
- the Python environment can import `lightrag`
- the repository script can print the resolved pilot corpus and working
  directory before indexing

## Scope Boundary

This document fixes the local stack and interface only.

It does not yet define:

- the exact chunking rules
- the final metadata schema
- the retrieval evaluation questionnaire

Those belong to Phase 5 through Phase 7.

## References

- `docs/context-policy.md`
- `specs/042-repo-memory-platform-lightrag/spec.md`
- `specs/042-repo-memory-platform-lightrag/plan.md`
- `LightRAG` README: <https://github.com/HKUDS/LightRAG>
