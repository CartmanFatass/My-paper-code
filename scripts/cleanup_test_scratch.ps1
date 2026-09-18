# Reclaim completed Windows test scratch; preview unless -Delete is supplied.
[CmdletBinding()]
param(
    [string[]]$RunDirectory,
    # Explicit recovery of a caller-verified old review fixture, never a sweep.
    [switch]$ReviewFixture,
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

if ($Delete -and -not $PSBoundParameters.ContainsKey('RunDirectory')) {
    throw 'Deletion requires explicit -RunDirectory targets; omit -Delete to preview'
}
if ($ReviewFixture -and -not $PSBoundParameters.ContainsKey('RunDirectory')) {
    throw 'ReviewFixture requires explicit -RunDirectory targets and verified fixture ownership'
}
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

# Conservative maintenance only: callers must prevent concurrent test startup.
$busyReason = $null
if ($Delete) {
    try {
        $busy = @(Get-CimInstance Win32_Process | Where-Object {
            $_.Name -match '^(python|pythonw|pypy|pytest).*\.exe$' -and
            (-not $_.CommandLine -or $_.Name -match '^pytest' -or
             $_.CommandLine -match '(?i)(?:^|[\s"/\\])pytest(?:\.exe)?(?:[\s"]|$)')
        })
        if ($busy.Count) { $busyReason = "Tests may still be running: $($busy.ProcessId -join ', ')" }
    } catch { $busyReason = "Could not establish test inactivity: $_" }
}

$failed = $false
foreach ($rawTarget in ($RunDirectory | Sort-Object -Unique)) {
  $target = $rawTarget
  try {
    $target = if ([IO.Path]::IsPathRooted($rawTarget)) { [IO.Path]::GetFullPath($rawTarget) }
              else { [IO.Path]::GetFullPath((Join-Path $repoRoot $rawTarget)) }
    $relative = [IO.Path]::GetRelativePath($repoRoot, $target).Replace('\', '/')
    $reviewTarget = $ReviewFixture -and $relative -match '^temp/scratch-review-[a-z0-9_-]+$'
    if ($relative -notmatch '^temp/tests/[^/]+$' -and
        $relative -notmatch '^temp/directions/[^/]+/test/[^/]+$' -and -not $reviewTarget) {
        throw "Not a single test invocation directory: $target"
    }
    if ($relative -match '~[0-9]') { throw 'Short-name aliases require separate inspection' }
    # Check every ancestor under temp as Resolve-Path alone does not reject junctions.
    $ancestor = $target
    while ($ancestor -ne $repoRoot) {
        if (Test-Path -LiteralPath $ancestor) { Assert-PlainDirectory $ancestor }
        $ancestor = [IO.Path]::GetDirectoryName($ancestor)
    }
    # Windows paths are case-insensitive even though literal Git pathspecs are not.
    $tracked = @(& git -C $repoRoot ls-files -- ":(icase,literal)$relative")
    if ($LASTEXITCODE -ne 0) { throw 'Could not verify Git ownership of scratch' }
    if ($tracked.Count) { throw "Refusing tracked content: $target" }
    if (-not (Test-Path -LiteralPath $target)) {
        [pscustomobject]@{Action='AlreadyAbsent'; Directory=$target; Reason=$null}
        continue
    }
    $links = @(Get-ChildItem -LiteralPath $target -Recurse -Force |
        Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
    if ($links.Count) { throw "Linked fixture requires separate inspection: $($links[0].FullName)" }
    if (-not $Delete) {
        [pscustomobject]@{Action='Preview'; Directory=$target; Reason=$null}
        continue
    }
    if ($busyReason) { throw $busyReason }
    Assert-PlainDirectory $target
    Remove-Item -LiteralPath $target -Recurse -Force
    if (Test-Path -LiteralPath $target) { throw "Cleanup incomplete: $target" }
    [pscustomobject]@{Action='Deleted'; Directory=$target; Reason=$null}
  } catch {
    $failed = $true
    [pscustomobject]@{Action='PreservedOrIncomplete'; Directory=$target; Reason="$($_.Exception.Message)"}
  }
}
if ($failed) { throw 'Some targets were preserved or could not be fully reclaimed; see per-target results' }
