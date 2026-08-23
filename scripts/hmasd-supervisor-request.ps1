[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Command,
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ArgumentsJson,
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Operator,
    [string]$RuntimeHome,
    [string]$PythonExecutable = 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe',
    [ValidateRange(1, 86400)]
    [int]$TimeoutSeconds = 30
)

$ErrorActionPreference = 'Stop'

function Resolve-RuntimeHome([string]$Candidate) {
    if ([string]::IsNullOrWhiteSpace($Candidate)) {
        if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) { throw 'LOCALAPPDATA is required' }
        $Candidate = Join-Path $env:LOCALAPPDATA 'HMASD\codex-supervisor'
    }
    return [System.IO.Path]::GetFullPath($Candidate)
}

function Test-ExactFields([object]$Value, [string[]]$Expected) {
    if ($null -eq $Value) { return $false }
    $actual = @($Value.PSObject.Properties | ForEach-Object { $_.Name } | Sort-Object)
    $wanted = @($Expected | Sort-Object)
    return (($actual -join "`n") -eq ($wanted -join "`n"))
}

function Test-ExactReadyHost([string]$RuntimePath) {
    $processPath = Join-Path $RuntimePath 'supervisor-process.json'
    if (-not (Test-Path -LiteralPath $processPath -PathType Leaf)) { return $false }
    try {
        $record = Get-Content -Raw -LiteralPath $processPath | ConvertFrom-Json -ErrorAction Stop
        if (-not (Test-ExactFields $record @('schema', 'pid', 'process_start_time_utc', 'executable', 'repo_root', 'runtime_home', 'profile', 'started_at', 'ready_file'))) { return $false }
        if ($record.schema -ne 'HMASD_SUPERVISOR_PROCESS_V1' -or [int]$record.pid -le 0) { return $false }
        if ([System.IO.Path]::GetFullPath([string]$record.runtime_home).TrimEnd('\', '/').ToLowerInvariant() -ne $RuntimePath.TrimEnd('\', '/').ToLowerInvariant()) { return $false }
        $process = Get-Process -Id ([int]$record.pid) -ErrorAction Stop
        $actualStart = $process.StartTime.ToUniversalTime().ToString('o')
        $actualExecutable = [System.IO.Path]::GetFullPath([string]$process.Path).TrimEnd('\', '/').ToLowerInvariant()
        if ($actualStart -ne [string]$record.process_start_time_utc -or $actualExecutable -ne ([string]$record.executable).TrimEnd('\', '/').ToLowerInvariant()) { return $false }
        $readyPath = [System.IO.Path]::GetFullPath([string]$record.ready_file)
        if (-not (Test-Path -LiteralPath $readyPath -PathType Leaf)) { return $false }
        $ready = Get-Content -Raw -LiteralPath $readyPath | ConvertFrom-Json -ErrorAction Stop
        if (-not (Test-ExactFields $ready @('schema', 'run_id', 'process_id', 'initialized_at', 'watcher_active', 'first_reconciliation_completed', 'thread_count', 'runtime_home', 'profile'))) { return $false }
        if ($ready.schema -ne 'HMASD_SUPERVISOR_READY_V2' -or [int]$ready.process_id -ne [int]$record.pid) { return $false }
        if ([string]::IsNullOrWhiteSpace([string]$ready.run_id) -or [string]::IsNullOrWhiteSpace([string]$ready.initialized_at)) { return $false }
        if ($ready.watcher_active -ne $true -or $ready.first_reconciliation_completed -ne $true -or [int]$ready.thread_count -lt 0) { return $false }
        if ([System.IO.Path]::GetFullPath([string]$ready.runtime_home).TrimEnd('\', '/').ToLowerInvariant() -ne $RuntimePath.TrimEnd('\', '/').ToLowerInvariant()) { return $false }
        return ([string]$ready.profile -eq [string]$record.profile)
    } catch { return $false }
}

function Test-ActiveObserverRun([string]$RuntimePath, [string]$RunId, [string]$Interpreter) {
    $database = Join-Path $RuntimePath 'state.sqlite3'
    if (-not (Test-Path -LiteralPath $database -PathType Leaf)) { return $false }
    $snippet = 'import sqlite3,sys; row=sqlite3.connect(sys.argv[1]).execute(\"SELECT initialized_at, ended_at FROM observer_runs WHERE run_id = ?\",(sys.argv[2],)).fetchone(); raise SystemExit(0 if row and row[0] is not None and row[1] is None else 1)'
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $Interpreter -c $snippet $database $RunId
        $queryExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousPreference
    }
    return ($queryExitCode -eq 0)
}

function Get-ValidatedControlHome([string]$RuntimePath, [object]$Record) {
    $evidencePath = Join-Path $RuntimePath 'supervisor-launch-evidence.json'
    if (-not (Test-Path -LiteralPath $evidencePath -PathType Leaf)) { return $null }
    try {
        $evidence = Get-Content -Raw -LiteralPath $evidencePath | ConvertFrom-Json -ErrorAction Stop
        if (-not (Test-ExactFields $evidence @('schema', 'observed_at', 'argument_vector', 'control_home', 'ready_file'))) { return $null }
        if ($evidence.schema -ne 'HMASD_SUPERVISOR_LAUNCH_EVIDENCE_V2' -or -not ($evidence.argument_vector -is [System.Array])) { return $null }
        if ([string]::IsNullOrWhiteSpace([string]$evidence.observed_at) -or [string]::IsNullOrWhiteSpace([string]$evidence.control_home) -or [string]::IsNullOrWhiteSpace([string]$evidence.ready_file)) { return $null }
        $controlPath = [System.IO.Path]::GetFullPath([string]$evidence.control_home)
        $repoRoot = [System.IO.Path]::GetFullPath([string]$Record.repo_root)
        $readyPath = [System.IO.Path]::GetFullPath([string]$evidence.ready_file)
        if ($readyPath.TrimEnd('\', '/').ToLowerInvariant() -ne ([System.IO.Path]::GetFullPath([string]$Record.ready_file)).TrimEnd('\', '/').ToLowerInvariant()) { return $null }
        $repoKey = $repoRoot.TrimEnd('\', '/').ToLowerInvariant()
        $controlKey = $controlPath.TrimEnd('\', '/').ToLowerInvariant()
        if ($controlKey -eq $repoKey -or $controlKey.StartsWith($repoKey + '\') -or $controlKey.StartsWith($repoKey + '/')) { return $null }
        return $controlPath
    } catch { return $null }
}

function Write-AtomicRequest([string]$Destination, [string]$Json) {
    $directory = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    $temporary = Join-Path $directory ('.{0}.{1}.tmp' -f (Split-Path -Leaf $Destination), [guid]::NewGuid().ToString('N'))
    try {
        [System.IO.File]::WriteAllText($temporary, $Json + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
        [System.IO.File]::Move($temporary, $Destination)
    } finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
}

try {
    $arguments = $ArgumentsJson | ConvertFrom-Json -ErrorAction Stop
    if ($null -eq $arguments -or -not ($arguments -is [pscustomobject])) { throw 'ArgumentsJson must be one JSON object' }
    $RuntimeHome = Resolve-RuntimeHome $RuntimeHome
    # No inbox directory is created until a ready record and the exact live process identity agree.
    if (-not (Test-ExactReadyHost $RuntimeHome)) {
        Write-Output 'HMASD_SUPERVISOR_HOST_REQUIRED_V1'
        exit 1
    }
    $processRecord = Get-Content -Raw -LiteralPath (Join-Path $RuntimeHome 'supervisor-process.json') | ConvertFrom-Json -ErrorAction Stop
    $readyRecord = Get-Content -Raw -LiteralPath ([System.IO.Path]::GetFullPath([string]$processRecord.ready_file)) | ConvertFrom-Json -ErrorAction Stop
    if (-not (Test-ActiveObserverRun $RuntimeHome ([string]$readyRecord.run_id) $PythonExecutable)) {
        Write-Output 'HMASD_SUPERVISOR_HOST_REQUIRED_V1'
        exit 1
    }
    $control = Get-ValidatedControlHome $RuntimeHome $processRecord
    if ($null -eq $control) {
        Write-Output 'HMASD_SUPERVISOR_HOST_REQUIRED_V1'
        exit 1
    }
    $requestId = [guid]::NewGuid().ToString()
    $request = [ordered]@{
        schema = 'HMASD_SUPERVISOR_CONTROL_REQUEST_V1'
        request_id = $requestId
        # Python's datetime parser accepts ISO-8601 microseconds (six digits),
        # while .NET's round-trip format emits seven fractional digits.
        created_at = [datetime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.ffffffK')
        operator = $Operator
        command = $Command
        arguments = $arguments
    }
    $requestJson = $request | ConvertTo-Json -Depth 32 -Compress
    $requestPath = Join-Path (Join-Path $control 'inbox') ($requestId + '.json')
    Write-AtomicRequest $requestPath $requestJson
    $responsePath = Join-Path (Join-Path $control 'outbox') ($requestId + '.json')
    $deadline = [datetime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([datetime]::UtcNow -lt $deadline) {
        if (Test-Path -LiteralPath $responsePath -PathType Leaf) {
            $rawResponse = Get-Content -Raw -LiteralPath $responsePath
            $response = $rawResponse | ConvertFrom-Json -ErrorAction Stop
            if (-not (Test-ExactFields $response @('schema', 'request_id', 'status', 'payload', 'error', 'completed_at'))) { throw 'control response fields are invalid' }
            if ($response.schema -ne 'HMASD_SUPERVISOR_CONTROL_RESPONSE_V1') { throw 'control response schema is invalid' }
            if ($response.request_id -ne $requestId) { throw 'control response request_id does not match the submitted request' }
            if (@('OK', 'ERROR', 'REJECTED', 'NOT_IMPLEMENTED', 'SUBMISSION_UNCERTAIN') -notcontains [string]$response.status) { throw 'control response status is invalid' }
            # In particular, SUBMISSION_UNCERTAIN is emitted verbatim; this wrapper never replaces its request ID.
            Write-Output $rawResponse.TrimEnd("`r", "`n")
            exit 0
        }
        Start-Sleep -Milliseconds 100
    }
    # The request is already durable and may have crossed the host mutation
    # boundary.  Report uncertainty under the original ID and never resubmit.
    $timeoutResponse = [ordered]@{
        schema = 'HMASD_SUPERVISOR_CONTROL_RESPONSE_V1'
        request_id = $requestId
        status = 'SUBMISSION_UNCERTAIN'
        payload = [ordered]@{
            local_response_timeout = $true
            durable_request_written = $true
            timeout_seconds = $TimeoutSeconds
        }
        error = 'local response timeout after durable request write; inspect the durable request and host state; do not retry this request'
        completed_at = [datetime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.ffffffK')
    }
    Write-Output ($timeoutResponse | ConvertTo-Json -Depth 32 -Compress)
    exit 0
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
