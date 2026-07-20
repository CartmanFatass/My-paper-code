[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$round = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md') -Raw
$exchange = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-exchange/SKILL.md') -Raw
$registry = Get-Content (Join-Path $repo 'docs/external-review/REVIEWER_CONVERSATIONS.json') -Raw | ConvertFrom-Json
$heartbeat = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-exchange/scripts/render_review_heartbeat.ps1') -Raw
if ($registry.schema_version -ne 23 -or @($registry.reviewers.PSObject.Properties).Count -ne 1 -or
    $registry.reviewers.open_divergent.session_role -ne 'open_divergent_exchange' -or
    $registry.round_controller.scientific_convergence -ne 'research_project_manager') { throw 'Review registry mismatch' }
foreach ($required in @('one Open-Pro divergent question','SCIENTIFIC_CONVERGENCE_TASK','Research Project Manager','one external divergent stage followed by internal convergence','50_DISPOSITION.md')) {
    if (-not $round.Contains($required)) { throw "Review round missing: $required" }
}
foreach ($required in @('reviewer_role=OPEN_DIVERGENT','ARCHIVE_NATURAL_RESPONSE_AND_REPORT_QUALITY','COMPLETE_WITH_GAPS','callback delivery','heartbeat was deleted')) {
    if (-not $exchange.Contains($required)) { throw "Exchange missing: $required" }
}
if (-not $heartbeat.Contains('[ValidateSet("OPEN_DIVERGENT")]') -or
    ([regex]::Matches($heartbeat, 'ValidateSet\(').Count -ne 1)) { throw 'Heartbeat role set is not singular' }
Write-Output 'HMASD_REVIEW_ROUND_CONTRACT_OK'
