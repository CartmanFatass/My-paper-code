[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [string]$RuntimeHome
)

$ErrorActionPreference = 'Stop'

function Write-AtomicJson([string]$Path, [object]$Value) {
    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    $temporary = Join-Path $directory ('.{0}.{1}.tmp' -f (Split-Path -Leaf $Path), [guid]::NewGuid().ToString('N'))
    try {
        [System.IO.File]::WriteAllText($temporary, (($Value | ConvertTo-Json -Depth 8 -Compress) + [Environment]::NewLine), (New-Object System.Text.UTF8Encoding($false)))
        Move-Item -LiteralPath $temporary -Destination $Path -Force
    } finally { if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force } }
}

function Resolve-ExternalRuntimeHome([string]$Root, [string]$RuntimeCandidate) {
    $resolvedRoot = (Resolve-Path -LiteralPath $Root -ErrorAction Stop).Path
    if ([string]::IsNullOrWhiteSpace($RuntimeCandidate)) {
        if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) { throw 'LOCALAPPDATA is required' }
        $RuntimeCandidate = Join-Path $env:LOCALAPPDATA 'HMASD\codex-supervisor'
    }
    $fullHome = [System.IO.Path]::GetFullPath($RuntimeCandidate)
    if (Test-Path -LiteralPath $fullHome) { $fullHome = (Resolve-Path -LiteralPath $fullHome -ErrorAction Stop).Path }
    $rootKey = $resolvedRoot.TrimEnd('\', '/').ToLowerInvariant(); $homeKey = $fullHome.TrimEnd('\', '/').ToLowerInvariant()
    if ($homeKey -eq $rootKey -or $homeKey.StartsWith($rootKey + '\') -or $homeKey.StartsWith($rootKey + '/')) { throw 'runtime home must be external to the repository' }
    return $fullHome
}

function Test-ExternalPath([string]$Root, [string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    $rootKey = (Resolve-Path -LiteralPath $Root -ErrorAction Stop).Path.TrimEnd('\', '/').ToLowerInvariant()
    $pathKey = [System.IO.Path]::GetFullPath($Path).TrimEnd('\', '/').ToLowerInvariant()
    return -not ($pathKey -eq $rootKey -or $pathKey.StartsWith($rootKey + '\') -or $pathKey.StartsWith($rootKey + '/'))
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
    if ([int]$Actual.Pid -ne [int]$Expected.Pid -or [string]$Actual.StartTimeUtc -ne [string]$Expected.StartTimeUtc) { return $false }
    if (-not [string]::IsNullOrWhiteSpace([string]$Expected.Executable)) {
        return (Test-SamePath ([string]$Actual.Executable) ([string]$Expected.Executable))
    }
    return $true
}

function Get-ProcessTreeSnapshot([object]$ExpectedParent) {
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
    return [pscustomobject]@{ complete = $true; parent_state = $(if ($null -eq $currentParent) { 'MISSING' } else { 'MATCHED' }); identities = @($identities); descendant_count = $descendantIds.Count; error = $null }
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

function Stop-ProcessTreeFromSnapshot([object]$Snapshot, [object]$ExpectedParent) {
    if (-not [bool]$Snapshot.complete -or $Snapshot.parent_state -ne 'MATCHED') {
        return [pscustomobject]@{ cleanup_attempted = $false; cleanup_succeeded = $false; taskkill_exit_code = $null; remaining_identity_count = $null; action = 'TREE_SNAPSHOT_UNKNOWN_LEFT_UNTOUCHED' }
    }
    if (-not (Test-ProcessIdentitiesSafeToTerminate @($Snapshot.identities))) {
        return [pscustomobject]@{ cleanup_attempted = $false; cleanup_succeeded = $false; taskkill_exit_code = $null; remaining_identity_count = $null; action = 'IDENTITY_CHANGED_LEFT_UNTOUCHED' }
    }
    $taskkillExitCode = Invoke-TaskkillTree ([int]$ExpectedParent.Pid)
    $deadline = [datetime]::UtcNow.AddSeconds(5)
    $remaining = @(Get-MatchingProcessIdentities @($Snapshot.identities))
    while ($remaining.Count -gt 0 -and [datetime]::UtcNow -lt $deadline) {
        Start-Sleep -Milliseconds 100
        $remaining = @(Get-MatchingProcessIdentities @($Snapshot.identities))
    }
    $clean = ($taskkillExitCode -eq 0 -and $remaining.Count -eq 0)
    return [pscustomobject]@{
        cleanup_attempted = $true; cleanup_succeeded = $clean; taskkill_exit_code = $taskkillExitCode
        remaining_identity_count = $remaining.Count; action = $(if ($clean) { 'TREE_STOP_CONFIRMED' } elseif ($taskkillExitCode -ne 0) { 'TASKKILL_FAILED_SIGNALS_RETAINED' } else { 'TREE_STOP_NOT_CONFIRMED' })
    }
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

function Clear-StoppedSignals([string]$RuntimePath, [string]$ProcessPath, [string]$ReadyPath) {
    if (-not [string]::IsNullOrWhiteSpace($ReadyPath)) {
        if (-not (Test-ExternalPath $RepoRoot $ReadyPath)) { throw 'ready file recorded inside repository was left untouched' }
        Archive-SignalFile $RuntimePath $ReadyPath 'ready-stopped' | Out-Null
    }
    Archive-SignalFile $RuntimePath $ProcessPath 'supervisor-process-stopped' | Out-Null
    Archive-SignalFile $RuntimePath (Join-Path $RuntimePath 'supervisor-process-started.json') 'supervisor-process-started-stopped' | Out-Null
}

function Write-Incident([string]$RuntimePath, [string]$Reason) {
    Write-AtomicJson (Join-Path $RuntimePath 'supervisor-incident.json') ([ordered]@{ schema = 'HMASD_SUPERVISOR_INCIDENT_V2'; observed_at = [datetime]::UtcNow.ToString('o'); reason = $Reason })
}

try {
    $RuntimeHome = Resolve-ExternalRuntimeHome $RepoRoot $RuntimeHome
    $processPath = Join-Path $RuntimeHome 'supervisor-process.json'
    if (-not (Test-Path -LiteralPath $processPath)) { Write-Output 'HMASD_SUPERVISOR_STOPPED_V2'; exit 0 }
    $record = Get-Content -Raw -LiteralPath $processPath | ConvertFrom-Json -ErrorAction Stop
    if (-not (Test-ExactFields $record @('schema', 'pid', 'process_start_time_utc', 'executable', 'repo_root', 'runtime_home', 'profile', 'started_at', 'ready_file')) -or $record.schema -ne 'HMASD_SUPERVISOR_PROCESS_V1') {
        throw 'strict supervisor process record validation failed; readiness signals were retained'
    }
    if (-not (Test-SamePath ([string]$record.repo_root) ((Resolve-Path -LiteralPath $RepoRoot -ErrorAction Stop).Path)) -or -not (Test-SamePath ([string]$record.runtime_home) $RuntimeHome)) {
        throw 'process record repository/runtime binding mismatch; readiness signals were retained'
    }
    $expectedParent = [pscustomobject]@{ Pid = [int]$record.pid; StartTimeUtc = [string]$record.process_start_time_utc; Executable = [string]$record.executable }
    $snapshot = Get-ProcessTreeSnapshot $expectedParent
    if ($snapshot.parent_state -eq 'MISMATCH') {
        Write-Incident $RuntimeHome 'PID reuse or executable/start-time identity mismatch; process was left untouched'
        Write-Output 'HMASD_SUPERVISOR_INCIDENT_V2'
        exit 1
    }
    if (-not [bool]$snapshot.complete) {
        throw ('supervisor process tree snapshot was incomplete; readiness signals were retained: ' + [string]$snapshot.error)
    }
    if ($snapshot.parent_state -eq 'MISSING') {
        $knownDescendantsRemain = @(Get-MatchingProcessIdentities @($snapshot.identities | Select-Object -Skip 1)).Count
        if ($knownDescendantsRemain -ne 0) {
            throw "supervisor parent was already missing but $knownDescendantsRemain known descendant identities remain unverified; readiness signals were retained"
        }
        Clear-StoppedSignals $RuntimeHome $processPath ([string]$record.ready_file)
        Write-Output 'HMASD_SUPERVISOR_STOPPED_V2'
        exit 0
    }
    $outcome = Stop-ProcessTreeFromSnapshot $snapshot $expectedParent
    if (-not [bool]$outcome.cleanup_succeeded) {
        throw ('supervisor process tree stop was not confirmed; readiness signals were retained; action=' + [string]$outcome.action + '; taskkill_exit_code=' + [string]$outcome.taskkill_exit_code + '; remaining_identity_count=' + [string]$outcome.remaining_identity_count)
    }
    Clear-StoppedSignals $RuntimeHome $processPath ([string]$record.ready_file)
    Write-Output 'HMASD_SUPERVISOR_STOPPED_V2'
} catch {
    try { if ($RuntimeHome) { Write-Incident $RuntimeHome $_.Exception.Message } } catch { }
    Write-Output 'HMASD_SUPERVISOR_INCIDENT_V2'
    exit 1
}
