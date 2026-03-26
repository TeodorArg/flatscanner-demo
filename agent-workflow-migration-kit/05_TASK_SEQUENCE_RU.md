# 05. Последовательность задач для другой системы

Ниже порядок задач, который лучше всего воспроизводит workflow в новом проекте.

## Задача 1. Bootstrap repository memory

Цель:

- создать `AGENTS.md`
- создать `CLAUDE.md`
- создать `docs/`
- создать `specs/`
- зафиксировать read order и durable memory model

Prompt:

- `prompts/01_bootstrap_repository_memory.txt`

## Задача 2. Define agent roles and working rules

Цель:

- формализовать роли
- формализовать boundaries
- закрепить completion rules

Prompt:

- `prompts/02_define_agent_roles_and_rules.txt`

## Задача 3. Bootstrap GitHub repository settings

Цель:

- настроить сам GitHub-репозиторий под workflow
- зафиксировать required checks, protection rules, variables/secrets и merge policy

Prompt:

- `prompts/04a_bootstrap_github_repository_settings.txt`

## Задача 4. Add orchestration contract

Цель:

- описать как создавать isolated worktrees
- как выбирать implementation agent
- как публиковать PR

Prompt:

- `prompts/03_add_orchestration_scripts_contract.txt`

## Задача 5. Define CI and AI review loop

Цель:

- ввести required checks
- зафиксировать merge-ready contract

Prompt:

- `prompts/04_define_ci_and_review_loop.txt`

## Задача 6. Define delivery and smoke process

Цель:

- описать test deploy path
- описать smoke process
- связать post-merge и runtime verification

Prompt:

- `prompts/05_define_delivery_and_smoke_flow.txt`

## Задача 7. Conduct one full validation feature

Цель:

- провести один тестовый feature через полный цикл
- убедиться, что workflow реально работает

Prompt:

- `prompts/06_run_first_test_feature_through_full_loop.txt`
