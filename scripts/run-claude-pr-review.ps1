$ErrorActionPreference = 'Stop'
$script:exitCode = 1
$script:transcriptStarted = $false
$script:tempRoot = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { $env:TEMP }
$script:diagnosticPath = Join-Path $script:tempRoot 'ai-review-diagnostics.log'
$script:transcriptPath = Join-Path $script:tempRoot 'ai-review-transcript.log'
$script:rawOutputPath = Join-Path $script:tempRoot 'ai-review-raw-output.log'

. (Join-Path $PSScriptRoot 'ai-review-policy.ps1')
. (Join-Path $PSScriptRoot 'claude-review-output.ps1')

function Write-Diagnostic {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    $timestamp = Get-Date -Format 'yyyy-MM-ddTHH:mm:ss.fffK'
    $line = "[$timestamp] $Message"
    Write-Host $line
    Add-Content -Path $script:diagnosticPath -Value $line
}

try {
    if (Test-Path $script:diagnosticPath) {
        Remove-Item $script:diagnosticPath -Force
    }
    if (Test-Path $script:transcriptPath) {
        Remove-Item $script:transcriptPath -Force
    }
    if (Test-Path $script:rawOutputPath) {
        Remove-Item $script:rawOutputPath -Force
    }

    New-Item -ItemType File -Path $script:diagnosticPath -Force | Out-Null
    Start-Transcript -Path $script:transcriptPath -Force | Out-Null
    $script:transcriptStarted = $true

    $repoRoot = (Get-Location).Path
    $eventPath = $env:GITHUB_EVENT_PATH
    $githubToken = $env:GITHUB_TOKEN
    $repository = $env:GITHUB_REPOSITORY
    $marker = '<!-- ai-review -->'
    $agentLabel = 'Claude'
    $claudePath = if ($env:CLAUDE_CLI_PATH) { $env:CLAUDE_CLI_PATH } else { 'C:\Users\User\.local\bin\claude.exe' }

    if (-not (Test-Path $claudePath)) {
        throw "Claude CLI not found at $claudePath"
    }

    if (-not $eventPath -or -not (Test-Path $eventPath)) {
        throw 'GITHUB_EVENT_PATH is missing. This script must run inside GitHub Actions.'
    }

    if (-not $githubToken) {
        throw 'GITHUB_TOKEN is missing.'
    }

    if (-not $repository) {
        throw 'GITHUB_REPOSITORY is missing.'
    }

    Write-Diagnostic "Diagnostics file: $script:diagnosticPath"
    Write-Diagnostic "Repository root: $repoRoot"
    Write-Diagnostic "Selected AI reviewer: $agentLabel"

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

        Write-Diagnostic "Loading PR #$($env:PR_NUMBER) via GitHub API"
        $pullRequest = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$repository/pulls/$($env:PR_NUMBER)"
    }

    $prNumber = [string]$pullRequest.number
    $baseRef = [string]$pullRequest.base.ref
    $headRef = [string]$pullRequest.head.ref
    $baseSha = [string]$pullRequest.base.sha
    $headSha = [string]$pullRequest.head.sha

    Write-Diagnostic "Preparing review context for PR #$prNumber ($baseSha..$headSha)"

    git fetch --no-tags origin $baseRef
    if ($LASTEXITCODE -ne 0) {
        throw "git fetch origin $baseRef failed with exit code $LASTEXITCODE."
    }

    git fetch --no-tags origin "+refs/pull/$prNumber/head:refs/remotes/origin/pr/$prNumber"
    if ($LASTEXITCODE -ne 0) {
        throw "git fetch PR head refs/pull/$prNumber/head failed with exit code $LASTEXITCODE."
    }

    $changedFiles = git diff --name-only $baseSha $headSha
    $changedFilesBlock = if ($changedFiles) { ($changedFiles -join [Environment]::NewLine) } else { '(no changed files reported)' }
    $diffBlock = git diff --unified=3 $baseSha $headSha
    if (-not $diffBlock) {
        $diffBlock = '(no diff reported)'
    }

    $contextFiles = @(
        '.specify/memory/constitution.md',
        'docs/README.md',
        'docs/project-idea.md',
        'docs/project/frontend/frontend-docs.md',
        'docs/project/backend/backend-docs.md'
    )

    $adrFiles = Get-ChildItem (Join-Path $repoRoot 'docs\adr') -Filter '*.md' | Sort-Object Name | ForEach-Object {
        $_.FullName.Substring($repoRoot.Length + 1)
    }

    $specFiles = @()
    if ($changedFiles) {
        $specFiles = $changedFiles | Where-Object { $_ -like 'specs/*/spec.md' -or $_ -like 'specs/*/plan.md' -or $_ -like 'specs/*/tasks.md' }
    }

    $governingFiles = @($contextFiles + $adrFiles + $specFiles) | Where-Object { $_ } | Select-Object -Unique
    $contextBlocks = foreach ($relativePath in $governingFiles) {
        $normalizedPath = $relativePath -replace '^[.][\\/]', ''
        $fullPath = Join-Path $repoRoot $normalizedPath
        if (Test-Path $fullPath) {
            @(
                "### File: $normalizedPath",
                (Get-Content $fullPath -Raw)
            ) -join [Environment]::NewLine
        }
    }
    $contextBlock = if ($contextBlocks) { $contextBlocks -join ([Environment]::NewLine + [Environment]::NewLine) } else { 'No governing context files were loaded.' }

    $runtimePrompt = Join-Path $script:tempRoot 'claude-review-prompt.md'
    $templatePrompt = Join-Path $repoRoot '.github\claude\prompts\pr-review.md'
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

