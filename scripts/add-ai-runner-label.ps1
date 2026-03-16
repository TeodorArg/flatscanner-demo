param(
    [string]$Repository = 'alexgoodman53/flatscanner',
    [string]$RunnerName = $env:COMPUTERNAME,
    [switch]$RemoveLegacyCodexLabel
)

$ErrorActionPreference = 'Stop'

$ghCommand = Get-Command gh -ErrorAction SilentlyContinue
$ghPath = if ($ghCommand) { $ghCommand.Source } else { Join-Path $env:ProgramFiles 'GitHub CLI\gh.exe' }
if (-not (Test-Path $ghPath)) {
    throw "GitHub CLI not found at $ghPath"
}

$runnerResponse = & $ghPath api "repos/$Repository/actions/runners?per_page=100"
if ($LASTEXITCODE -ne 0) {
    throw 'Unable to load GitHub Actions runners.'
}

$runnerData = $runnerResponse | ConvertFrom-Json
$runner = $runnerData.runners | Where-Object { $_.name -eq $RunnerName } | Select-Object -First 1
if (-not $runner) {
    throw "Runner '$RunnerName' was not found in $Repository."
}

$currentLabels = @($runner.labels | ForEach-Object { $_.name })

if ('ai-runner' -notin $currentLabels) {
    & $ghPath api --method POST "repos/$Repository/actions/runners/$($runner.id)/labels" -F "labels[]=ai-runner"
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to add ai-runner label to runner '$RunnerName'."
    }
}

if ($RemoveLegacyCodexLabel -and ('codex' -in $currentLabels)) {
    & $ghPath api --method DELETE "repos/$Repository/actions/runners/$($runner.id)/labels/codex"
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to remove legacy codex label from runner '$RunnerName'."
    }
}
elseif ('codex' -in $currentLabels) {
    Write-Warning "Keeping legacy codex label on '$RunnerName'. Use -RemoveLegacyCodexLabel when you are ready to drop the transition label."
}

Write-Output "Updated runner '$RunnerName' labels."
