$ErrorActionPreference = 'Stop'

param(
    [string]$Repository = 'alexgoodman53/flatscanner'
)

$ghCommand = Get-Command gh -ErrorAction SilentlyContinue
$ghPath = if ($ghCommand) { $ghCommand.Source } else { Join-Path $env:ProgramFiles 'GitHub CLI\gh.exe' }
if (-not (Test-Path $ghPath)) {
    throw "GitHub CLI not found at $ghPath"
}

$body = @{
    strict = $true
    contexts = @('baseline-checks', 'guard', 'AI Review')
} | ConvertTo-Json -Depth 3

$body | & $ghPath api --method PATCH "repos/$Repository/branches/main/protection/required_status_checks" --input -
