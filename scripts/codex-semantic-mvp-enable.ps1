[CmdletBinding()]
param(
    [ValidateSet("Shadow", "Active")]
    [string]$Mode = "Shadow",
    [string]$RepoRoot = ".",
    [string]$ExpectedHooksHash = "",
    [ValidateSet("none", "backup", "hooks", "config", "state")]
    [string]$InjectFailureAt = "none",
    [string]$PythonExecutable = "C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$root = if ([IO.Path]::IsPathRooted($RepoRoot)) { [IO.Path]::GetFullPath($RepoRoot) } else { [IO.Path]::GetFullPath((Join-Path (Get-Location) $RepoRoot)) }
if (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) {
    throw "PYTHON_EXECUTABLE_MISSING: $PythonExecutable"
}
$python = [IO.Path]::GetFullPath($PythonExecutable)
$tomlPython = $python.Replace('\', '\\')

function Get-BytesHash([byte[]]$Bytes) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace("-", "").ToLowerInvariant() }
    finally { $sha.Dispose() }
}

function Write-BytesAtomic([string]$Path, [byte[]]$Bytes) {
    $directory = Split-Path -Parent $Path
    [IO.Directory]::CreateDirectory($directory) | Out-Null
    $temporary = Join-Path $directory ("." + [IO.Path]::GetFileName($Path) + ".tmp-" + [guid]::NewGuid().ToString("N"))
    try {
        [IO.File]::WriteAllBytes($temporary, $Bytes)
        if ([IO.File]::Exists($Path)) {
            $replacementBackup = $Path + ".replace-" + [guid]::NewGuid().ToString("N")
            try { [IO.File]::Replace($temporary, $Path, $replacementBackup, $true) }
            finally { if ([IO.File]::Exists($replacementBackup)) { [IO.File]::Delete($replacementBackup) } }
        }
        else { [IO.File]::Move($temporary, $Path) }
    }
    finally {
        if ([IO.File]::Exists($temporary)) { [IO.File]::Delete($temporary) }
    }
}

function Invoke-InjectedFailure([string]$Point) {
    if ($InjectFailureAt -eq $Point) { throw "INJECTED_FAILURE:$Point" }
}

function Get-SemanticHookEvents([string]$Mode) {
    $events = @('SessionStart', 'SubagentStart', 'SubagentStop', 'Stop')
    if ($Mode -eq 'Shadow') { $events += @('PreToolUse', 'PreCompact', 'PostCompact') }
    if ($Mode -eq 'Active') { $events += @('PreCompact', 'PostCompact') }
    return $events
}

function New-SemanticHookToml([string]$Mode, [string]$TomlPython) {
    $command = $TomlPython + ' -m tools.codex_semantic_mvp.hook_entry --mode ' + $Mode.ToLowerInvariant()
    $lines = @(
        '# BEGIN HMASD CODEX SEMANTIC HOOKS',
        '[hooks]'
    )
    foreach ($event in (Get-SemanticHookEvents $Mode)) {
        $lines += "[[hooks.$event]]"
        $lines += "[[hooks.$event.hooks]]"
        $lines += 'type = "command"'
        $lines += 'command = "' + $command + '"'
        $lines += 'commandWindows = "' + $command + '"'
        $lines += 'timeout = 5'
        $lines += ''
    }
    $lines += '# END HMASD CODEX SEMANTIC HOOKS'
    return ($lines -join "`n")
}

