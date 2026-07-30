# Deterministic browser bring-up for project-manager-direct review transport.
#
# Why this exists: on 2026-07-26 a session restart left no browser process at
# all, and the Project Manager re-derived the whole bring-up sequence by hand --
# Edge vs Chrome, sandboxed process launch failing silently, foreground focus,
# tab activation. Every one of those failures was "environment not in the
# expected state", which is a script's job, not a judgement call. The capture
# DECISION that follows -- which message is the ruling, and whether a failed
# capture is archivable anyway -- IS a judgement call and stays with the Project
# Manager. See `.claude/skills/hmasd-review-round/SKILL.md`, "Capture may be
# delegated, but only against a digest bond".
#
# CORRECTED 2026-07-30. This comment previously carried, in quotation marks and
# attributed to AGENTS.md twice over, the sentence "Do not delegate the browser
# and do not create any other relay". A repository-wide search for that string
# returns this file and nothing else: it was never in AGENTS.md, never in the
# Skill, and a reader who trusted the citation would have gone looking for a rule
# that does not exist. The substance was real -- the Skill did say "There is no
# transport delegate" -- but the quotation was invented, and an invented
# quotation is worse than a paraphrase because it forecloses checking. The rule
# it named has since been narrowed: capture may now be delegated under a digest
# bond, while the judgement above may not.
#
# This script only puts the environment into the expected state and reports what
# it could not fix. It never submits, captures, or archives anything.
#
# Usage:
#   scripts/ensure_review_browser.ps1 -ReviewerKey open_divergent
#   scripts/ensure_review_browser.ps1 -ReviewerKey adjudicator -NoLaunch
#
# Exit status is carried in the printed BROWSER_STATUS block, not in $LASTEXITCODE.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ReviewerKey,

    [string]$RegistryPath = "docs/external-review/REVIEWER_CONVERSATIONS.json",

    # Report only; never start a browser.
    [switch]$NoLaunch,

    [int]$LaunchWaitSeconds = 15
)

$ErrorActionPreference = 'Stop'

function Write-Kv([string]$k, $v) { Write-Output ("{0}={1}" -f $k, $v) }

# ---------------------------------------------------------------- registry ---

if (-not (Test-Path -LiteralPath $RegistryPath)) {
    Write-Output 'BROWSER_STATUS'
    Write-Kv 'status' 'REGISTRY_MISSING'
    Write-Kv 'registry_path' $RegistryPath
    return
}

$registry = Get-Content -LiteralPath $RegistryPath -Raw -Encoding UTF8 | ConvertFrom-Json
$reviewer = $registry.reviewers.$ReviewerKey

if ($null -eq $reviewer) {
    Write-Output 'BROWSER_STATUS'
    Write-Kv 'status' 'REVIEWER_KEY_NOT_REGISTERED'
    Write-Kv 'reviewer_key' $ReviewerKey
    Write-Kv 'known_keys' (($registry.reviewers | Get-Member -MemberType NoteProperty).Name -join ',')
    return
}

# The registration rule is normative: anything short of a fully registered
# conversation blocks transport, and this script never registers one itself.
if ($reviewer.registration_status -ne 'registered' -or
    [string]::IsNullOrWhiteSpace($reviewer.conversation_id) -or
    [string]::IsNullOrWhiteSpace($reviewer.url)) {

    Write-Output 'BROWSER_STATUS'
    Write-Kv 'status' 'TRANSPORT_BLOCKED_REVIEWER_NOT_REGISTERED'
    Write-Kv 'reviewer_key' $ReviewerKey
    Write-Kv 'registration_status' $reviewer.registration_status
    return
}

$convId = $reviewer.conversation_id
$convUrl = $reviewer.url

# ----------------------------------------------------------------- browser ---

$edgeCandidates = @(
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
)
$edgeExe = $edgeCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

$procs = @(Get-Process msedge -ErrorAction SilentlyContinue)
$launched = $false

if ($procs.Count -eq 0 -and -not $NoLaunch) {
    if ($null -eq $edgeExe) {
        Write-Output 'BROWSER_STATUS'
        Write-Kv 'status' 'EDGE_NOT_INSTALLED'
        return
    }

    # NOTE: a sandboxed shell silently fails to create the GUI process -- the
    # call returns cleanly and no msedge process appears. If that happens, rerun
    # this script with the sandbox disabled; it is not an Edge fault.
    Start-Process -FilePath $edgeExe -ArgumentList $convUrl | Out-Null
    $launched = $true

    $deadline = (Get-Date).AddSeconds($LaunchWaitSeconds)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 750
        $procs = @(Get-Process msedge -ErrorAction SilentlyContinue)
        if ($procs.Count -gt 0) { break }
    }
}

if ($procs.Count -eq 0) {
    Write-Output 'BROWSER_STATUS'
    Write-Kv 'status' $(if ($NoLaunch) { 'BROWSER_NOT_RUNNING_NOLAUNCH' } else { 'LAUNCH_PRODUCED_NO_PROCESS_RETRY_WITHOUT_SANDBOX' })
    Write-Kv 'conversation_url' $convUrl
    return
}

$mainWindow = Get-Process msedge -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowTitle -ne '' } |
    Select-Object -First 1

# --------------------------------------------------------------- foreground ---
# Clipboard writes from the page fail silently unless the window owns OS
# foreground focus. Setting it here does not guarantee the extension's own tab
# is the *active* one -- see the caveat block below.

$foregrounded = $false
if ($null -ne $mainWindow) {
    # Add-Type throws a terminating error when the type is already loaded, which
    # -ErrorAction cannot suppress; a rerun in the same session must not fail here.
    try {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class HmasdFg {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
'@ -ErrorAction Stop
    } catch {
        if (-not ('HmasdFg' -as [type])) { throw }
    }

    [void][HmasdFg]::ShowWindow($mainWindow.MainWindowHandle, 9)   # SW_RESTORE
    [void][HmasdFg]::SetForegroundWindow($mainWindow.MainWindowHandle)
    Start-Sleep -Milliseconds 800
    $foregrounded = ([HmasdFg]::GetForegroundWindow() -eq $mainWindow.MainWindowHandle)
}

# ------------------------------------------------------------------ report ---

Write-Output 'BROWSER_STATUS'
Write-Kv 'status' 'BROWSER_READY'
Write-Kv 'reviewer_key' $ReviewerKey
Write-Kv 'conversation_id' $convId
Write-Kv 'conversation_url' $convUrl
Write-Kv 'expected_model_ui' $reviewer.expected_model_ui
Write-Kv 'browser' 'msedge'
Write-Kv 'launched_by_this_script' $launched
Write-Kv 'main_window_pid' $(if ($mainWindow) { $mainWindow.Id } else { 'none' })
Write-Kv 'os_foreground' $foregrounded

Write-Output ''
Write-Output 'BROWSER_CAVEATS'
Write-Output 'extension_connection=not_verifiable_from_powershell -- call tabs_context_mcp; if it reports not connected, the Claude side panel in Edge is not signed in and that needs the user'
Write-Output 'mcp_tab_focus=extension_group_tabs_can_report_visibility_hidden -- a hidden tab refuses clipboard writes, so Copy response will click without copying'
Write-Output 'tab_activation=SendKeys_and_keybd_event_were_both_undelivered_to_edge_on_20260726 -- do not budget on switching tabs programmatically'
Write-Output 'capture_decisions_stay_with_pm=a_failed_Copy_response_is_never_a_licence_to_archive_rendered_text'
