Set-StrictMode -Version Latest

function Get-HmasdSha256 {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)

    $hasher = [Security.Cryptography.SHA256]::Create()
    try {
        return -join @($hasher.ComputeHash($Bytes) | ForEach-Object { $_.ToString('x2') })
    } finally {
        $hasher.Dispose()
    }
}

function New-HmasdBrowserProDispatch {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Repository,
        [Parameter(Mandatory = $true)][string]$ReviewBranch,
        [Parameter(Mandatory = $true)][string]$StageCommit,
        [Parameter(Mandatory = $true)][string]$QuestionSha256,
        [Parameter(Mandatory = $true)][string]$QuestionPath
    )

    foreach ($identity in @($Repository, $ReviewBranch, $StageCommit, $QuestionSha256, $QuestionPath)) {
        if ($identity.IndexOf("`r", [StringComparison]::Ordinal) -ge 0 -or
            $identity.IndexOf("`n", [StringComparison]::Ordinal) -ge 0) {
            throw 'Browser Pro dispatch identity must be single-line'
        }
    }
    if ($Repository -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$' -or
        $Repository.Contains('..') -or $Repository.EndsWith('.')) {
        throw 'Browser Pro dispatch repository token is invalid'
    }
    if ($ReviewBranch -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._/-]*$' -or
        $ReviewBranch.Contains('..') -or $ReviewBranch.Contains('//') -or
        $ReviewBranch.Contains('@{') -or $ReviewBranch.EndsWith('/') -or
        $ReviewBranch.EndsWith('.') -or $ReviewBranch.EndsWith('.lock')) {
        throw 'Browser Pro dispatch review branch token is invalid'
    }
    if ($StageCommit -cnotmatch '^[0-9a-f]{40}$') {
        throw 'Browser Pro dispatch stage commit must be exact 40-character lowercase hex'
    }
    if ($QuestionSha256 -cnotmatch '^[0-9a-f]{64}$') {
        throw 'Browser Pro dispatch question digest must be exact 64-character lowercase hex'
    }
    if ($QuestionPath -cnotmatch '^docs/external-review/rounds/[A-Za-z0-9][A-Za-z0-9._-]*/20_PRO_OPEN_QUESTION\.md$') {
        throw 'Browser Pro dispatch question path is not canonical repo-relative path'
    }

    $roundId = [regex]::Match($QuestionPath, '^docs/external-review/rounds/([^/]+)/20_PRO_OPEN_QUESTION\.md$').Groups[1].Value
    $message = "HMASD_BP_D1 repo=$Repository b=$ReviewBranch stage=$StageCommit q=$QuestionSha256 round=$roundId file=20_PRO_OPEN_QUESTION.md Read via GitHub connector; follow fully; no upload/code/compute."
    if ($message.IndexOf("`r", [StringComparison]::Ordinal) -ge 0 -or
        $message.IndexOf("`n", [StringComparison]::Ordinal) -ge 0) {
        throw 'Browser Pro dispatch output must contain zero CR or LF characters'
    }
    if ($message.Length -gt 352) {
        throw "Browser Pro dispatch output exceeds the bounded 352 UTF-16 code-unit limit: $($message.Length)"
    }

    $utf8 = [Text.UTF8Encoding]::new($false, $true)
    $bytes = $utf8.GetBytes($message)
    return [pscustomobject][ordered]@{
        message = $message
        dispatch_base64 = [Convert]::ToBase64String($bytes)
        dispatch_sha256 = Get-HmasdSha256 $bytes
        utf16_length = $message.Length
        byte_count = $bytes.Length
        question_path = $QuestionPath
    }
}

Export-ModuleMember -Function New-HmasdBrowserProDispatch
