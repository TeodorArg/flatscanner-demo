[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$FeatureFolder,

    [Parameter(Mandatory = $true)]
    [string]$TaskSummary,

    [Parameter(Mandatory = $true)]
    [string]$WorktreePath,

    [string]$TaskId,

    [string]$PullRequestTitle,

    [switch]$OpenPullRequest,

    [switch]$DraftPullRequest,

    [switch]$PromptOnly,

    [string[]]$AllowedTools = @('Bash', 'Glob', 'Grep', 'Read', 'Edit', 'Write')
)

$ErrorActionPreference = 'Stop'

function Resolve-ClaudePath {
    $candidates = @(
        'C:\Users\User\.local\bin\claude.exe',
        (Get-Command claude -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
    ) | Where-Object { $_ }

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw 'Claude CLI was not found. Install Claude Code CLI or add it to PATH.'
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
$featurePath = Join-Path $repoRoot "specs\$FeatureFolder"
if (-not (Test-Path $featurePath)) {
    throw "Feature folder not found: $featurePath"
}

if (-not (Test-Path $WorktreePath)) {
    throw "Worktree path not found: $WorktreePath"
}

$claudePath = Resolve-ClaudePath
$templatePath = Join-Path $repoRoot '.github\claude\prompts\implementation-worker.md'
if (-not (Test-Path $templatePath)) {
    throw "Worker prompt template not found: $templatePath"
}

$currentBranch = (git -C $WorktreePath branch --show-current).Trim()
if (-not $currentBranch) {
    throw "Unable to determine branch for worktree: $WorktreePath"
}

$promptDir = Join-Path $WorktreePath '.codex\worker-prompts'
New-Item -ItemType Directory -Force -Path $promptDir | Out-Null

$promptFile = Join-Path $promptDir ("worker-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.md')
$outputFile = Join-Path $promptDir ("worker-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.out.txt')

$publishGuidance = if ($OpenPullRequest) {
    $draftArg = if ($DraftPullRequest) { ' -Draft' } else { '' }
    "When implementation is complete, publish or reuse the PR with:`n`npowershell -ExecutionPolicy Bypass -File scripts\publish-claude-branch.ps1 -Title '$PullRequestTitle' -FeatureFolder '$FeatureFolder'$draftArg"
}
else {
    'Do not open a pull request automatically unless Codex asks in a follow-up step.'
}

$runtimeSection = @"

## Runtime Worker Context

- Active feature folder: $FeatureFolder
- Assigned branch: $currentBranch
- Assigned worktree: $WorktreePath
- Task id: $(if ($TaskId) { $TaskId } else { 'not provided' })
- Task summary: $TaskSummary

## Runtime Instructions

- Stay inside the assigned worktree and branch only
- Keep the change scoped to this task
- Update `specs/$FeatureFolder/tasks.md` if task state needs to move
- Run relevant validation before finishing
- Commit your changes locally when the task is complete
- $publishGuidance
"@

$promptText = (Get-Content $templatePath -Raw) + $runtimeSection
Set-Content -Path $promptFile -Value $promptText

Write-Host "Prompt file: $promptFile"
Write-Host "Branch: $currentBranch"
Write-Host "Worktree: $WorktreePath"

if ($PromptOnly) {
    Write-Host 'PromptOnly was set; Claude CLI was not launched.'
    return
}

$allowedToolsArg = $AllowedTools -join ','

Push-Location $WorktreePath
try {
    Get-Content $promptFile -Raw |
        & $claudePath -p - --output-format text --permission-mode bypassPermissions --allowedTools $allowedToolsArg |
        Tee-Object -FilePath $outputFile
}
finally {
    Pop-Location
}

Write-Host "Worker output saved to: $outputFile"
