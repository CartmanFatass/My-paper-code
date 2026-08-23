[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [string]$RuntimeHome,
    [string]$PythonPath = 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe',
    [string]$CodexBin,
    [ValidateSet('OBSERVER', 'MANAGED_MANUAL', 'MAILBOX_MANUAL', 'SINGLE_WAKE')]
    [string]$Profile = 'OBSERVER',
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
    return (Resolve-Path -LiteralPath $Executable -ErrorAction Stop).Path
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
    [string]$ReadyPath,
    [string]$ControlPath,
    [string]$CodexExecutable,
    [bool]$IncludeDuration,
    [double]$DurationValue
) {
    $arguments = @('-m', 'tools.codex_supervisor', '--repo-root', $Root, '--runtime-home', $RuntimePath)
    if (-not [string]::IsNullOrWhiteSpace($CodexExecutable)) { $arguments += @('--codex-bin', $CodexExecutable) }
    $arguments += @('serve', '--profile', $ProfileName, '--ready-file', $ReadyPath, '--control-home', $ControlPath)
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

function Test-LaunchEvidenceBinding([string]$EvidencePath, [string[]]$ExpectedVector, [string]$ReadyPath, [string]$ControlPath) {
    try {
        if (-not (Test-Path -LiteralPath $EvidencePath -PathType Leaf)) { return $false }
        $evidence = Get-Content -Raw -LiteralPath $EvidencePath | ConvertFrom-Json -ErrorAction Stop
        if (-not (Test-ExactFields $evidence @('schema', 'observed_at', 'argument_vector', 'control_home', 'ready_file'))) { return $false }
        if ($evidence.schema -ne 'HMASD_SUPERVISOR_LAUNCH_EVIDENCE_V2' -or -not ($evidence.argument_vector -is [System.Array])) { return $false }
        if (-not (Test-SamePath ([string]$evidence.control_home) $ControlPath)) { return $false }
        if (-not (Test-SamePath ([string]$evidence.ready_file) $ReadyPath)) { return $false }
        return (Test-ExactArgumentVector @($evidence.argument_vector) $ExpectedVector)
    } catch { return $false }
}

function Test-ReadyAndActiveRun([string]$ProcessPath, [string]$ReadyPath, [string]$RuntimePath, [string]$Root) {
    $snippet = @'
import sqlite3, sys
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
            "SELECT initialized_at, ended_at, runtime_home FROM observer_runs WHERE run_id = ?",
            (ready.run_id,),
        ).fetchone()
    active = bool(row and row[0] is not None and row[1] is None)
    same_home = bool(row and Path(row[2]).resolve() == Path(sys.argv[3]).resolve())
    raise SystemExit(0 if active and same_home else 1)
except Exception:
    raise SystemExit(1)
'@
    Push-Location -LiteralPath $Root
    try {
        & $PythonPath -c $snippet $ProcessPath $ReadyPath $RuntimePath 2>$null
        return ($LASTEXITCODE -eq 0)
    } finally { Pop-Location }
}

function Test-ExistingInvocation(
    [object]$Record,
    [string]$Root,
    [string]$RuntimePath,
    [string]$ProfileName,
    [string]$ReadyPath,
    [string]$ControlPath,
    [string]$RequestedPythonPath,
    [string[]]$ExpectedVector
) {
    if (-not (Test-ExactFields $Record @('schema', 'pid', 'process_start_time_utc', 'executable', 'repo_root', 'runtime_home', 'profile', 'started_at', 'ready_file'))) { return $false }
    if ([string]$Record.schema -cne 'HMASD_SUPERVISOR_PROCESS_V1') { return $false }
    if (-not (Test-SamePath ([string]$Record.repo_root) $Root)) { return $false }
    if (-not (Test-SamePath ([string]$Record.runtime_home) $RuntimePath)) { return $false }
    if ([string]$Record.profile -ne $ProfileName) { return $false }
    if (-not (Test-SamePath ([string]$Record.ready_file) $ReadyPath)) { return $false }
    if (-not (Test-SamePath ([string]$Record.executable) $RequestedPythonPath)) { return $false }
    $evidencePath = Join-Path $RuntimePath 'supervisor-launch-evidence.json'
    return (Test-LaunchEvidenceBinding $evidencePath $ExpectedVector $ReadyPath $ControlPath)
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
    if ([string]::IsNullOrWhiteSpace($ReadyFile)) { $ReadyFile = Join-Path $RuntimeHome 'ready.json' }
    if ([string]::IsNullOrWhiteSpace($ControlHome)) { $ControlHome = Join-Path $RuntimeHome 'control' }
    $ReadyFile = Resolve-ExternalTarget $ReadyFile $RepoRoot 'ready file'
    $ControlHome = Resolve-ExternalTarget $ControlHome $RepoRoot 'control home'
    New-Item -ItemType Directory -Force -Path $ControlHome | Out-Null
    $durationWasBound = $PSBoundParameters.ContainsKey('DurationSeconds')
    if ($durationWasBound -and ([double]::IsNaN($DurationSeconds) -or [double]::IsInfinity($DurationSeconds) -or $DurationSeconds -le 0)) {
        throw 'DurationSeconds must be a finite positive value when supplied'
    }
    $arguments = @(Get-SupervisorArgumentVector $RepoRoot $RuntimeHome $Profile $ReadyFile $ControlHome $CodexBin $durationWasBound $DurationSeconds)

    $processPath = Join-Path $RuntimeHome 'supervisor-process.json'
    if (Test-Path -LiteralPath $processPath) {
        try {
            $existing = Get-Content -Raw -LiteralPath $processPath | ConvertFrom-Json -ErrorAction Stop
            $existingIdentity = Test-ProcessRecordIdentity $existing
            $matchesInvocation = Test-ExistingInvocation $existing $RepoRoot $RuntimeHome $Profile $ReadyFile $ControlHome $PythonPath $arguments
            if ($existingIdentity -and $matchesInvocation -and (Test-ReadyAndActiveRun $processPath ([string]$existing.ready_file) $RuntimeHome $RepoRoot)) {
                Write-Output 'HMASD_SUPERVISOR_READY_V2'
                exit 0
            }
            Write-Incident $RuntimeHome 'existing host does not match the requested executable and exact repo/runtime/profile/ready/control/codex/duration launch vector and active run; stop then start is required'
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

    Write-AtomicJson (Join-Path $RuntimeHome 'supervisor-launch-evidence.json') ([ordered]@{
        schema = 'HMASD_SUPERVISOR_LAUNCH_EVIDENCE_V2'; observed_at = [datetime]::UtcNow.ToString('o'); argument_vector = @($arguments)
        control_home = $ControlHome; ready_file = $ReadyFile
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

    $deadline = [datetime]::UtcNow.AddSeconds(20)
    while ([datetime]::UtcNow -lt $deadline) {
        if ($null -eq (Test-ProcessRecordIdentity $record)) {
            throw 'supervisor process exited or identity changed before readiness'
        }
        if ((Test-Path -LiteralPath $ReadyFile) -and (Test-ReadyAndActiveRun $processPath $ReadyFile $RuntimeHome $RepoRoot)) {
            $readyValidated = $true
            Write-Output 'HMASD_SUPERVISOR_READY_V2'
            exit 0
        }
        Start-Sleep -Milliseconds 200
    }
    throw 'ready.json did not identify a newly initialized active observer run before the 20-second deadline'
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
