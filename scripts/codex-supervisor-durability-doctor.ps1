param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable
)
$ErrorActionPreference = "Stop"
& $PythonExecutable -m tools.codex_supervisor doctor --repo-root $RepoRoot