## Governing Context

$contextBlock

## Unified Diff

$diffBlock
"@
    Set-Content -Path $runtimePrompt -Value ($template + $runtimeSection)
    Write-Diagnostic "Runtime prompt written to $runtimePrompt"

    $promptText = (Get-Content $runtimePrompt -Raw).Trim()

    Write-Diagnostic 'Running local Claude CLI review'
    # Claude CLI expects the literal string '""' to disable tools in print mode on Windows.
    $noTools = '""'
    $resultText = $promptText | & $claudePath -p --output-format text --permission-mode default --tools $noTools
    $claudeExitCode = $LASTEXITCODE
    Write-Diagnostic "claude review completed with exit code $claudeExitCode"

    if ($claudeExitCode -ne 0) {
        throw "Claude CLI review failed with exit code $claudeExitCode."
    }

    Set-Content -Path $script:rawOutputPath -Value $resultText
    Write-Diagnostic "Raw Claude output saved to $script:rawOutputPath"
    Write-Diagnostic ("Claude output preview: " + (Get-ClaudeReviewOutputPreview -Text $resultText))

    $parsedOutput = ConvertFrom-ClaudeReviewOutput -RawText $resultText
    $result = $parsedOutput.Result

    foreach ($note in @($parsedOutput.NormalizationNotes)) {
        Write-Diagnostic $note
    }

    Assert-ClaudeReviewResultContract -Result $result

    $outcome = Resolve-AiReviewOutcome -Result $result
    $findings = $outcome.Findings

    if ($outcome.PolicyNote) {
        Write-Diagnostic $outcome.PolicyNote
    }

    Write-Diagnostic "Review verdict=$($result.verdict); effectiveVerdict=$($outcome.EffectiveVerdict); findings=$($findings.Count)"

    $verdictLabel = switch ($outcome.EffectiveVerdict) {
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
## AI Review

Agent: **$agentLabel**
Verdict: **$verdictLabel**
$(
    if ($outcome.PolicyNote) {
        "`r`n$($outcome.PolicyNote)"
    }
)

### Summary
$($result.summary)

### Findings
$findingsBlock
"@

    $commentsUrl = "https://api.github.com/repos/$repository/issues/$prNumber/comments"
    $legacyMarker = '<!-- codex-ai-review -->'
    $comments = Invoke-RestMethod -Headers $headers -Uri $commentsUrl -Method Get
    $existing = $comments | Where-Object { $_.body -like "*$marker*" -or $_.body -like "*$legacyMarker*" } | Select-Object -First 1
    $payload = @{ body = $body } | ConvertTo-Json

    if ($existing) {
        $updateUrl = "https://api.github.com/repos/$repository/issues/comments/$($existing.id)"
        Write-Diagnostic "Updating existing sticky review comment $($existing.id)"
        Invoke-RestMethod -Headers $headers -Uri $updateUrl -Method Patch -Body $payload | Out-Null
    }
    else {
        Write-Diagnostic 'Creating new sticky review comment'
        Invoke-RestMethod -Headers $headers -Uri $commentsUrl -Method Post -Body $payload | Out-Null
    }

    if ($outcome.EffectiveVerdict -eq 'request_changes') {
        throw 'AI review requested changes.'
    }

    Write-Diagnostic 'Claude AI review completed successfully'
    $script:exitCode = 0
}
catch {
    Write-Diagnostic "Failure: $($_.Exception.Message)"
    throw
}
finally {
    Write-Diagnostic "Exiting review script with code $script:exitCode"
    if ($script:transcriptStarted) {
        Stop-Transcript | Out-Null
    }
    exit $script:exitCode
}
