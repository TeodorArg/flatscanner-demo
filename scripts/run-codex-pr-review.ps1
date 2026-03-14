$ErrorActionPreference = 'Stop'

$repoRoot = (Get-Location).Path
$eventPath = $env:GITHUB_EVENT_PATH
$githubToken = $env:GITHUB_TOKEN
$repository = $env:GITHUB_REPOSITORY
$marker = '<!-- codex-ai-review -->'

if (-not $eventPath -or -not (Test-Path $eventPath)) {
    throw 'GITHUB_EVENT_PATH is missing. This script must run inside GitHub Actions.'
}

if (-not $githubToken) {
    throw 'GITHUB_TOKEN is missing.'
}

if (-not $repository) {
    throw 'GITHUB_REPOSITORY is missing.'
}

$event = Get-Content $eventPath -Raw | ConvertFrom-Json
$pullRequest = $event.pull_request

$headers = @{
    Authorization = "Bearer $githubToken"
    Accept = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2022-11-28'
}

if (-not $pullRequest) {
    if (-not $env:PR_NUMBER) {
        throw 'This workflow expects a pull_request event or PR_NUMBER when dispatched manually.'
    }

    $pullRequest = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$repository/pulls/$($env:PR_NUMBER)"
}

$prNumber = [string]$pullRequest.number
$baseRef = [string]$pullRequest.base.ref
$headRef = [string]$pullRequest.head.ref
$baseSha = [string]$pullRequest.base.sha
$headSha = [string]$pullRequest.head.sha

Write-Host "Preparing review context for PR #$prNumber"

git fetch --no-tags origin $baseRef
git fetch --no-tags origin "+refs/pull/$prNumber/head:refs/remotes/origin/pr/$prNumber"

$changedFiles = git diff --name-only $baseSha $headSha
$changedFilesBlock = if ($changedFiles) { ($changedFiles -join [Environment]::NewLine) } else { '(no changed files reported)' }

$runtimePrompt = Join-Path $env:RUNNER_TEMP 'codex-review-prompt.md'
$templatePrompt = Join-Path $repoRoot '.github\codex\prompts\pr-review.md'
$schemaPath = Join-Path $repoRoot '.github\codex\schemas\pr-review.schema.json'
$outputPath = Join-Path $env:RUNNER_TEMP 'codex-review-output.json'

$template = Get-Content $templatePrompt -Raw
$runtimeSection = @"

## Runtime PR Context

- Repository: $repository
- PR number: $prNumber
- Base ref: $baseRef
- Head ref: $headRef
- Base SHA: $baseSha
- Head SHA: $headSha
- PR title: $($pullRequest.title)

### Changed Files
$changedFilesBlock

Review the git diff between $baseSha and $headSha only, but use the repository docs and specs as governing context.
You may inspect repository files and run read-only git commands if needed.
"@
Set-Content -Path $runtimePrompt -Value ($template + $runtimeSection)

Write-Host 'Running local Codex CLI review'
Get-Content $runtimePrompt -Raw | codex exec - --output-schema $schemaPath --output-last-message $outputPath --sandbox read-only --color never --ephemeral -C $repoRoot

if (-not (Test-Path $outputPath)) {
    throw 'Codex review did not produce an output file.'
}

$result = Get-Content $outputPath -Raw | ConvertFrom-Json
if (-not $result.summary -or -not $result.verdict) {
    throw 'Codex review output is missing required fields.'
}

$findings = @()
if ($result.findings) {
    $findings = @($result.findings)
}

$verdictLabel = switch ($result.verdict) {
    'approve' { 'Approve' }
    'comment' { 'Comment' }
    'request_changes' { 'Request changes' }
    default { 'Comment' }
}

if ($findings.Count -gt 0) {
    $index = 0
    $findingsBlock = ($findings | ForEach-Object {
        $index += 1
        $location = if ($_.line) { "$($_.file):$($_.line)" } else { [string]$_.file }
        @(
            "$index. [$($_.severity)] $($_.title)",
            "Location: $location",
            [string]$_.body
        ) -join [Environment]::NewLine
    }) -join ([Environment]::NewLine + [Environment]::NewLine)
}
else {
    $findingsBlock = 'No review findings.'
}

$body = @"
$marker
## Codex AI Review

Verdict: **$verdictLabel**

### Summary
$($result.summary)

### Findings
$findingsBlock
"@

$commentsUrl = "https://api.github.com/repos/$repository/issues/$prNumber/comments"
$comments = Invoke-RestMethod -Headers $headers -Uri $commentsUrl -Method Get
$existing = $comments | Where-Object { $_.body -like "*$marker*" } | Select-Object -First 1
$payload = @{ body = $body } | ConvertTo-Json

if ($existing) {
    $updateUrl = "https://api.github.com/repos/$repository/issues/comments/$($existing.id)"
    Invoke-RestMethod -Headers $headers -Uri $updateUrl -Method Patch -Body $payload | Out-Null
}
else {
    Invoke-RestMethod -Headers $headers -Uri $commentsUrl -Method Post -Body $payload | Out-Null
}

if ($result.verdict -eq 'request_changes') {
    throw 'Codex review requested changes.'
}
