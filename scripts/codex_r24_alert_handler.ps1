param(
    [string]$RunRoot = "logs_r24_overnight_existing_local_cuda",
    [string]$WatchOutputRoot = "",
    [string]$HandlerOutputRoot = "",
    [string]$CodexCli = "codex",
    [string]$CodexSandbox = "workspace-write",
    [string]$PromptTemplate = "scripts\prompts\r24_codex_recovery_prompt.md",
    [string]$DecisionSchema = "scripts\schemas\r24_codex_recovery_decision.schema.json",
    [switch]$AutoRunRecovery,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path "ha_ctse_process\train.py")) {
    throw "Run this script from the HMASD repo root."
}

function Resolve-R24RunDir {
    param([string]$Root)
    if (-not (Test-Path $Root)) {
        return $null
    }
    $rootItem = Get-Item -LiteralPath $Root -ErrorAction SilentlyContinue
    if ($null -eq $rootItem -or -not $rootItem.PSIsContainer) {
        return $null
    }
    $armDirs = @(Get-ChildItem -LiteralPath $rootItem.FullName -Directory -Filter "arm*" -ErrorAction SilentlyContinue)
    if ($armDirs.Count -gt 0) {
        return $rootItem.FullName
    }
    $runs = @(Get-ChildItem -LiteralPath $rootItem.FullName -Directory -Filter "run_*" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending)
    if ($runs.Count -gt 0) {
        return $runs[0].FullName
    }
    return $rootItem.FullName
}

function Get-RecentLines {
    param(
        [string]$Path,
        [int]$Tail = 80
    )
    if (-not $Path -or -not (Test-Path $Path)) {
        return @()
    }
    return @(Get-Content -LiteralPath $Path -Tail $Tail -ErrorAction SilentlyContinue)
}

function Read-KeyValueFile {
    param([string]$Path)
    $map = @{}
    if (-not $Path -or -not (Test-Path $Path)) {
        return $map
    }
    foreach ($line in @(Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue)) {
        if ($line -match "^\s*([^=]+)=(.*)$") {
            $map[$Matches[1].Trim()] = $Matches[2].Trim()
        }
    }
    return $map
}

function Get-ArmStatuses {
    param([string]$RunDir)
    if (-not $RunDir -or -not (Test-Path $RunDir)) {
        return @()
    }
    $items = New-Object System.Collections.Generic.List[object]
    $armDirs = @(Get-ChildItem -LiteralPath $RunDir -Directory -Filter "arm*" -ErrorAction SilentlyContinue |
        Sort-Object Name)
    foreach ($arm in $armDirs) {
        $statusPath = Join-Path $arm.FullName "runner_status.txt"
        $status = Read-KeyValueFile -Path $statusPath
        $state = if ($status.ContainsKey("state")) { $status["state"] } else { "missing" }
        $exitCode = if ($status.ContainsKey("exit_code")) { $status["exit_code"] } else { "" }
        $outputFile = if ($status.ContainsKey("output_file")) { $status["output_file"] } else { Join-Path $arm.FullName "runner_output.log" }
        $commandFile = if ($status.ContainsKey("command_file")) { $status["command_file"] } else { Join-Path $arm.FullName "command.txt" }
        $items.Add([pscustomobject]@{
            Arm = $arm.Name
            State = $state
            ExitCode = $exitCode
            StatusPath = $statusPath
            OutputFile = $outputFile
            CommandFile = $commandFile
        })
    }
    return @($items.ToArray())
}

function Find-FailedOrActiveArm {
    param([object[]]$Arms)
    $failed = @($Arms | Where-Object { $_.State -eq "finished" -and $_.ExitCode -ne "" -and $_.ExitCode -ne "0" })
    if ($failed.Count -gt 0) {
        return $failed[0]
    }
    $running = @($Arms | Where-Object { $_.State -eq "running" })
    if ($running.Count -gt 0) {
        return $running[0]
    }
    if ($Arms.Count -gt 0) {
        return $Arms[-1]
    }
    return $null
}

function Assert-RestartCommandAllowed {
    param([string]$Command)
    if ([string]::IsNullOrWhiteSpace($Command)) {
        return $false
    }
    $blocked = @(
        "Remove-Item",
        "rm ",
        "rmdir",
        "del ",
        "git reset",
        "git checkout",
        "Stop-Process",
        "taskkill",
        "format ",
        "shutdown"
    )
    foreach ($term in $blocked) {
        if ($Command -like "*$term*") {
            return $false
        }
    }
    $allowed = @(
        "run_r24_overnight_existing_local_cuda.ps1",
        "run_r24_qd_probe_local_cuda.ps1",
        "run_r24_behavior_audit_local_cuda.ps1",
        "r24_forced_behavior_audit.py",
        "ha_ctse_process.train"
    )
    foreach ($term in $allowed) {
        if ($Command -like "*$term*") {
            return $true
        }
    }
    return $false
}

