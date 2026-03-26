# 03. Playbook оркестратора

## Роль оркестратора

Оркестратор — это не просто агент, который пишет код. Его задача:

- держать в голове целостность процесса
- читать repository memory
- резать работу на небольшие slices
- следить за PR loop
- не допускать незавершенных полу-состояний

## Алгоритм работы по шагам

1. Получить задачу от пользователя.
2. Прочитать memory в установленном read order.
3. Решить, новая это фича или продолжение текущей.
4. Создать или обновить `spec.md`, `plan.md`, `tasks.md`.
5. Выделить небольшой implementation slice.
6. Проверить текущий `main`.
7. Создать isolated branch/worktree.
8. Выбрать implementation agent.
9. Передать ему конкретный bounded task.
10. Проверить результат локально.
11. Убедиться, что tasks/docs/specs обновлены.
12. Открыть PR.
13. Следить за CI и AI review.
14. Если есть findings, вести fixes на той же ветке.
15. Повторять loop до merge-ready.
16. Смёржить.
17. Синхронизировать `main`.
18. Если задача затрагивает runtime — выполнить deploy и smoke.

## OS-agnostic правило для orchestration scripts

Оркестратор не должен требовать буквального воспроизведения локальных скриптов
из другой среды.

Он должен требовать воспроизведения следующих возможностей:

- `set current implementation agent`
- `create isolated task branch/worktree`
- `start implementation worker`
- `publish branch and PR`
- `run or observe PR review loop`
- `sync main after merge`

Если новая среда использует:

- `bash` вместо PowerShell
- `zsh` вместо `bash`
- `python` launcher вместо shell scripts
- `make`/`just`/`task` вместо прямых команд

это допустимо, пока behavior contract сохранен.

## Чего оркестратор не должен делать

- не должен работать из старой feature branch
- не должен смешивать несколько coding agents в одном worktree
- не должен объявлять задачу завершенной при статусе `checks running`
- не должен держать критичный контекст только в памяти диалога
- не должен пропускать update `tasks.md`
- не должен навязывать Windows-specific automation в Unix-like среде

## Что оркестратор обязан фиксировать

- архитектурные решения — в `docs/` или `docs/adr/`
- task intent — в `spec.md`
- implementation approach — в `plan.md`
- execution state — в `tasks.md`
- follow-up work — в том же feature folder или в новом feature spec
