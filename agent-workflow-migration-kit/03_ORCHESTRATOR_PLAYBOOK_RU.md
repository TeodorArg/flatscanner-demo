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
3. Убедиться, что implementation agent имеет явный contract file (`CLAUDE.md` или эквивалент).
4. Решить, новая это фича или продолжение текущей.
5. Создать или обновить `spec.md`, `plan.md`, `tasks.md`.
6. Выделить небольшой implementation slice.
7. Проверить текущий `main`.
8. Создать isolated branch/worktree.
9. Выбрать implementation agent.
10. Передать ему конкретный bounded task.
11. Проверить результат локально.
12. Убедиться, что tasks/docs/specs обновлены.
13. Открыть PR.
14. Следить за CI и AI review.
15. Если есть findings, вести fixes на той же ветке.
16. Повторять loop до merge-ready.
17. Смёржить.
18. Синхронизировать `main`.
19. Если задача затрагивает runtime — выполнить deploy и smoke.

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
