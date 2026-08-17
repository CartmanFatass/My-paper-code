[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [string]$PythonExecutable = "C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe"
)

$ErrorActionPreference = "Stop"
$root = if ([IO.Path]::IsPathRooted($RepoRoot)) { [IO.Path]::GetFullPath($RepoRoot) } else { [IO.Path]::GetFullPath((Join-Path (Get-Location) $RepoRoot)) }
$index = Join-Path $root "docs\project\DECISIONS_INDEX.md"
$before = if (Test-Path -LiteralPath $index) { Get-FileHash -LiteralPath $index } else { $null }
& $PythonExecutable -m tools.codex_context_lifecycle.cli decisions-index --repo-root $root
if ($LASTEXITCODE -ne 0) { throw "decision index generation failed" }
& $PythonExecutable -m tools.codex_context_lifecycle.cli decisions-index --repo-root $root
$after = Get-FileHash -LiteralPath $index
if ($before -and $before.Hash -ne $after.Hash) {
    # First generation may write the file; a second run must be byte-stable.
}
$secondBefore = $after
& $PythonExecutable -m tools.codex_context_lifecycle.cli decisions-index --repo-root $root
$secondAfter = Get-FileHash -LiteralPath $index
if ($secondBefore.Hash -ne $secondAfter.Hash) { throw "decision index is not deterministic" }