if (-not (Test-Path $PromptTemplate)) {
    throw "Prompt template not found: $PromptTemplate"
}
if (-not (Test-Path $DecisionSchema)) {
    throw "Decision schema not found: $DecisionSchema"
}
if ($DryRun -eq $false -and -not (Get-Command $CodexCli -ErrorAction SilentlyContinue)) {
    throw "Codex CLI not found on PATH: $CodexCli"
}

$runDir = Resolve-R24RunDir -Root $RunRoot
if ([string]::IsNullOrWhiteSpace($WatchOutputRoot)) {
    $WatchOutputRoot = if ($runDir) { Join-Path $runDir "_watch" } else { Join-Path $RunRoot "_watch" }
}
if ([string]::IsNullOrWhiteSpace($HandlerOutputRoot)) {
    $HandlerOutputRoot = Join-Path $WatchOutputRoot "codex_recovery"
}
New-Item -ItemType Directory -Force -Path $HandlerOutputRoot | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$evidencePath = Join-Path $HandlerOutputRoot "codex_recovery_evidence_$timestamp.md"
$promptPath = Join-Path $HandlerOutputRoot "codex_recovery_prompt_$timestamp.md"
$decisionPath = Join-Path $HandlerOutputRoot "codex_recovery_decision_$timestamp.json"
$codexTranscript = Join-Path $HandlerOutputRoot "codex_recovery_transcript_$timestamp.log"
$handlerStatus = Join-Path $HandlerOutputRoot "codex_recovery_status.txt"

$watchStatePath = Join-Path $WatchOutputRoot "watch_state.json"
$watchAlertPath = Join-Path $WatchOutputRoot "watch_alert.txt"
$arms = @(Get-ArmStatuses -RunDir $runDir)
$focusArm = Find-FailedOrActiveArm -Arms $arms

$focusOutput = if ($null -ne $focusArm) { $focusArm.OutputFile } else { "" }
$focusCommand = if ($null -ne $focusArm) { $focusArm.CommandFile } else { "" }
$focusCommandText = if ($focusCommand -and (Test-Path $focusCommand)) {
    (Get-Content -LiteralPath $focusCommand -Raw -ErrorAction SilentlyContinue).Trim()
} else {
    ""
}

$watchStateText = if (Test-Path $watchStatePath) { Get-Content -LiteralPath $watchStatePath -Raw } else { "{}" }
$watchAlertTail = Get-RecentLines -Path $watchAlertPath -Tail 40
$focusOutputTail = Get-RecentLines -Path $focusOutput -Tail 160

$evidence = @()
$evidence += "# R24 Overnight Alert Evidence"
$evidence += ""
$evidence += "- repo_root: $((Get-Location).Path)"
$evidence += "- run_root_input: $RunRoot"
$evidence += "- resolved_run_dir: $runDir"
$evidence += "- watch_output_root: $WatchOutputRoot"
$evidence += "- focus_arm: $(if ($focusArm) { $focusArm.Arm } else { '<none>' })"
$evidence += "- focus_state: $(if ($focusArm) { $focusArm.State } else { '<none>' })"
$evidence += "- focus_exit_code: $(if ($focusArm) { $focusArm.ExitCode } else { '<none>' })"
$evidence += "- focus_command_file: $focusCommand"
$evidence += "- focus_output_file: $focusOutput"
$evidence += ""
$evidence += "## Arm Statuses"
$evidence += ""
foreach ($arm in $arms) {
    $evidence += "- $($arm.Arm): state=$($arm.State) exit_code=$($arm.ExitCode) status=$($arm.StatusPath)"
}
$evidence += ""
$evidence += "## Focus Command"
$evidence += ""
$evidence += '```powershell'
$evidence += $focusCommandText
$evidence += '```'
$evidence += ""
$evidence += "## Watch State JSON"
$evidence += ""
$evidence += '```json'
$evidence += $watchStateText
$evidence += '```'
$evidence += ""
$evidence += "## Watch Alert Tail"
$evidence += ""
$evidence += '```text'
$evidence += $watchAlertTail
$evidence += '```'
$evidence += ""
$evidence += "## Focus Output Tail"
$evidence += ""
$evidence += '```text'
$evidence += $focusOutputTail
$evidence += '```'
$evidence += ""
$evidence -join [Environment]::NewLine | Set-Content -Path $evidencePath -Encoding UTF8

