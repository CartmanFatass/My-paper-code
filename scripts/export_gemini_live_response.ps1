#requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ConversationId,

    [Parameter(Mandatory = $true)]
    [string]$ResponsePath,

    [int]$StepIndex,

    [switch]$Force
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$parsedConversationId = [guid]::Empty
if (-not [guid]::TryParse($ConversationId, [ref]$parsedConversationId)) {
    throw "ConversationId is not a UUID: $ConversationId"
}
$conversationIdText = $parsedConversationId.ToString()

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\')
$allowedReviewRoots = @(
    [System.IO.Path]::GetFullPath(
        (Join-Path $repoRoot 'docs\external-review\gemini_3_1_pro')
    ).TrimEnd('\'),
    [System.IO.Path]::GetFullPath(
        (Join-Path $repoRoot 'docs\external-review\rounds')
    ).TrimEnd('\')
)

if ([System.IO.Path]::IsPathRooted($ResponsePath)) {
    $responseFullPath = [System.IO.Path]::GetFullPath($ResponsePath)
} else {
    $responseFullPath = [System.IO.Path]::GetFullPath(
        (Join-Path (Get-Location).Path $ResponsePath)
    )
}

$underAllowedRoot = $false
foreach ($root in $allowedReviewRoots) {
    if ($responseFullPath.StartsWith(
            $root + '\',
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
        $underAllowedRoot = $true
        break
    }
}
if (-not $underAllowedRoot) {
    throw "ResponsePath must stay under an approved external-review root: $responseFullPath"
}
if ((Test-Path -LiteralPath $responseFullPath) -and -not $Force) {
    throw "Raw response already exists; refusing to overwrite: $responseFullPath"
}

$transcriptPath = Join-Path $HOME (
    ".gemini\antigravity-cli\brain\$conversationIdText\.system_generated" +
    '\logs\transcript_full.jsonl'
)
if (-not (Test-Path -LiteralPath $transcriptPath -PathType Leaf)) {
    throw "Full Antigravity transcript not found: $transcriptPath"
}

$selected = $null
$hasRequestedStep = $PSBoundParameters.ContainsKey('StepIndex')
foreach ($line in [System.IO.File]::ReadLines($transcriptPath)) {
    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }
    $entry = $line | ConvertFrom-Json
    if ($hasRequestedStep -and [int]$entry.step_index -ne $StepIndex) {
        continue
    }
    if ([string]$entry.status -ne 'DONE') {
        continue
    }
    if ([string]$entry.type -notin @('PLANNER_RESPONSE', 'ASSISTANT_RESPONSE')) {
        continue
    }
    if ([string]::IsNullOrWhiteSpace([string]$entry.content)) {
        continue
    }
    $selected = $entry
}

if ($null -eq $selected) {
    if ($hasRequestedStep) {
        throw "No completed Gemini response exists at step $StepIndex."
    }
    throw 'No completed Gemini response exists in the full transcript.'
}

$responseDirectory = Split-Path -Parent $responseFullPath
if (-not (Test-Path -LiteralPath $responseDirectory -PathType Container)) {
    [System.IO.Directory]::CreateDirectory($responseDirectory) | Out-Null
}
[System.IO.File]::WriteAllText(
    $responseFullPath,
    ([string]$selected.content).TrimEnd() + "`n",
    [System.Text.UTF8Encoding]::new($false)
)

[ordered]@{
    status = 'LIVE_RESPONSE_ARCHIVED'
    conversation_id = $conversationIdText
    step_index = [int]$selected.step_index
    response_type = [string]$selected.type
    transcript_path = $transcriptPath
    response_path = $responseFullPath
    response_characters = ([string]$selected.content).Length
} | ConvertTo-Json -Depth 3