function Ensure-SemanticFeatureFlags([string]$Text) {
    $featuresMatches = [regex]::Matches($Text, '(?ms)^\[features\][ \t]*(?:\r?$).*?(?=^\[|\Z)')
    if ($featuresMatches.Count -ne 1) { throw "FEATURES_SECTION_INVALID" }
    $featuresMatch = $featuresMatches[0]
    $section = $featuresMatch.Value
    $newline = if ($Text.Contains("`r`n")) { "`r`n" } else { "`n" }
    $missing = @()
    foreach ($name in @('hooks')) {
        $assignments = [regex]::Matches($section, "(?m)^[ \t]*$name[ \t]*=[ \t]*(?:true|false)[ \t]*(?:\r?$)")
        if ($assignments.Count -gt 1) { throw "FEATURES_ASSIGNMENT_INVALID:$name" }
        if ($assignments.Count -eq 0) { $missing += $name }
    }
    if ($missing.Count -gt 0) {
        $heading = [regex]::Match($section, '(?m)^\[features\][ \t]*(?:\r?$)')
        $insert = (($missing | ForEach-Object { "$_ = true" }) -join $newline) + $newline
        $offset = $heading.Index + $heading.Length
        $section = $section.Substring(0, $offset) + $insert + $section.Substring($offset)
    }
    foreach ($name in @('hooks')) {
        $assignment = [regex]::Match($section, "(?m)^[ \t]*$name[ \t]*=[ \t]*(?:true|false)[ \t]*(?:\r?$)")
        $oldLine = $assignment.Value
        $ending = if ($oldLine.EndsWith("`r")) { "`r" } else { "" }
        $indent = ([regex]::Match($oldLine, '^[ \t]*')).Value
        $newLine = $indent + $name + " = true" + $ending
        $section = $section.Substring(0, $assignment.Index) + $newLine + $section.Substring($assignment.Index + $assignment.Length)
    }
    return $Text.Substring(0, $featuresMatch.Index) + $section + $Text.Substring($featuresMatch.Index + $featuresMatch.Length)
}

function Test-RootHookAssignment([string]$Text, [string]$Pattern) {
    $tableName = ""
    foreach ($line in ($Text -split "`r?`n")) {
        if ($line -match '^[ \t]*\[\[([^\]]+)\]\]') {
            $tableName = $Matches[1]
            continue
        }
        if ($line -match '^[ \t]*\[([^\]]+)\]') {
            $tableName = $Matches[1]
            continue
        }
        if ($line -match $Pattern) {
            if ($tableName -eq "features" -and $line -match '^[ \t]*hooks[ \t]*=[ \t]*true[ \t]*(?:#.*)?$') { continue }
            return $true
        }
    }
    return $false
}

