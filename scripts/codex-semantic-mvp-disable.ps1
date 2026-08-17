[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [ValidateSet("none", "hooks", "config", "state")]
    [string]$InjectFailureAt = "none",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$root = if ([IO.Path]::IsPathRooted($RepoRoot)) { [IO.Path]::GetFullPath($RepoRoot) } else { [IO.Path]::GetFullPath((Join-Path (Get-Location) $RepoRoot)) }

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
    finally { if ([IO.File]::Exists($temporary)) { [IO.File]::Delete($temporary) } }
}
function Invoke-InjectedFailure([string]$Point) {
    if ($InjectFailureAt -eq $Point) { throw "INJECTED_FAILURE:$Point" }
}
function Get-StrictConfigMutation([string]$Text) {
    $beginMatches = [regex]::Matches($Text, '(?m)^# BEGIN HMASD CODEX SEMANTIC MVP[ \t]*(?:\r?$)')
    $endMatches = [regex]::Matches($Text, '(?m)^# END HMASD CODEX SEMANTIC MVP[ \t]*(?:\r?$)')
    if ($beginMatches.Count -ne 1 -or $endMatches.Count -ne 1 -or $endMatches[0].Index -le $beginMatches[0].Index) { throw "CONFIG_MARKER_BLOCK_INVALID" }
    $beginMatch = $beginMatches[0]; $endMatch = $endMatches[0]
    $blockStart = $beginMatch.Index; $blockLength = ($endMatch.Index + $endMatch.Length) - $blockStart
    $block = $Text.Substring($blockStart, $blockLength)
    $sectionMatches = [regex]::Matches($block, '(?m)^\[mcp_servers\.hmasd_orchestrator\][ \t]*(?:\r?$)')
    if ($sectionMatches.Count -ne 1) { throw "MCP_SERVER_SECTION_INVALID" }
    $sectionMatch = $sectionMatches[0]; $headings = [regex]::Matches($block, '(?m)^\[[^\r\n\]]+\][ \t]*(?:\r?$)'); $sectionEnd = $block.Length
    foreach ($heading in $headings) { if ($heading.Index -gt $sectionMatch.Index) { $sectionEnd = $heading.Index; break } }
    $section = $block.Substring($sectionMatch.Index, $sectionEnd - $sectionMatch.Index)
    $enabledMatches = [regex]::Matches($section, '(?m)^[ \t]*enabled[ \t]*=[ \t]*(true|false)[ \t]*(?:\r?$)')
    if ($enabledMatches.Count -ne 1) { throw "MCP_ENABLED_FIELD_INVALID" }
    if ($section -notmatch [regex]::Escape('command = "C:\\Users\\fires\\.conda\\envs\\hmasd-amd-cpu\\python.exe"')) { throw "MCP_PYTHON_PATH_INVALID" }
    if ($section -notmatch '(?m)^tool_timeout_sec[ \t]*=[ \t]*1800[ \t]*(?:\r?$)') { throw "MCP_TIMEOUT_INVALID" }
    $enabledMatch = $enabledMatches[0]; $ending = if ($enabledMatch.Value.EndsWith("`r")) { "`r" } else { "" }
    $indent = ([regex]::Match($enabledMatch.Value, '^[ \t]*')).Value
    $newLine = $indent + "enabled = false" + $ending
    $updatedSection = $section.Substring(0, $enabledMatch.Index) + $newLine + $section.Substring($enabledMatch.Index + $enabledMatch.Length)
    $updatedBlock = $block.Substring(0, $sectionMatch.Index) + $updatedSection + $block.Substring($sectionEnd)
    $updatedText = $Text.Substring(0, $blockStart) + $updatedBlock + $Text.Substring($blockStart + $blockLength)
    $hookBeginMatches = [regex]::Matches($updatedText, '(?m)^# BEGIN HMASD CODEX SEMANTIC HOOKS[ \t]*(?:\r?$)')
    $hookEndMatches = [regex]::Matches($updatedText, '(?m)^# END HMASD CODEX SEMANTIC HOOKS[ \t]*(?:\r?$)')
    if ($hookBeginMatches.Count -gt 1 -or $hookEndMatches.Count -gt 1) { throw "HOOK_MARKER_BLOCK_INVALID" }
    if ($hookBeginMatches.Count -ne $hookEndMatches.Count) { throw "HOOK_MARKER_BLOCK_INVALID" }
    if ($hookBeginMatches.Count -eq 1) {
        $hookStart = $hookBeginMatches[0].Index
        $hookEnd = $hookEndMatches[0].Index + $hookEndMatches[0].Length
        $prefix = $updatedText.Substring(0, $hookStart)
        if ($prefix.EndsWith("`r`n")) { $prefix = $prefix.Substring(0, $prefix.Length - 2) }
        elseif ($prefix.EndsWith("`n")) { $prefix = $prefix.Substring(0, $prefix.Length - 1) }
        $suffix = $updatedText.Substring($hookEnd)
        if ($suffix.StartsWith("`r`n")) { $suffix = $suffix.Substring(2) }
        elseif ($suffix.StartsWith("`n")) { $suffix = $suffix.Substring(1) }
        $updatedText = $prefix + $suffix
    }
    elseif ($updatedText -match '(?m)^\[hooks(?:\.[^\]\r\n]+)?\][ \t]*(?:\r?$)' -or $updatedText -match '(?m)^\[\[hooks(?:\.[^\]\r\n]+)?\]\][ \t]*(?:\r?$)') {
        throw "HOOKS_TABLE_OUTSIDE_MANAGED_BLOCK"
    }
    return $updatedText
}
function Read-ActivationState([string]$Path, [string]$Runtime, [string]$CurrentHooksHash, [string]$CurrentConfigHash) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "ACTIVATION_STATE_INVALID_MISSING" }
    try { $state = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json } catch { throw "ACTIVATION_STATE_INVALID_JSON" }
    foreach ($name in @("baseline_hooks_sha256", "current_hooks_sha256", "baseline_backup")) { if (-not ($state.PSObject.Properties.Name -contains $name)) { throw "ACTIVATION_STATE_INVALID_MISSING:$name" } }
    foreach ($name in @("baseline_hooks_sha256", "current_hooks_sha256")) { if ([string]$state.$name -notmatch '^[0-9a-fA-F]{64}$') { throw "ACTIVATION_STATE_INVALID_HASH:$name" } }
    if ($state.PSObject.Properties.Name -contains "current_config_sha256" -and [string]$state.current_config_sha256 -notmatch '^[0-9a-fA-F]{64}$') { throw "ACTIVATION_STATE_INVALID_HASH:current_config_sha256" }
    $relative = [string]$state.baseline_backup
    if ([IO.Path]::IsPathRooted($relative) -or $relative -notmatch '^backups[\\/][^\\/]+\.bak$') { throw "ACTIVATION_STATE_INVALID_BACKUP_PATH" }
    $backupDir = [IO.Path]::GetFullPath((Join-Path $Runtime "backups")); $backupPath = [IO.Path]::GetFullPath((Join-Path $Runtime $relative))
    if ([IO.Path]::GetDirectoryName($backupPath) -ne $backupDir) { throw "ACTIVATION_STATE_INVALID_BACKUP_PATH" }
    if (-not (Test-Path -LiteralPath $backupPath -PathType Leaf)) { throw "ACTIVATION_STATE_INVALID_BACKUP_MISSING" }
    $backupBytes = [IO.File]::ReadAllBytes($backupPath); $backupHash = Get-BytesHash $backupBytes
    if ($backupHash -ne ([string]$state.baseline_hooks_sha256).ToLowerInvariant()) { throw "ACTIVATION_STATE_INVALID_BACKUP_HASH" }
    if ($CurrentHooksHash -ne ([string]$state.current_hooks_sha256).ToLowerInvariant()) { throw "LIVE_HOOK_HASH_MISMATCH expected=$($state.current_hooks_sha256) actual=$CurrentHooksHash" }
    if ($state.PSObject.Properties.Name -contains "current_config_sha256" -and $CurrentConfigHash -ne ([string]$state.current_config_sha256).ToLowerInvariant()) { throw "CONFIG_HASH_MISMATCH expected=$($state.current_config_sha256) actual=$CurrentConfigHash" }
    return [pscustomobject]@{ Object = $state; BackupPath = $backupPath; Bytes = $backupBytes }
}
function New-DryRunRoot([string]$Source) {
    $stage = Join-Path ([IO.Path]::GetTempPath()) ("hmasd-codex-semantic-mvp-" + [guid]::NewGuid().ToString("N"))
    [IO.Directory]::CreateDirectory((Join-Path $stage ".codex")) | Out-Null
    [IO.Directory]::CreateDirectory((Join-Path $stage "runtime")) | Out-Null
    foreach ($name in @("hooks.json", "config.toml", "hooks.semantic-mvp.shadow.json", "hooks.semantic-mvp.active.json")) {
        Copy-Item -LiteralPath (Join-Path $Source ".codex\$name") -Destination (Join-Path $stage ".codex\$name")
    }
    $sourceRuntime = Join-Path $Source "runtime\codex-semantic-mvp"
    if (Test-Path -LiteralPath $sourceRuntime -PathType Container) {
        Copy-Item -LiteralPath $sourceRuntime -Destination (Join-Path $stage "runtime\codex-semantic-mvp") -Recurse
    }
    return $stage
}

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw "Repository root does not exist: $root" }
$temporaryRoot = $null
$workRoot = $root
if ($DryRun) { $temporaryRoot = New-DryRunRoot $root; $workRoot = $temporaryRoot }

