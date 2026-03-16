# Self-Hosted AI Review Setup

This repository expects automated PR review to run on a Windows self-hosted GitHub Actions runner labeled `ai-runner`.

## One-Time Runner Setup

1. In GitHub, open repository settings and create a new self-hosted runner for Windows.
2. Copy the registration token shown by GitHub.
3. Run:
   `powershell -ExecutionPolicy Bypass -File .\scripts\setup-self-hosted-runner.ps1 -RepoUrl https://github.com/alexgoodman53/flatscanner -RegistrationToken <token> -AsService`
4. Confirm the runner appears online in GitHub with labels `self-hosted`, `windows`, and `ai-runner`.

## Runner Label Migration

- Existing runners created before the neutral-label migration may still have the historical `codex` label
- Apply the repository-local migration helper before switching workflow `runs-on` targets:
  `powershell -ExecutionPolicy Bypass -File .\scripts\add-ai-runner-label.ps1`
- The helper defaults `-RunnerName` to the current Windows hostname; pass `-RunnerName <github-runner-name>` if the registered GitHub runner uses a different name
- By default the helper keeps the legacy `codex` label during the transition window
- Use `-RemoveLegacyCodexLabel` only when you are ready for the runner to stop satisfying legacy `codex` workflow labels

## Reviewer Selection

- Automated PR review is selected only through the repository variable `AI_REVIEW_AGENT`
- Supported values are `claude` and `codex`
- If `AI_REVIEW_AGENT` is missing or invalid, the workflow falls back to `claude`
- Set the repository variable with GitHub CLI, for example:
  `gh variable set AI_REVIEW_AGENT --body claude --repo alexgoodman53/flatscanner`

## Local Codex Requirements

- Install the official CLI with `npm install -g @openai/codex`
- Make sure `codex login status` works for the same Windows user that runs the GitHub runner
- If the runner is installed as a service, run that service under the same Windows user profile that owns `C:\Users\User\.codex\auth.json`, or configure an equivalent authenticated `CODEX_HOME`

## Local Claude Requirements

- Install Claude Code CLI on the runner host
- Make sure the runner user can execute Claude non-interactively
- By default, the repository scripts expect `C:\Users\User\.local\bin\claude.exe`
- If Claude is installed elsewhere, set the repository variable `CLAUDE_CLI_PATH` to the full executable path
- The Claude review adapter runs with `--permission-mode default` and `--tools '""'` so PR review stays non-editing and tool-free

## Review Flow

- A new pull request triggers `.github/workflows/ai-review.yml`
- GitHub schedules the job on the self-hosted runner
- The workflow passes `AI_REVIEW_AGENT` to `scripts\run-ai-pr-review.ps1`
- That selector script chooses `scripts\run-claude-pr-review.ps1` or `scripts\run-codex-pr-review.ps1`
- The selected adapter builds review context, calls the local CLI, posts one sticky PR comment marked `<!-- ai-review -->`, and fails the job when verdict is `request_changes`
- The workflow invokes the script with `powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File ...` to avoid inline shell exit-code ambiguity
- After every run, the workflow prints `ai-review-diagnostics.log` and `ai-review-transcript.log` from the runner temp directory so success-path and failure-path behavior are visible in the GitHub job logs
- The review script recreates those temp files on each run so the printed diagnostics always match the current PR attempt

## Required GitHub Branch Protection

- Migration note:
  If this repository is upgrading from the earlier `codex-review` job name, update the required status check to `AI Review` before merging the workflow change.
- Example:
  `gh api --method PATCH repos/alexgoodman53/flatscanner/branches/main/protection/required_status_checks --input -`
  with body `{"strict":true,"contexts":["baseline-checks","guard","AI Review"]}`
- Repository helper:
  `powershell -ExecutionPolicy Bypass -File .\scripts\set-required-ai-review-check.ps1`
- Runner-label helper:
  `powershell -ExecutionPolicy Bypass -File .\scripts\add-ai-runner-label.ps1`
- Protect `main`
- Require pull requests before merge
- Require status checks `baseline-checks`, `guard`, and `AI Review`
- Require at least one human approval
- Restrict direct pushes to `main`