function Get-StrictConfigMutation([string]$Text, [string]$DesiredEnabled, [string]$Mode, [string]$TomlPython) {
    $beginMatches = [regex]::Matches($Text, '(?m)^# BEGIN HMASD CODEX SEMANTIC MVP[ \t]*(?:\r?$)')
    $endMatches = [regex]::Matches($Text, '(?m)^# END HMASD CODEX SEMANTIC MVP[ \t]*(?:\r?$)')
    if ($beginMatches.Count -ne 1 -or $endMatches.Count -ne 1 -or $endMatches[0].Index -le $beginMatches[0].Index) {
        throw "CONFIG_MARKER_BLOCK_INVALID"
    }
    $beginMatch = $beginMatches[0]
    $endMatch = $endMatches[0]
    $blockStart = $beginMatch.Index
    $blockLength = ($endMatch.Index + $endMatch.Length) - $blockStart
    $block = $Text.Substring($blockStart, $blockLength)
    $sectionMatches = [regex]::Matches($block, '(?m)^\[mcp_servers\.hmasd_orchestrator\][ \t]*(?:\r?$)')
    if ($sectionMatches.Count -ne 1) { throw "MCP_SERVER_SECTION_INVALID" }
    $sectionMatch = $sectionMatches[0]
    $headings = [regex]::Matches($block, '(?m)^\[[^\r\n\]]+\][ \t]*(?:\r?$)')
    $sectionEnd = $block.Length
    foreach ($heading in $headings) {
        if ($heading.Index -gt $sectionMatch.Index) { $sectionEnd = $heading.Index; break }
    }
    $section = $block.Substring($sectionMatch.Index, $sectionEnd - $sectionMatch.Index)
    $enabledMatches = [regex]::Matches($section, '(?m)^[ \t]*enabled[ \t]*=[ \t]*(true|false)[ \t]*(?:\r?$)')
    if ($enabledMatches.Count -ne 1) { throw "MCP_ENABLED_FIELD_INVALID" }
    $commandMatches = [regex]::Matches($section, '(?m)^[ \t]*command[ \t]*=[ \t]*"[^"]*"[ \t]*(?:\r?$)')
    if ($commandMatches.Count -ne 1) { throw "MCP_COMMAND_INVALID" }
    $commandMatch = $commandMatches[0]
    $commandEnding = if ($commandMatch.Value.EndsWith("`r")) { "`r" } else { "" }
    $commandIndent = ([regex]::Match($commandMatch.Value, '^[ \t]*')).Value
    $newCommandLine = $commandIndent + 'command = "' + $TomlPython + '"' + $commandEnding
    $section = $section.Substring(0, $commandMatch.Index) + $newCommandLine + $section.Substring($commandMatch.Index + $commandMatch.Length)
    if ($section -notmatch '(?m)^tool_timeout_sec[ \t]*=[ \t]*1800[ \t]*(?:\r?$)') { throw "MCP_TIMEOUT_INVALID" }
    $enabledMatches = [regex]::Matches($section, '(?m)^[ \t]*enabled[ \t]*=[ \t]*(true|false)[ \t]*(?:\r?$)')
    if ($enabledMatches.Count -ne 1) { throw "MCP_ENABLED_FIELD_INVALID" }
    $enabledMatch = $enabledMatches[0]
    $oldLine = $enabledMatch.Value
    $ending = if ($oldLine.EndsWith("`r")) { "`r" } else { "" }
    $indent = ([regex]::Match($oldLine, '^[ \t]*')).Value
    $newLine = $indent + "enabled = " + $DesiredEnabled + $ending
    $updatedSection = $section.Substring(0, $enabledMatch.Index) + $newLine + $section.Substring($enabledMatch.Index + $enabledMatch.Length)
    $updatedBlock = $block.Substring(0, $sectionMatch.Index) + $updatedSection + $block.Substring($sectionEnd)
    $updatedText = $Text.Substring(0, $blockStart) + $updatedBlock + $Text.Substring($blockStart + $blockLength)
    $hookBeginMatches = [regex]::Matches($updatedText, '(?m)^# BEGIN HMASD CODEX SEMANTIC HOOKS[ \t]*(?:\r?$)')
    $hookEndMatches = [regex]::Matches($updatedText, '(?m)^# END HMASD CODEX SEMANTIC HOOKS[ \t]*(?:\r?$)')
    if ($hookBeginMatches.Count -gt 1 -or $hookEndMatches.Count -gt 1) { throw "HOOK_MARKER_BLOCK_INVALID" }
    if ($hookBeginMatches.Count -ne $hookEndMatches.Count) { throw "HOOK_MARKER_BLOCK_INVALID" }
    $singleHookTable = '(?m)^\[hooks(?:\.[^\]\r\n]+)?\][ \t]*(?:\r?$)'
    $arrayHookTable = '(?m)^\[\[hooks(?:\.[^\]\r\n]+)?\]\][ \t]*(?:\r?$)'
    $newline = if ($updatedText.Contains("`r`n")) { "`r`n" } else { "`n" }
    $assignmentPattern = '(?m)^[ \t]*hooks(?:\.[A-Za-z0-9_-]+)*[ \t]*='
    if ($hookBeginMatches.Count -eq 1) {
        $hookStart = $hookBeginMatches[0].Index
        $hookEnd = $hookEndMatches[0].Index + $hookEndMatches[0].Length
        $managedBlock = $updatedText.Substring($hookStart, $hookEnd - $hookStart)
        if ([regex]::Matches($managedBlock, '(?m)^\[hooks\][ \t]*(?:\r?$)').Count -ne 1) { throw "HOOK_MARKER_BLOCK_INVALID" }
        foreach ($event in @('SessionStart', 'SubagentStart', 'SubagentStop', 'Stop')) {
            if ([regex]::Matches($managedBlock, "(?m)^\[\[hooks\.$event\]\][ \t]*(?:\r?$)").Count -ne 1) { throw "HOOK_MARKER_BLOCK_INVALID" }
            if ([regex]::Matches($managedBlock, "(?m)^\[\[hooks\.$event\.hooks\]\][ \t]*(?:\r?$)").Count -ne 1) { throw "HOOK_MARKER_BLOCK_INVALID" }
        }
        $optionalHookCount = 0
        foreach ($optionalEvent in @('PreToolUse', 'PreCompact', 'PostCompact')) {
            $optionalCount = [regex]::Matches($managedBlock, "(?m)^\[\[hooks\.$optionalEvent\]\][ \t]*(?:\r?$)").Count
            if ($optionalCount -gt 1) { throw "HOOK_MARKER_BLOCK_INVALID" }
            $optionalHookCount += $optionalCount
        }
        $expectedHookCount = 4 + $optionalHookCount
        $commandMatches = [regex]::Matches($managedBlock, '(?m)^[ \t]*command[ \t]*=[ \t]*"([^"]*)"[ \t]*(?:\r?$)')
        $commandWindowsMatches = [regex]::Matches($managedBlock, '(?m)^[ \t]*commandWindows[ \t]*=[ \t]*"([^"]*)"[ \t]*(?:\r?$)')
        $commandWindowsLines = [regex]::Matches($managedBlock, '(?m)^[ \t]*commandWindows[ \t]*=')
        if ($commandMatches.Count -ne $expectedHookCount -or $commandWindowsMatches.Count -ne $commandWindowsLines.Count -or ($commandWindowsMatches.Count -ne 0 -and $commandWindowsMatches.Count -ne $expectedHookCount)) { throw "HOOK_MARKER_BLOCK_INVALID" }
        if ($commandWindowsMatches.Count -eq $expectedHookCount) {
            for ($index = 0; $index -lt $commandMatches.Count; $index++) {
                $commandValue = $commandMatches[$index].Groups[1].Value
                $commandWindowsValue = $commandWindowsMatches[$index].Groups[1].Value
                if ($commandValue -ne $commandWindowsValue -or
                    $commandValue -notmatch ' -m tools\.codex_semantic_mvp\.hook_entry --mode (?:active|shadow)$') {
                    throw "HOOK_MARKER_BLOCK_INVALID"
                }
            }
        }
        $outsideText = $updatedText.Substring(0, $hookStart) + $updatedText.Substring($hookEnd)
        if ($outsideText -match $singleHookTable -or $outsideText -match $arrayHookTable -or (Test-RootHookAssignment $outsideText $assignmentPattern)) { throw "HOOKS_TABLE_CONFLICT" }
        $hookBlock = (New-SemanticHookToml $Mode $TomlPython) -replace "`n", $newline
        $updatedText = $updatedText.Substring(0, $hookStart) + $hookBlock + $updatedText.Substring($hookEnd)
    }
    else {
        if ($updatedText -match $singleHookTable -or $updatedText -match $arrayHookTable -or (Test-RootHookAssignment $updatedText $assignmentPattern)) { throw "HOOKS_TABLE_CONFLICT" }
        $hookBlock = (New-SemanticHookToml $Mode $TomlPython) -replace "`n", $newline
        $updatedText = $updatedText + $newline + $hookBlock + $newline
    }
    $updatedText = Ensure-SemanticFeatureFlags $updatedText
    return [pscustomobject]@{ Text = $updatedText; Enabled = $enabledMatches[0].Groups[1].Value; Block = $block }
}

