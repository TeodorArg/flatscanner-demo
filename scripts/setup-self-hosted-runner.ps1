param(
    [string]$RunnerVersion = '2.325.0',
    [Parameter(Mandatory = $true)][string]$RepoUrl,
    [Parameter(Mandatory = $true)][string]$RegistrationToken,
    [string]$RunnerName = $env:COMPUTERNAME,
    [string]$Labels = 'ai-runner,windows',
    [string]$InstallPath = 'C:\actions-runner',
    [switch]$AsService
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath | Out-Null
}

$zipPath = Join-Path $env:TEMP "actions-runner-win-x64-$RunnerVersion.zip"
$downloadUrl = "https://github.com/actions/runner/releases/download/v$RunnerVersion/actions-runner-win-x64-$RunnerVersion.zip"

Write-Host "Downloading GitHub Actions runner $RunnerVersion"
Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath

Write-Host "Extracting runner to $InstallPath"
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, $InstallPath, $true)

Push-Location $InstallPath
try {
    Write-Host 'Configuring runner'
    & .\config.cmd --unattended --replace --url $RepoUrl --token $RegistrationToken --name $RunnerName --labels $Labels

    if ($AsService) {
        Write-Host 'Installing runner service'
        & .\svc.cmd install
        & .\svc.cmd start
    }
    else {
        Write-Host 'Runner configured. Start it with .\\run.cmd'
    }
}
finally {
    Pop-Location
}
