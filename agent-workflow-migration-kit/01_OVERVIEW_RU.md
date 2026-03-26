# 01. Что именно переносится

## Цель

Нужно воспроизвести не код конкретного продукта, а алгоритм разработки, в
котором:

- знания проекта живут в репозитории
- новая задача всегда проходит через spec/plan/tasks
- implementation выполняется изолированно
- приемка идет через PR, checks и AI review
- завершенной считается только задача, дошедшая до merge-ready состояния

## Обязательные инварианты

Следующие правила нельзя терять при переносе:

1. `docs/` хранит долговременную память проекта.
2. `specs/<feature-id>/` хранит память конкретной задачи.
3. `CLAUDE.md` или эквивалентный файл хранит контракт primary implementation agent.
4. Любая работа начинается от текущего `main`.
5. Один implementation worker работает только в одном worktree.
6. Один task slice = одна branch = один PR.
7. Поведенческие и архитектурные изменения сначала фиксируются в docs/specs.
8. Задача не считается завершенной, пока текущий PR head SHA не прошел приемку.

## Роли

В целевом проекте нужно сохранить 4 роли:

- `User / Owner`
- `Orchestrator`
- `Implementation Agent`
- `Review Agent`

Оркестратор отвечает за:

- чтение repository memory
- постановку задачи
- разбиение на slice
- запуск implementation agent
- PR loop
- merge decision readiness
- post-merge deploy/smoke coordination

Implementation agent отвечает за:

- код
- тесты
- update `tasks.md`
- локальную валидацию
- публикацию PR

Его операционный контракт должен быть зафиксирован в отдельном файле вида
`CLAUDE.md` или в другом явном implementation-agent guide.

Review agent отвечает за:

- автоматизированный review PR
- поиск рисков, регрессий и дыр в контракте

## Что можно адаптировать

Можно менять:

- конкретную нейросеть для implementation
- конкретную нейросеть для review
- конкретный CI provider
- конкретный staging/deploy способ
- конкретные shell scripts и язык локальной automation-обвязки

Но нельзя размывать:

- memory split
- isolated execution
- PR loop
- merge-ready definition

## Важное правило переносимости

Локальные orchestration scripts не являются канонической частью алгоритма.
Каноническим является только их поведение.

Это значит:

- scripts из одной среды не нужно механически копировать в другую
- в новом окружении их нужно написать заново под его OS, shell и toolchain
- для macOS/Linux это могут быть `bash`, `zsh`, `python`, `make`, `just`,
  `task` или другой нативный слой automation

При переносе нужно воспроизводить не синтаксис исходных скриптов, а контракт
действий:

- выбрать implementation agent
- создать isolated branch/worktree
- запустить bounded implementation task
- опубликовать PR
- дожать PR loop до merge-ready
- выполнить post-merge sync/deploy/smoke при необходимости
