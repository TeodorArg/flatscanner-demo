$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'ai-review-policy.ps1')

$cases = @(
    @{
        Name = 'low-only findings downgrade request_changes to comment'
        Result = [pscustomobject]@{
            verdict = 'request_changes'
            findings = @(
                [pscustomobject]@{ severity = 'low'; file = 'docs/example.md'; line = 10; title = 'Minor doc note'; body = 'Advisory only.' }
            )
        }
        ExpectedVerdict = 'comment'
        ExpectPolicyNote = $true
    },
    @{
        Name = 'no findings downgrade request_changes to comment'
        Result = [pscustomobject]@{
            verdict = 'request_changes'
            findings = @()
        }
        ExpectedVerdict = 'comment'
        ExpectPolicyNote = $true
    },
    @{
        Name = 'medium finding keeps request_changes blocking'
        Result = [pscustomobject]@{
            verdict = 'request_changes'
            findings = @(
                [pscustomobject]@{ severity = 'medium'; file = 'scripts/example.ps1'; line = 4; title = 'Operational risk'; body = 'Should block.' }
            )
        }
        ExpectedVerdict = 'request_changes'
        ExpectPolicyNote = $false
    },
    @{
        Name = 'high finding keeps request_changes blocking'
        Result = [pscustomobject]@{
            verdict = 'request_changes'
            findings = @(
                [pscustomobject]@{ severity = 'high'; file = 'scripts/example.ps1'; line = 9; title = 'Correctness risk'; body = 'Should also block.' }
            )
        }
        ExpectedVerdict = 'request_changes'
        ExpectPolicyNote = $false
    },
    @{
        Name = 'comment verdict with low findings stays comment'
        Result = [pscustomobject]@{
            verdict = 'comment'
            findings = @(
                [pscustomobject]@{ severity = 'low'; file = 'docs/example.md'; line = 8; title = 'Minor follow-up'; body = 'Still advisory.' }
            )
        }
        ExpectedVerdict = 'comment'
        ExpectPolicyNote = $false
    }
)

foreach ($case in $cases) {
    $outcome = Resolve-AiReviewOutcome -Result $case.Result
    if ($outcome.EffectiveVerdict -ne $case.ExpectedVerdict) {
        throw "Case failed: $($case.Name). Expected verdict '$($case.ExpectedVerdict)' but got '$($outcome.EffectiveVerdict)'."
    }

    $hasPolicyNote = -not [string]::IsNullOrWhiteSpace([string]$outcome.PolicyNote)
    if ($hasPolicyNote -ne $case.ExpectPolicyNote) {
        throw "Case failed: $($case.Name). Policy note expectation mismatch."
    }
}

Write-Output 'AI review verdict normalization validation passed.'
