[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [string]$PythonExecutable = "C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe"
)

$ErrorActionPreference = "Stop"
$root = if ([IO.Path]::IsPathRooted($RepoRoot)) { [IO.Path]::GetFullPath($RepoRoot) } else { [IO.Path]::GetFullPath((Join-Path (Get-Location) $RepoRoot)) }
if (-not (Test-Path -LiteralPath $root -PathType Container)) {
    throw "Repository root does not exist: $root"
}
if (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) {
    throw "PYTHON_EXECUTABLE_MISSING: $PythonExecutable"
}

$runtime = Join-Path $root "runtime\codex-semantic-mvp"
$statePath = Join-Path $runtime "activation-state.json"
$probePath = Join-Path $runtime "topology-probe.jsonl"
$capabilityPath = Join-Path $runtime "topology-capabilities.json"

if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
    throw "PROBE_REQUIRES_SHADOW: activation-state.json is missing. Enable SHADOW first."
}
try {
    $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
} catch {
    throw "PROBE_REQUIRES_SHADOW: activation-state.json is not valid JSON."
}
if ([string]$state.mode -ne "shadow") {
    throw "PROBE_REQUIRES_SHADOW: current mode is '$($state.mode)'. Enable SHADOW first."
}

[IO.Directory]::CreateDirectory($runtime) | Out-Null
if (Test-Path -LiteralPath $probePath -PathType Leaf) { Remove-Item -LiteralPath $probePath -Force }
if (Test-Path -LiteralPath $capabilityPath -PathType Leaf) { Remove-Item -LiteralPath $capabilityPath -Force }
if (Test-Path -LiteralPath (Join-Path $runtime "state.sqlite3") -PathType Leaf) {
    Write-Output "Leaving state.sqlite3 untouched."
}

Write-Output @"
TOPOLOGY PROBE CANARIES
Complete these manual Codex canaries, then rerun this script without deleting
the resulting topology-probe.jsonl if you want to summarize an existing capture.
This first invocation cleared only probe files.

A. Operational Root startup, compact, resume
B. Portfolio session compact, resume
C. Root spawns one EM and one CM
D. EM spawns one Research Scout
E. CM spawns one Implementer
F. Trigger compaction in EM if the client permits
G. Trigger compaction in CM if the client permits
H. Trigger compaction in one leaf if the client permits

Do not modify scientific or role files during the probe.
"@

$code = @'
import json
from pathlib import Path
from tools.codex_semantic_mvp.topology_probe import summarize_probe_file

probe = Path(r"""__PROBE__""")
output = Path(r"""__OUTPUT__""")
summary = summarize_probe_file(probe, output)
print(json.dumps(summary, ensure_ascii=False, indent=2))
'@
$code = $code.Replace("__PROBE__", $probePath).Replace("__OUTPUT__", $capabilityPath)

Push-Location $root
try {
    $result = & $PythonExecutable -c $code
    if ($LASTEXITCODE -ne 0) { throw "topology probe summarization failed with code $LASTEXITCODE" }
    Write-Output $result
    Write-Output "Wrote $capabilityPath"
}
finally {
    Pop-Location
}
