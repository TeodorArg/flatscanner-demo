param(
    [string]$FeaturePath = "."
)

$requiredFiles = @("spec.md", "plan.md", "tasks.md")
$missing = @()

foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $FeaturePath $file
    if (-not (Test-Path $fullPath)) {
        $missing += $fullPath
    }
}

if ($missing.Count -gt 0) {
    Write-Error ("Missing required spec files:`n" + ($missing -join "`n"))
    exit 1
}

Write-Host "Spec prerequisites look good."
