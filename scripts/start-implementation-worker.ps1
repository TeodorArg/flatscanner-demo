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

    [switch]$PromptOnly
)

$ErrorActionPreference = 'Stop'

$repoRoot = (git rev-parse --show-toplevel).Trim()
$agentFile = Join-Path $repoRoot '.codex\implementation-agent'

$agent = 'claude'
if (Test-Path $agentFile) {
    $rawContent = Get-Content $agentFile -Raw
    $fileContent = if ($rawContent) { $rawContent.Trim().ToLowerInvariant() } else { '' }
    if ($fileContent -eq 'codex') {
        $agent = 'codex'
    }
    elseif ($fileContent -eq 'claude') {
        $agent = 'claude'
    }
    else {
        Write-Warning "Unrecognised or empty value '$fileContent' in $agentFile; defaulting to claude."
    }
}

Write-Host "Implementation agent: $agent"

$workerScript = switch ($agent) {
    'codex' { Join-Path $PSScriptRoot 'start-codex-worker.ps1' }
    'claude' { Join-Path $PSScriptRoot 'start-claude-worker.ps1' }
}

Write-Host "Dispatching to: $workerScript"

$passThrough = @{
    FeatureFolder = $FeatureFolder
    TaskSummary   = $TaskSummary
    WorktreePath  = $WorktreePath
}

if ($TaskId) { $passThrough['TaskId'] = $TaskId }
if ($PullRequestTitle) { $passThrough['PullRequestTitle'] = $PullRequestTitle }
if ($OpenPullRequest) { $passThrough['OpenPullRequest'] = $true }
if ($DraftPullRequest) { $passThrough['DraftPullRequest'] = $true }
if ($PromptOnly) { $passThrough['PromptOnly'] = $true }

& $workerScript @passThrough
exit $LASTEXITCODE
