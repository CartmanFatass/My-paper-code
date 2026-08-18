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
    [Parameter(Mandatory = $true)]
    [string]$Text,
    [string]$CodexBinary,
    [string]$RuntimeHome
)

$ErrorActionPreference = "Stop"
$arguments = @("-m", "tools.codex_supervisor", "--repo-root", $RepoRoot)
if ($RuntimeHome) { $arguments += @("--runtime-home", $RuntimeHome) }
if ($CodexBinary) { $arguments += @("--codex-bin", $CodexBinary) }
$arguments += @("managed", "--operator", $Operator, "turn", "--binding-id", $BindingId, "--text", $Text)
& $PythonExecutable @arguments
if ($LASTEXITCODE -ne 0) { throw "managed turn exited with code $LASTEXITCODE" }
