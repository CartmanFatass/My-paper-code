param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable
)
$ErrorActionPreference = "Stop"
& $PythonExecutable -m tools.codex_supervisor --repo-root $RepoRoot doctor
exit $LASTEXITCODE
