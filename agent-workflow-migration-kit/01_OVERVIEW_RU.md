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
3. Любая работа начинается от текущего `main`.
4. Один implementation worker работает только в одном worktree.
5. Один task slice = одна branch = один PR.
6. Поведенческие и архитектурные изменения сначала фиксируются в docs/specs.
7. Задача не считается завершенной, пока текущий PR head SHA не прошел приемку.

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

Review agent отвечает за:

- автоматизированный review PR
- поиск рисков, регрессий и дыр в контракте

## Что можно адаптировать

Можно менять:

- конкретную нейросеть для implementation
- конкретную нейросеть для review
- конкретный CI provider
- конкретный staging/deploy способ
- конкретные shell scripts

Но нельзя размывать:

- memory split
- isolated execution
- PR loop
- merge-ready definition

