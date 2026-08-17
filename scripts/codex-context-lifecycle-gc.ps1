[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [string]$PythonExecutable = "C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe",
    [string]$Actor,
    [switch]$MarkArchived
)

$ErrorActionPreference = "Stop"
$root = if ([IO.Path]::IsPathRooted($RepoRoot)) { [IO.Path]::GetFullPath($RepoRoot) } else { [IO.Path]::GetFullPath((Join-Path (Get-Location) $RepoRoot)) }
$cliArgs = @("-m", "tools.codex_context_lifecycle.cli", "gc", "--repo-root", $root)
if ($Actor) { $cliArgs += @("--actor", $Actor) }
if ($MarkArchived) { $cliArgs += "--mark-archived" } else { $cliArgs += "--dry-run" }
& $PythonExecutable @cliArgs
if ($LASTEXITCODE -ne 0) { throw "context lifecycle gc failed" }
