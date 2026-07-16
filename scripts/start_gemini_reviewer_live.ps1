#requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$QuestionPath,

    [Parameter(Mandatory = $true)]
    [string]$SourceManifestPath,

    [string]$ResponsePath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\')
$invokeScript = Join-Path $PSScriptRoot 'invoke_gemini_reviewer.ps1'
$exportScript = Join-Path $PSScriptRoot 'export_gemini_live_response.ps1'
$agyPath = Join-Path $env:LOCALAPPDATA 'agy\bin\agy.exe'
$model = 'Gemini 3.1 Pro (High)'

$dryRunJson = & $invokeScript `
    -QuestionPath $QuestionPath `
    -SourceManifestPath $SourceManifestPath `
    -DryRun
if ($LASTEXITCODE -ne 0) {
    throw 'Gemini review preflight failed.'
}
$preflight = $dryRunJson | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace([string]$preflight.conversation_id)) {
    throw 'No HMASD Gemini conversation exists. Initialize it with invoke_gemini_reviewer.ps1 first.'
}

$question = Get-Content -Raw -LiteralPath $preflight.question_path
$manifest = Get-Content -Raw -LiteralPath $preflight.source_manifest_path
$prompt = @"
$question

---

The following source manifest is the complete local-file access policy for this
live research phase. Obey it exactly and do not inspect files outside it.

$manifest
"@

$arguments = @(
    '--conversation', [string]$preflight.conversation_id,
    '--model', $model,
    '--mode', 'plan',
    '--sandbox',
    '--prompt-interactive', $prompt
)

Write-Host "Starting persistent HMASD Gemini reviewer conversation $($preflight.conversation_id)."
Write-Host 'Keep this process alive for the review round; press Ctrl+C twice only after the final answer is visible.'
& $agyPath @arguments
$agyExitCode = $LASTEXITCODE

if ($agyExitCode -eq 0 -and -not [string]::IsNullOrWhiteSpace($ResponsePath)) {
    & $exportScript `
        -ConversationId ([string]$preflight.conversation_id) `
        -ResponsePath $ResponsePath
    if ($LASTEXITCODE -ne 0) {
        throw 'The live Gemini process ended, but transcript archival failed.'
    }
}

exit $agyExitCode