try {
    $runtime = Join-Path $workRoot "runtime\codex-semantic-mvp"
    $statePath = Join-Path $runtime "activation-state.json"
    $codex = Join-Path $workRoot ".codex"
    $hooksPath = Join-Path $codex "hooks.json"
    $configPath = Join-Path $codex "config.toml"
    $hooksBytes = [IO.File]::ReadAllBytes($hooksPath); $configBytes = [IO.File]::ReadAllBytes($configPath)
    $currentHooksHash = Get-BytesHash $hooksBytes; $currentConfigHash = Get-BytesHash $configBytes
    $stateValidation = Read-ActivationState $statePath $runtime $currentHooksHash $currentConfigHash
    $state = $stateValidation.Object; $oldStateBytes = [IO.File]::ReadAllBytes($statePath); $backupBytes = $stateValidation.Bytes; $backupHash = Get-BytesHash $backupBytes
    $configText = [Text.UTF8Encoding]::new($false).GetString($configBytes)
    $updatedConfigText = Get-StrictConfigMutation $configText
    $updatedConfigBytes = [Text.UTF8Encoding]::new($false).GetBytes($updatedConfigText)
    $state | Add-Member -NotePropertyName current_hooks_sha256 -NotePropertyValue $backupHash -Force
    $state | Add-Member -NotePropertyName current_config_sha256 -NotePropertyValue (Get-BytesHash $updatedConfigBytes) -Force
    $state | Add-Member -NotePropertyName mode -NotePropertyValue "off" -Force
    $newStateBytes = [Text.UTF8Encoding]::new($false).GetBytes(($state | ConvertTo-Json -Depth 4))
    $hooksWritten = $false; $configWritten = $false; $stateWritten = $false
    try {
        Invoke-InjectedFailure "hooks"
        $configWritten = $true; Write-BytesAtomic $configPath $updatedConfigBytes
        Invoke-InjectedFailure "config"
        $stateWritten = $true; Write-BytesAtomic $statePath $newStateBytes
        Invoke-InjectedFailure "state"
    }
    catch {
        $originalError = $_; $compensationErrors = @()
        try { if ($stateWritten) { Write-BytesAtomic $statePath $oldStateBytes } } catch { $compensationErrors += "state:$($_.Exception.Message)" }
        try { if ($configWritten) { Write-BytesAtomic $configPath $configBytes } } catch { $compensationErrors += "config:$($_.Exception.Message)" }
        try { if ($hooksWritten) { Write-BytesAtomic $hooksPath $hooksBytes } } catch { $compensationErrors += "hooks:$($_.Exception.Message)" }
        if ($compensationErrors.Count -gt 0) { throw "TRANSACTION_COMPENSATION_FAILED: $($compensationErrors -join '; ')" }
        throw $originalError
    }
    $restoredHash = Get-BytesHash ([IO.File]::ReadAllBytes($hooksPath))
    if ($restoredHash -ne $backupHash) { throw "ROLLBACK_HASH_MISMATCH expected=$backupHash actual=$restoredHash" }
    Write-Output "ROLLBACK_VERIFIED=true"
    [ordered]@{ MODE = "OFF"; DRY_RUN = [bool]$DryRun; RESTORED_SHA256 = $restoredHash; CONFIG_HASH = (Get-BytesHash ([IO.File]::ReadAllBytes($configPath))) } | ConvertTo-Json -Compress
}
finally {
    if ($temporaryRoot -and (Test-Path -LiteralPath $temporaryRoot)) { Remove-Item -LiteralPath $temporaryRoot -Recurse -Force }
}
