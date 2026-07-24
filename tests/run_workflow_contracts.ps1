[CmdletBinding()]
param()
$ErrorActionPreference = 'Continue'
$here = $PSScriptRoot

# The workflow contracts. Each is standalone and exits nonzero on a violation.
$contracts = @(
    'review_round_contract_test.ps1',
    'hmasd_research_workflow_contract_test.ps1',
    'hmasd_experiment_operator_contract_test.ps1')

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

Write-Output ''
if ($failed.Count -gt 0) {
    Write-Output "WORKFLOW_CONTRACTS_FAILED: $($failed -join ', ')"
    exit 1
}
Write-Output 'WORKFLOW_CONTRACTS_OK'
exit 0
