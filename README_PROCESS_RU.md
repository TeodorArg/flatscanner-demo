# repo-memory-platform: устройство репозитория и алгоритм разработки

## Зачем нужен этот документ

Этот репозиторий предназначен для spec-driven и AI-assisted разработки с
явной repository memory.

Он описывает:

1. как устроена долговременная память репозитория
2. как ведется feature memory
3. какие роли участвуют в delivery loop
4. как работа проходит путь от запроса до merge-ready PR
5. как retrieval-слой должен соотноситься с каноническими файлами

## 1. Кратко о подходе

В репозитории используются базовые правила:

- **Specs before code**: сначала формализуем задачу, потом меняем код
- **Repository memory over hidden session memory**: важный контекст живет в
  файлах репозитория
- **Small reviewable slices**: работа делается через понятные PR-срезы
- **Role separation**: orchestration, implementation, review и merge authority
  разделены
- **Completion = merge-ready PR loop**: локальный код сам по себе не считается
  завершением

## 2. Основная модель памяти

В репозитории есть четыре уровня памяти.

### Durable docs

`docs/` хранит долговременную память:

- product framing
- архитектурные решения
- glossary и ADR
- устойчивые process rules

### Feature memory

`specs/<feature-id>/` хранит память конкретной фичи:

- `spec.md` отвечает за intent и scope
- `plan.md` отвечает за технический подход
- `tasks.md` отвечает за execution state

### Process memory

`.specify/`, `AGENTS.md` и root process docs фиксируют правила, по которым
агенты и люди работают с репозиторием.

### Historical artifacts

Исторические документы допустимы, но они должны быть явно отделены от текущего
канона и не должны становиться обязательным контекстом по умолчанию.

## 3. Структура репозитория

- `.specify/` — constitution и spec-kit templates
- `docs/` — durable repository memory
- `specs/` — feature memory
- `src/` — implementation code
- `tests/` — automated validation
- `scripts/` — orchestration и workflow tooling
- `.github/` — CI, AI review workflows и prompt assets

## 4. Роли в процессе

### Human requester

- ставит цель
- подтверждает направление
- принимает продуктовые решения

### Orchestrator

- читает repository memory
- формирует или обновляет `spec.md`, `plan.md`, `tasks.md`
- выбирает implementation slice
- следит за quality gates и merge readiness

### Implementation agent

- реализует согласованный slice в isolated branch/worktree
- обновляет код, тесты и `tasks.md`
- публикует или обновляет PR

### Review agent

- проверяет PR и оставляет findings
- не подменяет собой human approval

### CI / checks

- гоняют required validation
- формализуют machine gates для merge

### Human approver

- принимает финальное решение о merge

Конкретный вендор implementation/review agent может меняться. Роли от этого не
меняются.

## 5. Алгоритм работы

### Шаг 1. Получение задачи

Оркестратор сначала определяет scope и находит релевантную repository memory.

### Шаг 2. Чтение памяти

Рекомендуемый порядок чтения:

1. `.specify/memory/constitution.md`
2. `docs/README.md`
3. `docs/project-idea.md`
4. `docs/project/frontend/frontend-docs.md`
5. `docs/project/backend/backend-docs.md`
6. `docs/adr/*.md`
7. релевантные `specs/*/spec.md`
8. релевантные `specs/*/plan.md`
9. релевантные `specs/*/tasks.md`
10. только потом implementation files

### Шаг 3. Формализация фичи

Перед product-code изменениями создается или обновляется активная feature
папка в `specs/`.

### Шаг 4. Изолированный implementation loop

Работа по product code идет через:

- актуальный `main`
- отдельную branch/worktree
- один понятный slice на PR

### Шаг 5. Реализация

Implementation agent:

- меняет код в рамках scope
- обновляет тесты при изменении поведения
- синхронизирует `tasks.md`

### Шаг 6. PR loop

После публикации PR идут:

- required checks
- AI review
- follow-up fixes на той же ветке, если нужно

### Шаг 7. Completion

Задача считается завершенной только когда текущий PR head SHA:

- не имеет blocking findings
- имеет green required checks
- не имеет merge conflicts
- требует только human approval или final merge

## 6. Retrieval и canonical files

Retrieval-слой может ускорять сбор контекста, но не заменяет канон.

Жесткое правило:

- Markdown-файлы в репозитории остаются source of truth
- retrieval является производным слоем
- mandatory process docs не должны зависеть только от retrieval

Каноническая policy для сборки context pack и pilot corpus зафиксирована в
`docs/context-policy.md`.

Канонический workflow для budget profiles, bootstrap order, retrieval triggers
и checkpoint checklist по `LightRAG`/MCP/local-memory refresh зафиксирован в
`docs/context-economy-workflow.md`.

## 7. Практический смысл подхода

Подход нужен для того, чтобы:

- продолжать работу между сессиями без потери контекста
- уменьшать зависимость от скрытой памяти агента
- делать изменения reviewable и traceable
- безопасно подключать разные implementation/review agents
- позже добавить retrieval по repository memory без разрушения файлового канона

## 8. Рекомендуемый вход для нового участника

1. [`.specify/memory/constitution.md`](./.specify/memory/constitution.md)
2. [`docs/README.md`](./docs/README.md)
3. [`docs/project-idea.md`](./docs/project-idea.md)
4. [`AGENTS.md`](./AGENTS.md)
5. [`docs/ai-pr-workflow.md`](./docs/ai-pr-workflow.md)
6. актуальный `specs/<feature-id>/`
7. затем implementation files
