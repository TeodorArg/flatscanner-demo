$ErrorActionPreference = 'Stop'
$tempRoot = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { $env:TEMP }
$rawOutputPath = Join-Path $tempRoot 'ai-review-raw-output.log'

if (Test-Path $rawOutputPath) {
    Remove-Item $rawOutputPath -Force
}

$requestedAgent = ''
if ($env:AI_REVIEW_AGENT) {
    $requestedAgent = $env:AI_REVIEW_AGENT.Trim().ToLowerInvariant()
}

$selectedAgent = switch ($requestedAgent) {
    'codex' { 'codex' }
    'claude' { 'claude' }
    default { 'claude' }
}

if ($selectedAgent -ne $requestedAgent) {
    if ([string]::IsNullOrWhiteSpace($requestedAgent)) {
        Write-Host 'AI_REVIEW_AGENT is not set; defaulting to claude.'
    }
    else {
        Write-Host "AI_REVIEW_AGENT='$requestedAgent' is invalid; defaulting to claude."
    }
}
else {
    Write-Host "AI_REVIEW_AGENT resolved to '$selectedAgent'."
}

$env:AI_REVIEW_SELECTED_AGENT = $selectedAgent
$scriptPath = switch ($selectedAgent) {
    'codex' { '.\scripts\run-codex-pr-review.ps1' }
    'claude' { '.\scripts\run-claude-pr-review.ps1' }
}

if ($env:AI_REVIEW_DRY_RUN -eq '1') {
    Write-Host "Dry run selected review script: $scriptPath"
    exit 0
}

& $scriptPath
exit $LASTEXITCODE
