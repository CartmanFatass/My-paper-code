[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$python = "C:\Users\wu\.conda\envs\SB3\python.exe"
$root = if ([IO.Path]::IsPathRooted($RepoRoot)) { [IO.Path]::GetFullPath($RepoRoot) } else { [IO.Path]::GetFullPath((Join-Path (Get-Location) $RepoRoot)) }
if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw "Repository root does not exist: $root" }

Push-Location $root
try {
    & $python -m pytest tests\codex_semantic_mvp -q
    if ($LASTEXITCODE -ne 0) { throw "semantic MVP tests exited with code $LASTEXITCODE" }
    & $python -m tools.codex_semantic_mvp.doctor --repo-root .
    if ($LASTEXITCODE -ne 0) { throw "doctor exited with code $LASTEXITCODE" }

    if ($DryRun) {
        $scriptDir = Join-Path $root "scripts"
        foreach ($activationMode in @("Shadow", "Active")) {
            $stage = Join-Path ([IO.Path]::GetTempPath()) ("hmasd-codex-semantic-mvp-test-" + [guid]::NewGuid().ToString("N"))
            try {
                New-Item -ItemType Directory -Path (Join-Path $stage ".codex") -Force | Out-Null
                foreach ($name in @("hooks.json", "config.toml", "hooks.semantic-mvp.shadow.json", "hooks.semantic-mvp.active.json")) {
                    Copy-Item -LiteralPath (Join-Path $root ".codex\$name") -Destination (Join-Path $stage ".codex\$name")
                }
                $before = [IO.File]::ReadAllBytes((Join-Path $stage ".codex\hooks.json"))
                & (Join-Path $scriptDir "codex-semantic-mvp-enable.ps1") -RepoRoot $stage -Mode $activationMode
                if ($LASTEXITCODE -ne 0) { throw "dry-run $activationMode enable failed" }
                & (Join-Path $scriptDir "codex-semantic-mvp-disable.ps1") -RepoRoot $stage
                if ($LASTEXITCODE -ne 0) { throw "dry-run $activationMode disable failed" }
                $after = [IO.File]::ReadAllBytes((Join-Path $stage ".codex\hooks.json"))
                if (-not [Linq.Enumerable]::SequenceEqual($before, $after)) { throw "DRY_RUN_$activationMode_ROLLBACK_BYTES_CHANGED" }
                Write-Output "DRY_RUN_$($activationMode.ToUpperInvariant())_ROLLBACK_VERIFIED=true"
            }
            finally {
                if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
            }
        }
    }
}
finally {
    Pop-Location
}
