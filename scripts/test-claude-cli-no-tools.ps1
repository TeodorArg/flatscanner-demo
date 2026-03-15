$ErrorActionPreference = 'Stop'

$claudePath = if ($env:CLAUDE_CLI_PATH) { $env:CLAUDE_CLI_PATH } else { 'C:\Users\User\.local\bin\claude.exe' }
if (-not (Test-Path $claudePath)) {
    throw "Claude CLI not found at $claudePath"
}

$noTools = '""'
$result = 'Reply with exactly OK' | & $claudePath -p --output-format text --permission-mode default --tools $noTools
if ($LASTEXITCODE -ne 0) {
    throw 'Claude CLI no-tools smoke test failed.'
}

if ($result.Trim() -ne 'OK') {
    throw "Unexpected Claude CLI no-tools output: $result"
}

Write-Output 'PASS test-claude-cli-no-tools.ps1'
