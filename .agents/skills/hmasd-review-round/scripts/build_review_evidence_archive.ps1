[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-f]{40}$')][string]$Commit,
    [Parameter(Mandatory = $true)][string]$QuestionPath,
    [Parameter(Mandatory = $true)][string]$OutputPath,
    [string]$RepoRoot = (Join-Path $PSScriptRoot '..\..\..\..')
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path -LiteralPath $RepoRoot).Path
$gitCommand = Get-Command git.exe -ErrorAction Stop

function Normalize-RepositoryPath {
    param([Parameter(Mandatory = $true)][string]$Path)
    $normalized = $Path.Replace('\', '/').Trim()
    if ([string]::IsNullOrWhiteSpace($normalized) -or
        [IO.Path]::IsPathRooted($normalized) -or
        $normalized.StartsWith('/') -or
        @($normalized.Split('/')) -contains '..') {
        throw "Unsafe repository-relative path: $Path"
    }
    return $normalized
}

$question = Normalize-RepositoryPath -Path $QuestionPath
& $gitCommand.Source -C $repo rev-parse --verify "$Commit`^{commit}" | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Unknown review commit: $Commit" }

$questionLines = @(& $gitCommand.Source -C $repo show "$Commit`:$question")
if ($LASTEXITCODE -ne 0) {
    throw "Question is not present at commit: $question"
}

$inEvidence = $false
$paths = [Collections.Generic.List[string]]::new()
foreach ($line in $questionLines) {
    if ($line -ceq '## Evidence to read') {
        $inEvidence = $true
        continue
    }
    if ($inEvidence -and $line -match '^##\s+') { break }
    if ($inEvidence -and $line -match '^\s*-\s+`([^`]+)`\s*$') {
        $paths.Add((Normalize-RepositoryPath -Path $Matches[1]))
    }
}
if ($paths.Count -eq 0) {
    throw "Question has no exact evidence allow-list: $question"
}

$distinct = @($paths | Sort-Object -Unique)
if ($distinct.Count -ne $paths.Count) {
    throw "Question evidence allow-list contains duplicate paths: $question"
}
foreach ($path in $paths) {
    & $gitCommand.Source -C $repo cat-file -e "$Commit`:$path"
    if ($LASTEXITCODE -ne 0) {
        throw "Evidence path is not present at commit: $path"
    }
}

$output = if ([IO.Path]::IsPathRooted($OutputPath)) {
    [IO.Path]::GetFullPath($OutputPath)
}
else {
    [IO.Path]::GetFullPath((Join-Path $repo $OutputPath))
}
if (Test-Path -LiteralPath $output) {
    throw "Refusing to overwrite evidence archive: $output"
}
$parent = Split-Path -Parent $output
if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
    New-Item -ItemType Directory -Path $parent | Out-Null
}

$archiveArgs = @('-C', $repo, 'archive', '--format=zip', "--output=$output", $Commit, '--') + @($paths)
& $gitCommand.Source @archiveArgs
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $output -PathType Leaf)) {
    throw "Unable to create review evidence archive: $output"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($output)
try {
    $members = @($zip.Entries |
        Where-Object { -not $_.FullName.EndsWith('/') } |
        ForEach-Object { $_.FullName.Replace('\', '/') } |
        Sort-Object)
}
finally {
    $zip.Dispose()
}
$expected = @($paths | Sort-Object)
if ($members.Count -ne $expected.Count) {
    throw "Evidence archive member-count mismatch: expected $($expected.Count), found $($members.Count)"
}
for ($index = 0; $index -lt $expected.Count; $index++) {
    if ($members[$index] -cne $expected[$index]) {
        throw "Evidence archive member mismatch: expected $($expected[$index]), found $($members[$index])"
    }
}

$item = Get-Item -LiteralPath $output
[ordered]@{
    status = 'REVIEW_EVIDENCE_ARCHIVE_READY'
    commit = $Commit
    question = $question
    output = $item.FullName
    file_count = $expected.Count
    files = $expected
    bytes = $item.Length
} | ConvertTo-Json -Depth 4 -Compress
