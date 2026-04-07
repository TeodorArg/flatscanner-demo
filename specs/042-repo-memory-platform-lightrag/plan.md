# Plan: Repo-Memory Platform with `LightRAG`

## Goal

Реализовать controlled migration от `flatscanner` к reusable repo-memory platform, не ломая базовые process guarantees:

- repository truth остается в Markdown
- retrieval добавляется как новый слой
- legacy-домен убирается в два шага

## Implementation Strategy

### Phase 1. Reframe top-level identity

Переписать документы, которые задают рамку проекта:

- `README.md`
- `README_PROCESS_RU.md`
- `PROCESS_OVERVIEW_EN.md`
- `DELIVERY_FLOW_RU.md`
- `docs/project-idea.md`

Результат:

- репозиторий описывает новый продукт
- old product narrative больше не является основным

### Phase 2. Neutralize process roles

Переписать process memory, где роли зашиты под конкретных вендоров:

- `.specify/memory/constitution.md`
- `AGENTS.md`
- docs с Claude-specific orchestration language

Результат:

- появляются generic роли
- сохраняется idea of orchestrator / implementation / review / checks

### Phase 3. Define retrieval boundaries

Зафиксировать:

- что входит в source of truth
- какие документы always-read
- какие документы retrieve-on-demand
- какой pilot corpus используется

Pilot corpus:

- `.specify/memory/constitution.md`
- `AGENTS.md`
- `README_PROCESS_RU.md`
- `PROCESS_OVERVIEW_EN.md`
- `DELIVERY_FLOW_RU.md`
- `docs/README.md`
- `docs/project-idea.md`

Excluded from pilot:

- `src/`
- `tests/`
- domain-specific `flatscanner` docs/specs

### Phase 4. Set local LightRAG stack

Зафиксировать локальный pilot stack:

- `Ollama`
- `qwen2.5:1.5b`
- `nomic-embed-text`
- repository-local script as the canonical executable interface
- local `Ollama` on the Mac host with local `LightRAG` in the repository
  Python environment
- `LightRAG` default local storage via repository-local `working_dir`

Default pilot storage components:

- `JsonKVStorage`
- `NanoVectorDBStorage`
- `NetworkXStorage`
- `JsonDocStatusStorage`
- repository-local pilot working directory rooted at `.lightrag/`

Правила:

- embedding model выбирается до первой индексации
- при смене embedding model индекс пересоздается
- на старте не добавляем дополнительные provider options
- local API не вводим в baseline до завершения script-first pilot

### Phase 5. Build simple ingestion MVP

Сделать минимальный ingestion pipeline:

1. собрать Markdown-файлы pilot corpus
2. разрезать по заголовкам и логическим секциям
3. добавить metadata:
   - path
   - headings
   - doc_type
   - language
4. передать чанки в `LightRAG`

Важно:

- без сложной graph ontology
- без полной индексации всего репозитория

#### Fixed Chunking Rules

- preface до первого heading сохраняется отдельным chunk, если он не пустой
- базовый split идет по Markdown headings
- короткие соседние секции можно схлопывать, если иначе получаются шумовые
  чанки без самостоятельной retrieval value
- большие секции можно делить на подчанки по подпунктам или абзацным блокам
- списки и таблицы не должны терять ближайший heading context
- chunking должен быть deterministic для одинакового входного corpus

#### Fixed Metadata Schema

Каждый chunk в pilot-е должен содержать:

- `path`
- `doc_class`
- `title`
- `heading_path`
- `language`
- `feature_id`
- `chunk_id`
- `chunk_order`
- `mandatory_candidate`

Правила заполнения:

- `doc_class` назначается repository-local policy, а не выводится моделью
- `title` берется из верхнего document title или file-level fallback
- `heading_path` хранит путь заголовков от верхнего уровня до текущего chunk-а
- `feature_id` заполняется только для feature memory, иначе `null`
- `chunk_id` должен быть стабильным в рамках одного file path и chunk order
- `mandatory_candidate` отмечает chunks из always-read docs, чтобы retrieval
  flow мог смешивать ranked results с policy injection

