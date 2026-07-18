[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("init", "show", "transition", "validate")]
    [string]$Mode,
    [Parameter(Mandatory = $true)]
    [string]$RunPath,
    [ValidateSet("RUNNING", "TERMINAL_DETECTED", "RELAY_CONFIRMED", "AUTOMATION_PAUSED", "CLOSED", "BLOCKED")]
    [string]$State,
    [string]$RunId,
    [string]$StatusAuthority,
    [string]$ControllerHostId,
    [string]$ControllerThreadId,
    [string]$ControllerModelId,
    [string]$ControllerReasoningEffort,
    [string]$MonitorHostId,
    [string]$MonitorThreadId,
    [string]$MonitorModelId,
    [string]$MonitorReasoningEffort,
    [string]$AutomationId,
    [string]$HandoffId,
    [ValidateSet("completed", "failed", "missing")]
    [string]$RunState,
    [string]$Phase,
    [string]$StatusUpdatedAt,
    [string]$StatusPath,
    [string]$PayloadPath,
    [string]$ReadThreadReceipt,
    [string]$Blocker,
    [string]$ResolutionReceipt
)

$ErrorActionPreference = "Stop"
$run = (Resolve-Path -LiteralPath $RunPath).Path
$statePath = Join-Path $run "monitor_state.json"
$orderedStates = @("RUNNING", "TERMINAL_DETECTED", "RELAY_CONFIRMED", "AUTOMATION_PAUSED", "CLOSED")
$allowedStates = $orderedStates + "BLOCKED"
$turnIdPattern = '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
$automationIdPattern = '^[A-Za-z0-9._-]+$'

function Require-Text([string]$Value, [string]$Name) {
    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw "Missing required field: $Name"
    }
}

function Read-State {
    if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
        throw "Missing monitor state: $statePath"
    }
    Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json -DateKind String
}

function Assert-RunPath([string]$Path, [string]$Name) {
    if ([string]::IsNullOrWhiteSpace($Path)) {
        throw "Missing required path: $Name"
    }
    $resolved = if ([IO.Path]::IsPathRooted($Path)) {
        [IO.Path]::GetFullPath($Path)
    } else {
        [IO.Path]::GetFullPath((Join-Path $run $Path))
    }
    if (-not $resolved.StartsWith($run + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Name escapes run directory: $Path"
    }
}

function Resolve-RunFile([string]$Path, [string]$Name) {
    Assert-RunPath $Path $Name
    if ([IO.Path]::IsPathRooted($Path)) {
        return [IO.Path]::GetFullPath($Path)
    }
    return [IO.Path]::GetFullPath((Join-Path $run $Path))
}

function Read-StatusAuthority([object]$Document) {
    $path = Resolve-RunFile ([string]$Document.status_authority) "status_authority"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        return [pscustomobject]@{ exists = $false; path = $path; values = @{} }
    }
    $values = @{}
    foreach ($line in Get-Content -LiteralPath $path) {
        if ($line -match '^\s*([^=]+?)\s*=\s*(.*?)\s*$') {
            $key = $matches[1].Trim()
            if ($values.ContainsKey($key)) {
                throw "Duplicate status-authority key: $key"
            }
            $values[$key] = $matches[2]
        }
    }
    return [pscustomobject]@{ exists = $true; path = $path; values = $values }
}

