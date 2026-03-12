param(
    [Parameter(Mandatory = $true)]
    [string]$FeatureId
)

$featurePath = Join-Path "specs" $FeatureId

& ".specify/scripts/check-prerequisites.ps1" -FeaturePath $featurePath
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Ready to plan feature in $featurePath"