#### Canonical Phase-5 Validation Contract

Перед переходом к Phase 6 implementation должен появиться repository-local
script-first interface, который поддерживает как минимум:

1. build or refresh index for the fixed pilot corpus
2. run a retrieval query against that index
3. emit enough debug output to confirm which files and chunks were indexed

Readiness before the first real indexing run must confirm:

- local `Ollama` is running on the Mac host
- `qwen2.5:1.5b` and `nomic-embed-text` are locally available in `Ollama`
- `LightRAG` is installed in the repository Python environment
- the pilot working directory is resolved under `.lightrag/`
- the fixed pilot corpus is readable from the repository root

Phase 5 считается завершенной, когда:

- ingestion run охватывает весь pilot corpus из `docs/context-policy.md`
- metadata schema заполнена для каждого indexed chunk
- index build воспроизводим на одинаковом corpus без ручных ad hoc правок
- можно показать retrieval-ready index state для перехода к policy-driven query
  work

### Phase 6. Build policy-driven retrieval MVP

Сделать retrieval flow:

1. инженерный вопрос
2. retrieval по pilot corpus
3. добавление mandatory docs
4. сборка final context pack

Стартовые query modes для проверки:

- `hybrid`
- `mix`

Стартовый набор инженерных вопросов для проверки:

- what must be read before changing the orchestration or delivery flow
- which documents constrain the review and merge loop
- which files define the repository memory taxonomy
- where the local `LightRAG` pilot boundary and pilot corpus are defined
- which artifacts are mandatory versus retrieve-on-demand for product-code work

### Phase 7. Evaluate usefulness

Проверить:

- насколько релевантны найденные документы
- теряются ли process constraints
- меньше ли контекста, чем при полном ручном чтении
- удобно ли использовать это для новой feature planning session

### Phase 8. Cleanup legacy domain

Двухшаговая политика:

1. сначала исключить legacy из pilot и новых docs
2. после успешного pilot удалить legacy физически

Legacy cleanup targets:

- Telegram/rental product code
- domain tests
- old product specs
- old domain docs, если они больше не нужны новому продукту

## Touched Areas

- `.specify/`
- `docs/`
- root process docs
- `AGENTS.md`
- `specs/042-repo-memory-platform-lightrag/`
- future local RAG scripts/config

## Validation Plan

### Docs validation

Проверить, что:

- root docs не противоречат друг другу
- constitution и AGENTS согласованы
- в docs больше нет обязательной Claude-only модели

### Pilot validation

Проверить, что:

- локальный `Ollama` поднимается
- `LightRAG` может проиндексировать pilot corpus
- retrieval отвечает на 3-5 инженерных вопросов
- mandatory docs не теряются

Дополнительно для ingestion validation:

- debug output показывает все входные pilot files
- chunk boundaries объяснимы через fixed chunking rules
- metadata fields заполняются без model-side inference

### Cleanup gate

Физическое удаление legacy допустимо только после того, как:

- top-level docs переписаны
- pilot retrieval работает
- policy for mandatory docs зафиксирована

## Decisions Fixed By This Plan

- canonical source remains Markdown in repo
- MVP uses simple chunk-based retrieval, not advanced graph ontology
- current pilot extraction LLM is `qwen2.5:1.5b` because it completes local
  indexing substantially faster than `qwen3:4b` on the Mac pilot environment
- local stack is `Ollama + qwen2.5:1.5b + nomic-embed-text`
- pilot corpus is intentionally small
- legacy `flatscanner` removal is two-step, not immediate
- local `in_memory/memory.jsonl` is a derivative mirror of MCP memory and does
  not add a new canonical memory layer
- repository-local manual sync helper is `scripts/sync_memory.py`
- the helper now covers validate, upsert, remove-observation, and delete-entity

## Follow-Up Candidates

- добавить bilingual ingestion policy
- расширить corpus после pilot success
- решить, нужен ли CLI wrapper или local API после script-first pilot
- решить, нужен ли phase 2 graph enrichment later
