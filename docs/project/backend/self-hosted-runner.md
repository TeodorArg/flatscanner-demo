# Self-Hosted Codex Review Setup

This repository expects automated PR review to run on a Windows self-hosted GitHub Actions runner labeled `codex`.

## One-Time Runner Setup

1. In GitHub, open repository settings and create a new self-hosted runner for Windows.
2. Copy the registration token shown by GitHub.
3. Run:
   `powershell -ExecutionPolicy Bypass -File .\scripts\setup-self-hosted-runner.ps1 -RepoUrl https://github.com/alexgoodman53/flatscanner -RegistrationToken <token> -AsService`
4. Confirm the runner appears online in GitHub with labels `self-hosted`, `windows`, and `codex`.

## Local Codex Requirements

- Install the official CLI with `npm install -g @openai/codex`
- Make sure `codex login status` works for the same Windows user that runs the GitHub runner
- If the runner is installed as a service, run that service under the same Windows user profile that owns `C:\Users\User\.codex\auth.json`, or configure an equivalent authenticated `CODEX_HOME`

## Review Flow

- A new pull request triggers `.github/workflows/ai-review.yml`
- GitHub schedules the job on the self-hosted runner
- The runner executes `scripts\run-codex-pr-review.ps1`
- That script builds review context, calls local `codex exec` with the repository review schema, posts a sticky PR comment, and fails the job when verdict is `request_changes`

## Required GitHub Branch Protection

- Protect `main`
- Require pull requests before merge
- Require status checks `CI`, `PR Guard`, and `AI Review`
- Require at least one human approval
- Restrict direct pushes to `main`
