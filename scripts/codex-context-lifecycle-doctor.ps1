[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [string]$PythonExecutable = "C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe"
)

$ErrorActionPreference = "Stop"
$root = if ([IO.Path]::IsPathRooted($RepoRoot)) { [IO.Path]::GetFullPath($RepoRoot) } else { [IO.Path]::GetFullPath((Join-Path (Get-Location) $RepoRoot)) }
& $PythonExecutable -m tools.codex_context_lifecycle.cli doctor --repo-root $root
if ($LASTEXITCODE -ne 0) { throw "context lifecycle doctor failed" }
