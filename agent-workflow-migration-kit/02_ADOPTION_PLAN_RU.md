# 02. Пошаговый план внедрения в новый проект

## Этап 1. Подготовить repository memory

Создать в новом проекте:

- `AGENTS.md`
- `docs/README.md`
- `docs/project-idea.md`
- `docs/project/backend/backend-docs.md`
- `docs/project/frontend/frontend-docs.md` при наличии frontend
- `docs/adr/`
- `specs/`

На этом этапе еще не нужно писать orchestration scripts.

Результат:

- проект получает durable memory layer
- появляется единая read order

## Этап 2. Ввести feature-memory workflow

Для любой новой задачи создавать:

- `specs/<feature-id>/spec.md`
- `specs/<feature-id>/plan.md`
- `specs/<feature-id>/tasks.md`

Нужно сразу зафиксировать:

- как нумеруются feature folders
- как обновляется `tasks.md`
- когда задача считается завершенной

Результат:

- каждая задача становится воспроизводимой и переносимой между сессиями

## Этап 3. Ввести роли агентов

В `AGENTS.md` закрепить:

- кто оркестратор
- кто implementation agent
- кто review agent
- кто и что может менять напрямую

Также зафиксировать:

- один worker = один worktree
- один PR на один task slice

## Этап 4. Ввести orchestration contract

Нужно описать и затем реализовать минимальный набор действий:

1. выбрать текущий implementation agent
2. создать isolated branch/worktree от `main`
3. запустить implementation task
4. опубликовать PR
5. дождаться CI и AI review
6. продолжать fixes на той же ветке до merge-ready

На этом этапе можно начать с manual commands, а не с полноценного automation.

## Этап 5. Ввести CI и AI review loop

Нужно определить required checks:

- baseline
- guard
- tests
- AI review

И зафиксировать правило:

PR loop считается завершенным только когда на текущем head SHA:

- нет blocking findings
- required checks green
- нет merge conflicts
- осталось только human approval или merge

## Этап 6. Ввести delivery loop

После merge нужно зафиксировать процесс:

1. sync local `main`
2. deploy на тестовую среду
3. smoke test
4. фиксация результата
5. follow-up task при необходимости

## Этап 7. Прогнать один тестовый feature slice

Нельзя считать workflow внедренным только потому, что написаны docs.
Нужно провести одну тестовую задачу полностью:

- task -> spec -> implementation -> PR -> review -> merge -> deploy -> smoke

Только после этого процесс считается реально установленным.

