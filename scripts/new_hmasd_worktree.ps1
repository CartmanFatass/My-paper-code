param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]*$')]
    [string]$Name,

    [string]$StartPoint = 'HEAD',

    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._/-]*$')]
    [string]$NewBranch
)

$ErrorActionPreference = 'Stop'

$commonRaw = & git rev-parse --path-format=absolute --git-common-dir
if ($LASTEXITCODE -ne 0 -or -not $commonRaw) {
    throw 'Run this script from an HMASD Git checkout.'
}
$common = [System.IO.Path]::GetFullPath(([string]$commonRaw).Trim())
$repo = Split-Path -Parent $common

$container = Join-Path (Split-Path -Parent $repo) "$(Split-Path -Leaf $repo)-worktrees"
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
