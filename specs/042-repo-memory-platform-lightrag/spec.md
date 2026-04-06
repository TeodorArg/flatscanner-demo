# Spec: Repo-Memory Platform with `LightRAG`

## Feature ID

- `042-repo-memory-platform-lightrag`

## Summary

Преобразовать текущий репозиторий из demo-проекта `flatscanner` в reusable platform для AI-assisted разработки, где:

- repository memory хранится в Markdown-файлах
- `LightRAG` индексирует это знание и помогает доставать релевантный контекст
- orchestration остается spec-driven
- vendor-specific привязки к Telegram, rental domain и Claude убраны

## Problem

Сейчас репозиторий сочетает:

- процессную систему, которую можно переиспользовать
- старый demo-домен, который больше не нужен

Из-за этого:

- верхнеуровневые docs описывают уже не тот продукт, который нужно развивать
- read order будет становиться тяжелее по мере роста истории
- знание из `docs/` и `specs/` неудобно использовать как retrieval-ready memory layer для новых проектов

Нужен новый контур:

- files stay canonical
- retrieval становится вспомогательным умным слоем
- агентам не нужно читать весь архив целиком для каждой новой задачи

## Goal

После завершения MVP репозиторий должен:

1. Описывать новый vendor-neutral продукт.
2. Сохранять `docs/` и `specs/` как source of truth.
3. Иметь рабочий local pilot `LightRAG` для индексирования repository memory.
4. Поддерживать policy-driven context assembly:
   - mandatory docs
   - retrieved docs
5. Быть готовым к использованию как основа для разработки других продуктов.

## Users

- разработчик, который хочет поднять repo-memory систему для нового проекта
- AI orchestrator/planner, которому нужен релевантный контекст по репозиторию
- implementation/review agents, которым нужен context pack вместо полного ручного чтения всего архива

## Scope

В scope MVP входит:

- переписывание верхнеуровневых документов под новый продукт
- удаление или нейтрализация Telegram/rental narrative
- удаление или нейтрализация Claude-specific process naming
- определение taxonomy для repository memory
- проектирование retrieval architecture поверх `docs/`, `specs/`, `.specify/`
- выбор локального model provider для pilot
- локальная интеграция `LightRAG`
- ingestion pilot для Markdown-документов
- тестовый retrieval flow по инженерным вопросам
- определение mandatory-vs-retrieved context policy
- двухшаговая cleanup policy для legacy `flatscanner`

## Out Of Scope

Вне scope MVP:

- production deployment новой платформы
- UI beyond minimal developer interface
- сложная graph ontology на первом этапе
- автоматическая переработка legacy-артефактов
- agent marketplace / plugin ecosystem
- любые Telegram/rental/listing-specific элементы старого продукта

## Non-Goals

Этот проект на данном этапе не должен:

- заменять Markdown-файлы RAG-хранилищем
- превращаться в generic chatbot без process rules
- полностью полагаться на retrieval для выбора обязательного контекста
- сохранять старый `flatscanner` narrative “на всякий случай” в основном README

## Core Principles

### 1. Files are canonical

`docs/`, `specs/`, `ADR`, `.specify/` остаются каноническими артефактами.

### 2. Retrieval is derivative

`LightRAG` помогает находить и собирать знания, но не заменяет repository truth.

### 3. Mandatory context stays explicit

Ключевые process rules не должны зависеть только от retrieval.

### 4. Repo structure remains understandable to humans

Даже без RAG человек должен понимать, где лежит долговременная память и где лежит feature memory.

### 5. Migration is controlled

Сначала новая продуктовая рамка и pilot, потом cleanup legacy-кода.

## Functional Requirements

### FR1. New product framing

Репозиторий должен быть переписан так, чтобы верхнеуровневые docs описывали repo-memory platform, а не rental analysis bot.

### FR2. Vendor-neutral roles

Документы процесса должны описывать generic роли:

- orchestrator
- implementation agent
- review agent
- CI/checks
- human approver

Без обязательной привязки к Claude.

### FR3. Repository memory taxonomy

Должны быть явно описаны:

- durable docs
- feature memory
- process memory
- optional historical artifacts
- derivative memory layers such as MCP memory and any local mirror file

### FR4. Markdown ingestion

Должен существовать pilot ingestion pipeline, который читает ключевые Markdown-файлы и готовит их к индексированию в `LightRAG`.

Pilot ingestion для Markdown должен следовать фиксированным правилам chunking:

- document preface до первого heading сохраняется как отдельный chunk, если он
  не пустой
- основной split идет по Markdown headings
- короткие соседние секции не должны дробиться до шумовых чанков только ради
  формального split
- большие секции допускается делить на подчанки по подпунктам или абзацным
  блокам
- списки и таблицы должны оставаться рядом со своим ближайшим heading context,
  а не отрываться в отдельные бессвязные чанки

### FR5. Local model provider

Pilot должен использовать локальный model stack:

- `Ollama`
- `qwen3:4b` как LLM
- `nomic-embed-text` как embedding model

### FR6. Retrieval queries

Система должна поддерживать хотя бы несколько инженерных retrieval-сценариев, например:

- что нужно прочитать перед изменением orchestration flow
- какие документы ограничивают review loop
- какие прошлые feature artifacts связаны с worker orchestration

### FR7. Limited pilot corpus

Pilot не должен индексировать весь репозиторий.

В pilot corpus входят только core process-memory документы:

- `.specify/memory/constitution.md`
- `AGENTS.md`
- `README_PROCESS_RU.md`
- `PROCESS_OVERVIEW_EN.md`
- `DELIVERY_FLOW_RU.md`
- `docs/README.md`
- `docs/project-idea.md`

