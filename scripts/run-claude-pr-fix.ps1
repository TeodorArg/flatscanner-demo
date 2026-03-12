$ErrorActionPreference = 'Stop'

$repoRoot = (Get-Location).Path
$eventPath = $env:GITHUB_EVENT_PATH
$githubToken = $env:GITHUB_TOKEN
$repository = $env:GITHUB_REPOSITORY
$marker = '<!-- claude-pr-fix -->'
$claudePath = 'C:\Users\User\.local\bin\claude.exe'

if (-not (Test-Path $claudePath)) {
    throw "Claude CLI not found at $claudePath"
}

if (-not $eventPath -or -not (Test-Path $eventPath)) {
    throw 'GITHUB_EVENT_PATH is missing. This script must run inside GitHub Actions.'
}

$event = Get-Content $eventPath -Raw | ConvertFrom-Json
$prNumber = $env:PR_NUMBER
$headRef = $env:PR_HEAD_REF
$baseRef = $env:PR_BASE_REF

if (-not $prNumber) {
    throw 'PR_NUMBER is missing.'
}

if (-not $githubToken) {
    throw 'GITHUB_TOKEN is missing.'
}

$headers = @{
    Authorization = "Bearer $githubToken"
    Accept = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2022-11-28'
}

$pr = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$repository/pulls/$prNumber"
$issueComments = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$repository/issues/$prNumber/comments"
$reviewComments = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$repository/pulls/$prNumber/comments"

$codexReview = $issueComments | Where-Object { $_.body -like '*<!-- codex-ai-review -->*' } | Select-Object -Last 1
$humanIssueComments = $issueComments | Where-Object { $_.body -notlike '*<!-- codex-ai-review -->*' -and $_.body -notlike '*<!-- claude-pr-fix -->*' }

$changedFiles = git diff --name-only "origin/$baseRef...HEAD"
$changedFilesBlock = if ($changedFiles) { ($changedFiles -join [Environment]::NewLine) } else { '(no changed files reported)' }

$promptTemplate = Get-Content (Join-Path $repoRoot '.github\claude\prompts\pr-fix.md') -Raw
$runtimePrompt = Join-Path $env:RUNNER_TEMP 'claude-pr-fix-prompt.md'
$outputPath = Join-Path $env:RUNNER_TEMP 'claude-pr-fix-output.json'

$codexBlock = if ($codexReview) { $codexReview.body } else { 'No Codex review comment found.' }
$humanIssueBlock = if ($humanIssueComments) { ($humanIssueComments | ForEach-Object { "- @$($_.user.login):`n$($_.body)" }) -join ([Environment]::NewLine + [Environment]::NewLine) } else { 'No additional issue comments.' }
$reviewCommentBlock = if ($reviewComments) { ($reviewComments | ForEach-Object { "- @$($_.user.login) on $($_.path):`n$($_.body)" }) -join ([Environment]::NewLine + [Environment]::NewLine) } else { 'No inline review comments.' }

$runtimeSection = @"

## Runtime PR Context

- Repository: $repository
- PR number: $prNumber
- PR title: $($pr.title)
- Head ref: $($pr.head.ref)
- Base ref: $($pr.base.ref)

### Changed Files
$changedFilesBlock

### Sticky Codex Review Comment
$codexBlock

### Issue Comments
$humanIssueBlock

### Inline Review Comments
$reviewCommentBlock
"@
Set-Content -Path $runtimePrompt -Value ($promptTemplate + $runtimeSection)

$schema = '{"type":"object","additionalProperties":false,"required":["summary","tests","follow_up"],"properties":{"summary":{"type":"string"},"tests":{"type":"string"},"follow_up":{"type":"string"}}}'

Write-Host "Running Claude CLI for PR #$prNumber"
Get-Content $runtimePrompt -Raw | & $claudePath -p --output-format json --json-schema $schema --permission-mode bypassPermissions --allowedTools Bash,Glob,Grep,Read,Edit,Write --verbose | Tee-Object -FilePath $outputPath.stdout | Out-Null

$jsonLine = Select-String -Path $outputPath.stdout -Pattern '"type":"result"' | Select-Object -Last 1
if (-not $jsonLine) {
    throw 'Claude CLI did not emit a result payload.'
}

$resultEnvelope = $jsonLine.Line | ConvertFrom-Json
$resultText = [string]$resultEnvelope.result
if (-not $resultText) {
    throw 'Claude CLI result payload was empty.'
}

$result = $resultText | ConvertFrom-Json

git config user.name 'Claude Code'
git config user.email 'claude-code@users.noreply.github.com'

$hasChanges = (git status --porcelain)
if ($hasChanges) {
    git add -A
    git commit -m 'Address PR review findings'
    git push origin HEAD:$headRef
    $changeSummary = 'Claude pushed follow-up commits to this PR branch.'
}
else {
    $changeSummary = 'Claude did not produce any file changes for this PR branch.'
}

$body = @"
$marker
## Claude PR Fix Run

$changeSummary

### Summary
$($result.summary)

### Tests
$($result.tests)

### Follow-Up
$($result.follow_up)
"@

$commentsUrl = "https://api.github.com/repos/$repository/issues/$prNumber/comments"
$existing = $issueComments | Where-Object { $_.body -like "*$marker*" } | Select-Object -Last 1
$payload = @{ body = $body } | ConvertTo-Json

if ($existing) {
    $updateUrl = "https://api.github.com/repos/$repository/issues/comments/$($existing.id)"
    Invoke-RestMethod -Headers $headers -Uri $updateUrl -Method Patch -Body $payload | Out-Null
}
else {
    Invoke-RestMethod -Headers $headers -Uri $commentsUrl -Method Post -Body $payload | Out-Null
}

if ($env:TRIGGER_LABEL -eq 'claude-fix') {
    try {
        Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$repository/issues/$prNumber/labels/claude-fix" -Method Delete | Out-Null
    }
    catch {
        Write-Warning 'Unable to remove claude-fix label after run.'
    }
}
