#requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$QuestionPath,

    [string]$SourceManifestPath,

    [string]$ResponsePath,

    [ValidateRange(1, 120)]
    [int]$TimeoutMinutes = 30,

    [switch]$DryRun,

    [switch]$Force
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\')
$geminiRoot = [System.IO.Path]::GetFullPath(
    (Join-Path $repoRoot 'docs\external-review\gemini_3_1_pro')
).TrimEnd('\')
$roundsRoot = [System.IO.Path]::GetFullPath(
    (Join-Path $repoRoot 'docs\external-review\rounds')
).TrimEnd('\')
$allowedReviewRoots = @($geminiRoot, $roundsRoot)
$model = 'Gemini 3.1 Pro (High)'
$agyPath = Join-Path $env:LOCALAPPDATA 'agy\bin\agy.exe'
$cachePath = Join-Path $HOME '.gemini\antigravity-cli\cache\last_conversations.json'
$briefPath = Join-Path $geminiRoot 'REVIEWER_BRIEF.md'

function Resolve-ExistingFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    $resolved = (Resolve-Path -LiteralPath $Path).Path
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        throw "$Label is not a file: $resolved"
    }
    return [System.IO.Path]::GetFullPath($resolved)
}

function Assert-UnderAllowedReviewRoot {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    foreach ($root in $allowedReviewRoots) {
        $prefix = $root.TrimEnd('\') + '\'
        if ($Path.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            return
        }
    }
    throw "$Label must stay under an approved external-review root: $Path"
}

function Get-ConversationId {
    if (-not (Test-Path -LiteralPath $cachePath -PathType Leaf)) {
        return $null
    }

    $cache = Get-Content -Raw -LiteralPath $cachePath | ConvertFrom-Json
    foreach ($property in $cache.PSObject.Properties) {
        $normalized = [System.IO.Path]::GetFullPath([string]$property.Name).TrimEnd('\')
        if ($normalized.Equals($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            return [string]$property.Value
        }
    }
    return $null
}

function Invoke-AgyPrompt {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Prompt,

        [string]$ConversationId
    )

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $agyPath
    $startInfo.WorkingDirectory = $repoRoot
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true

    if ($ConversationId) {
        $startInfo.ArgumentList.Add('--conversation')
        $startInfo.ArgumentList.Add($ConversationId)
    }
    $startInfo.ArgumentList.Add('--model')
    $startInfo.ArgumentList.Add($model)
    $startInfo.ArgumentList.Add('--mode')
    $startInfo.ArgumentList.Add('plan')
    $startInfo.ArgumentList.Add('--sandbox')
    $startInfo.ArgumentList.Add('--print-timeout')
    $startInfo.ArgumentList.Add("${TimeoutMinutes}m")
    $startInfo.ArgumentList.Add('--print')
    $startInfo.ArgumentList.Add($Prompt)

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    if (-not $process.Start()) {
        throw 'Failed to start Antigravity CLI.'
    }

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $timeoutMs = [Math]::Max(60000, $TimeoutMinutes * 60 * 1000 + 30000)
    if (-not $process.WaitForExit($timeoutMs)) {
        $process.Kill($true)
        throw "Antigravity CLI exceeded the ${TimeoutMinutes}-minute timeout."
    }

    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    if ($process.ExitCode -ne 0) {
        throw "Antigravity CLI failed with exit code $($process.ExitCode): $stderr"
    }
    if ([string]::IsNullOrWhiteSpace($stdout)) {
        throw "Antigravity CLI returned an empty response. stderr: $stderr"
    }
    return $stdout.TrimEnd()
}

if (-not (Test-Path -LiteralPath $agyPath -PathType Leaf)) {
    throw "Antigravity CLI not found: $agyPath"
}

$questionFullPath = Resolve-ExistingFile -Path $QuestionPath -Label 'QuestionPath'
Assert-UnderAllowedReviewRoot -Path $questionFullPath -Label 'QuestionPath'

if ([string]::IsNullOrWhiteSpace($SourceManifestPath)) {
    $SourceManifestPath = Join-Path (Split-Path -Parent $questionFullPath) 'SOURCE_MANIFEST.md'
}
$manifestFullPath = Resolve-ExistingFile -Path $SourceManifestPath -Label 'SourceManifestPath'
Assert-UnderAllowedReviewRoot -Path $manifestFullPath -Label 'SourceManifestPath'

if ([string]::IsNullOrWhiteSpace($ResponsePath)) {
    $ResponsePath = Join-Path (Split-Path -Parent $questionFullPath) 'GEMINI_3_1_PRO_RESPONSE_RAW.md'
}
if ([System.IO.Path]::IsPathRooted($ResponsePath)) {
    $responseFullPath = [System.IO.Path]::GetFullPath($ResponsePath)
} else {
    $responseFullPath = [System.IO.Path]::GetFullPath(
        (Join-Path (Get-Location).Path $ResponsePath)
    )
}
Assert-UnderAllowedReviewRoot -Path $responseFullPath -Label 'ResponsePath'

$question = Get-Content -Raw -LiteralPath $questionFullPath
$manifest = Get-Content -Raw -LiteralPath $manifestFullPath
$prompt = @"
$question

---

The following source manifest is the complete local-file access policy for this
round. Obey it exactly. Do not inspect files not listed by it.

$manifest
"@

$existingConversationId = Get-ConversationId
if ($DryRun) {
    [ordered]@{
        status = 'DRY_RUN_VALID'
        model = $model
        repo_root = $repoRoot
        conversation_id = $existingConversationId
        question_path = $questionFullPath
        source_manifest_path = $manifestFullPath
        response_path = $responseFullPath
        prompt_characters = $prompt.Length
    } | ConvertTo-Json -Depth 3
    exit 0
}

if ((Test-Path -LiteralPath $responseFullPath) -and -not $Force) {
    throw "Raw response already exists; refusing to overwrite: $responseFullPath"
}

$conversationId = $existingConversationId
if (-not $conversationId) {
    $brief = Get-Content -Raw -LiteralPath $briefPath
    $initialResponse = Invoke-AgyPrompt -Prompt $brief
    $normalizedInitialResponse = ($initialResponse -replace '(?m)^```(?:text)?\s*$', '' -replace '(?m)^```\s*$', '').Trim()
    if ($normalizedInitialResponse -ne 'READY_HMASD_REVIEWER') {
        throw "Unexpected reviewer initialization response: $initialResponse"
    }
    $conversationId = Get-ConversationId
    if (-not $conversationId) {
        throw 'Antigravity CLI initialized, but no HMASD conversation ID was recorded.'
    }
}

$rawResponse = Invoke-AgyPrompt -Prompt $prompt -ConversationId $conversationId
$responseDirectory = Split-Path -Parent $responseFullPath
if (-not (Test-Path -LiteralPath $responseDirectory -PathType Container)) {
    [System.IO.Directory]::CreateDirectory($responseDirectory) | Out-Null
}
[System.IO.File]::WriteAllText(
    $responseFullPath,
    $rawResponse + [Environment]::NewLine,
    [System.Text.UTF8Encoding]::new($false)
)

[ordered]@{
    status = 'RESPONSE_ARCHIVED'
    model = $model
    conversation_id = $conversationId
    question_path = $questionFullPath
    source_manifest_path = $manifestFullPath
    response_path = $responseFullPath
    response_characters = $rawResponse.Length
} | ConvertTo-Json -Depth 3
