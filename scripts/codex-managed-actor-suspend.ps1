[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable,
    [Parameter(Mandatory = $true)]
    [string]$Operator,
    [Parameter(Mandatory = $true)]
    [string]$BindingId,
    [string]$CodexBinary,
    [string]$RuntimeHome
)

$ErrorActionPreference = "Stop"
$arguments = @("-m", "tools.codex_supervisor", "--repo-root", $RepoRoot)
if ($RuntimeHome) { $arguments += @("--runtime-home", $RuntimeHome) }
if ($CodexBinary) { $arguments += @("--codex-bin", $CodexBinary) }
$arguments += @("managed", "--operator", $Operator, "suspend", "--binding-id", $BindingId)
& $PythonExecutable @arguments
if ($LASTEXITCODE -ne 0) { throw "managed suspend exited with code $LASTEXITCODE" }
