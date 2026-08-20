param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable
)
$ErrorActionPreference = "Stop"
Set-Location $RepoRoot
& $PythonExecutable -m pytest tests/codex_supervisor/durability -q --basetemp="$RepoRoot/.tmp_durability"
