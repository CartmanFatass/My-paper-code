[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path

function Get-GitValue([string[]]$Arguments) {
    $value = (& git -C $repo @Arguments).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($value)) {
        throw "Git resolution failed: git $($Arguments -join ' ')"
    }
    return $value
}

$branch = Get-GitValue @('branch', '--show-current')
if ($branch -ne 'aggressive') { throw "SOURCE_BOUNDARY_DIVERGED: local branch is $branch, expected aggressive" }
$local = Get-GitValue @('rev-parse', 'HEAD')
$remote = Get-GitValue @('rev-parse', 'refs/remotes/My-paper-code/aggressive')
if ($local -notmatch '^[0-9a-f]{40}$' -or $remote -notmatch '^[0-9a-f]{40}$') {
    throw 'SOURCE_BOUNDARY_DIVERGED: non-canonical Git object ID'
}
if ($local -ne $remote) { throw "SOURCE_BOUNDARY_DIVERGED: local=$local remote=$remote" }

[pscustomobject]@{
    source_boundary = 'local_and_remote_aggressive_tip'
    branch = $branch
    source_commit = $local
} | ConvertTo-Json -Compress
