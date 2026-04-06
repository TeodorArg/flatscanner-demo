[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('windows', 'macOS')]
    [string]$Runner,

    [string]$Repo
)

$ErrorActionPreference = 'Stop'

if ($PSCmdlet.ShouldProcess('AI_REVIEW_RUNNER', "Set repo variable to '$Runner'")) {
    $ghArgs = @('variable', 'set', 'AI_REVIEW_RUNNER', '--body', $Runner)
    if ($Repo) {
        $ghArgs += '--repo'
        $ghArgs += $Repo
    }

    & gh @ghArgs
    if ($LASTEXITCODE -ne 0) {
        throw "gh variable set failed with exit code $LASTEXITCODE"
    }

    Write-Host "Repo variable AI_REVIEW_RUNNER set to '$Runner'"
}
