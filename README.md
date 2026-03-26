# flatscanner

`flatscanner` — Telegram-сервис для анализа объявлений об аренде и одновременно
демонстрационный репозиторий, показывающий spec-driven и AI-assisted алгоритм
разработки.

## Что здесь находится

- продуктовый backend для анализа rental listings
- repository memory в `docs/` и `specs/`
- orchestration scripts для implementation agents и AI review
- пример управляемого цикла разработки: задача -> spec -> implementation -> PR -> CI -> AI review -> merge

## С чего начать

### Для понимания проекта

- [Русское описание процесса и структуры проекта](./README_PROCESS_RU.md)
- [English process overview](./PROCESS_OVERVIEW_EN.md)
- [Durable docs layer](./docs/README.md)
- [Product idea](./docs/project-idea.md)
- [Backend docs](./docs/project/backend/backend-docs.md)

### Для process/workflow

- [AI PR workflow](./docs/ai-pr-workflow.md)
- [Claude worker orchestration](./docs/claude-worker-orchestration.md)
- [Agent roles and repository rules](./AGENTS.md)

## Основная идея

В проекте разделены:

- `docs/` — долговременная память продукта и архитектуры
- `specs/<feature-id>/` — память конкретных задач и этапов
- `src/` — продуктовый код
- `tests/` — автоматическая проверка поведения
- `scripts/` — orchestration и process tooling

Ключевой принцип:

**код не считается завершенной задачей, пока текущий PR не прошел полный loop приемки.**