Legacy `flatscanner`-артефакты исключаются из pilot corpus до cleanup phase.

### FR8. Context policy

Должна быть зафиксирована политика:

- what is always included
- what is retrieved dynamically
- как агент получает итоговый context pack

### FR9. Testable pilot

Должен существовать локально воспроизводимый тестовый запуск, доказывающий, что retrieval работает на репозиторной памяти.

### FR10. Canonical pilot interface

Для MVP должен быть зафиксирован один canonical executable interface для local
pilot-а.

Для Phase 4 это repository-local script, а не long-running local API.

## Technical Requirements

### TR1. Storage of truth

Все канонические знания остаются в файлах внутри репозитория.

### TR2. Metadata-aware ingestion

При ingestion должны сохраняться как минимум:

- file path
- document type
- headings
- feature id, если применимо
- language, если применимо

Для pilot-а фиксируется минимальная metadata schema на уровень chunk:

- `path`
- `doc_class`
- `title`
- `heading_path`
- `language`
- `feature_id`
- `chunk_id`
- `chunk_order`
- `mandatory_candidate`

`doc_class` в MVP использует ограниченный набор значений:

- `process_memory`
- `durable_doc`
- `feature_memory`
- `draft`

### TR3. Safe retrieval boundaries

Policy layer должна гарантировать, что mandatory process docs не пропускаются.

### TR4. Incremental adoption

Интеграция `LightRAG` должна быть добавлена как новый слой, а не как немедленная замена всей repository navigation логики.

### TR5. Simple MVP retrieval model

Для MVP используется простая схема:

- Markdown chunks
- metadata per chunk
- retrieval query
- mandatory docs added by policy

Сложная graph ontology для MVP не требуется.

### TR6. Deterministic pilot chunking

Chunking rules для pilot-а должны быть deterministic и repository-local, чтобы
повторная индексация одного и того же corpus без смены embedding model давала
сопоставимую структуру chunk boundaries и metadata.

### TR7. Pilot validation contract

Для MVP должен существовать явный validation contract, который определяет:

- canonical command or script entrypoint для index build/refresh
- canonical command or script entrypoint для retrieval query
- фиксированный набор инженерных контрольных вопросов для pilot evaluation
- минимальные условия успешной индексации и retrieval

## Acceptance Criteria

### AC1. Docs reframed

`README.md`, process overview docs и `docs/project-idea.md` больше не описывают Telegram/rental bot как основной продукт.

### AC2. Agent model neutralized

Верхнеуровневые process docs больше не требуют Claude как единственного implementation agent.

### AC3. Pilot indexing works

Есть локальный сценарий, в котором `LightRAG` индексирует ограниченный набор ключевых Markdown-документов.

Успешная индексация означает как минимум:

- все документы pilot corpus попали в ingestion run
- для каждого chunk сохранен обязательный metadata minimum
- index build завершается без ручной подправки corpus на лету

### AC4. Local provider works

Pilot работает на локальном стеке `Ollama + qwen3:4b + nomic-embed-text`.

### AC5. Pilot retrieval works

Есть локальный сценарий, в котором по инженерному вопросу система возвращает релевантные документы или чанки.

Для pilot evaluation фиксируются стартовые инженерные вопросы:

- what must be read before changing the orchestration or delivery flow
- which documents constrain the review and merge loop
- which files define the repository memory taxonomy
- where the local `LightRAG` pilot boundary and pilot corpus are defined
- which artifacts are mandatory versus retrieve-on-demand for product-code work

### AC6. Mandatory context is preserved

Есть зафиксированная policy, по которой конституция и core process rules не могут быть пропущены retrieval-слоем.

Успешный pilot retrieval также должен показывать, что mandatory docs
добавляются policy layer-ом даже если ranked retrieval вернул неполный набор
релевантных chunk-ов.

### AC7. Two-step legacy removal is defined

Legacy `flatscanner`-артефакты сначала исключаются из pilot corpus и новых docs, а физически удаляются только после успешного pilot-а.

## Risks

### R1. Over-deletion

Можно удалить полезные process artifacts вместе со старым продуктом.

### R2. Weak retrieval quality

Если ingestion будет слишком примитивным, `LightRAG` будет возвращать шумные результаты.

### R3. Underpowered local model stack

Локальный стек может дать более слабое качество retrieval/answer synthesis, чем облачные модели.

### R4. Hidden policy drift

Если mandatory context не будет жестко зафиксирован, агент может начать пропускать важные правила процесса.

### R5. Half-migrated repo identity

Если часть docs останется про `flatscanner`, а часть уже будет про новый продукт, репозиторий станет противоречивым.

## Validation

Минимальная валидация MVP:

1. Проверка, что верхнеуровневые docs согласованы между собой.
2. Локальный indexing run на выбранном наборе Markdown-файлов.
3. Локальный retrieval run на 3-5 типовых вопросах.
4. Проверка, что mandatory docs попадают в final context pack.
5. Ручной review результатов retrieval на релевантность.

## Open Questions

- Нужен ли bilingual ingestion policy для RU/EN документов уже в MVP?
- Переписываем ли `docs/project/backend/*` и `docs/project/frontend/*` под новый продукт или удаляем их в cleanup phase?

## Decisions Fixed In Phase 4

- local stack is `Ollama + qwen3:4b + nomic-embed-text`
- canonical pilot interface is a repository-local script
- local API is deferred until the script-first pilot proves useful
- local `in_memory/memory.jsonl` is a derivative mirror of MCP memory, not a
  canonical repository-memory layer

## References

- LightRAG GitHub: https://github.com/HKUDS/LightRAG
- LightRAG PyPI: https://pypi.org/project/lightrag-hku/
- LightRAG paper: https://arxiv.org/abs/2410.05779
