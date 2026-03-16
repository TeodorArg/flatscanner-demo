$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'claude-review-output.ps1')

$cases = @(
    @{
        Name = 'verdict field passes through unchanged'
        RawText = '{"verdict":"comment","summary":"ok","findings":[]}'
        ExpectedVerdict = 'comment'
        ExpectedNotes = 0
    },
    @{
        Name = 'action field is normalized to verdict'
        RawText = '{"action":"comment","summary":"ok","findings":[]}'
        ExpectedVerdict = 'comment'
        ExpectedNotes = 1
    },
    @{
        Name = 'review_status field is normalized to verdict'
        RawText = '{"review_status":"comment","summary":"ok","findings":[]}'
        ExpectedVerdict = 'comment'
        ExpectedNotes = 1
    },
    @{
        Name = 'review_action field is normalized to verdict'
        RawText = '{"review_action":"request_changes","summary":"ok","findings":[]}'
        ExpectedVerdict = 'request_changes'
        ExpectedNotes = 1
    },
    @{
        Name = 'fenced json with action is normalized'
        RawText = @'
```json
{"action":"approve","summary":"clean","findings":[]}
```
'@
        ExpectedVerdict = 'approve'
        ExpectedNotes = 1
    }
)

foreach ($case in $cases) {
    $parsed = ConvertFrom-ClaudeReviewOutput -RawText $case.RawText
    Assert-ClaudeReviewResultContract -Result $parsed.Result
    if ([string]$parsed.Result.verdict -ne $case.ExpectedVerdict) {
        throw "Case failed: $($case.Name). Expected verdict '$($case.ExpectedVerdict)' but got '$($parsed.Result.verdict)'."
    }

    if (@($parsed.NormalizationNotes).Count -ne $case.ExpectedNotes) {
        throw "Case failed: $($case.Name). Expected $($case.ExpectedNotes) normalization notes but got $(@($parsed.NormalizationNotes).Count)."
    }
}

$invalidFailed = $false
try {
    ConvertFrom-ClaudeReviewOutput -RawText 'not-json at all' | Out-Null
}
catch {
    $invalidFailed = $true
}

if (-not $invalidFailed) {
    throw 'Invalid Claude review output should fail parsing.'
}

$missingVerdictFailed = $false
try {
    $parsed = ConvertFrom-ClaudeReviewOutput -RawText '{"summary":"missing verdict","findings":[]}'
    if (-not $parsed.Result.verdict) {
        throw 'Missing verdict remained unresolved.'
    }
}
catch {
    $missingVerdictFailed = $true
}

if (-not $missingVerdictFailed) {
    throw 'Structured payload missing verdict/action should fail validation.'
}

$unsupportedActionFailed = $false
try {
    $parsed = ConvertFrom-ClaudeReviewOutput -RawText '{"action":"reject","summary":"bad","findings":[]}'
    if (@('approve', 'comment', 'request_changes') -notcontains [string]$parsed.Result.verdict) {
        throw 'Unsupported action did not produce a valid verdict.'
    }
}
catch {
    $unsupportedActionFailed = $true
}

if (-not $unsupportedActionFailed) {
    throw 'Structured payload with unsupported action should fail validation.'
}

$missingLineFailed = $false
try {
    $parsed = ConvertFrom-ClaudeReviewOutput -RawText '{"verdict":"comment","summary":"ok","findings":[{"severity":"low","file":"x","title":"t","body":"b"}]}'
    Assert-ClaudeReviewResultContract -Result $parsed.Result
}
catch {
    $missingLineFailed = $true
}

if (-not $missingLineFailed) {
    throw 'Finding payload without a line field should fail validation.'
}

Write-Output 'Claude review output parsing validation passed.'
