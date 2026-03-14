[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory = $true)]
    [string]$Title,

    [string]$FeatureFolder,

    [string]$BaseBranch = 'main',

    [string]$HeadBranch,

    [string]$BodyFile,

    [switch]$Draft
)

$ErrorActionPreference = 'Stop'

function Get-GitHubToken {
    if ($env:GITHUB_TOKEN) {
        return $env:GITHUB_TOKEN
    }

    $credentialInput = "protocol=https`nhost=github.com`n"
    $credentialOutput = $credentialInput | git credential-manager get
    $tokenLine = $credentialOutput | Select-String '^password=' | Select-Object -First 1

    if (-not $tokenLine) {
        throw 'Unable to resolve a GitHub token from git credential-manager or GITHUB_TOKEN.'
    }

    return $tokenLine.ToString().Substring(9)
}

function Get-RepositoryCoordinates {
    $remoteUrl = (git remote get-url origin).Trim()
    if ($remoteUrl -match 'github\.com[:/](?<owner>[^/]+)/(?<repo>[^/.]+)(?:\.git)?$') {
        return @{
            Owner = $Matches.owner
            Repo = $Matches.repo
        }
    }

    throw "Unable to parse GitHub owner/repo from origin URL: $remoteUrl"
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

if (-not $HeadBranch) {
    $HeadBranch = (git branch --show-current).Trim()
}

if (-not $HeadBranch) {
    throw 'Unable to determine the current branch.'
}

if ($HeadBranch -eq 'main') {
    throw 'Refusing to publish from main.'
}

$coords = Get-RepositoryCoordinates
$token = Get-GitHubToken
$headers = @{
    Authorization = "Bearer $token"
    Accept = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2022-11-28'
}

$body = if ($BodyFile -and (Test-Path $BodyFile)) {
    Get-Content $BodyFile -Raw
}
else {
@"
Feature folder: ${FeatureFolder}

Automated Claude worker pull request.

- Tests run: documented in commits or follow-up comments
- Risks: review branch summary before merge
"@
}

if ($PSCmdlet.ShouldProcess($HeadBranch, 'Push branch to origin')) {
    git push -u origin $HeadBranch | Out-Null
}

$existingUrl = "https://api.github.com/repos/$($coords.Owner)/$($coords.Repo)/pulls?state=open&head=$($coords.Owner):$HeadBranch"
$existing = Invoke-RestMethod -Headers $headers -Uri $existingUrl
if ($existing.Count -gt 0) {
    Write-Host "Pull request already exists: $($existing[0].html_url)"
    return
}

$payload = @{
    title = $Title
    head = $HeadBranch
    base = $BaseBranch
    body = $body
    draft = [bool]$Draft
} | ConvertTo-Json

if ($PSCmdlet.ShouldProcess($HeadBranch, 'Create pull request')) {
    $response = Invoke-RestMethod -Method Post -Headers $headers -Uri "https://api.github.com/repos/$($coords.Owner)/$($coords.Repo)/pulls" -Body $payload
    Write-Host "Created pull request: $($response.html_url)"
}