$prompt = @()
$prompt += Get-Content -LiteralPath $PromptTemplate -Raw
$prompt += ""
$prompt += "---"
$prompt += ""
$prompt += Get-Content -LiteralPath $evidencePath -Raw
$prompt -join [Environment]::NewLine | Set-Content -Path $promptPath -Encoding UTF8

@(
    "time=$(Get-Date -Format o)"
    "state=prepared"
    "dry_run=$DryRun"
    "run_dir=$runDir"
    "focus_arm=$(if ($focusArm) { $focusArm.Arm } else { '' })"
    "evidence=$evidencePath"
    "prompt=$promptPath"
    "decision=$decisionPath"
    "transcript=$codexTranscript"
) | Set-Content -Path $handlerStatus -Encoding UTF8

if ($DryRun) {
    Write-Host "dry_run=true"
    Write-Host "evidence=$evidencePath"
    Write-Host "prompt=$promptPath"
    Write-Host "decision=$decisionPath"
    exit 0
}

$promptText = Get-Content -LiteralPath $promptPath -Raw
$codexArgs = @(
    "exec",
    "--sandbox",
    $CodexSandbox,
    "--output-schema",
    $DecisionSchema,
    "-o",
    $decisionPath,
    "-"
)

@(
    "time=$(Get-Date -Format o)"
    "state=codex_running"
    "dry_run=false"
    "run_dir=$runDir"
    "focus_arm=$(if ($focusArm) { $focusArm.Arm } else { '' })"
    "evidence=$evidencePath"
    "prompt=$promptPath"
    "decision=$decisionPath"
    "transcript=$codexTranscript"
) | Set-Content -Path $handlerStatus -Encoding UTF8

$promptText | & $CodexCli @codexArgs *>&1 | Tee-Object -FilePath $codexTranscript
$codexExit = $LASTEXITCODE
if ($codexExit -ne 0) {
    @(
        "time=$(Get-Date -Format o)"
        "state=codex_failed"
        "exit_code=$codexExit"
        "decision=$decisionPath"
        "transcript=$codexTranscript"
    ) | Set-Content -Path $handlerStatus -Encoding UTF8
    exit $codexExit
}

if (-not (Test-Path $decisionPath)) {
    throw "Codex did not write decision JSON: $decisionPath"
}

$decision = Get-Content -LiteralPath $decisionPath -Raw | ConvertFrom-Json
$restartCommand = [string]$decision.restart_command
$safe = [bool]$decision.safe_to_execute
$allowed = Assert-RestartCommandAllowed -Command $restartCommand

if ($AutoRunRecovery -and $safe -and $allowed) {
    $recoveryScript = Join-Path $HandlerOutputRoot "run_recovery_$timestamp.ps1"
    @(
        '$ErrorActionPreference = "Stop"',
        'Set-Location -LiteralPath "' + ((Get-Location).Path -replace '"', '\"') + '"',
        $restartCommand
    ) | Set-Content -Path $recoveryScript -Encoding UTF8
    @(
        "time=$(Get-Date -Format o)"
        "state=recovery_running"
        "decision=$decisionPath"
        "recovery_script=$recoveryScript"
    ) | Set-Content -Path $handlerStatus -Encoding UTF8
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File $recoveryScript
    $recoveryExit = $LASTEXITCODE
    @(
        "time=$(Get-Date -Format o)"
        "state=recovery_finished"
        "recovery_exit_code=$recoveryExit"
        "decision=$decisionPath"
        "recovery_script=$recoveryScript"
    ) | Set-Content -Path $handlerStatus -Encoding UTF8
    exit $recoveryExit
}

$reason = if (-not $AutoRunRecovery) {
    "auto_run_recovery_disabled"
} elseif (-not $safe) {
    "decision_not_safe_to_execute"
} elseif (-not $allowed) {
    "restart_command_not_allowlisted"
} else {
    "no_restart_command"
}

@(
    "time=$(Get-Date -Format o)"
    "state=codex_finished_no_auto_restart"
    "reason=$reason"
    "decision=$decisionPath"
    "transcript=$codexTranscript"
) | Set-Content -Path $handlerStatus -Encoding UTF8

Write-Host "codex_recovery_decision=$decisionPath"
Write-Host "auto_restart=$AutoRunRecovery safe=$safe allowed=$allowed reason=$reason"
