[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$Command,
    [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$ArgumentsJson,
    [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$Operator,
    [string]$RuntimeHome,
    [string]$PythonExecutable = 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe',
    [ValidateRange(1, 86400)][int]$TimeoutSeconds = 30
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

function Test-SamePath([string]$Left, [string]$Right) {
    if ([string]::IsNullOrWhiteSpace($Left) -or [string]::IsNullOrWhiteSpace($Right)) { return $false }
    try { return ([System.IO.Path]::GetFullPath($Left).TrimEnd('\', '/').ToLowerInvariant() -eq [System.IO.Path]::GetFullPath($Right).TrimEnd('\', '/').ToLowerInvariant()) } catch { return $false }
}

function Test-FullyQualifiedPath([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    try {
        if ($Path -notmatch '^(?:[A-Za-z]:[\\/]|[\\/]{2}[^\\/]+[\\/][^\\/]+(?:[\\/]|$))') { return $false }
        [void][System.IO.Path]::GetFullPath($Path)
        return $true
    } catch { return $false }
}

function Test-ExternalPath([string]$Path, [string]$RepoRoot) {
    if (-not (Test-FullyQualifiedPath $Path)) { return $false }
    try {
        $pathKey = [System.IO.Path]::GetFullPath($Path).TrimEnd('\', '/').ToLowerInvariant()
        $rootKey = [System.IO.Path]::GetFullPath($RepoRoot).TrimEnd('\', '/').ToLowerInvariant()
        return -not ($pathKey -eq $rootKey -or $pathKey.StartsWith($rootKey + '\') -or $pathKey.StartsWith($rootKey + '/'))
    } catch { return $false }
}

function Test-ExternalExistingFile([string]$Path, [string]$RepoRoot) {
    if (-not (Test-ExternalPath $Path $RepoRoot)) { return $false }
    try { return (Test-Path -LiteralPath $Path -PathType Leaf) } catch { return $false }
}

function Parse-StrictLaunchArgumentVector([object[]]$ArgumentVector) {
    try {
        if ($null -eq $ArgumentVector) { return $null }
        $values = @($ArgumentVector | ForEach-Object { [string]$_ })
        if ($values.Count -notin @(13, 15, 17, 19)) { return $null }
        if ($values[0] -cne '-m' -or $values[1] -cne 'tools.codex_supervisor' -or $values[2] -cne '--repo-root' -or $values[4] -cne '--runtime-home') { return $null }
        $index = 6
        if ($values[$index] -ceq '--codex-bin') {
            if ($index + 1 -ge $values.Count -or -not (Test-FullyQualifiedPath $values[$index + 1])) { return $null }
            $index += 2
        }
        if ($index + 2 -ge $values.Count -or $values[$index] -cne 'serve' -or $values[$index + 1] -cne '--profile') { return $null }
        $profile = $values[$index + 2]
        if ($profile -notin @('OBSERVER', 'MANAGED_MANUAL', 'MAILBOX_MANUAL', 'SINGLE_WAKE')) { return $null }
        $next = $index + 3; $semanticState = $null
        if ($next -lt $values.Count -and $values[$next] -ceq '--semantic-state') {
            if ($next + 1 -ge $values.Count) { return $null }
            $semanticState = $values[$next + 1]; $next += 2
        }
        if ($profile -eq 'OBSERVER') {
            if ($null -ne $semanticState) { return $null }
        } elseif ($null -eq $semanticState -or -not (Test-ExternalExistingFile $semanticState $values[3])) { return $null }
        if ($next + 3 -ge $values.Count -or $values[$next] -cne '--ready-file' -or $values[$next + 2] -cne '--control-home') { return $null }
        if ([string]::IsNullOrWhiteSpace($values[3]) -or [string]::IsNullOrWhiteSpace($values[5]) -or [string]::IsNullOrWhiteSpace($values[$next + 1]) -or [string]::IsNullOrWhiteSpace($values[$next + 3])) { return $null }
        $readyFile = $values[$next + 1]; $controlHome = $values[$next + 3]; $next += 4
        if ($next -lt $values.Count) {
            if ($next + 2 -ne $values.Count -or $values[$next] -cne '--duration-seconds') { return $null }
            $duration = [double]0
            if (-not [double]::TryParse($values[$next + 1], [System.Globalization.NumberStyles]::Float, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$duration) -or [double]::IsNaN($duration) -or [double]::IsInfinity($duration) -or $duration -le 0) { return $null }
            $next += 2
        }
        if ($next -ne $values.Count) { return $null }
        return [pscustomobject]@{ repo_root = $values[3]; runtime_home = $values[5]; profile = $profile; semantic_state = $semanticState; ready_file = $readyFile; control_home = $controlHome }
    } catch { return $null }
}

function Get-ReadyStatus([string]$RecordedRepoRoot, [string]$RuntimePath, [string]$Interpreter) {
    $statusScript = Join-Path $PSScriptRoot 'hmasd-root-supervisor-status.ps1'
    try {
        $raw = & $statusScript -RepoRoot $RecordedRepoRoot -RuntimeHome $RuntimePath -PythonPath $Interpreter 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $raw) { return $null }
        $status = (($raw -join "`n") | ConvertFrom-Json -ErrorAction Stop)
        if (-not (Test-ExactFields $status @('schema', 'state', 'observed_at', 'process', 'ready', 'doctor', 'incident'))) { return $null }
        if ($status.schema -ne 'HMASD_SUPERVISOR_STATUS_V2' -or $status.state -ne 'READY' -or $null -eq $status.process -or $null -eq $status.ready) { return $null }
        return $status
    } catch { return $null }
}

function Get-ValidatedControlHome([string]$RuntimePath, [object]$Status, [object]$Record) {
    try {
        $fields = @('schema', 'pid', 'process_start_time_utc', 'executable', 'repo_root', 'runtime_home', 'profile', 'started_at', 'ready_file')
        if (-not (Test-ExactFields $Record $fields) -or -not (Test-ExactFields $Status.process $fields)) { return $null }
        foreach ($name in $fields) {
            $statusValue = [string]$Status.process.$name; $recordValue = [string]$Record.$name
            if ($name -in @('executable', 'repo_root', 'runtime_home', 'ready_file')) {
                if (-not (Test-SamePath $statusValue $recordValue)) { return $null }
            } elseif ($statusValue -cne $recordValue) { return $null }
        }
        if (-not (Test-SamePath ([string]$Record.runtime_home) $RuntimePath)) { return $null }
        $evidence = Get-Content -Raw -LiteralPath (Join-Path $RuntimePath 'supervisor-launch-evidence.json') | ConvertFrom-Json -ErrorAction Stop
        if (-not (Test-ExactFields $evidence @('schema', 'observed_at', 'argument_vector', 'control_home', 'ready_file'))) { return $null }
        if ($evidence.schema -ne 'HMASD_SUPERVISOR_LAUNCH_EVIDENCE_V2' -or -not ($evidence.argument_vector -is [System.Array])) { return $null }
        $launch = Parse-StrictLaunchArgumentVector @($evidence.argument_vector)
        if ($null -eq $launch) { return $null }
        if (-not (Test-SamePath ([string]$launch.repo_root) ([string]$Record.repo_root)) -or -not (Test-SamePath ([string]$launch.runtime_home) $RuntimePath) -or [string]$launch.profile -cne [string]$Record.profile) { return $null }
        if (-not (Test-SamePath ([string]$launch.ready_file) ([string]$Record.ready_file)) -or -not (Test-SamePath ([string]$evidence.ready_file) ([string]$launch.ready_file))) { return $null }
        if (-not (Test-SamePath ([string]$launch.control_home) ([string]$evidence.control_home)) -or -not (Test-ExternalPath ([string]$launch.control_home) ([string]$Record.repo_root))) { return $null }
        return [System.IO.Path]::GetFullPath([string]$launch.control_home)
    } catch { return $null }
}

function Invoke-ValidationSnippet([string]$RepoRoot, [string]$Interpreter, [string]$Snippet, [string[]]$Arguments) {
    $oldPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'; Push-Location -LiteralPath $RepoRoot
        & $Interpreter -c $Snippet @Arguments 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
    finally { if ((Get-Location).Path -eq $RepoRoot) { Pop-Location }; $ErrorActionPreference = $oldPreference }
}

function Test-CommandAllowed([string]$RepoRoot, [string]$Interpreter, [string]$Profile, [string]$Kind) {
    return (Invoke-ValidationSnippet $RepoRoot $Interpreter 'import sys; from tools.codex_supervisor.runtime_profiles import CommandKind, RuntimeProfile, require_command_allowed; require_command_allowed(RuntimeProfile(sys.argv[1]), CommandKind(sys.argv[2]))' @($Profile, $Kind))
}

function Test-ValidatedResponse([string]$RepoRoot, [string]$Interpreter, [string]$ResponsePath, [string]$RequestId) {
    return (Invoke-ValidationSnippet $RepoRoot $Interpreter 'import json,sys; from pathlib import Path; from tools.codex_supervisor.host_control import parse_response; value=json.loads(Path(sys.argv[1]).read_bytes().decode()); response=parse_response(value); raise SystemExit(0 if response.request_id == sys.argv[2] else 1)' @($ResponsePath, $RequestId))
}

function Write-AtomicRequest([string]$Destination, [string]$Json) {
    $directory = Split-Path -Parent $Destination; New-Item -ItemType Directory -Force -Path $directory | Out-Null
    $temporary = Join-Path $directory ('.{0}.{1}.tmp' -f (Split-Path -Leaf $Destination), [guid]::NewGuid().ToString('N'))
    try { [System.IO.File]::WriteAllText($temporary, $Json + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false))); [System.IO.File]::Move($temporary, $Destination) }
    finally { if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force } }
}

try {
    $arguments = $ArgumentsJson | ConvertFrom-Json -ErrorAction Stop
    if ($null -eq $arguments -or -not ($arguments -is [pscustomobject])) { throw 'ArgumentsJson must be one JSON object' }
    $RuntimeHome = Resolve-RuntimeHome $RuntimeHome; $processPath = Join-Path $RuntimeHome 'supervisor-process.json'
    if (-not (Test-Path -LiteralPath $processPath -PathType Leaf)) { Write-Output 'HMASD_SUPERVISOR_HOST_REQUIRED_V1'; exit 1 }
    $processRecord = Get-Content -Raw -LiteralPath $processPath | ConvertFrom-Json -ErrorAction Stop
    $recordedRepoRoot = [System.IO.Path]::GetFullPath([string]$processRecord.repo_root)
    $status = Get-ReadyStatus $recordedRepoRoot $RuntimeHome $PythonExecutable
    if ($null -eq $status) { Write-Output 'HMASD_SUPERVISOR_HOST_REQUIRED_V1'; exit 1 }
    $control = Get-ValidatedControlHome $RuntimeHome $status $processRecord
    if ($null -eq $control -or -not (Test-CommandAllowed $recordedRepoRoot $PythonExecutable ([string]$processRecord.profile) $Command)) { Write-Output 'HMASD_SUPERVISOR_HOST_REQUIRED_V1'; exit 1 }
    $requestId = [guid]::NewGuid().ToString()
    $request = [ordered]@{ schema = 'HMASD_SUPERVISOR_CONTROL_REQUEST_V1'; request_id = $requestId; created_at = [datetime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.ffffffK'); operator = $Operator; command = $Command; arguments = $arguments }
    $requestJson = $request | ConvertTo-Json -Depth 32 -Compress
    $requestPath = Join-Path (Join-Path $control 'inbox') ($requestId + '.json'); Write-AtomicRequest $requestPath $requestJson
    $responsePath = Join-Path (Join-Path $control 'outbox') ($requestId + '.json'); $deadline = [datetime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([datetime]::UtcNow -lt $deadline) {
        if (Test-Path -LiteralPath $responsePath -PathType Leaf) {
            if (-not (Test-ValidatedResponse $recordedRepoRoot $PythonExecutable $responsePath $requestId)) { throw 'control response violates the HostControlResponse contract' }
            Write-Output ((Get-Content -Raw -LiteralPath $responsePath).TrimEnd("`r", "`n")); exit 0
        }
        Start-Sleep -Milliseconds 100
    }
    $timeoutResponse = [ordered]@{ schema = 'HMASD_SUPERVISOR_CONTROL_RESPONSE_V1'; request_id = $requestId; status = 'SUBMISSION_UNCERTAIN'; payload = [ordered]@{ local_response_timeout = $true; durable_request_written = $true; timeout_seconds = $TimeoutSeconds }; error = 'local response timeout after durable request write; inspect the durable request and host state; do not retry this request'; completed_at = [datetime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.ffffffK') }
    Write-Output ($timeoutResponse | ConvertTo-Json -Depth 32 -Compress); exit 0
} catch { Write-Error $_.Exception.Message; exit 1 }
