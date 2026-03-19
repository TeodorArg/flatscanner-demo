$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$dispatcherPath = Join-Path $repoRoot 'scripts\start-implementation-worker.ps1'
$setAgentPath = Join-Path $repoRoot 'scripts\set-implementation-agent.ps1'
$agentFile = Join-Path $repoRoot '.codex\implementation-agent'
$codexDir = Join-Path $repoRoot '.codex'

$passed = 0
$failed = 0

function Invoke-DispatchDryRun {
    param([string]$AgentFileValue)

    # Write a temp helper script to set up the agent file then call the dispatcher
    $tempScript = [System.IO.Path]::GetTempFileName() + '.ps1'
    try {
        if ($null -eq $AgentFileValue) {
            $setup = "if (Test-Path '$($agentFile -replace `"'`", `"''`")') { Remove-Item '$($agentFile -replace `"'`", `"''`")' -Force }"
        }
        else {
            $setup = @"
New-Item -ItemType Directory -Force -Path '$($codexDir -replace "'", "''")' | Out-Null
Set-Content -Path '$($agentFile -replace "'", "''")' -Value '$AgentFileValue' -NoNewline
"@
        }

        $scriptBody = @"
$setup
Set-Location '$($repoRoot -replace "'", "''")'
& '$($dispatcherPath -replace "'", "''")' -FeatureFolder '014-implementation-agent-switcher' -TaskSummary 'test' -WorktreePath '$($repoRoot -replace "'", "''")' -PromptOnly 2>&1
"@
        Set-Content -Path $tempScript -Value $scriptBody
        $output = & powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $tempScript 2>&1
        return ($output | Out-String)
    }
    finally {
        Remove-Item $tempScript -Force -ErrorAction SilentlyContinue
    }
}

$cases = @(
    @{ Name = 'absent (default claude)'; AgentFileValue = $null;    Expected = 'start-claude-worker' },
    @{ Name = 'claude explicit';          AgentFileValue = 'claude'; Expected = 'start-claude-worker' },
    @{ Name = 'codex explicit';           AgentFileValue = 'codex';  Expected = 'start-codex-worker' }
)

foreach ($case in $cases) {
    $outputText = Invoke-DispatchDryRun -AgentFileValue $case.AgentFileValue

    if ($outputText -match [regex]::Escape($case.Expected)) {
        Write-Host "PASS: $($case.Name)"
        $passed++
    }
    else {
        Write-Host "FAIL: $($case.Name) -- expected '$($case.Expected)' in output:"
        Write-Host $outputText
        $failed++
    }
}

# Validate set-implementation-agent.ps1 rejects invalid agents (ValidateSet enforces this)
$invalidTemp = [System.IO.Path]::GetTempFileName() + '.ps1'
try {
    Set-Content -Path $invalidTemp -Value "& '$($setAgentPath -replace "'", "''")' -Agent invalid 2>&1"
    $invalidExitCode = 0
    try {
        & powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $invalidTemp 2>&1 | Out-Null
        $invalidExitCode = $LASTEXITCODE
    }
    catch {
        $invalidExitCode = 1
    }
    if ($invalidExitCode -eq 0) { $invalidExitCode = $LASTEXITCODE }
}
finally {
    Remove-Item $invalidTemp -Force -ErrorAction SilentlyContinue
}

if ($invalidExitCode -ne 0) {
    Write-Host 'PASS: invalid agent rejected with non-zero exit'
    $passed++
}
else {
    Write-Host "FAIL: invalid agent was not rejected (exit=$invalidExitCode)"
    $failed++
}

Write-Host ''
Write-Host "Results: $passed passed, $failed failed"

if ($failed -gt 0) {
    exit 1
}

Write-Output 'PASS test-implementation-agent-switcher.ps1'
