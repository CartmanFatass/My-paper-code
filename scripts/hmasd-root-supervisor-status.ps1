[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [string]$RuntimeHome,
    [string]$PythonPath = 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe',
    [string]$CodexBin
)

$ErrorActionPreference = 'Stop'

function Resolve-ExternalRuntimeHome([string]$Root, [string]$RuntimeCandidate) {
    $resolvedRoot = (Resolve-Path -LiteralPath $Root -ErrorAction Stop).Path
    if ([string]::IsNullOrWhiteSpace($RuntimeCandidate)) {
        if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) { throw 'LOCALAPPDATA is required' }
        $RuntimeCandidate = Join-Path $env:LOCALAPPDATA 'HMASD\codex-supervisor'
    }
    $fullHome = [System.IO.Path]::GetFullPath($RuntimeCandidate)
    if (Test-Path -LiteralPath $fullHome) { $fullHome = (Resolve-Path -LiteralPath $fullHome -ErrorAction Stop).Path }
    $rootKey = $resolvedRoot.TrimEnd('\', '/').ToLowerInvariant()
    $homeKey = $fullHome.TrimEnd('\', '/').ToLowerInvariant()
    if ($homeKey -eq $rootKey -or $homeKey.StartsWith($rootKey + '\') -or $homeKey.StartsWith($rootKey + '/')) { throw 'runtime home must be external to the repository' }
    return [pscustomobject]@{ RepoRoot = $resolvedRoot; RuntimeHome = $fullHome }
}

function Test-SamePath([string]$Left, [string]$Right) {
    if ([string]::IsNullOrWhiteSpace($Left) -or [string]::IsNullOrWhiteSpace($Right)) { return $false }
    $leftKey = [System.IO.Path]::GetFullPath($Left).TrimEnd('\', '/').ToLowerInvariant()
    $rightKey = [System.IO.Path]::GetFullPath($Right).TrimEnd('\', '/').ToLowerInvariant()
    return ($leftKey -eq $rightKey)
}

function Test-FullyQualifiedPath([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    try {
        if ($Path -notmatch '^(?:[A-Za-z]:[\\/]|[\\/]{2}[^\\/]+[\\/][^\\/]+(?:[\\/]|$))') { return $false }
        [void][System.IO.Path]::GetFullPath($Path)
        return $true
    } catch { return $false }
}

function Test-ExactFields([object]$Value, [string[]]$Expected) {
    if ($null -eq $Value) { return $false }
    $actual = @($Value.PSObject.Properties | ForEach-Object { $_.Name } | Sort-Object)
    $wanted = @($Expected | Sort-Object)
    return (($actual -join "`n") -eq ($wanted -join "`n"))
}

function Resolve-CanonicalExecutable([string]$Executable, [string]$Label) {
    if ([string]::IsNullOrWhiteSpace($Executable)) { throw "$Label is required" }
    return (Resolve-Path -LiteralPath $Executable -ErrorAction Stop).Path
}

function Parse-StrictLaunchArgumentVector([object[]]$ArgumentVector) {
    try {
        if ($null -eq $ArgumentVector) { return $null }
        $values = @($ArgumentVector | ForEach-Object { [string]$_ })
        if ($values.Count -notin @(13, 15, 17)) { return $null }
        if ($values[0] -cne '-m' -or $values[1] -cne 'tools.codex_supervisor' -or $values[2] -cne '--repo-root' -or $values[4] -cne '--runtime-home') { return $null }
        $index = 6
        $codexExecutable = $null
        if ($values[$index] -ceq '--codex-bin') {
            if (-not (Test-FullyQualifiedPath $values[$index + 1])) { return $null }
            $codexExecutable = $values[$index + 1]
            $index += 2
        }
        if ($values[$index] -cne 'serve' -or $values[$index + 1] -cne '--profile' -or $values[$index + 3] -cne '--ready-file' -or $values[$index + 5] -cne '--control-home') { return $null }
        if ([string]::IsNullOrWhiteSpace($values[3]) -or [string]::IsNullOrWhiteSpace($values[5]) -or [string]::IsNullOrWhiteSpace($values[$index + 2]) -or [string]::IsNullOrWhiteSpace($values[$index + 4]) -or [string]::IsNullOrWhiteSpace($values[$index + 6])) { return $null }
        if ($values[$index + 2] -notin @('OBSERVER', 'MANAGED_MANUAL', 'MAILBOX_MANUAL', 'SINGLE_WAKE')) { return $null }
        $next = $index + 7
        $durationPresent = $false
        $durationValue = $null
        if ($next -lt $values.Count) {
            if ($next + 2 -ne $values.Count -or $values[$next] -cne '--duration-seconds') { return $null }
            $parsedDuration = [double]0
            if (-not [double]::TryParse($values[$next + 1], [System.Globalization.NumberStyles]::Float, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$parsedDuration)) { return $null }
            if ([double]::IsNaN($parsedDuration) -or [double]::IsInfinity($parsedDuration) -or $parsedDuration -le 0) { return $null }
            $durationPresent = $true
            $durationValue = $parsedDuration
            $next += 2
        }
        if ($next -ne $values.Count) { return $null }
        return [pscustomobject]@{
            repo_root = $values[3]; runtime_home = $values[5]; codex_bin = $codexExecutable
            profile = $values[$index + 2]; ready_file = $values[$index + 4]; control_home = $values[$index + 6]
            duration_present = $durationPresent; duration_seconds = $durationValue
        }
    } catch { return $null }
}

function Test-RecordAndLaunchBinding(
    [object]$Record,
    [string]$RequestedRoot,
    [string]$RequestedHome,
    [string]$RequestedPythonPath
) {
    try {
        if (-not (Test-ExactFields $Record @('schema', 'pid', 'process_start_time_utc', 'executable', 'repo_root', 'runtime_home', 'profile', 'started_at', 'ready_file'))) { return $false }
        if ($Record.schema -ne 'HMASD_SUPERVISOR_PROCESS_V1') { return $false }
        if (-not (Test-SamePath ([string]$Record.repo_root) $RequestedRoot)) { return $false }
        if (-not (Test-SamePath ([string]$Record.runtime_home) $RequestedHome)) { return $false }
        if (-not (Test-SamePath ([string]$Record.executable) $RequestedPythonPath)) { return $false }
        $evidencePath = Join-Path $RequestedHome 'supervisor-launch-evidence.json'
        if (-not (Test-Path -LiteralPath $evidencePath -PathType Leaf)) { return $false }
        $evidence = Get-Content -Raw -LiteralPath $evidencePath | ConvertFrom-Json -ErrorAction Stop
        if (-not (Test-ExactFields $evidence @('schema', 'observed_at', 'argument_vector', 'control_home', 'ready_file'))) { return $false }
        if ($evidence.schema -ne 'HMASD_SUPERVISOR_LAUNCH_EVIDENCE_V2' -or -not ($evidence.argument_vector -is [System.Array])) { return $false }
        $parsed = Parse-StrictLaunchArgumentVector @($evidence.argument_vector)
        if ($null -eq $parsed) { return $false }
        if (-not (Test-SamePath ([string]$parsed.repo_root) $RequestedRoot)) { return $false }
        if (-not (Test-SamePath ([string]$parsed.runtime_home) $RequestedHome)) { return $false }
        if ([string]$parsed.profile -cne [string]$Record.profile) { return $false }
        if (-not (Test-SamePath ([string]$parsed.ready_file) ([string]$Record.ready_file)) -or -not (Test-SamePath ([string]$evidence.ready_file) ([string]$parsed.ready_file))) { return $false }
        if (-not (Test-SamePath ([string]$evidence.control_home) ([string]$parsed.control_home))) { return $false }
        return $parsed
    } catch { return $false }
}

function Test-ActiveCodexBinding(
    [string]$ActiveCodexBin,
    [string]$LaunchCodexBin,
    [bool]$CallerCodexWasBound,
    [string]$CallerCodexBin
) {
    try {
        if (-not (Test-FullyQualifiedPath $ActiveCodexBin)) { return $false }
        if (-not [string]::IsNullOrWhiteSpace($LaunchCodexBin)) {
            if (-not (Test-FullyQualifiedPath $LaunchCodexBin)) { return $false }
            if (-not (Test-SamePath $LaunchCodexBin $ActiveCodexBin)) { return $false }
        }
        if ($CallerCodexWasBound) {
            if (-not (Test-FullyQualifiedPath $CallerCodexBin)) { return $false }
            if (-not (Test-SamePath $CallerCodexBin $ActiveCodexBin)) { return $false }
        }
        return $true
    } catch { return $false }
}

function Test-ProcessRecordIdentity([object]$Record) {
    try {
        $process = Get-Process -Id ([int]$Record.pid) -ErrorAction Stop
        $start = $process.StartTime.ToUniversalTime().ToString('o')
        $path = [System.IO.Path]::GetFullPath([string]$process.Path).TrimEnd('\', '/').ToLowerInvariant()
        return ($start -eq [string]$Record.process_start_time_utc -and $path -eq ([string]$Record.executable).TrimEnd('\', '/').ToLowerInvariant())
    } catch { return $false }
}

function Test-ReadyAndActiveRun([string]$ProcessPath, [string]$ReadyPath, [string]$RuntimePath, [string]$Root) {
    $snippet = @'
import json, sqlite3, sys
from pathlib import Path
from tools.codex_supervisor.host_state import load_process_record, load_ready_record, validate_ready_record
try:
    process = load_process_record(Path(sys.argv[1]))
    ready = load_ready_record(Path(sys.argv[2]))
    errors = validate_ready_record(process, ready)
    active = False
    active_codex_binary = None
    db = Path(sys.argv[3]) / "state.sqlite3"
    if not errors and db.is_file():
        with sqlite3.connect(str(db)) as connection:
            row = connection.execute("SELECT initialized_at, ended_at, runtime_home, codex_binary FROM observer_runs WHERE run_id = ?", (ready.run_id,)).fetchone()
        active = bool(
            row
            and row[0] is not None
            and str(row[0]).strip()
            and row[1] is None
            and row[2] is not None
            and Path(row[2]).resolve() == Path(sys.argv[3]).resolve()
            and row[3] is not None
            and str(row[3]).strip()
        )
        active_codex_binary = str(row[3]) if active else None
    print(json.dumps({"valid_ready": not errors, "active_observer_run": active, "run_id": ready.run_id, "codex_binary": active_codex_binary}))
except Exception as exc:
    print(json.dumps({"valid_ready": False, "active_observer_run": False, "codex_binary": None, "error": str(exc)}))
    raise SystemExit(1)
'@
    $encodedSnippet = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($snippet))
    Push-Location -LiteralPath $Root
    try {
        $raw = & $PythonPath -c 'import base64,sys;code=base64.b64decode(sys.argv.pop(1));exec(code)' $encodedSnippet $ProcessPath $ReadyPath $RuntimePath 2>$null
        if (-not $raw) { return $null }
        try { return (($raw -join "`n") | ConvertFrom-Json) } catch { return $null }
    } finally { Pop-Location }
}

function Get-Doctor([string]$Root, [string]$RuntimePath, [string]$ActiveCodexBin) {
    $arguments = @('-m', 'tools.codex_supervisor', '--repo-root', $Root, '--runtime-home', $RuntimePath)
    if (-not [string]::IsNullOrWhiteSpace($ActiveCodexBin)) { $arguments += @('--codex-bin', $ActiveCodexBin) }
    $arguments += 'doctor'
    Push-Location -LiteralPath $Root
    try {
        $raw = & $PythonPath @arguments 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $raw) { return $null }
        return (($raw -join "`n") | ConvertFrom-Json)
    } catch { return $null }
    finally { Pop-Location }
}

function Test-DoctorGuards([object]$Doctor, [string]$ActiveCodexBin) {
    if ($null -eq $Doctor) { return $false }
    if (-not (Test-FullyQualifiedPath $ActiveCodexBin)) { return $false }
    $doctorCodexBin = [string]$Doctor.codex_binary
    if (-not (Test-FullyQualifiedPath $doctorCodexBin)) { return $false }
    return ($Doctor.status -eq 'OK' -and $null -eq $Doctor.binary_error -and (Test-SamePath $doctorCodexBin $ActiveCodexBin) -and [bool]$Doctor.codex_version -and [bool]$Doctor.schema_capture_present -and @($Doctor.static_guard_violations).Count -eq 0 -and [int]$Doctor.direct_state_write_violations -eq 0 -and [int]$Doctor.direct_mutation_call_violations -eq 0 -and [int]$Doctor.new_legacy_mutation_writes -eq 0)
}

$payload = [ordered]@{ schema = 'HMASD_SUPERVISOR_STATUS_V2'; state = 'INCIDENT'; observed_at = [datetime]::UtcNow.ToString('o'); process = $null; ready = $null; doctor = $null; incident = $null }
try {
    $callerCodexWasBound = $PSBoundParameters.ContainsKey('CodexBin')
    $paths = Resolve-ExternalRuntimeHome $RepoRoot $RuntimeHome
    $RepoRoot = $paths.RepoRoot; $RuntimeHome = $paths.RuntimeHome
    $processPath = Join-Path $RuntimeHome 'supervisor-process.json'
    if (-not (Test-Path -LiteralPath $processPath)) { $payload.state = 'STOPPED'; $payload | ConvertTo-Json -Depth 8; exit 0 }
    $PythonPath = Resolve-CanonicalExecutable $PythonPath 'PythonPath'
    $record = Get-Content -Raw -LiteralPath $processPath | ConvertFrom-Json -ErrorAction Stop
    $launchBinding = Test-RecordAndLaunchBinding $record $RepoRoot $RuntimeHome $PythonPath
    if (-not $launchBinding) {
        $payload.state = 'INCIDENT'
        $payload.incident = 'process executable or strict launch vector does not match the requested repository/runtime binding'
        $payload | ConvertTo-Json -Depth 8
        exit 0
    }
    $payload.process = $record
    if (-not (Test-ProcessRecordIdentity $record)) { $payload.state = 'STALE_IDENTITY'; $payload | ConvertTo-Json -Depth 8; exit 0 }
    $readyPath = [string]$record.ready_file
    if (-not (Test-Path -LiteralPath $readyPath)) { $payload.state = 'PROCESS_STARTING'; $payload | ConvertTo-Json -Depth 8; exit 0 }
    $ready = Test-ReadyAndActiveRun $processPath $readyPath $RuntimeHome $RepoRoot
    $payload.ready = $ready
    if ($null -eq $ready -or -not [bool]$ready.valid_ready -or -not [bool]$ready.active_observer_run) { $payload.state = 'INCIDENT'; $payload.incident = 'ready record or matching active observer run is invalid'; $payload | ConvertTo-Json -Depth 8; exit 0 }
    $activeCodexBin = [string]$ready.codex_binary
    if (-not (Test-ActiveCodexBinding $activeCodexBin ([string]$launchBinding.codex_bin) $callerCodexWasBound $CodexBin)) {
        $payload.state = 'INCIDENT'
        $payload.incident = 'launch or caller Codex binary does not match the active observer run'
        $payload | ConvertTo-Json -Depth 8
        exit 0
    }
    $doctor = Get-Doctor $RepoRoot $RuntimeHome $activeCodexBin
    $payload.doctor = $doctor
    if (-not (Test-DoctorGuards $doctor $activeCodexBin)) { $payload.state = 'INCIDENT'; $payload.incident = 'doctor binary, schema, or static guard failed'; $payload | ConvertTo-Json -Depth 8; exit 0 }
    $payload.state = 'READY'
} catch { $payload.state = 'INCIDENT'; $payload.incident = $_.Exception.Message }
$payload | ConvertTo-Json -Depth 8
