[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable,
    [Parameter(Mandatory = $true)]
    [string]$RuntimeHome,
    [Parameter(Mandatory = $true)]
    [string]$NormalRuntimeHome,
    [string]$CodexBinary,
    [switch]$StatusPreflightOnly
)

$ErrorActionPreference = "Stop"
$resolvedRepo = (Resolve-Path -LiteralPath $RepoRoot -ErrorAction Stop).Path
function Resolve-ExternalRuntime([string]$Candidate, [string]$Label) {
    if ([string]::IsNullOrWhiteSpace($Candidate)) { throw "$Label must be explicitly supplied" }
    $full = [System.IO.Path]::GetFullPath($Candidate)
    if (Test-Path -LiteralPath $full) { $full = (Resolve-Path -LiteralPath $full -ErrorAction Stop).Path }
    $rootKey = $resolvedRepo.TrimEnd('\', '/').ToLowerInvariant()
    $pathKey = $full.TrimEnd('\', '/').ToLowerInvariant()
    if ($pathKey -eq $rootKey -or $pathKey.StartsWith($rootKey + '\') -or $pathKey.StartsWith($rootKey + '/')) {
        throw "$Label must be external to the repository"
    }
    return $full
}

$RuntimeHome = Resolve-ExternalRuntime $RuntimeHome 'canary RuntimeHome'
$NormalRuntimeHome = Resolve-ExternalRuntime $NormalRuntimeHome 'normal supervisor RuntimeHome'
if ($RuntimeHome.TrimEnd('\', '/').ToLowerInvariant() -eq $NormalRuntimeHome.TrimEnd('\', '/').ToLowerInvariant()) {
    throw 'canary RuntimeHome must differ from normal supervisor RuntimeHome'
}
$statusScript = Join-Path $PSScriptRoot 'hmasd-root-supervisor-status.ps1'
if ($CodexBinary) {
    $statusRaw = & $statusScript -RepoRoot $resolvedRepo -RuntimeHome $NormalRuntimeHome -PythonPath $PythonExecutable -CodexBin $CodexBinary
} else {
    $statusRaw = & $statusScript -RepoRoot $resolvedRepo -RuntimeHome $NormalRuntimeHome -PythonPath $PythonExecutable
}
if ($LASTEXITCODE -ne 0) { throw "normal supervisor status preflight exited with code $LASTEXITCODE" }
$status = $statusRaw | ConvertFrom-Json -ErrorAction Stop
if ([string]$status.state -ne 'STOPPED') {
    throw "normal supervisor must be exactly STOPPED before canary; observed $($status.state)"
}
if ($StatusPreflightOnly) { return }
$arguments = @(
    "-m", "tools.codex_supervisor",
    "--repo-root", $resolvedRepo,
    "--runtime-home", $RuntimeHome
)
if ($CodexBinary) { $arguments += @("--codex-bin", $CodexBinary) }
$arguments += @("canary", "--normal-runtime-home", $NormalRuntimeHome)
& $PythonExecutable @arguments
if ($LASTEXITCODE -ne 0) { throw "canary exited with code $LASTEXITCODE" }
