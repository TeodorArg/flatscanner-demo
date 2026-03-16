$ErrorActionPreference = 'Stop'
$script:exitCode = 1
$script:transcriptStarted = $false
$script:tempRoot = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { $env:TEMP }
$script:diagnosticPath = Join-Path $script:tempRoot 'ai-review-diagnostics.log'
$script:transcriptPath = Join-Path $script:tempRoot 'ai-review-transcript.log'

. (Join-Path $PSScriptRoot 'ai-review-policy.ps1')
. (Join-Path $PSScriptRoot 'ai-review-comment.ps1')

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

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command,
        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    Write-Diagnostic "Starting native command: $Description"
    & $Command
    $nativeExitCode = $LASTEXITCODE
    Write-Diagnostic "Completed native command: $Description (exit=$nativeExitCode)"
    if ($nativeExitCode -ne 0) {
        throw "$Description failed with exit code $nativeExitCode."
    }
}

try {
    if (Test-Path $script:diagnosticPath) {
        Remove-Item $script:diagnosticPath -Force
    }
    if (Test-Path $script:transcriptPath) {
        Remove-Item $script:transcriptPath -Force
    }

    New-Item -ItemType File -Path $script:diagnosticPath -Force | Out-Null
    Start-Transcript -Path $script:transcriptPath -Force | Out-Null
    $script:transcriptStarted = $true

    $repoRoot = (Get-Location).Path
    $eventPath = $env:GITHUB_EVENT_PATH
    $githubToken = $env:GITHUB_TOKEN
    $repository = $env:GITHUB_REPOSITORY
    $marker = '<!-- ai-review -->'
    $legacyMarker = '<!-- codex-ai-review -->'
    $agentLabel = 'Codex'

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

    Invoke-NativeCommand -Description "git fetch origin $baseRef" -Command { git fetch --no-tags origin $baseRef }
    Invoke-NativeCommand -Description "git fetch PR head refs/pull/$prNumber/head" -Command { git fetch --no-tags origin "+refs/pull/$prNumber/head:refs/remotes/origin/pr/$prNumber" }

    $changedFiles = git diff --name-only $baseSha $headSha
    $changedFilesBlock = if ($changedFiles) { ($changedFiles -join [Environment]::NewLine) } else { '(no changed files reported)' }

    $runtimePrompt = Join-Path $script:tempRoot 'ai-review-prompt.md'
    $templatePrompt = Join-Path $repoRoot '.github\codex\prompts\pr-review.md'
    $schemaPath = Join-Path $repoRoot '.github\review\schemas\pr-review.schema.json'
    $outputPath = Join-Path $script:tempRoot 'ai-review-output.json'

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
    Write-Diagnostic "Runtime prompt written to $runtimePrompt"

    Write-Diagnostic 'Running local Codex CLI review'
    if (Test-Path $outputPath) {
        Remove-Item $outputPath -Force
        Write-Diagnostic "Removed stale output file $outputPath"
    }

    Get-Content $runtimePrompt -Raw | codex exec - --output-schema $schemaPath --output-last-message $outputPath --sandbox read-only --color never --ephemeral -C $repoRoot
    $codexExitCode = $LASTEXITCODE
    Write-Diagnostic "codex exec completed with exit code $codexExitCode"

    if ($codexExitCode -ne 0) {
        throw "codex exec failed with exit code $codexExitCode."
    }

    if (-not (Test-Path $outputPath)) {
        throw 'AI review did not produce an output file.'
    }

    $outputMetadata = Get-Item $outputPath
    Write-Diagnostic "Codex output file present at $outputPath (size=$($outputMetadata.Length))"

    $result = Get-Content $outputPath -Raw | ConvertFrom-Json
    if (-not $result.summary -or -not $result.verdict) {
        throw 'AI review output is missing required fields.'
    }

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
    $comments = Invoke-RestMethod -Headers $headers -Uri $commentsUrl -Method Get
    $existing = $comments | Where-Object { $_.body -like "*$marker*" -or $_.body -like "*$legacyMarker*" } | Select-Object -First 1
    $commentPayload = ConvertTo-GitHubIssueCommentPayload -Body $body
    Write-Diagnostic "Review comment body length=$($commentPayload.Body.Length); truncated=$($commentPayload.WasTruncated)"

    if ($existing) {
        $updateUrl = "https://api.github.com/repos/$repository/issues/comments/$($existing.id)"
        Write-Diagnostic "Updating existing sticky review comment $($existing.id)"
        Invoke-RestMethod -Headers $headers -Uri $updateUrl -Method Patch -Body $commentPayload.Payload -ContentType 'application/json; charset=utf-8' | Out-Null
    }
    else {
        Write-Diagnostic 'Creating new sticky review comment'
        Invoke-RestMethod -Headers $headers -Uri $commentsUrl -Method Post -Body $commentPayload.Payload -ContentType 'application/json; charset=utf-8' | Out-Null
    }

    if ($outcome.EffectiveVerdict -eq 'request_changes') {
        throw 'AI review requested changes.'
    }

    Write-Diagnostic 'Codex AI review completed successfully'
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
