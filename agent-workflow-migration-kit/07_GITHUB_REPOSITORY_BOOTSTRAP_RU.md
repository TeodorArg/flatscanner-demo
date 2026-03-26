# 07. Настройка GitHub-репозитория

## Зачем нужен этот слой

Даже если документы, шаблоны и prompts перенесены правильно, workflow не будет
воспроизводиться без корректной настройки самого GitHub-репозитория.

Нужно перенести не только файловую структуру, но и repository policy.

## Что обязательно настроить

### 1. Default branch

Нужно определить каноническую ветку, от которой всегда стартуют задачи.

Обычно это:

- `main`

Это правило должно совпадать:

- с `AGENTS.md`
- с CI
- с branch protection
- с orchestration scripts

### 2. Branch protection / rulesets

Для основной ветки нужно включить правила, которые поддерживают workflow:

- изменения в основную ветку идут через PR
- требуется актуальный branch status
- required checks должны пройти до merge
- прямой push в основную ветку запрещен или ограничен
- merge при конфликтах запрещен

Если в проекте нужны исключения для администратора, это должно быть
задокументировано отдельно.

### 3. Required status checks

Нужно зафиксировать минимальный набор required checks.

Примерный набор:

- `baseline-checks`
- `guard`
- `tests` или эквивалентный тестовый workflow
- `AI Review`

Важно:

- названия required checks должны совпадать с реальными workflow names/job names
- merge-ready definition в docs должна ссылаться именно на эти checks

### 4. GitHub Actions permissions

Нужно определить:

- какие workflows запускаются на PR
- каким workflows нужен доступ к contents/pull-requests/check-runs
- есть ли self-hosted runner
- какие права нужны review automation

Нельзя полагаться на неявные дефолты.

### 5. Repository variables

Если workflow использует переключаемые агенты и runtime configuration,
нужно явно завести repository variables.

Пример category:

- review agent selector
- model/provider selector
- environment flags

Идея:

- configuration, влияющая на workflow, не должна жить только в голове оператора

### 6. Repository secrets

Нужно заранее определить, какие secrets нужны для:

- AI review
- CI integrations
- deployment
- staging smoke

Каждый secret должен быть:

- назван явно
- описан
- привязан к конкретному workflow или окружению

### 7. Self-hosted runner или hosted runner policy

Нужно решить:

- достаточно ли GitHub-hosted runner
- нужен ли self-hosted runner
- какие labels будут использовать workflows
- где документируется runner contract

### 8. Pull request settings

Нужно определить:

- нужны ли auto-delete branch
- разрешены ли merge commits / squash / rebase
- включен ли auto-merge
- обязательны ли approvals
- как ведет себя AI review относительно human approval

## Что должна сделать новая система

При переносе workflow новая система должна:

1. описать нужную конфигурацию репозитория
2. сравнить ее с текущими настройками target repo
3. зафиксировать gaps
4. обновить docs и workflows
5. если возможно — настроить репозиторий через GitHub CLI/API
6. если невозможно — выдать точный manual checklist для владельца

## Минимальный результат

После bootstrap GitHub-репозитория должны быть согласованы:

- default branch
- branch protection
- required checks
- Actions permissions
- secrets/variables
- runner policy
- merge policy

