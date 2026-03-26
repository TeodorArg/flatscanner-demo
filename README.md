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

- [Русское описание процесса и структуры проекта](C:\Users\User\FlatProject\flatscanner\README_PROCESS_RU.md)
- [English process overview](C:\Users\User\FlatProject\flatscanner\PROCESS_OVERVIEW_EN.md)
- [Durable docs layer](C:\Users\User\FlatProject\flatscanner\docs\README.md)
- [Product idea](C:\Users\User\FlatProject\flatscanner\docs\project-idea.md)
- [Backend docs](C:\Users\User\FlatProject\flatscanner\docs\project\backend\backend-docs.md)

### Для process/workflow

- [AI PR workflow](C:\Users\User\FlatProject\flatscanner\docs\ai-pr-workflow.md)
- [Claude worker orchestration](C:\Users\User\FlatProject\flatscanner\docs\claude-worker-orchestration.md)
- [Agent roles and repository rules](C:\Users\User\FlatProject\flatscanner\AGENTS.md)

## Основная идея

В проекте разделены:

- `docs/` — долговременная память продукта и архитектуры
- `specs/<feature-id>/` — память конкретных задач и этапов
- `src/` — продуктовый код
- `tests/` — автоматическая проверка поведения
- `scripts/` — orchestration и process tooling

Ключевой принцип:

**код не считается завершенной задачей, пока текущий PR не прошел полный loop приемки.**
