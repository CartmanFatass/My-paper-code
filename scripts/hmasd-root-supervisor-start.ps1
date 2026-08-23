[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [string]$RuntimeHome,
    [string]$PythonPath = 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe',
    [string]$CodexBin,
    [ValidateSet('OBSERVER', 'MANAGED_MANUAL', 'MAILBOX_MANUAL', 'SINGLE_WAKE')]
    [string]$Profile = 'OBSERVER',
    [string]$SemanticState,
    [string]$ReadyFile,
    [string]$ControlHome,
    [double]$DurationSeconds
)

$ErrorActionPreference = 'Stop'

function Write-AtomicJson([string]$Path, [object]$Value) {
    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    $temporary = Join-Path $directory ('.{0}.{1}.tmp' -f (Split-Path -Leaf $Path), [guid]::NewGuid().ToString('N'))
    try {
        $json = $Value | ConvertTo-Json -Depth 8 -Compress
        [System.IO.File]::WriteAllText($temporary, $json + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
        Move-Item -LiteralPath $temporary -Destination $Path -Force
    } finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
}

function Resolve-ExternalRuntimeHome([string]$Root, [string]$RuntimeCandidate) {
    $resolvedRoot = (Resolve-Path -LiteralPath $Root -ErrorAction Stop).Path
    if ([string]::IsNullOrWhiteSpace($RuntimeCandidate)) {
        if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) { throw 'LOCALAPPDATA is required' }
        $RuntimeCandidate = Join-Path $env:LOCALAPPDATA 'HMASD\codex-supervisor'
    }
    $fullHome = [System.IO.Path]::GetFullPath($RuntimeCandidate)
    $resolvedHome = $fullHome
    if (Test-Path -LiteralPath $fullHome) { $resolvedHome = (Resolve-Path -LiteralPath $fullHome -ErrorAction Stop).Path }
    $rootKey = $resolvedRoot.TrimEnd('\', '/').ToLowerInvariant()
    $homeKey = $resolvedHome.TrimEnd('\', '/').ToLowerInvariant()
    if ($homeKey -eq $rootKey -or $homeKey.StartsWith($rootKey + '\') -or $homeKey.StartsWith($rootKey + '/')) {
        throw 'runtime home must be external to the repository'
    }
    New-Item -ItemType Directory -Force -Path $fullHome | Out-Null
    $resolvedHome = (Resolve-Path -LiteralPath $fullHome -ErrorAction Stop).Path
    return [pscustomobject]@{ RepoRoot = $resolvedRoot; RuntimeHome = $resolvedHome }
}

function Resolve-ExternalTarget([string]$Target, [string]$Root, [string]$Label) {
    $candidate = [System.IO.Path]::GetFullPath($Target)
    $probe = $candidate
    $suffix = New-Object 'System.Collections.Generic.List[string]'
    while (-not (Test-Path -LiteralPath $probe)) {
        $leaf = Split-Path -Leaf $probe
        $parent = Split-Path -Parent $probe
        if ([string]::IsNullOrWhiteSpace($leaf) -or [string]::IsNullOrWhiteSpace($parent) -or $parent -eq $probe) {
            throw "cannot canonicalize $Label"
        }
        $suffix.Insert(0, $leaf)
        $probe = $parent
    }
    $candidate = (Resolve-Path -LiteralPath $probe -ErrorAction Stop).Path
    foreach ($part in $suffix) { $candidate = Join-Path $candidate $part }
    $rootKey = $Root.TrimEnd('\', '/').ToLowerInvariant()
    $targetKey = $candidate.TrimEnd('\', '/').ToLowerInvariant()
    if ($targetKey -eq $rootKey -or $targetKey.StartsWith($rootKey + '\') -or $targetKey.StartsWith($rootKey + '/')) {
        throw "$Label must be external to the repository"
    }
    return $candidate
}

function Resolve-ExternalExistingFile([string]$Target, [string]$Root, [string]$Label) {
    if ([string]::IsNullOrWhiteSpace($Target)) { throw "$Label is required" }
    if (-not (Test-Path -LiteralPath $Target -PathType Leaf)) {
        throw "$Label must be an existing regular file"
    }
    $resolved = (Resolve-Path -LiteralPath $Target -ErrorAction Stop).Path
    $rootKey = $Root.TrimEnd('\', '/').ToLowerInvariant()
    $targetKey = $resolved.TrimEnd('\', '/').ToLowerInvariant()
    if ($targetKey -eq $rootKey -or $targetKey.StartsWith($rootKey + '\') -or $targetKey.StartsWith($rootKey + '/')) {
        throw "$Label must be external to the repository"
    }
    return $resolved
}

function Test-SamePath([string]$Left, [string]$Right) {
    if ([string]::IsNullOrWhiteSpace($Left) -or [string]::IsNullOrWhiteSpace($Right)) { return $false }
    $leftKey = [System.IO.Path]::GetFullPath($Left).TrimEnd('\', '/').ToLowerInvariant()
    $rightKey = [System.IO.Path]::GetFullPath($Right).TrimEnd('\', '/').ToLowerInvariant()
    return ($leftKey -eq $rightKey)
}

function Test-ExactFields([object]$Value, [string[]]$Expected) {
    if ($null -eq $Value) { return $false }
    $actual = @($Value.PSObject.Properties | ForEach-Object { $_.Name } | Sort-Object)
    $wanted = @($Expected | Sort-Object)
    return (($actual -join "`n") -eq ($wanted -join "`n"))
}

function Resolve-CanonicalExecutable([string]$Executable, [string]$Label) {
    if ([string]::IsNullOrWhiteSpace($Executable)) { throw "$Label is required" }
    if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) { throw "$Label must be an existing regular file" }
    return (Resolve-Path -LiteralPath $Executable -ErrorAction Stop).Path
}

function Get-StartupReadyTimeout([string]$Root, [string]$RuntimePath, [string]$Interpreter) {
    Push-Location -LiteralPath $Root
    try {
        $raw = & $Interpreter -c 'import sys; from pathlib import Path; from tools.codex_supervisor.config import load_observer_config; root=Path(sys.argv[1]).resolve(); print(load_observer_config(root, root.parent / ".hmasd-supervisor-config-probe").startup_ready_timeout_seconds)' $Root 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $raw) { throw 'observer startup timeout configuration is invalid' }
        $value = [double]0
        if (-not [double]::TryParse([string]($raw | Select-Object -Last 1), [Globalization.NumberStyles]::Float, [Globalization.CultureInfo]::InvariantCulture, [ref]$value) -or [double]::IsNaN($value) -or [double]::IsInfinity($value) -or $value -le 0) {
            throw 'observer startup timeout configuration is invalid'
        }
        return $value
    } finally { Pop-Location }
}

function Test-SafeCmdBatchPath([string]$CanonicalBatchPath) {
    if ([string]::IsNullOrWhiteSpace($CanonicalBatchPath)) { return $false }
    if ($CanonicalBatchPath.IndexOfAny([char[]]"`r`n`"%!") -ge 0) { return $false }
    $hasQuoteSensitive = ($CanonicalBatchPath.IndexOfAny([char[]]"^&|<>()") -ge 0)
    return (-not $hasQuoteSensitive -or $CanonicalBatchPath -match '\s')
}

function Test-ExactCmdAppServerVector(
    [object[]]$Actual,
    [string]$CommandProcessor,
    [string]$CanonicalBatchPath
) {
    try {
        $values = @($Actual | ForEach-Object { [string]$_ })
        if ($values.Count -ne 7 -or -not (Test-SamePath $values[0] $CommandProcessor)) { return $false }
        if ($values[1] -cne '/d' -or $values[2] -cne '/s' -or $values[3] -cne '/c') { return $false }
        if ($values[4] -cne 'call' -or -not (Test-SafeCmdBatchPath $CanonicalBatchPath)) { return $false }
        if ($values[5] -cne $CanonicalBatchPath -or $values[6] -cne 'app-server') { return $false }
        return $true
    } catch { return $false }
}

function ConvertFrom-WindowsCommandLine([string]$CommandLine) {
    if ([string]::IsNullOrWhiteSpace($CommandLine)) { return $null }
    if ($null -eq ([System.Management.Automation.PSTypeName]'HMASD.NativeCommandLine').Type) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
namespace HMASD {
    public static class NativeCommandLine {
        [DllImport("shell32.dll", SetLastError = true)]
        public static extern IntPtr CommandLineToArgvW(
            [MarshalAs(UnmanagedType.LPWStr)] string commandLine,
            out int argumentCount);
        [DllImport("kernel32.dll")]
        public static extern IntPtr LocalFree(IntPtr memory);
    }
}
'@
    }
    $argumentCount = 0
    $native = [HMASD.NativeCommandLine]::CommandLineToArgvW($CommandLine, [ref]$argumentCount)
    if ($native -eq [IntPtr]::Zero -or $argumentCount -le 0) { return $null }
    try {
        $result = @()
        for ($index = 0; $index -lt $argumentCount; $index++) {
            $pointer = [Runtime.InteropServices.Marshal]::ReadIntPtr($native, $index * [IntPtr]::Size)
            $result += [Runtime.InteropServices.Marshal]::PtrToStringUni($pointer)
        }
        return @($result)
    } finally {
        [void][HMASD.NativeCommandLine]::LocalFree($native)
    }
}

function Get-ObservedProcessFacts([int]$ProcessId) {
    try {
        if ($ProcessId -le 0) { return $null }
        $rows = @(Get-CimInstance -ClassName Win32_Process -Filter ("ProcessId = {0}" -f $ProcessId) -ErrorAction Stop)
        if ($rows.Count -ne 1) { return $null }
        $row = $rows[0]
        if ([int]$row.ProcessId -ne $ProcessId -or [string]::IsNullOrWhiteSpace([string]$row.ExecutablePath) -or [string]::IsNullOrWhiteSpace([string]$row.CommandLine)) { return $null }
        $process = Get-Process -Id $ProcessId -ErrorAction Stop
        $processPath = [System.IO.Path]::GetFullPath([string]$process.Path)
        $cimPath = [System.IO.Path]::GetFullPath([string]$row.ExecutablePath)
        if (-not (Test-SamePath $processPath $cimPath)) { return $null }
        return [pscustomobject]@{
            process_id = [int]$row.ProcessId
            parent_process_id = [int]$row.ParentProcessId
            executable = $processPath
            command_line = [string]$row.CommandLine
            argument_vector = @(ConvertFrom-WindowsCommandLine ([string]$row.CommandLine))
            process_start_time_utc = $process.StartTime.ToUniversalTime().ToString('o')
        }
    } catch { return $null }
}

function Test-ExactObservedProcessVector([object]$Facts, [string]$ExpectedExecutable, [string[]]$ExpectedArguments) {
    try {
        if ($null -eq $Facts -or -not (Test-SamePath ([string]$Facts.executable) $ExpectedExecutable)) { return $false }
        $actual = @($Facts.argument_vector)
        if ($actual.Count -ne ($ExpectedArguments.Count + 1)) { return $false }
        if (-not (Test-SamePath ([string]$actual[0]) $ExpectedExecutable)) { return $false }
        for ($index = 0; $index -lt $ExpectedArguments.Count; $index++) {
            if ([string]$actual[$index + 1] -cne [string]$ExpectedArguments[$index]) { return $false }
        }
        return $true
    } catch { return $false }
}

function Test-SupervisorHostProcessBinding([object]$Record, [string]$RequestedPythonPath, [string[]]$ExpectedArguments) {
    try {
        $facts = Get-ObservedProcessFacts ([int]$Record.pid)
        if ($null -eq $facts) { return $false }
        if ([string]$facts.process_start_time_utc -ne [string]$Record.process_start_time_utc) { return $false }
        if (-not (Test-SamePath ([string]$facts.executable) ([string]$Record.executable)) -or -not (Test-SamePath ([string]$facts.executable) $RequestedPythonPath)) { return $false }
        return (Test-ExactObservedProcessVector $facts $RequestedPythonPath $ExpectedArguments)
    } catch { return $false }
}

function Test-AppServerProcessBinding(
    [int]$ChildProcessId,
    [object]$HostRecord,
    [string]$ActiveCodexBin,
    [string]$InitializedAt
) {
    try {
        if ($ChildProcessId -le 0 -or $ChildProcessId -eq [int]$HostRecord.pid) { return $false }
        $hostFacts = Get-ObservedProcessFacts ([int]$HostRecord.pid)
        $childFacts = Get-ObservedProcessFacts $ChildProcessId
        if ($null -eq $hostFacts -or $null -eq $childFacts) { return $false }
        if ([string]$hostFacts.process_start_time_utc -ne [string]$HostRecord.process_start_time_utc) { return $false }
        if ([int]$childFacts.parent_process_id -ne [int]$HostRecord.pid) { return $false }
        $initialized = [DateTimeOffset]::Parse($InitializedAt, [Globalization.CultureInfo]::InvariantCulture).UtcDateTime
        $hostStarted = [DateTimeOffset]::Parse([string]$hostFacts.process_start_time_utc, [Globalization.CultureInfo]::InvariantCulture).UtcDateTime
        $childStarted = [DateTimeOffset]::Parse([string]$childFacts.process_start_time_utc, [Globalization.CultureInfo]::InvariantCulture).UtcDateTime
        if ($childStarted -lt $hostStarted.AddSeconds(-1) -or $childStarted -gt $initialized.AddSeconds(1)) { return $false }
        $activeBinary = Resolve-CanonicalExecutable $ActiveCodexBin 'active Codex binary'
        $suffix = [System.IO.Path]::GetExtension($activeBinary).ToLowerInvariant()
        if ($suffix -eq '.cmd' -or $suffix -eq '.bat') {
            $commandProcessor = $env:COMSPEC
            if ([string]::IsNullOrWhiteSpace($commandProcessor)) { $commandProcessor = Join-Path $env:SystemRoot 'System32\cmd.exe' }
            $commandProcessor = Resolve-CanonicalExecutable $commandProcessor 'COMSPEC'
            if (-not (Test-SamePath ([string]$childFacts.executable) $commandProcessor)) { return $false }
            return (Test-ExactCmdAppServerVector @($childFacts.argument_vector) $commandProcessor $activeBinary)
        }
        return (Test-ExactObservedProcessVector $childFacts $activeBinary @('app-server'))
    } catch { return $false }
}

function Test-ExactArgumentVector([object[]]$Actual, [string[]]$Expected) {
    if ($null -eq $Actual -or $Actual.Count -ne $Expected.Count) { return $false }
    for ($index = 0; $index -lt $Expected.Count; $index++) {
        if ([string]$Actual[$index] -cne [string]$Expected[$index]) { return $false }
    }
    return $true
}

function Get-SupervisorArgumentVector(
    [string]$Root,
    [string]$RuntimePath,
    [string]$ProfileName,
    [string]$SemanticPath,
    [string]$ReadyPath,
    [string]$ControlPath,
    [string]$CodexExecutable,
    [bool]$IncludeDuration,
    [double]$DurationValue
) {
    $arguments = @('-m', 'tools.codex_supervisor', '--repo-root', $Root, '--runtime-home', $RuntimePath)
    if (-not [string]::IsNullOrWhiteSpace($CodexExecutable)) { $arguments += @('--codex-bin', $CodexExecutable) }
    $arguments += @('serve', '--profile', $ProfileName)
    if (-not [string]::IsNullOrWhiteSpace($SemanticPath)) { $arguments += @('--semantic-state', $SemanticPath) }
    $arguments += @('--ready-file', $ReadyPath, '--control-home', $ControlPath)
    if ($IncludeDuration) {
        $arguments += @('--duration-seconds', $DurationValue.ToString([System.Globalization.CultureInfo]::InvariantCulture))
    }
    return $arguments
}

function ConvertTo-WindowsCommandLineArgument([string]$Argument) {
    if ($null -eq $Argument) { $Argument = '' }
    if ($Argument.Length -gt 0 -and $Argument -notmatch '[\s"]') { return $Argument }
    $builder = New-Object System.Text.StringBuilder
    [void]$builder.Append('"')
    $backslashes = 0
    foreach ($character in $Argument.ToCharArray()) {
        if ($character -eq '\') {
            $backslashes++
            continue
        }
        if ($character -eq '"') {
            if ($backslashes -gt 0) { [void]$builder.Append(('\' * ($backslashes * 2))) }
            [void]$builder.Append('\"')
        } else {
            if ($backslashes -gt 0) { [void]$builder.Append(('\' * $backslashes)) }
            [void]$builder.Append($character)
        }
        $backslashes = 0
    }
    if ($backslashes -gt 0) { [void]$builder.Append(('\' * ($backslashes * 2))) }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function ConvertTo-WindowsCommandLine([string[]]$ArgumentVector) {
    return ((@($ArgumentVector) | ForEach-Object { ConvertTo-WindowsCommandLineArgument ([string]$_) }) -join ' ')
}

function Get-ExactProcessIdentity([int]$ProcessId) {
    try {
        $process = Get-Process -Id $ProcessId -ErrorAction Stop
        $start = $process.StartTime.ToUniversalTime().ToString('o')
        $path = $null
        try {
            if (-not [string]::IsNullOrWhiteSpace([string]$process.Path)) {
                $path = [System.IO.Path]::GetFullPath([string]$process.Path)
            }
        } catch { $path = $null }
        return [pscustomobject]@{ Process = $process; Pid = $process.Id; StartTimeUtc = $start; Executable = $path }
    } catch { return $null }
}

function Test-IdentityMatches([object]$Actual, [object]$Expected) {
    if ($null -eq $Actual -or $null -eq $Expected) { return $false }
    if ([int]$Actual.Pid -ne [int]$Expected.Pid) { return $false }
    if ([string]$Actual.StartTimeUtc -ne [string]$Expected.StartTimeUtc) { return $false }
    if (-not [string]::IsNullOrWhiteSpace([string]$Expected.Executable)) {
        return (Test-SamePath ([string]$Actual.Executable) ([string]$Expected.Executable))
    }
    return $true
}

function Test-ProcessRecordIdentity([object]$Record) {
    if ($null -eq $Record -or [int]$Record.pid -le 0) { return $null }
    $identity = Get-ExactProcessIdentity ([int]$Record.pid)
    if ($null -eq $identity) { return $null }
    if ($identity.StartTimeUtc -ne [string]$Record.process_start_time_utc) { return $null }
    if (-not (Test-SamePath $identity.Executable ([string]$Record.executable))) { return $null }
    return $identity
}

function Test-LaunchEvidenceBinding([string]$EvidencePath, [string[]]$ExpectedVector, [string]$ReadyPath, [string]$ControlPath, [double]$ExpectedReadyTimeout) {
    try {
        if (-not (Test-Path -LiteralPath $EvidencePath -PathType Leaf)) { return $false }
        $evidence = Get-Content -Raw -LiteralPath $EvidencePath | ConvertFrom-Json -ErrorAction Stop
        if (-not (Test-ExactFields $evidence @('schema', 'observed_at', 'argument_vector', 'control_home', 'ready_file', 'startup_ready_timeout_seconds'))) { return $false }
        if ($evidence.schema -ne 'HMASD_SUPERVISOR_LAUNCH_EVIDENCE_V2' -or -not ($evidence.argument_vector -is [System.Array])) { return $false }
        if (-not (Test-SamePath ([string]$evidence.control_home) $ControlPath)) { return $false }
        if (-not (Test-SamePath ([string]$evidence.ready_file) $ReadyPath)) { return $false }
        if ([double]$evidence.startup_ready_timeout_seconds -ne $ExpectedReadyTimeout) { return $false }
        return (Test-ExactArgumentVector @($evidence.argument_vector) $ExpectedVector)
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
    if validate_ready_record(process, ready):
        raise SystemExit(1)
    database = Path(sys.argv[3]) / "state.sqlite3"
    if not database.is_file():
        raise SystemExit(1)
    with sqlite3.connect(str(database)) as connection:
        row = connection.execute(
            "SELECT initialized_at, ended_at, runtime_home, codex_binary, process_id FROM observer_runs WHERE run_id = ?",
            (ready.run_id,),
        ).fetchone()
    active = bool(
        row and row[0] is not None and str(row[0]).strip() and row[1] is None
        and row[2] is not None and Path(row[2]).resolve() == Path(sys.argv[3]).resolve()
        and row[3] is not None and str(row[3]).strip()
        and type(row[4]) is int and row[4] > 0
    )
    print(json.dumps({
        "valid_ready": True, "active_observer_run": active, "run_id": ready.run_id,
        "codex_binary": str(row[3]) if active else None,
        "app_server_process_id": int(row[4]) if active else None,
        "initialized_at": ready.initialized_at,
    }))
except Exception as exc:
    print(json.dumps({"valid_ready": False, "active_observer_run": False, "codex_binary": None, "app_server_process_id": None, "initialized_at": None, "error": str(exc)}))
    raise SystemExit(1)
'@
    $encodedSnippet = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($snippet))
    Push-Location -LiteralPath $Root
    try {
        $raw = & $PythonPath -c 'import base64,sys;code=base64.b64decode(sys.argv.pop(1));exec(code)' $encodedSnippet $ProcessPath $ReadyPath $RuntimePath 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $raw) { return $null }
        try { return (($raw -join "`n") | ConvertFrom-Json) } catch { return $null }
    } finally { Pop-Location }
}

function Test-ReadyProcessTruth(
    [object]$ReadyFacts,
    [object]$HostRecord,
    [string]$LaunchCodexBin,
    [bool]$LaunchCodexWasBound
) {
    try {
        if ($null -eq $ReadyFacts -or -not [bool]$ReadyFacts.valid_ready -or -not [bool]$ReadyFacts.active_observer_run) { return $false }
        $activeCodexBin = Resolve-CanonicalExecutable ([string]$ReadyFacts.codex_binary) 'active Codex binary'
        if ($LaunchCodexWasBound -and -not (Test-SamePath $activeCodexBin $LaunchCodexBin)) { return $false }
        return (Test-AppServerProcessBinding ([int]$ReadyFacts.app_server_process_id) $HostRecord $activeCodexBin ([string]$ReadyFacts.initialized_at))
    } catch { return $false }
}

function Test-ExistingInvocation(
    [object]$Record,
    [string]$Root,
    [string]$RuntimePath,
    [string]$ProfileName,
    [string]$ReadyPath,
    [string]$ControlPath,
    [string]$RequestedPythonPath,
    [string[]]$ExpectedVector,
    [double]$ExpectedReadyTimeout
) {
    if (-not (Test-ExactFields $Record @('schema', 'pid', 'process_start_time_utc', 'executable', 'repo_root', 'runtime_home', 'profile', 'started_at', 'ready_file'))) { return $false }
    if ([string]$Record.schema -cne 'HMASD_SUPERVISOR_PROCESS_V1') { return $false }
    if (-not (Test-SamePath ([string]$Record.repo_root) $Root)) { return $false }
    if (-not (Test-SamePath ([string]$Record.runtime_home) $RuntimePath)) { return $false }
    if ([string]$Record.profile -ne $ProfileName) { return $false }
    if (-not (Test-SamePath ([string]$Record.ready_file) $ReadyPath)) { return $false }
    if (-not (Test-SamePath ([string]$Record.executable) $RequestedPythonPath)) { return $false }
    $evidencePath = Join-Path $RuntimePath 'supervisor-launch-evidence.json'
    return (Test-LaunchEvidenceBinding $evidencePath $ExpectedVector $ReadyPath $ControlPath $ExpectedReadyTimeout)
}

function Archive-SignalFile([string]$RuntimePath, [string]$Path, [string]$Label) {
    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $archive = Join-Path $RuntimePath 'archive'
    New-Item -ItemType Directory -Force -Path $archive | Out-Null
    $destination = Join-Path $archive ('{0}.{1}.{2}.json' -f $Label, [datetime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ'), [guid]::NewGuid().ToString('N'))
    Copy-Item -LiteralPath $Path -Destination $destination -ErrorAction Stop
    Remove-Item -LiteralPath $Path -Force -ErrorAction Stop
    return $destination
}

function Get-ProcessTreeSnapshot([object]$ExpectedParent) {
    if ($null -eq $ExpectedParent) {
        return [pscustomobject]@{ complete = $false; parent_state = 'UNAVAILABLE'; identities = @(); descendant_count = 0; error = 'parent identity unavailable' }
    }
    $currentParent = Get-ExactProcessIdentity ([int]$ExpectedParent.Pid)
    if ($null -ne $currentParent -and -not (Test-IdentityMatches $currentParent $ExpectedParent)) {
        return [pscustomobject]@{ complete = $false; parent_state = 'MISMATCH'; identities = @($ExpectedParent); descendant_count = 0; error = 'parent identity changed' }
    }
    try {
        $rows = @(Get-CimInstance -ClassName Win32_Process -ErrorAction Stop | Select-Object ProcessId, ParentProcessId)
    } catch {
        return [pscustomobject]@{ complete = $false; parent_state = $(if ($null -eq $currentParent) { 'MISSING' } else { 'MATCHED' }); identities = @($ExpectedParent); descendant_count = 0; error = ('process tree enumeration failed: ' + $_.Exception.Message) }
    }
    $children = @{}
    foreach ($row in $rows) {
        $parentKey = [string][int]$row.ParentProcessId
        if (-not $children.ContainsKey($parentKey)) { $children[$parentKey] = @() }
        $children[$parentKey] += [int]$row.ProcessId
    }
    $descendantIds = New-Object 'System.Collections.Generic.List[int]'
    $visited = @{}
    $queue = New-Object 'System.Collections.Generic.Queue[int]'
    $queue.Enqueue([int]$ExpectedParent.Pid)
    while ($queue.Count -gt 0) {
        $ancestor = $queue.Dequeue()
        $ancestorKey = [string]$ancestor
        if (-not $children.ContainsKey($ancestorKey)) { continue }
        foreach ($childPid in @($children[$ancestorKey])) {
            $childKey = [string]$childPid
            if ($visited.ContainsKey($childKey)) { continue }
            $visited[$childKey] = $true
            $descendantIds.Add([int]$childPid)
            $queue.Enqueue([int]$childPid)
        }
    }
    $identities = @($ExpectedParent)
    foreach ($descendantPid in $descendantIds) {
        $descendant = Get-ExactProcessIdentity $descendantPid
        if ($null -eq $descendant) {
            return [pscustomobject]@{ complete = $false; parent_state = $(if ($null -eq $currentParent) { 'MISSING' } else { 'MATCHED' }); identities = @($identities); descendant_count = $descendantIds.Count; error = "descendant identity $descendantPid could not be captured" }
        }
        $identities += $descendant
    }
    return [pscustomobject]@{
        complete = $true; parent_state = $(if ($null -eq $currentParent) { 'MISSING' } else { 'MATCHED' })
        identities = @($identities); descendant_count = $descendantIds.Count; error = $null
    }
}

function Test-ProcessIdentitiesSafeToTerminate([object[]]$Identities) {
    foreach ($identity in @($Identities)) {
        $current = Get-ExactProcessIdentity ([int]$identity.Pid)
        if ($null -ne $current -and -not (Test-IdentityMatches $current $identity)) { return $false }
    }
    return $true
}

function Get-MatchingProcessIdentities([object[]]$Identities) {
    $matching = @()
    foreach ($identity in @($Identities)) {
        $current = Get-ExactProcessIdentity ([int]$identity.Pid)
        if ($null -ne $current -and (Test-IdentityMatches $current $identity)) { $matching += $identity }
    }
    return @($matching)
}

function Invoke-TaskkillTree([int]$ProcessId) {
    $taskkill = Join-Path $env:SystemRoot 'System32\taskkill.exe'
    & $taskkill /PID ([string]$ProcessId) /T /F *> $null
    return [int]$LASTEXITCODE
}

function Stop-LaunchedProcessTreeIdentityChecked([object]$Identity) {
    $snapshot = Get-ProcessTreeSnapshot $Identity
    if (-not [bool]$snapshot.complete) {
        return [pscustomobject]@{ identity_matched = ($snapshot.parent_state -eq 'MATCHED'); cleanup_attempted = $false; process_exited = $false; cleanup_succeeded = $false; taskkill_exit_code = $null; descendant_count = [int]$snapshot.descendant_count; remaining_identity_count = $null; action = 'TREE_SNAPSHOT_UNKNOWN_LEFT_UNTOUCHED'; detail = [string]$snapshot.error }
    }
    if ($snapshot.parent_state -eq 'MISSING') {
        $knownDescendantsRemain = @(Get-MatchingProcessIdentities @($snapshot.identities | Select-Object -Skip 1)).Count
        $clean = ($knownDescendantsRemain -eq 0)
        return [pscustomobject]@{ identity_matched = $false; cleanup_attempted = $false; process_exited = $true; cleanup_succeeded = $clean; taskkill_exit_code = $null; descendant_count = [int]$snapshot.descendant_count; remaining_identity_count = $knownDescendantsRemain; action = $(if ($clean) { 'ALREADY_EXITED_NO_KNOWN_DESCENDANTS' } else { 'PARENT_MISSING_DESCENDANTS_RETAINED' }); detail = $null }
    }
    if ($snapshot.parent_state -ne 'MATCHED' -or -not (Test-ProcessIdentitiesSafeToTerminate @($snapshot.identities))) {
        return [pscustomobject]@{ identity_matched = $false; cleanup_attempted = $false; process_exited = $false; cleanup_succeeded = $false; taskkill_exit_code = $null; descendant_count = [int]$snapshot.descendant_count; remaining_identity_count = $null; action = 'IDENTITY_CHANGED_LEFT_UNTOUCHED'; detail = 'a snapshotted process identity changed before termination' }
    }
    $taskkillExitCode = Invoke-TaskkillTree ([int]$Identity.Pid)
    $deadline = [datetime]::UtcNow.AddSeconds(5)
    $remaining = @(Get-MatchingProcessIdentities @($snapshot.identities))
    while ($remaining.Count -gt 0 -and [datetime]::UtcNow -lt $deadline) {
        Start-Sleep -Milliseconds 100
        $remaining = @(Get-MatchingProcessIdentities @($snapshot.identities))
    }
    $clean = ($taskkillExitCode -eq 0 -and $remaining.Count -eq 0)
    return [pscustomobject]@{
        identity_matched = $true; cleanup_attempted = $true; process_exited = (@($remaining | Where-Object { [int]$_.Pid -eq [int]$Identity.Pid }).Count -eq 0)
        cleanup_succeeded = $clean; taskkill_exit_code = $taskkillExitCode; descendant_count = [int]$snapshot.descendant_count
        remaining_identity_count = $remaining.Count; action = $(if ($clean) { 'TREE_STOP_CONFIRMED' } elseif ($taskkillExitCode -ne 0) { 'TASKKILL_FAILED_SIGNALS_RETAINED' } else { 'TREE_STOP_NOT_CONFIRMED' }); detail = $null
    }
}

function Complete-FailedLaunchCleanup(
    [string]$RuntimePath,
    [object]$Identity,
    [string]$ProcessPath,
    [string]$ReadyPath,
    [string]$Reason
) {
    $outcome = Stop-LaunchedProcessTreeIdentityChecked $Identity
    $archived = @()
    $signalErrors = @()
    $signalsInvalidated = $true
    if ([bool]$outcome.cleanup_succeeded) {
        foreach ($signal in @(
            [pscustomobject]@{ Path = $ReadyPath; Label = 'ready' },
            [pscustomobject]@{ Path = $ProcessPath; Label = 'supervisor-process' },
            [pscustomobject]@{ Path = (Join-Path $RuntimePath 'supervisor-process-started.json'); Label = 'supervisor-process-started' }
        )) {
            try {
                $saved = Archive-SignalFile $RuntimePath $signal.Path $signal.Label
                if ($saved) { $archived += $saved }
            } catch {
                $signalErrors += ($signal.Label + ': ' + $_.Exception.Message)
                try {
                    if (Test-Path -LiteralPath $signal.Path -PathType Leaf) {
                        Remove-Item -LiteralPath $signal.Path -Force -ErrorAction Stop
                    }
                } catch {
                    $signalsInvalidated = $false
                    $signalErrors += ($signal.Label + ' invalidation: ' + $_.Exception.Message)
                }
            }
        }
    } else {
        $signalsInvalidated = $false
    }
    $record = [ordered]@{
        schema = 'HMASD_SUPERVISOR_START_CLEANUP_V1'; observed_at = [datetime]::UtcNow.ToString('o')
        launched_pid = $(if ($null -eq $Identity) { $null } else { [int]$Identity.Pid })
        identity_matched = [bool]$outcome.identity_matched; cleanup_attempted = [bool]$outcome.cleanup_attempted
        process_exited = [bool]$outcome.process_exited
        cleanup_succeeded = ([bool]$outcome.cleanup_succeeded -and $signalsInvalidated)
        taskkill_exit_code = $outcome.taskkill_exit_code; action = [string]$outcome.action
        descendant_count = $outcome.descendant_count; remaining_identity_count = $outcome.remaining_identity_count
        reason = $Reason; archived_signals = @($archived); signal_errors = @($signalErrors)
    }
    Write-AtomicJson (Join-Path $RuntimePath 'supervisor-start-cleanup.json') $record
    return [pscustomobject]$record
}

function Write-Incident([string]$RuntimePath, [string]$Reason) {
    Write-AtomicJson (Join-Path $RuntimePath 'supervisor-incident.json') ([ordered]@{
        schema = 'HMASD_SUPERVISOR_INCIDENT_V2'; observed_at = [datetime]::UtcNow.ToString('o'); reason = $Reason
    })
}

$launched = $false
$readyValidated = $false
$launchedIdentity = $null
$processPath = $null
try {
    $paths = Resolve-ExternalRuntimeHome $RepoRoot $RuntimeHome
    $RepoRoot = $paths.RepoRoot
    $RuntimeHome = $paths.RuntimeHome
    $PythonPath = Resolve-CanonicalExecutable $PythonPath 'PythonPath'
    $startupReadyTimeoutSeconds = Get-StartupReadyTimeout $RepoRoot $RuntimeHome $PythonPath
    $codexWasBound = $PSBoundParameters.ContainsKey('CodexBin')
    if ($codexWasBound) { $CodexBin = Resolve-CanonicalExecutable $CodexBin 'CodexBin' }
    if ([string]::IsNullOrWhiteSpace($ReadyFile)) { $ReadyFile = Join-Path $RuntimeHome 'ready.json' }
    if ([string]::IsNullOrWhiteSpace($ControlHome)) { $ControlHome = Join-Path $RuntimeHome 'control' }
    $ReadyFile = Resolve-ExternalTarget $ReadyFile $RepoRoot 'ready file'
    $ControlHome = Resolve-ExternalTarget $ControlHome $RepoRoot 'control home'
    $semanticWasBound = $PSBoundParameters.ContainsKey('SemanticState')
    if ($Profile -eq 'OBSERVER') {
        if ($semanticWasBound) { throw 'OBSERVER profile forbids SemanticState' }
        $SemanticState = $null
    } else {
        if (-not $semanticWasBound -or [string]::IsNullOrWhiteSpace($SemanticState)) {
            throw "$Profile profile requires SemanticState"
        }
        $SemanticState = Resolve-ExternalExistingFile $SemanticState $RepoRoot 'semantic state'
    }
    New-Item -ItemType Directory -Force -Path $ControlHome | Out-Null
    $durationWasBound = $PSBoundParameters.ContainsKey('DurationSeconds')
    if ($durationWasBound -and ([double]::IsNaN($DurationSeconds) -or [double]::IsInfinity($DurationSeconds) -or $DurationSeconds -le 0)) {
        throw 'DurationSeconds must be a finite positive value when supplied'
    }
    $arguments = @(Get-SupervisorArgumentVector $RepoRoot $RuntimeHome $Profile $SemanticState $ReadyFile $ControlHome $CodexBin $durationWasBound $DurationSeconds)

    $processPath = Join-Path $RuntimeHome 'supervisor-process.json'
    if (Test-Path -LiteralPath $processPath) {
        try {
            $existing = Get-Content -Raw -LiteralPath $processPath | ConvertFrom-Json -ErrorAction Stop
            $existingIdentity = Test-ProcessRecordIdentity $existing
            $matchesInvocation = Test-ExistingInvocation $existing $RepoRoot $RuntimeHome $Profile $ReadyFile $ControlHome $PythonPath $arguments $startupReadyTimeoutSeconds
            $existingReady = Test-ReadyAndActiveRun $processPath ([string]$existing.ready_file) $RuntimeHome $RepoRoot
            if ($existingIdentity -and $matchesInvocation -and (Test-SupervisorHostProcessBinding $existing $PythonPath $arguments) -and (Test-ReadyProcessTruth $existingReady $existing $CodexBin $codexWasBound)) {
                Write-Output 'HMASD_SUPERVISOR_READY_V2'
                exit 0
            }
            Write-Incident $RuntimeHome 'existing host does not match the requested executable and exact repo/runtime/profile/semantic-state/ready/control/codex/duration launch vector and active run; stop then start is required'
            Write-Output 'HMASD_SUPERVISOR_INCIDENT_V2'
            exit 1
        } catch {
            Write-Incident $RuntimeHome ('existing process record is invalid: ' + $_.Exception.Message + '; stop then start is required')
            Write-Output 'HMASD_SUPERVISOR_INCIDENT_V2'
            exit 1
        }
    }

    Archive-SignalFile $RuntimeHome $ReadyFile 'ready-prelaunch' | Out-Null

    $stdout = Join-Path $RuntimeHome 'supervisor.stdout.log'
    $stderr = Join-Path $RuntimeHome 'supervisor.stderr.log'
    $serializedArguments = ConvertTo-WindowsCommandLine $arguments
    $process = Start-Process -FilePath $PythonPath -ArgumentList $serializedArguments -WorkingDirectory $RepoRoot -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    $launched = $true
    $launchedIdentity = Get-ExactProcessIdentity $process.Id
    if ($null -eq $launchedIdentity) { throw 'started supervisor process identity could not be observed' }
    if (-not (Test-SupervisorHostProcessBinding ([pscustomobject]@{ pid = $launchedIdentity.Pid; process_start_time_utc = $launchedIdentity.StartTimeUtc; executable = $launchedIdentity.Executable }) $PythonPath $arguments)) {
        throw 'started supervisor host executable or command line does not match the exact serialized launch vector'
    }

    Write-AtomicJson (Join-Path $RuntimeHome 'supervisor-launch-evidence.json') ([ordered]@{
        schema = 'HMASD_SUPERVISOR_LAUNCH_EVIDENCE_V2'; observed_at = [datetime]::UtcNow.ToString('o'); argument_vector = @($arguments)
        control_home = $ControlHome; ready_file = $ReadyFile
        startup_ready_timeout_seconds = $startupReadyTimeoutSeconds
    })
    $record = [ordered]@{
        schema = 'HMASD_SUPERVISOR_PROCESS_V1'; pid = $launchedIdentity.Pid; process_start_time_utc = $launchedIdentity.StartTimeUtc
        executable = $launchedIdentity.Executable; repo_root = $RepoRoot; runtime_home = $RuntimeHome; profile = $Profile
        started_at = [datetime]::UtcNow.ToString('o'); ready_file = $ReadyFile
    }
    Write-AtomicJson $processPath $record
    Write-AtomicJson (Join-Path $RuntimeHome 'supervisor-process-started.json') ([ordered]@{
        schema = 'HMASD_SUPERVISOR_PROCESS_STARTED_V2'; state = 'PROCESS_STARTED'; observed_at = [datetime]::UtcNow.ToString('o')
        pid = $launchedIdentity.Pid; process_start_time_utc = $launchedIdentity.StartTimeUtc; process_record = $processPath
    })

    $deadline = [datetime]::UtcNow.AddSeconds($startupReadyTimeoutSeconds)
    while ([datetime]::UtcNow -lt $deadline) {
        if ($null -eq (Test-ProcessRecordIdentity $record)) {
            throw 'supervisor process exited or identity changed before readiness'
        }
        $readyFacts = $(if (Test-Path -LiteralPath $ReadyFile) { Test-ReadyAndActiveRun $processPath $ReadyFile $RuntimeHome $RepoRoot } else { $null })
        if ($null -ne $readyFacts -and (Test-SupervisorHostProcessBinding ([pscustomobject]$record) $PythonPath $arguments) -and (Test-ReadyProcessTruth $readyFacts ([pscustomobject]$record) $CodexBin $codexWasBound)) {
            $readyValidated = $true
            Write-Output 'HMASD_SUPERVISOR_READY_V2'
            exit 0
        }
        Start-Sleep -Milliseconds 200
    }
    throw ('ready.json did not identify a newly initialized active observer run before the configured {0}-second deadline' -f $startupReadyTimeoutSeconds)
} catch {
    $reason = $_.Exception.Message
    if ($launched -and -not $readyValidated) {
        try {
            $cleanup = Complete-FailedLaunchCleanup $RuntimeHome $launchedIdentity $processPath $ReadyFile $reason
            $reason = $reason + '; identity-checked cleanup_succeeded=' + ([string][bool]$cleanup.cleanup_succeeded).ToLowerInvariant()
        } catch {
            $reason = $reason + '; cleanup recording failed: ' + $_.Exception.Message
        }
    }
    try { if ($RuntimeHome) { Write-Incident $RuntimeHome $reason } } catch { }
    Write-Output 'HMASD_SUPERVISOR_INCIDENT_V2'
    exit 1
}
