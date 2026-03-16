$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'ai-review-comment.ps1')

$unicodeBody = "Coordinate 0$([char]0x00B0) and em dash $([char]0x2014) should survive."
$unicodePayload = ConvertTo-GitHubIssueCommentPayload -Body $unicodeBody
if ($unicodePayload.Body -ne $unicodeBody) {
    throw 'Unicode characters should be preserved in the sanitized comment body.'
}
if ($unicodePayload.WasTruncated) {
    throw 'Short comment bodies should not be marked as truncated.'
}
if (-not (ConvertFrom-Json $unicodePayload.Payload).body) {
    throw 'Comment payload JSON should remain parseable.'
}

$controlBody = "ok$([char]0)still ok$([char]7)`nnext line"
$controlPayload = ConvertTo-GitHubIssueCommentPayload -Body $controlBody
if ($controlPayload.Body.Contains([char]0) -or $controlPayload.Body.Contains([char]7)) {
    throw 'Control characters should be removed from the comment body.'
}
if (-not $controlPayload.Body.Contains("`r`n")) {
    throw 'Line endings should be normalized to CRLF.'
}

$longBody = 'x' * 61000
$longPayload = ConvertTo-GitHubIssueCommentPayload -Body $longBody
if (-not $longPayload.WasTruncated) {
    throw 'Long comment bodies should be marked as truncated.'
}
if ($longPayload.Body.Length -gt 60000) {
    throw 'Long comment bodies must stay within the configured maximum length.'
}
if (-not $longPayload.Body.EndsWith('[truncated to fit GitHub comment limits]')) {
    throw 'Truncated comment bodies should end with the truncation note.'
}
if (-not (ConvertFrom-Json $longPayload.Payload).body) {
    throw 'Truncated comment payload JSON should remain parseable.'
}

Write-Host 'AI review comment payload validation passed.'