function Read-ActivationState([string]$Path, [string]$Runtime, [string]$CurrentHooksHash, [string]$CurrentConfigHash) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try { $state = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json } catch { throw "ACTIVATION_STATE_INVALID_JSON" }
    foreach ($name in @("baseline_hooks_sha256", "current_hooks_sha256", "baseline_backup")) {
        if (-not ($state.PSObject.Properties.Name -contains $name)) { throw "ACTIVATION_STATE_INVALID_MISSING:$name" }
    }
    foreach ($name in @("baseline_hooks_sha256", "current_hooks_sha256")) {
        if ([string]$state.$name -notmatch '^[0-9a-fA-F]{64}$') { throw "ACTIVATION_STATE_INVALID_HASH:$name" }
    }
    if ($state.PSObject.Properties.Name -contains "current_config_sha256" -and [string]$state.current_config_sha256 -notmatch '^[0-9a-fA-F]{64}$') { throw "ACTIVATION_STATE_INVALID_HASH:current_config_sha256" }
    $relative = [string]$state.baseline_backup
    if ([IO.Path]::IsPathRooted($relative) -or $relative -notmatch '^backups[\\/][^\\/]+\.bak$') { throw "ACTIVATION_STATE_INVALID_BACKUP_PATH" }
    $backupDir = [IO.Path]::GetFullPath((Join-Path $Runtime "backups"))
    $backupPath = [IO.Path]::GetFullPath((Join-Path $Runtime $relative))
    if ([IO.Path]::GetDirectoryName($backupPath) -ne $backupDir) { throw "ACTIVATION_STATE_INVALID_BACKUP_PATH" }
    if (-not (Test-Path -LiteralPath $backupPath -PathType Leaf)) { throw "ACTIVATION_STATE_INVALID_BACKUP_MISSING" }
    $backupHash = Get-BytesHash ([IO.File]::ReadAllBytes($backupPath))
    if ($backupHash -ne ([string]$state.baseline_hooks_sha256).ToLowerInvariant()) { throw "ACTIVATION_STATE_INVALID_BACKUP_HASH" }
    if ($CurrentHooksHash -ne ([string]$state.current_hooks_sha256).ToLowerInvariant()) { throw "LIVE_HOOK_HASH_MISMATCH expected=$($state.current_hooks_sha256) actual=$CurrentHooksHash" }
    if ($state.PSObject.Properties.Name -contains "current_config_sha256" -and $CurrentConfigHash -ne ([string]$state.current_config_sha256).ToLowerInvariant()) { throw "CONFIG_HASH_MISMATCH expected=$($state.current_config_sha256) actual=$CurrentConfigHash" }
    return [pscustomobject]@{ Object = $state; BackupPath = $backupPath }
}

