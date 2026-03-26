# Migration Kit: перенос AI-assisted workflow в новый проект

Этот набор файлов нужен для переноса workflow разработки в другой проект и в
другую агентскую систему без привязки к текущему продукту.

В kit входят:

- `01_OVERVIEW_RU.md` — что именно переносится и какие инварианты обязательны
- `02_ADOPTION_PLAN_RU.md` — пошаговый план внедрения в новый проект
- `03_ORCHESTRATOR_PLAYBOOK_RU.md` — как должен работать оркестратор
- `04_DELIVERY_PLAYBOOK_RU.md` — как вести приемку, деплой и smoke
- `05_TASK_SEQUENCE_RU.md` — порядок задач для переноса
- `06_AGENT_SYSTEM_MAPPING_RU.md` — как переложить workflow на другую агентную систему
- `07_GITHUB_REPOSITORY_BOOTSTRAP_RU.md` — как настроить сам GitHub-репозиторий под workflow
- `prompts/` — готовые тексты задач для другой нейросети
- `templates/` — шаблоны файлов и папок
- `checklists/` — контрольные списки по фазам процесса

## Что переносится

Переносится не продуктовый код, а framework разработки:

- repository memory через `docs/` и `specs/`
- spec-first execution
- роли оркестратора, implementation agent и review agent
- isolated worktrees
- обязательный PR loop
- приемка через CI и AI review
- post-merge deploy + smoke на тестовой среде

## Что не переносится

- код текущего продукта
- текущие продуктовые интеграции
- текущие provider-specific детали
- брендинг и имя исходного проекта

## Как использовать kit

1. Создайте новый репозиторий или откройте существующий целевой проект.
2. Дайте новой системе доступ к этой папке целиком.
3. Сначала дайте ей prompt:
   - `prompts/00_read_the_kit_first.txt`
4. Затем попросите ее прочитать:
   - `01_OVERVIEW_RU.md`
   - `02_ADOPTION_PLAN_RU.md`
   - `07_GITHUB_REPOSITORY_BOOTSTRAP_RU.md`
   - `05_TASK_SEQUENCE_RU.md`
5. Затем по очереди копируйте задачи из `prompts/` в диалог.
6. После каждой задачи требуйте:
   - update specs/tasks
   - локальную валидацию
   - PR loop до merge-ready

## Рекомендуемый порядок запуска prompts

1. `prompts/00_read_the_kit_first.txt`
2. `prompts/01_bootstrap_repository_memory.txt`
3. `prompts/02_define_agent_roles_and_rules.txt`
4. `prompts/04a_bootstrap_github_repository_settings.txt`
5. `prompts/03_add_orchestration_scripts_contract.txt`
6. `prompts/04_define_ci_and_review_loop.txt`
7. `prompts/05_define_delivery_and_smoke_flow.txt`
8. `prompts/06_run_first_test_feature_through_full_loop.txt`

## Минимальный ожидаемый результат внедрения

После прохождения всех шагов в новом проекте должны появиться:

- `AGENTS.md`
- `.specify/` или эквивалентный слой process templates
- `docs/` как durable memory
- `specs/` как task memory
- scripts/playbooks для isolated execution
- CI и AI review loop
- GitHub repository settings, согласованные с workflow
- documented delivery flow до тестового сервера
