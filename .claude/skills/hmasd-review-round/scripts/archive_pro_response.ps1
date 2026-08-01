<#
.SYNOPSIS
    Independently verify an archived Pro response against its transport
    receipt: the digest bond plus the protocol checks.

.DESCRIPTION
    The Agentify wrapper writes the raw archive (write-once, byte-exact from
    the receipt's responseText). This script is the OTHER side of the digest
    bond: it recomputes SHA-256 over the archived file's raw bytes and
    requires equality with the receipt's responseSha256 -- computed by the
    transport, recomputed here, never trusted from one side alone.

    What it checks, refusing rather than guessing:

      1. the archive exists and rereads byte-identically;
      2. its SHA-256 equals the receipt's responseSha256 -- a mismatch is a
         refusal, never a repair; do not reconcile by editing the file;
      3. whether the response cites this round's stage_commit is RECORDED,
         not enforced: under the receipt transport the response-to-round
         binding is proven by the receipt itself (operation key +
         userMessageId + two-snapshot completion), and a reviewer that
         paraphrases or omits the commit is ordinary (first observed
         2026-08-01, round 20260801_variable_k_algorithm_direction). The
         browser-era stale-capture risk this check refused no longer has a
         mechanism;
      4. it is at plausible size with a non-empty first line. (No markdown
         heading check: Agentify archives the rendered text, so '#' markers
         are not present -- measured in the 2026-08-01 transport smoke.)

    Its JSON output is the mechanical intake's '## Capture' record.

.EXAMPLE
    archive_pro_response.ps1 -RoundPath docs/external-review/rounds/20260801_x `
        -StageCommit b977e188... -ReceiptPath logs/review_transport/20260801_x/receipt.json
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RoundPath,
    [Parameter(Mandatory = $true)][string]$StageCommit,
    [Parameter(Mandatory = $true)][string]$ReceiptPath,
    [string]$FileName = '21_PRO_OPEN_RAW.md',
    [int]$MinimumChars = 500
)

$ErrorActionPreference = 'Stop'
$failures = [System.Collections.Generic.List[string]]::new()

$target = Join-Path $RoundPath $FileName
if (-not (Test-Path -LiteralPath $target)) {
    $failures.Add("Archive is missing: $target. The wrapper's archive command writes it; this script only verifies.")
}
if (-not (Test-Path -LiteralPath $ReceiptPath)) {
    $failures.Add("Receipt is missing: $ReceiptPath.")
}

$text = $null
$receipt = $null
if ($failures.Count -eq 0) {
    $bytes = [System.IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $target).Path)
    $text = [System.Text.UTF8Encoding]::new($false, $true).GetString($bytes)
    $receipt = Get-Content -Raw -LiteralPath $ReceiptPath | ConvertFrom-Json

    $sha = [System.Security.Cryptography.SHA256]::Create()
    $digest = ([System.BitConverter]::ToString($sha.ComputeHash($bytes)) -replace '-', '').ToLowerInvariant()
    if ($digest -ne $receipt.responseSha256) {
        $failures.Add("Digest bond FAILED: archived file SHA-256 $digest != receipt responseSha256 $($receipt.responseSha256). A mismatch is a refusal, never a repair -- do not edit the file to reconcile.")
    }
    if ($text.Length -lt $MinimumChars) {
        $failures.Add("Archive holds only $($text.Length) characters, below -MinimumChars $MinimumChars. That is not a ruling.")
    }
    $stageCommitCited = $text.Contains($StageCommit)
    $firstLine = ($text -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 1)
    if ([string]::IsNullOrWhiteSpace($firstLine)) {
        $failures.Add('Archive has no non-empty first line.')
    }
}

if ($failures.Count -gt 0) {
    [ordered]@{ status = 'ROUND_ARCHIVE_FAILED'; failures = @($failures) } | ConvertTo-Json -Depth 4
    exit 1
}

$lines = $text -split "`r?`n"
[ordered]@{
    status          = 'ROUND_ARCHIVE_OK'
    path            = (Resolve-Path -LiteralPath $target).Path
    chars           = $text.Length
    response_sha256 = $receipt.responseSha256
    operation_key   = $receipt.idempotencyKey
    terminal_state  = $receipt.terminalState
    stage_commit    = $StageCommit
    stage_commit_cited = $stageCommitCited
    first_line      = ($lines | Where-Object { $_.Trim() } | Select-Object -First 1)
    last_line       = ($lines | Where-Object { $_.Trim() } | Select-Object -Last 1)
    failures        = @()
} | ConvertTo-Json -Depth 4
exit 0