function New-DryRunRoot([string]$Source) {
    $stage = Join-Path ([IO.Path]::GetTempPath()) ("hmasd-codex-semantic-mvp-" + [guid]::NewGuid().ToString("N"))
    [IO.Directory]::CreateDirectory((Join-Path $stage ".codex")) | Out-Null
    [IO.Directory]::CreateDirectory((Join-Path $stage "runtime")) | Out-Null
    foreach ($name in @("hooks.json", "config.toml", "hooks.semantic-mvp.shadow.json", "hooks.semantic-mvp.active.json")) {
        Copy-Item -LiteralPath (Join-Path $Source ".codex\$name") -Destination (Join-Path $stage ".codex\$name")
    }
    return $stage
}

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw "Repository root does not exist: $root" }
$workRoot = $root
$temporaryRoot = $null
if ($DryRun) {
    $temporaryRoot = New-DryRunRoot $root
    $workRoot = $temporaryRoot
}

try {
    $codex = Join-Path $workRoot ".codex"
    $hooksPath = Join-Path $codex "hooks.json"
    $configPath = Join-Path $codex "config.toml"
    $runtime = Join-Path $workRoot "runtime\codex-semantic-mvp"
    $backupDir = Join-Path $runtime "backups"
    $statePath = Join-Path $runtime "activation-state.json"
    $hooksBytes = [IO.File]::ReadAllBytes($hooksPath)
    $currentHash = Get-BytesHash $hooksBytes
    $configBytes = [IO.File]::ReadAllBytes($configPath)
    $configHash = Get-BytesHash $configBytes
    if ($ExpectedHooksHash -and $ExpectedHooksHash -notmatch '^[0-9a-fA-F]{64}$') {
        throw "INITIAL_BASELINE_HASH_INVALID"
    }
    if ($ExpectedHooksHash -and $currentHash -ne $ExpectedHooksHash.ToLowerInvariant()) {
        throw "LIVE_HOOK_HASH_MISMATCH expected=$ExpectedHooksHash actual=$currentHash"
    }
    $stateValidation = Read-ActivationState $statePath $runtime $currentHash $configHash
    if (-not $stateValidation -and -not $ExpectedHooksHash) {
        throw "INITIAL_BASELINE_REQUIRED: supply -ExpectedHooksHash from a reviewed doctor baseline"
    }
    $state = if ($stateValidation) { $stateValidation.Object } else { $null }
    $configText = [Text.UTF8Encoding]::new($false).GetString($configBytes)
    $desired = if ($Mode -eq "Active") { "true" } else { "false" }
    $configMutation = Get-StrictConfigMutation $configText $desired $Mode $tomlPython
    $updatedConfigBytes = [Text.UTF8Encoding]::new($false).GetBytes($configMutation.Text)
    $backupName = "hooks-$currentHash.bak"
    $backupPath = Join-Path $backupDir $backupName
    $backupExisted = Test-Path -LiteralPath $backupPath -PathType Leaf
    $oldBackupBytes = if ($backupExisted) { [IO.File]::ReadAllBytes($backupPath) } else { $null }
    if ($backupExisted) {
        if ((Get-BytesHash ([IO.File]::ReadAllBytes($backupPath))) -ne $currentHash) { throw "BACKUP_HASH_MISMATCH $backupName" }
    }

    if (-not $state) {
        $state = [pscustomobject]@{
            schema_version = 1
            baseline_hooks_sha256 = $currentHash
            baseline_backup = "backups/$backupName"
        }
    }
    $state | Add-Member -NotePropertyName current_hooks_sha256 -NotePropertyValue $currentHash -Force
    $state | Add-Member -NotePropertyName current_config_sha256 -NotePropertyValue (Get-BytesHash $updatedConfigBytes) -Force
    $state | Add-Member -NotePropertyName mode -NotePropertyValue $Mode.ToLowerInvariant() -Force
    $state | Add-Member -NotePropertyName last_backup -NotePropertyValue "backups/$backupName" -Force
    $state | Add-Member -NotePropertyName python_executable -NotePropertyValue $python -Force
    $newStateBytes = [Text.UTF8Encoding]::new($false).GetBytes(($state | ConvertTo-Json -Depth 4))
    try { $null = ([Text.UTF8Encoding]::new($false).GetString($newStateBytes) | ConvertFrom-Json) } catch { throw "ACTIVATION_STATE_BUILD_INVALID" }

    $stateExisted = Test-Path -LiteralPath $statePath -PathType Leaf
    $oldStateBytes = if ($stateExisted) { [IO.File]::ReadAllBytes($statePath) } else { $null }
    $hooksWritten = $false; $configWritten = $false; $stateWritten = $false; $backupWritten = $false
    try {
        if (-not $backupExisted) { $backupWritten = $true; Write-BytesAtomic $backupPath $hooksBytes }
        Invoke-InjectedFailure "backup"
        Invoke-InjectedFailure "hooks"
        $configWritten = $true; Write-BytesAtomic $configPath $updatedConfigBytes
        Invoke-InjectedFailure "config"
        $stateWritten = $true; Write-BytesAtomic $statePath $newStateBytes
        Invoke-InjectedFailure "state"
    }
    catch {
        $originalError = $_; $compensationErrors = @()
        try {
            if ($stateWritten -and $stateExisted) { Write-BytesAtomic $statePath $oldStateBytes }
            elseif ($stateWritten -and -not $stateExisted -and (Test-Path -LiteralPath $statePath)) { [IO.File]::Delete($statePath) }
        } catch { $compensationErrors += "state:$($_.Exception.Message)" }
        try { if ($configWritten) { Write-BytesAtomic $configPath $configBytes } } catch { $compensationErrors += "config:$($_.Exception.Message)" }
        try { if ($hooksWritten) { Write-BytesAtomic $hooksPath $hooksBytes } } catch { $compensationErrors += "hooks:$($_.Exception.Message)" }
        try { if ($backupWritten -and (Test-Path -LiteralPath $backupPath)) { [IO.File]::Delete($backupPath) } } catch { $compensationErrors += "backup:$($_.Exception.Message)" }
        if ($compensationErrors.Count -gt 0) { throw "TRANSACTION_COMPENSATION_FAILED: $($compensationErrors -join '; ')" }
        throw $originalError
    }
    $result = [ordered]@{ MODE = $Mode.ToUpperInvariant(); DRY_RUN = [bool]$DryRun; LIVE_HOOKS_HASH = (Get-BytesHash ([IO.File]::ReadAllBytes($hooksPath))); CONFIG_HASH = (Get-BytesHash ([IO.File]::ReadAllBytes($configPath))); BACKUP = "runtime/codex-semantic-mvp/$backupName" }
    $result | ConvertTo-Json -Compress
}
finally {
    if ($temporaryRoot -and (Test-Path -LiteralPath $temporaryRoot)) { Remove-Item -LiteralPath $temporaryRoot -Recurse -Force }
}
