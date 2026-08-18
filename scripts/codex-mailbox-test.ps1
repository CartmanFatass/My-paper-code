[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable,
    [string]$CodexBinary,
    [string]$RuntimeHome
)

$ErrorActionPreference = "Stop"
$baseTemp = Join-Path $RepoRoot ".tmp_mailbox"
$arguments = @(
    "-m", "pytest",
    "tests/codex_supervisor/test_mailbox_schema_v3.py",
    "tests/codex_supervisor/test_mailbox_acl.py",
    "tests/codex_supervisor/test_mailbox_store.py",
    "tests/codex_supervisor/test_semantic_scanner.py",
    "tests/codex_supervisor/test_scheduler_leases.py",
    "tests/codex_supervisor/test_wake_batches.py",
    "tests/codex_supervisor/test_wake_scheduler.py",
    "tests/codex_supervisor/test_mailbox_commands.py",
    "tests/codex_supervisor/test_managed_packet_send.py",
    "tests/codex_supervisor/test_mailbox_cli.py",
    "tests/codex_supervisor/test_stage4_end_to_end.py",
    "-q",
    "--basetemp=$baseTemp"
)
Push-Location $RepoRoot
try {
    & $PythonExecutable @arguments
    if ($LASTEXITCODE -ne 0) { throw "mailbox tests exited with code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
