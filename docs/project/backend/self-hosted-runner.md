# Self-Hosted AI Review Setup

Automated review runs on a self-hosted GitHub Actions runner labeled
`ai-runner`.

Runner operating system is selected through the repo variable
`AI_REVIEW_RUNNER`.

Supported values:

- `windows`
- `macOS`

Set it through the canonical init script:

- `powershell -ExecutionPolicy Bypass -File .\scripts\set-review-runner.ps1 -Runner windows`
- `pwsh -File ./scripts/set-review-runner.ps1 -Runner macOS`

## Setup

### Windows Runner Path

1. Create a Windows self-hosted runner in GitHub.
2. Register it with:
   `powershell -ExecutionPolicy Bypass -File .\scripts\setup-self-hosted-runner.ps1 -RepoUrl https://github.com/alexgoodman53/flatscanner -RegistrationToken <token> -AsService`
3. Confirm labels `self-hosted`, `windows`, and `ai-runner`.
4. Confirm `pwsh` is available on the runner host for workflow steps that use
   PowerShell 7.

### macOS Runner Path

1. Create a macOS self-hosted runner in GitHub.
2. Follow the repository runner setup steps shown by GitHub for macOS:
   - download the runner package
   - extract it into a local runner directory
   - run the generated `config.sh` with the repository URL and registration token
3. Install the runner as a service:
   - `./svc.sh install`
   - `./svc.sh start`
4. Confirm labels `self-hosted`, `macOS`, and `ai-runner`.
5. Confirm `pwsh` is installed and available on the runner host.

For older runners still using `codex`, apply:

`powershell -ExecutionPolicy Bypass -File .\scripts\add-ai-runner-label.ps1`

Use `-RemoveLegacyCodexLabel` only after all workflows have moved off the old label.

## Reviewer Selection

- Reviewer choice comes only from repo variable `AI_REVIEW_AGENT`.
- Runner choice comes only from repo variable `AI_REVIEW_RUNNER`.
- Supported values: `claude`, `codex`.
- Missing or invalid values fall back to `claude`.
- Example:
  `gh variable set AI_REVIEW_AGENT --body claude --repo alexgoodman53/flatscanner`
- Example runner choice:
  `gh variable set AI_REVIEW_RUNNER --body macOS --repo alexgoodman53/flatscanner`

## Local CLI Requirements

- PowerShell 7 (`pwsh`) must be available on the runner host because the
  review workflows use `shell: pwsh`.
- Codex: authenticated CLI for the same Windows user that runs the runner.
- Claude: non-interactive CLI access; default path is `C:\Users\User\.local\bin\claude.exe`.
- Override Claude path with repo variable `CLAUDE_CLI_PATH` when needed.

## Review Flow

- `.github/workflows/ai-review.yml` resolves runner labels from
  `AI_REVIEW_RUNNER` and reviewer choice from `AI_REVIEW_AGENT`.
- The selector calls either the Claude or Codex adapter.
- The adapter posts one sticky `<!-- ai-review -->` PR comment and fails only on effective `request_changes`.
- Review comments are sanitized, UTF-8 encoded, and truncated before posting so unusual model output does not fail the GitHub comment API path.
- The workflow always prints per-run diagnostics, transcript, and raw-output logs.
- The Claude parser accepts the observed compatible aliases `action`, `review_status`, and `review_action` for `verdict`, but still rejects invalid payloads.

## Required GitHub Settings

- Protect `main`
- require pull requests before merge
- require status checks `baseline-checks`, `guard`, `AI Review`
- require at least one human approval
- restrict direct pushes to `main`

Helper:

`powershell -ExecutionPolicy Bypass -File .\scripts\set-required-ai-review-check.ps1`
