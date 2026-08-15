[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$HookScript,
    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$HookArgument
)

$ErrorActionPreference = 'Stop'

# Keep PowerShell's native-process bridge on UTF-8.  Windows PowerShell may
# still replace non-ASCII redirected-input characters before this script runs;
# the guard has a narrowly bounded marker-root recovery for that case.
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom

# Keep hook execution portable across the main checkout and Gitless fixture
# copies.  HMASD_PYTHON is an explicit per-process choice; this launcher never
# writes it or any other user environment setting.
$launcherRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $launcherRoot
$scriptPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $HookScript))
if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
    throw "HMASD hook script does not exist: $scriptPath"
}

$pythonCommand = $null
$pythonPrefix = @()
if ($env:HMASD_PYTHON) {
    $explicit = Get-Command $env:HMASD_PYTHON -ErrorAction SilentlyContinue
    if ($explicit) {
        $pythonCommand = $explicit.Source
    } elseif (Test-Path -LiteralPath $env:HMASD_PYTHON -PathType Leaf) {
        $pythonCommand = $env:HMASD_PYTHON
    } else {
        throw "HMASD_PYTHON does not resolve to a Python executable: $env:HMASD_PYTHON"
    }
} else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        $pythonCommand = $python.Source
    } else {
        $py = Get-Command py -ErrorAction SilentlyContinue
        if ($py) {
            $pythonCommand = $py.Source
            $pythonPrefix = @('-3')
        } else {
            throw 'No Python interpreter found; set HMASD_PYTHON or install python/py.'
        }
    }
}

$forwarded = @($pythonPrefix + $scriptPath + $HookArgument)
& $pythonCommand @forwarded
exit $LASTEXITCODE
