[CmdletBinding()]
param()
$ErrorActionPreference = 'Continue'
$here = $PSScriptRoot

# The workflow contracts. Each is standalone and exits nonzero on a violation.
$contracts = @(
    'review_round_contract_test.ps1',
    'hmasd_research_workflow_contract_test.ps1',
    'hmasd_experiment_operator_contract_test.ps1',
    'pretooluse_guard_contract_test.ps1')

$failed = @()
foreach ($name in $contracts) {
    $path = Join-Path $here $name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        Write-Output "MISSING  $name"
        $failed += $name
        continue
    }
    $out = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $path 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Output "FAIL     $name"
        $out | ForEach-Object { Write-Output "         $_" }
        $failed += $name
    }
    else {
        Write-Output "PASS     $name"
    }
}

# Structural closure of the control plane. The contracts above assert that named
# things say the right words; this asserts that the things they name exist at all.
# A rule whose referent is missing is unfalsifiable by any string check, which is
# how `iterations_since_last_compaction` survived as a cadence with no counter.
$python = 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe'
$checker = Join-Path (Split-Path -Parent $here) '.claude/skills/hmasd-workflow-change-audit/scripts/check_control_plane.py'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    Write-Output "MISSING  registered interpreter: $python"
    $failed += 'check_control_plane.py (no interpreter)'
}
elseif (-not (Test-Path -LiteralPath $checker -PathType Leaf)) {
    Write-Output "MISSING  check_control_plane.py"
    $failed += 'check_control_plane.py'
}
else {
    $out = & $python $checker --repo (Split-Path -Parent $here) 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Output 'FAIL     check_control_plane.py'
        $out | ForEach-Object { Write-Output "         $_" }
        $failed += 'check_control_plane.py'
    }
    else {
        Write-Output 'PASS     check_control_plane.py'
    }
}

Write-Output ''
if ($failed.Count -gt 0) {
    Write-Output "WORKFLOW_CONTRACTS_FAILED: $($failed -join ', ')"
    exit 1
}
Write-Output 'WORKFLOW_CONTRACTS_OK'
exit 0
