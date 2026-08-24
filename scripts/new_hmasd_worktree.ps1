param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]*$')]
    [string]$Name,

    [string]$StartPoint = 'HEAD',

    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._/-]*$')]
    [string]$NewBranch
)

$ErrorActionPreference = 'Stop'

$repo = [System.IO.Path]::GetFullPath(
    (& git rev-parse --show-toplevel).Trim()
)
if ($LASTEXITCODE -ne 0) {
    throw 'Run this script from an HMASD Git checkout.'
}

$container = Join-Path (Split-Path -Parent $repo) 'HMASD-worktrees'
$target = [System.IO.Path]::GetFullPath((Join-Path $container $Name))
$containerPrefix = [System.IO.Path]::GetFullPath($container) + [System.IO.Path]::DirectorySeparatorChar

if (-not $target.StartsWith($containerPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Worktree target escaped the canonical container: $target"
}
if (Test-Path -LiteralPath $target) {
    throw "Worktree target already exists: $target"
}

New-Item -ItemType Directory -Force -Path $container | Out-Null

if ($NewBranch) {
    & git worktree add -b $NewBranch $target $StartPoint
}
else {
    & git worktree add $target $StartPoint
}
if ($LASTEXITCODE -ne 0) {
    throw "git worktree add failed for $target"
}

Write-Output $target
