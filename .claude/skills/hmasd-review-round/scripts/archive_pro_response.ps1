<#
.SYNOPSIS
    Capture a Pro response from the clipboard, archive it, and verify the
    archive is byte-identical to what was captured.

.DESCRIPTION
    This is the mechanical tail of a review round, and it is the single most
    repeated sequence in the workflow. Five consecutive rounds recorded the
    same sentence in their intake records:

        "captured on the second click after the neutral-body focus step --
         the same failure mode and fix as the previous four rounds"

    The same fix was rediscovered five times because the procedure lived in
    prose and was re-derived from memory each round. Everything after the
    clipboard is deterministic and belongs here. The browser interaction is
    not scriptable; this is everything around it.

    What it checks, in order, refusing rather than guessing:

      1. the clipboard is non-empty and is not the sentinel left before the
         copy -- an unchanged sentinel means the copy never happened, which
         is the failure that costs a round;
      2. the response carries THIS round's stage_commit, not the previous
         round's. A stale capture reads as a fresh ruling;
      3. it opens with a heading rather than page furniture;
      4. the archived file rereads byte-identical (-ceq) at the same length.

    Writes with .NET WriteAllText and a UTF8Encoding($false) -- no BOM.
    Set-Content is not used anywhere here: it writes a BOM by default on this
    machine, which has already silently de-registered subagent definitions
    elsewhere in this repository.

.EXAMPLE
    archive_pro_response.ps1 -RoundPath docs/external-review/rounds/20260728_x `
        -StageCommit b977e188 -Sentinel "CLIPBOARD_SENTINEL_7741"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RoundPath,
    [Parameter(Mandatory = $true)][string]$StageCommit,
    [string]$FileName = '21_PRO_OPEN_RAW.md',
    [string]$Sentinel,
    [int]$MinimumChars = 500,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$result = [ordered]@{ status = 'ROUND_ARCHIVE_FAILED'; failures = @() }
$failures = [System.Collections.Generic.List[string]]::new()

$target = Join-Path $RoundPath $FileName
if ((Test-Path -LiteralPath $target) -and -not $Force) {
    $failures.Add("Archive already exists: $target. A round's raw capture is written once; pass -Force only to repair a known-bad capture.")
}

$text = Get-Clipboard -Raw
if ([string]::IsNullOrWhiteSpace($text)) {
    $failures.Add('Clipboard is empty. The copy did not happen; do not retype the response by hand.')
}
elseif ($Sentinel -and $text.Contains($Sentinel)) {
    $failures.Add("Clipboard still holds the pre-copy sentinel '$Sentinel'. The copy control did not fire -- this is the recurring second-click failure. Re-focus a neutral part of the page and click Copy response again.")
}
else {
    if ($text.Length -lt $MinimumChars) {
        $failures.Add("Captured only $($text.Length) characters, below -MinimumChars $MinimumChars. That is page furniture, not a ruling.")
    }
    if (-not $text.Contains($StageCommit)) {
        $failures.Add("Capture does not contain this round's stage_commit '$StageCommit'. A response carrying a different commit is the PREVIOUS round's ruling and must not be archived here.")
    }
    $firstLine = ($text -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 1)
    if ($firstLine -notmatch '^#{1,3}\s+\S') {
        $failures.Add("Capture does not open with a markdown heading; first non-blank line is: '$firstLine'. A ruling opens with its own title, not with surrounding page text.")
    }
}

if ($failures.Count -gt 0) {
    $result.failures = @($failures)
    $result | ConvertTo-Json -Depth 4
    exit 1
}

if (-not (Test-Path -LiteralPath $RoundPath)) {
    New-Item -ItemType Directory -Path $RoundPath -Force | Out-Null
}
$full = (Resolve-Path -LiteralPath $RoundPath).Path
$targetFull = Join-Path $full $FileName
[System.IO.File]::WriteAllText($targetFull, $text, (New-Object System.Text.UTF8Encoding($false)))

$reread = [System.IO.File]::ReadAllText($targetFull, [System.Text.UTF8Encoding]::new($false))
$exactEqual = $reread -ceq $text

$lines = $text -split "`r?`n"
$result = [ordered]@{
    status       = if ($exactEqual) { 'ROUND_ARCHIVE_OK' } else { 'ROUND_ARCHIVE_FAILED' }
    path         = $targetFull
    chars        = $text.Length
    chars_reread = $reread.Length
    exact_equal  = $exactEqual
    stage_commit = $StageCommit
    first_line   = ($lines | Where-Object { $_.Trim() } | Select-Object -First 1)
    last_line    = ($lines | Where-Object { $_.Trim() } | Select-Object -Last 1)
    failures     = @()
}
if (-not $exactEqual) {
    $result.failures = @("Reread is NOT byte-identical to the capture ($($text.Length) captured, $($reread.Length) reread). Do not reconcile by editing the file -- recapture.")
}
$result | ConvertTo-Json -Depth 4
if ($exactEqual) { exit 0 } else { exit 1 }
