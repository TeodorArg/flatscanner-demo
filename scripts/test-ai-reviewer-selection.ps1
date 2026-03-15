$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$selectorPath = Join-Path $repoRoot 'scripts\run-ai-pr-review.ps1'
$cases = @(
    @{ Name = 'claude'; Value = 'claude'; Expected = '.\scripts\run-claude-pr-review.ps1' },
    @{ Name = 'codex'; Value = 'codex'; Expected = '.\scripts\run-codex-pr-review.ps1' },
    @{ Name = 'invalid'; Value = 'invalid-agent'; Expected = '.\scripts\run-claude-pr-review.ps1' },
    @{ Name = 'missing'; Value = $null; Expected = '.\scripts\run-claude-pr-review.ps1' }
)

foreach ($case in $cases) {
    $envSetup = if ($null -eq $case.Value) {
        "Remove-Item Env:AI_REVIEW_AGENT -ErrorAction SilentlyContinue"
    }
    else {
        "`$env:AI_REVIEW_AGENT='$($case.Value)'"
    }

    $output = & powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command @"
`$env:AI_REVIEW_DRY_RUN='1'
$envSetup
& '$selectorPath'
"@ 2>&1

    if ($LASTEXITCODE -ne 0) {
        throw "Selector dry-run failed for $($case.Name)"
    }

    $outputText = ($output | Out-String)
    if ($outputText -notmatch [regex]::Escape($case.Expected)) {
        throw "Selector dry-run for $($case.Name) did not resolve $($case.Expected). Output: $outputText"
    }
}

Write-Output 'PASS test-ai-reviewer-selection.ps1'
