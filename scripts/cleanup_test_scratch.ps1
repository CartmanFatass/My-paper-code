# Reclaim completed Windows test scratch; preview unless -Delete is supplied.
[CmdletBinding()]
param(
    [string[]]$RunDirectory,
    [switch]$Delete
)

$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$tempRoot = Join-Path $repoRoot 'temp'

function Assert-PlainDirectory([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Expected an ordinary directory, not a link/junction: $Path"
    }
}

if (-not (Test-Path -LiteralPath $tempRoot)) { return }
Assert-PlainDirectory $tempRoot
if ($PSBoundParameters.ContainsKey('RunDirectory') -and
    (-not $RunDirectory -or @($RunDirectory | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count)) {
    throw 'RunDirectory must name an invocation; omit it to preview all test scratch'
}
if (-not $PSBoundParameters.ContainsKey('RunDirectory')) {
    $testRoot = Join-Path $tempRoot 'tests'
    if (-not (Test-Path -LiteralPath $testRoot)) { return }
    Assert-PlainDirectory $testRoot
    $RunDirectory = @(Get-ChildItem -LiteralPath $testRoot -Directory -Force |
        Select-Object -ExpandProperty FullName)
}

# Validate the complete selection before deleting any member of it.
$targets = @($RunDirectory | ForEach-Object {
    $target = if ([IO.Path]::IsPathRooted($_)) { [IO.Path]::GetFullPath($_) }
              else { [IO.Path]::GetFullPath((Join-Path $repoRoot $_)) }
    $relative = [IO.Path]::GetRelativePath($repoRoot, $target).Replace('\', '/')
    if ($relative -notmatch '^temp/tests/[^/]+$' -and
        $relative -notmatch '^temp/directions/[^/]+/test/[^/]+$') {
        throw "Not a single test invocation directory: $target"
    }
    # Check every ancestor under temp as Resolve-Path alone does not reject junctions.
    $ancestor = $target
    while ($ancestor -ne $tempRoot) {
        Assert-PlainDirectory $ancestor
        $ancestor = [IO.Path]::GetDirectoryName($ancestor)
    }
    $links = @(Get-ChildItem -LiteralPath $target -Recurse -Force |
        Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
    if ($links.Count) { throw "Linked fixture requires separate inspection: $($links[0].FullName)" }
    $tracked = @(& git --literal-pathspecs -C $repoRoot ls-files -- $relative)
    if ($LASTEXITCODE -ne 0) { throw 'Could not verify Git ownership of scratch' }
    if ($tracked.Count) { throw "Refusing tracked content: $target" }
    $target
} | Sort-Object -Unique)

if (-not $targets.Count) { return }
if (-not $Delete) {
    $targets | ForEach-Object { [pscustomobject]@{Action='Preview'; Directory=$_} }
    return
}

# Default pytest scratch does not appear on the command line, so refuse collection
# while any native pytest process is visible. This is a maintenance command, not
# a concurrent janitor or a process-killing tool.
$pythonProcesses = @(Get-CimInstance Win32_Process |
    Where-Object { $_.Name -match '^(python|pythonw|pypy|pytest).*\.exe$' })
$busy = @($pythonProcesses | Where-Object {
    -not $_.CommandLine -or $_.Name -match '^pytest' -or
    $_.CommandLine -match '(?i)(?:^|[\s"/\\])pytest(?:\.exe)?(?:[\s"]|$)'
})
if ($busy.Count) {
    throw "Tests may still be running; no deletion. Process IDs: $($busy.ProcessId -join ', ')"
}

foreach ($target in $targets) {
    Assert-PlainDirectory $target
    Remove-Item -LiteralPath $target -Recurse -Force
    if (Test-Path -LiteralPath $target) { throw "Cleanup incomplete: $target" }
    [pscustomobject]@{Action='Deleted'; Directory=$target}
}
