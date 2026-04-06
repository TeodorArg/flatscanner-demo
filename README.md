# repo-memory-platform

`repo-memory-platform` is a spec-driven, AI-assisted repository template for
building and operating software with explicit repository memory.

The repository is being migrated from the legacy `flatscanner` demo toward a
vendor-neutral platform where:

- Markdown files remain the canonical source of truth
- `docs/` holds durable repository memory
- `specs/<feature-id>/` holds feature memory
- pull requests, checks, and review loops remain explicit
- retrieval tooling such as `LightRAG` is additive, not canonical

## What Lives Here

- repository memory in `docs/`, `specs/`, and `.specify/`
- process docs for orchestration, review, and merge readiness
- product code and tests for concrete implementations that use this workflow
- automation scripts for worktrees, PR flow, and AI review operations

## Start Here

### Core Process And Memory

- [Russian process guide](./README_PROCESS_RU.md)
- [English process overview](./PROCESS_OVERVIEW_EN.md)
- [Delivery flow](./DELIVERY_FLOW_RU.md)
- [Repository docs layer](./docs/README.md)
- [Project idea](./docs/project-idea.md)
- [Repository rules](./AGENTS.md)

### Supporting Workflow Docs

- [AI PR workflow](./docs/ai-pr-workflow.md)
- [Claude worker orchestration](./docs/claude-worker-orchestration.md)
- [Claude implementation contract](./CLAUDE.md)
- [Agent roles and repository rules](./AGENTS.md)

### Для локального Python-окружения

Репозиторий использует `Python 3.13.8` и `uv` как канонический local workflow.

Минимальный setup:

```bash
uv venv --python 3.13.8
uv pip install --python .venv/bin/python -e ".[dev]"
```

## Repository Shape

- `docs/` for durable product, architecture, and process memory
- `specs/<feature-id>/` for active feature intent, plan, and task state
- `.specify/` for constitution and spec-kit process templates
- `src/` for implementation code
- `tests/` for automated validation
- `scripts/` for local orchestration and workflow tooling

## Core Rule

Code is not treated as complete when it merely exists locally.

A product-code task is complete only when the active PR loop is merge-ready:
required checks are green, blocking review findings are cleared, merge conflicts
are gone, and only human approval or final merge remains.
