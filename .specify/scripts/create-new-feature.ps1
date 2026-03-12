param(
    [Parameter(Mandatory = $true)]
    [string]$FeatureId,

    [Parameter(Mandatory = $true)]
    [string]$FeatureName
)

$root = Join-Path "specs" $FeatureId
New-Item -ItemType Directory -Force $root | Out-Null

$files = @{
    "spec.md" = ".specify/templates/spec-template.md"
    "plan.md" = ".specify/templates/plan-template.md"
    "tasks.md" = ".specify/templates/tasks-template.md"
}

foreach ($entry in $files.GetEnumerator()) {
    Copy-Item $entry.Value (Join-Path $root $entry.Key) -Force
}

(Get-Content (Join-Path $root "spec.md")) -replace "<feature-name>", $FeatureName | Set-Content (Join-Path $root "spec.md")
(Get-Content (Join-Path $root "plan.md")) -replace "<feature-name>", $FeatureName | Set-Content (Join-Path $root "plan.md")
(Get-Content (Join-Path $root "tasks.md")) -replace "<feature-name>", $FeatureName | Set-Content (Join-Path $root "tasks.md")

Write-Host "Created feature scaffold at $root"
