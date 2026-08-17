[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [string]$PythonExecutable = "C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe"
)

$ErrorActionPreference = "Stop"
$root = if ([IO.Path]::IsPathRooted($RepoRoot)) { [IO.Path]::GetFullPath($RepoRoot) } else { [IO.Path]::GetFullPath((Join-Path (Get-Location) $RepoRoot)) }
Set-Location -LiteralPath $root
& $PythonExecutable -m pytest tests\codex_semantic_mvp tests\codex_context_lifecycle -q --basetemp="$root\.tmp_ctx_lifecycle_pytest"
if ($LASTEXITCODE -ne 0) { throw "context lifecycle tests failed" }
& $PythonExecutable -m tools.codex_context_lifecycle.cli doctor --repo-root $root
if ($LASTEXITCODE -ne 0) { throw "context lifecycle doctor failed" }
$before = Get-FileHash -LiteralPath (Join-Path $root "docs\project\DECISIONS_INDEX.md")
& $PythonExecutable -m tools.codex_context_lifecycle.cli decisions-index --repo-root $root
if ($LASTEXITCODE -ne 0) { throw "decision index generation failed" }
$after = Get-FileHash -LiteralPath (Join-Path $root "docs\project\DECISIONS_INDEX.md")
if ($before.Hash -ne $after.Hash) { throw "decision index drifted after regeneration" }
