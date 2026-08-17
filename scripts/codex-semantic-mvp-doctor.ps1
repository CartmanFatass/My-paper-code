[CmdletBinding()]
param(
    [string]$RepoRoot = "."
)

$ErrorActionPreference = "Stop"
$python = "C:\Users\wu\.conda\envs\SB3\python.exe"
$root = if ([IO.Path]::IsPathRooted($RepoRoot)) { [IO.Path]::GetFullPath($RepoRoot) } else { [IO.Path]::GetFullPath((Join-Path (Get-Location) $RepoRoot)) }
if (-not (Test-Path -LiteralPath $root -PathType Container)) {
    throw "Repository root does not exist: $root"
}

Push-Location $root
try {
    & $python -m tools.codex_semantic_mvp.doctor --repo-root .
    if ($LASTEXITCODE -ne 0) { throw "doctor exited with code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