function Assert-TerminalAuthority([object]$Document) {
    $status = Read-StatusAuthority $Document
    $terminalStatusPath = Resolve-RunFile ([string]$Document.terminal.status_path) "terminal.status_path"
    if (-not [string]::Equals($status.path, $terminalStatusPath, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Terminal status_path must equal the frozen status_authority"
    }

    if ($Document.terminal.run_state -eq "missing") {
        if ($status.exists) {
            throw "run_state=missing is invalid because status_authority exists"
        }
        return
    }
    if (-not $status.exists) {
        throw "Terminal state requires the authoritative status file"
    }

    foreach ($key in @("state", "phase", "run_id", "updated")) {
        if ([string]::IsNullOrWhiteSpace([string]$status.values[$key])) {
            throw "Status authority is missing required key: $key"
        }
    }
    $actualState = switch ([string]$status.values.state) {
        "complete" { "completed" }
        "completed" { "completed" }
        "failed" { "failed" }
        default { throw "Status authority is not terminal: $($status.values.state)" }
    }
    if ($actualState -ne $Document.terminal.run_state -or
        [string]$status.values.phase -ne [string]$Document.terminal.phase -or
        [string]$status.values.run_id -ne $Document.run_id -or
        [string]$status.values.updated -ne [string]$Document.terminal.status_updated_at) {
        throw "Terminal identity does not match status_authority"
    }

    $payloadKey = if ($actualState -eq "completed") { "result_path" } else { "error_path" }
    $authorityPayload = [string]$status.values[$payloadKey]
    if ([string]::IsNullOrWhiteSpace($authorityPayload)) {
        throw "Status authority is missing terminal payload key: $payloadKey"
    }
    $resolvedAuthorityPayload = Resolve-RunFile $authorityPayload "status_authority.$payloadKey"
    $resolvedTerminalPayload = Resolve-RunFile ([string]$Document.terminal.payload_path) "terminal.payload_path"
    if (-not [string]::Equals($resolvedAuthorityPayload, $resolvedTerminalPayload, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Terminal payload_path does not match status_authority.$payloadKey"
    }
}

function Write-State([object]$Document) {
    $Document.updated_at = [DateTimeOffset]::Now.ToString("o")
    $Document | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statePath -Encoding UTF8
}

function Resolve-AutomationConfigPath([string]$Automation) {
    if ($Automation -notmatch $automationIdPattern) {
        throw "Invalid automation id: $Automation"
    }
    $codexHome = if (-not [string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
        [IO.Path]::GetFullPath($env:CODEX_HOME)
    } else {
        [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE ".codex"))
    }
    return Join-Path $codexHome "automations/$Automation/automation.toml"
}

function Read-AutomationConfig([string]$Automation, [string]$MonitorThread) {
    $configPath = Resolve-AutomationConfigPath $Automation
    if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
        throw "Missing automation config: $configPath"
    }
    $values = @{}
    foreach ($line in Get-Content -LiteralPath $configPath) {
        if ($line -match '^\s*(id|status|target_thread_id)\s*=\s*"([^"]*)"\s*$') {
            $values[$matches[1]] = $matches[2]
        } elseif ($line -match '^\s*updated_at\s*=\s*([0-9]+)\s*$') {
            $values.updated_at = $matches[1]
        }
    }
    if ($values.id -ne $Automation -or
        $values.target_thread_id -ne $MonitorThread -or
        [string]::IsNullOrWhiteSpace($values.status) -or
        [string]::IsNullOrWhiteSpace($values.updated_at)) {
        throw "Automation config does not match the frozen automation and monitor"
    }
    return [pscustomobject]@{
        config_path = $configPath
        status = $values.status
        updated_at = $values.updated_at
    }
}

function Parse-ReadThreadReceipt([string]$Receipt) {
    if ([string]::IsNullOrWhiteSpace($Receipt)) {
        throw "RELAY_CONFIRMED requires -ReadThreadReceipt"
    }
    $parsed = @{}
    foreach ($part in $Receipt.Split(";")) {
        $pair = $part.Split("=", 2)
        if ($pair.Count -ne 2 -or [string]::IsNullOrWhiteSpace($pair[0]) -or
            [string]::IsNullOrWhiteSpace($pair[1]) -or $parsed.ContainsKey($pair[0])) {
            throw "Malformed read_thread receipt"
        }
        $parsed[$pair[0]] = $pair[1]
    }
    $required = @("host", "thread", "turn", "handoff")
    if ($parsed.Keys.Count -ne $required.Count -or
        @($required | Where-Object { -not $parsed.ContainsKey($_) }).Count -ne 0) {
        throw "read_thread receipt must contain exactly host, thread, turn and handoff"
    }
    return $parsed
}

function Assert-State([object]$Document) {
    if ($Document.schema_version -ne 1) {
        throw "Unsupported monitor-state schema: $($Document.schema_version)"
    }
    if ($Document.run_id -ne (Split-Path -Leaf $run)) {
        throw "Run identity mismatch: $($Document.run_id)"
    }
    if ($Document.state -notin $allowedStates) {
        throw "Invalid monitor state: $($Document.state)"
    }
    foreach ($field in @(
        $Document.status_authority,
        $Document.controller.host_id,
        $Document.controller.thread_id,
        $Document.controller.model_id,
        $Document.controller.reasoning_effort,
        $Document.monitor.host_id,
        $Document.monitor.thread_id,
        $Document.monitor.model_id,
        $Document.monitor.reasoning_effort,
        $Document.automation_id
    )) {
        if ([string]::IsNullOrWhiteSpace([string]$field)) {
            throw "Monitor identity fields must be nonempty"
        }
    }
    if ($Document.automation_id -notmatch $automationIdPattern) {
        throw "Invalid automation_id"
    }
    $expectedAutomationPath = Resolve-AutomationConfigPath ([string]$Document.automation_id)
    if ($null -eq $Document.automation_baseline -or
        [string]::IsNullOrWhiteSpace([string]$Document.automation_baseline.status) -or
        $Document.automation_baseline.status -eq "PAUSED" -or
        [string]::IsNullOrWhiteSpace([string]$Document.automation_baseline.updated_at) -or
        -not [string]::Equals([string]$Document.automation_baseline.config_path, $expectedAutomationPath, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Monitor state requires a non-paused activation baseline for the frozen automation"
    }
    $baselineUpdated = 0L
    if (-not [long]::TryParse([string]$Document.automation_baseline.updated_at, [ref]$baselineUpdated)) {
        throw "Invalid automation baseline updated_at"
    }
    Assert-RunPath ([string]$Document.status_authority) "status_authority"
    if ($Document.state -eq "BLOCKED") {
        if ([string]::IsNullOrWhiteSpace($Document.blocker) -or
            $Document.previous_state -notin $orderedStates) {
            throw "BLOCKED requires blocker and previous_state"
        }
    }
    $effectiveState = if ($Document.state -eq "BLOCKED") {
        [string]$Document.previous_state
    } else {
        [string]$Document.state
    }
    $rank = [Array]::IndexOf($orderedStates, $effectiveState)
    if ($rank -ge 1) {
        if ($Document.terminal.run_state -notin @("completed", "failed", "missing")) {
            throw "Invalid terminal run_state"
        }
        foreach ($field in @(
            $Document.handoff_id,
            $Document.terminal.run_state,
            $Document.terminal.phase,
            $Document.terminal.status_updated_at,
            $Document.terminal.status_path,
            $Document.terminal.payload_path
        )) {
            if ([string]::IsNullOrWhiteSpace([string]$field)) {
                throw "Terminal state requires complete terminal identity"
            }
        }
        Assert-RunPath ([string]$Document.terminal.status_path) "terminal.status_path"
        Assert-RunPath ([string]$Document.terminal.payload_path) "terminal.payload_path"
        $parsedTimestamp = [DateTimeOffset]::MinValue
        if (-not [DateTimeOffset]::TryParse([string]$Document.terminal.status_updated_at, [ref]$parsedTimestamp)) {
            throw "Invalid terminal status_updated_at"
        }
        $expectedHandoff = "$($Document.run_id):$($Document.terminal.run_state):$($Document.terminal.status_updated_at)"
        if ($Document.handoff_id -ne $expectedHandoff) {
            throw "handoff_id does not match run/state/status timestamp"
        }
        Assert-TerminalAuthority $Document
    }
    if ($rank -ge 2) {
        if ($Document.relay_receipt.delivered_turn_id -notmatch $turnIdPattern -or
            $Document.relay_receipt.handoff_id -ne $Document.handoff_id -or
            $Document.relay_receipt.target_host_id -ne $Document.controller.host_id -or
            $Document.relay_receipt.target_thread_id -ne $Document.controller.thread_id -or
            [string]::IsNullOrWhiteSpace([string]$Document.relay_receipt.confirmed_at)) {
            throw "RELAY_CONFIRMED requires a receipt matching the frozen controller"
        }
    }
    if ($rank -ge 3) {
        if ($Document.pause_receipt.automation_id -ne $Document.automation_id -or
            $Document.pause_receipt.status -ne "PAUSED" -or
            -not [string]::Equals([string]$Document.pause_receipt.config_path, $expectedAutomationPath, [StringComparison]::OrdinalIgnoreCase) -or
            [string]::IsNullOrWhiteSpace($Document.pause_receipt.automation_updated_at)) {
            throw "AUTOMATION_PAUSED requires a PAUSED receipt for the frozen automation"
        }
        $pauseUpdated = 0L
        if (-not [long]::TryParse([string]$Document.pause_receipt.automation_updated_at, [ref]$pauseUpdated) -or
            $pauseUpdated -le $baselineUpdated) {
            throw "Pause receipt must be newer than the activation baseline"
        }
        $relayConfirmed = [DateTimeOffset]::MinValue
        if (-not [DateTimeOffset]::TryParse([string]$Document.relay_receipt.confirmed_at, [ref]$relayConfirmed) -or
            [DateTimeOffset]::FromUnixTimeMilliseconds($pauseUpdated) -lt $relayConfirmed) {
            throw "Pause receipt must occur after relay confirmation"
        }
    }
}

if ($Mode -eq "init") {
    if (Test-Path -LiteralPath $statePath) {
        throw "Monitor state already exists: $statePath"
    }
    foreach ($pair in @{
        RunId = $RunId
        StatusAuthority = $StatusAuthority
        ControllerHostId = $ControllerHostId
        ControllerThreadId = $ControllerThreadId
        ControllerModelId = $ControllerModelId
        ControllerReasoningEffort = $ControllerReasoningEffort
        MonitorHostId = $MonitorHostId
        MonitorThreadId = $MonitorThreadId
        MonitorModelId = $MonitorModelId
        MonitorReasoningEffort = $MonitorReasoningEffort
        AutomationId = $AutomationId
    }.GetEnumerator()) {
        Require-Text ([string]$pair.Value) $pair.Key
    }
    if ($RunId -ne (Split-Path -Leaf $run)) {
        throw "RunId must equal the run directory name"
    }
    $automationBaseline = Read-AutomationConfig $AutomationId $MonitorThreadId
    if ($automationBaseline.status -eq "PAUSED") {
        throw "Monitor activation requires a non-paused automation baseline"
    }
    $document = [ordered]@{
        schema_version = 1
        run_id = $RunId
        updated_at = [DateTimeOffset]::Now.ToString("o")
        status_authority = $StatusAuthority
        controller = [ordered]@{
            host_id = $ControllerHostId
            thread_id = $ControllerThreadId
            model_id = $ControllerModelId
            reasoning_effort = $ControllerReasoningEffort
        }
        monitor = [ordered]@{
            host_id = $MonitorHostId
            thread_id = $MonitorThreadId
            model_id = $MonitorModelId
            reasoning_effort = $MonitorReasoningEffort
        }
        automation_id = $AutomationId
        automation_baseline = [ordered]@{
            config_path = $automationBaseline.config_path
            status = $automationBaseline.status
            updated_at = $automationBaseline.updated_at
        }
        state = "RUNNING"
        previous_state = $null
        handoff_id = $null
        terminal = $null
        relay_receipt = $null
        pause_receipt = $null
        blocker = $null
        blocker_resolution = $null
    }
    Assert-State $document
    Write-State $document
    Write-Output $statePath
    exit 0
}

$document = Read-State

if ($Mode -eq "transition") {
    Require-Text $State "State"
    if ($document.state -eq "CLOSED") {
        if ($State -eq "CLOSED" -and $HandoffId -eq $document.handoff_id) {
            Write-Output "monitor_state=NOOP_CLOSED handoff_id=$($document.handoff_id)"
            exit 0
        }
        throw "CLOSED is immutable"
    }

    $from = [string]$document.state
    if ($from -eq "BLOCKED") {
        if ($ResolutionReceipt -notmatch '^(user|tool|evidence):\S+') {
            throw "Leaving BLOCKED requires typed -ResolutionReceipt"
        }
        $from = [string]$document.previous_state
        $document.blocker_resolution = [ordered]@{
            receipt = $ResolutionReceipt
            resolved_at = [DateTimeOffset]::Now.ToString("o")
        }
    }

    if ($State -eq "BLOCKED") {
        Require-Text $Blocker "Blocker"
        $document.previous_state = $from
        $document.state = "BLOCKED"
        $document.blocker = $Blocker
    } else {
        $expectedIndex = [Array]::IndexOf($orderedStates, $from) + 1
        if ($expectedIndex -ge $orderedStates.Count -or $State -ne $orderedStates[$expectedIndex]) {
            throw "Invalid transition: $from -> $State"
        }
        switch ($State) {
            "TERMINAL_DETECTED" {
                foreach ($pair in @{
                    HandoffId = $HandoffId
                    RunState = $RunState
                    Phase = $Phase
                    StatusUpdatedAt = $StatusUpdatedAt
                    StatusPath = $StatusPath
                    PayloadPath = $PayloadPath
                }.GetEnumerator()) {
                    Require-Text ([string]$pair.Value) $pair.Key
                }
                $expectedHandoff = "$($document.run_id):${RunState}:${StatusUpdatedAt}"
                if ($HandoffId -ne $expectedHandoff) {
                    throw "HandoffId must equal $expectedHandoff"
                }
                $authorityPath = Resolve-RunFile ([string]$document.status_authority) "status_authority"
                $terminalStatusPath = Resolve-RunFile $StatusPath "StatusPath"
                if (-not [string]::Equals($authorityPath, $terminalStatusPath, [StringComparison]::OrdinalIgnoreCase)) {
                    throw "StatusPath must equal the frozen status authority"
                }
                $document.handoff_id = $HandoffId
                $document.terminal = [ordered]@{
                    run_state = $RunState
                    phase = $Phase
                    status_updated_at = $StatusUpdatedAt
                    status_path = $StatusPath
                    payload_path = $PayloadPath
                }
            }
            "RELAY_CONFIRMED" {
                $receipt = Parse-ReadThreadReceipt $ReadThreadReceipt
                if ($receipt.host -ne $document.controller.host_id -or
                    $receipt.thread -ne $document.controller.thread_id -or
                    $receipt.turn -notmatch $turnIdPattern -or
                    $receipt.handoff -ne $document.handoff_id) {
                    throw "read_thread receipt does not match the frozen controller and handoff"
                }
                $document.relay_receipt = [ordered]@{
                    target_host_id = $receipt.host
                    target_thread_id = $receipt.thread
                    delivered_turn_id = $receipt.turn
                    handoff_id = $receipt.handoff
                    confirmed_at = [DateTimeOffset]::Now.ToString("o")
                }
            }
            "AUTOMATION_PAUSED" {
                $automation = Read-AutomationConfig ([string]$document.automation_id) ([string]$document.monitor.thread_id)
                if ($automation.status -ne "PAUSED") {
                    throw "Automation is not PAUSED"
                }
                $pauseUpdated = 0L
                $baselineUpdated = 0L
                [void][long]::TryParse([string]$automation.updated_at, [ref]$pauseUpdated)
                [void][long]::TryParse([string]$document.automation_baseline.updated_at, [ref]$baselineUpdated)
                $relayConfirmed = [DateTimeOffset]::Parse([string]$document.relay_receipt.confirmed_at)
                if ($pauseUpdated -le $baselineUpdated -or
                    [DateTimeOffset]::FromUnixTimeMilliseconds($pauseUpdated) -lt $relayConfirmed) {
                    throw "Observed pause does not belong to this post-relay handoff"
                }
                $document.pause_receipt = [ordered]@{
                    automation_id = $document.automation_id
                    status = "PAUSED"
                    config_path = $automation.config_path
                    automation_updated_at = $automation.updated_at
                    paused_at = [DateTimeOffset]::Now.ToString("o")
                }
            }
            "CLOSED" {
                if ([string]::IsNullOrWhiteSpace($HandoffId) -or
                    $HandoffId -ne $document.handoff_id) {
                    throw "CLOSED requires the exact explicit HandoffId"
                }
            }
        }
        $document.state = $State
        $document.previous_state = $null
        $document.blocker = $null
    }
    Assert-State $document
    Write-State $document
}

Assert-State $document

if ($Mode -eq "show") {
    [pscustomobject]@{
        run_id = $document.run_id
        state = $document.state
        handoff_id = $document.handoff_id
        automation_id = $document.automation_id
        blocker = $document.blocker
    }
} else {
    Write-Output "monitor_state=VALID path=$statePath"
}
