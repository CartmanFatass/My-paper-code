param(
    [string]$Config = (Join-Path $PSScriptRoot "remote_log_sync.config.json"),
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Format-CommandLine {
    param([Parameter(Mandatory = $true)][string[]]$Command)

    return (($Command | ForEach-Object {
        if ($_ -match '[\s"]') {
            '"' + ($_ -replace '"', '\"') + '"'
        } else {
            $_
        }
    }) -join " ")
}

function Get-PropertyValue {
    param(
        [object]$Object,
        [string]$Name,
        [object]$Default = $null
    )

    if ($null -eq $Object) { return $Default }
    $prop = $Object.PSObject.Properties | Where-Object { $_.Name -eq $Name } | Select-Object -First 1
    if ($null -eq $prop -or $null -eq $prop.Value) { return $Default }
    return $prop.Value
}

function Get-RequiredString {
    param(
        [object]$Object,
        [string]$Name
    )

    $value = [string](Get-PropertyValue -Object $Object -Name $Name -Default "")
    if (-not $value.Trim()) {
        throw "Config field '$Name' is required."
    }
    return $value.Trim()
}

function Get-ConfigInt {
    param(
        [object]$Object,
        [string]$Name,
        [int]$Default
    )

    $value = Get-PropertyValue -Object $Object -Name $Name -Default $Default
    return [int]$value
}

function Get-ConfigBool {
    param(
        [object]$Object,
        [string]$Name,
        [bool]$Default
    )

    $value = Get-PropertyValue -Object $Object -Name $Name -Default $Default
    return [System.Convert]::ToBoolean($value)
}

function ConvertTo-BashSingleQuoted {
    param([Parameter(Mandatory = $true)][string]$Value)

    if ($Value.Contains("'") -or $Value -match '[\r\n]') {
        throw "Values containing quotes or newlines are not supported: $Value"
    }
    return "'$Value'"
}

function Resolve-WorkspacePath {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$RepoRoot
    )

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $Path))
}

function Get-RemoteLogRootLeaf {
    param([Parameter(Mandatory = $true)][string]$RemoteLogRoot)

    $trimmed = $RemoteLogRoot.Trim().TrimEnd("/", "\")
    if (-not $trimmed) {
        throw "remoteLogRoot cannot be empty."
    }
    $parts = $trimmed -split '[\\/]+' | Where-Object { $_ }
    if ($parts.Count -eq 0) {
        throw "Cannot derive local directory from remoteLogRoot: $RemoteLogRoot"
    }
    $leaf = [string]$parts[-1]
    $invalid = [System.IO.Path]::GetInvalidFileNameChars()
    foreach ($char in $invalid) {
        $leaf = $leaf.Replace([string]$char, "_")
    }
    $leaf = $leaf.Trim()
    if (-not $leaf) {
        throw "Cannot derive safe local directory from remoteLogRoot: $RemoteLogRoot"
    }
    return $leaf
}

function Resolve-LocalLogRoot {
    param(
        [Parameter(Mandatory = $true)][string]$LocalLogRootRaw,
        [Parameter(Mandatory = $true)][string]$RemoteLogRoot,
        [Parameter(Mandatory = $true)][string]$RepoRoot
    )

    $raw = $LocalLogRootRaw.Trim()
    if (-not $raw -or $raw -ieq "auto") {
        $leaf = Get-RemoteLogRootLeaf -RemoteLogRoot $RemoteLogRoot
        return [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot (Join-Path "synced" $leaf)))
    }
    return Resolve-WorkspacePath -Path $raw -RepoRoot $RepoRoot
}

function New-FindPredicate {
    param([Parameter(Mandatory = $true)][string]$Pattern)

    $normalized = $Pattern.Trim().Replace("\", "/").TrimStart("./")
    if (-not $normalized) { return "" }
    if ($normalized.Contains("'") -or $normalized -match '[\r\n]' -or $normalized.StartsWith("/")) {
        throw "Unsafe include pattern: $Pattern"
    }
    if ($normalized -match '(^|/)\.\.(/|$)') {
        throw "Include patterns cannot traverse parent directories: $Pattern"
    }

    if ($normalized.Contains("/")) {
        if (-not $normalized.StartsWith("*/")) {
            $normalized = "*/$normalized"
        }
        return "-path $(ConvertTo-BashSingleQuoted -Value $normalized)"
    }
    return "-name $(ConvertTo-BashSingleQuoted -Value $normalized)"
}

function Test-SafeRelativePath {
    param([Parameter(Mandatory = $true)][string]$Path)

    if ([System.IO.Path]::IsPathRooted($Path)) { return $false }
    if ($Path -match '(^|[\\/])\.\.([\\/]|$)') { return $false }
    if ($Path -match '[\r\n]') { return $false }
    return $true
}

$configPath = Resolve-Path -Path $Config
$configObject = Get-Content -LiteralPath $configPath.Path -Raw -Encoding UTF8 | ConvertFrom-Json
$repoRoot = (Resolve-Path -Path (Join-Path $PSScriptRoot "..\..")).Path

$remote = Get-RequiredString -Object $configObject -Name "remote"
$remoteLogRoot = (Get-RequiredString -Object $configObject -Name "remoteLogRoot").TrimEnd("/")
$localLogRootRaw = [string](Get-PropertyValue -Object $configObject -Name "localLogRoot" -Default "auto")
$localLogRoot = Resolve-LocalLogRoot -LocalLogRootRaw $localLogRootRaw -RemoteLogRoot $remoteLogRoot -RepoRoot $repoRoot
$intervalMinutes = Get-ConfigInt -Object $configObject -Name "intervalMinutes" -Default 30

$sshConfig = Get-PropertyValue -Object $configObject -Name "ssh" -Default $null
$syncConfig = Get-PropertyValue -Object $configObject -Name "sync" -Default $null
$sshExe = [string](Get-PropertyValue -Object $sshConfig -Name "sshExe" -Default "ssh")
$scpExe = [string](Get-PropertyValue -Object $sshConfig -Name "scpExe" -Default "scp")
$port = Get-ConfigInt -Object $sshConfig -Name "port" -Default 0
$identityFile = [string](Get-PropertyValue -Object $sshConfig -Name "identityFile" -Default "")

$includePatterns = @(Get-PropertyValue -Object $syncConfig -Name "includePatterns" -Default @())
if ($includePatterns.Count -eq 0) {
    $includePatterns = @("standalone_train.log", "metrics/*.csv", "_monitor/*.txt")
}
if (Get-ConfigBool -Object $syncConfig -Name "includeFigures" -Default $false) {
    $includePatterns += @("*.png", "*.pdf")
}
if (Get-ConfigBool -Object $syncConfig -Name "includeCheckpoints" -Default $false) {
    $includePatterns += "checkpoints/*"
}

$predicates = @()
foreach ($pattern in $includePatterns) {
    $predicate = New-FindPredicate -Pattern ([string]$pattern)
    if ($predicate) {
        $predicates += $predicate
    }
}
if ($predicates.Count -eq 0) {
    throw "No sync include patterns configured."
}

$sshArgs = @()
if ($port -gt 0) { $sshArgs += @("-p", "$port") }
if ($identityFile) { $sshArgs += @("-i", $identityFile) }
$sshArgs += $remote

$scpBaseArgs = @()
if ($port -gt 0) { $scpBaseArgs += @("-P", "$port") }
if ($identityFile) { $scpBaseArgs += @("-i", $identityFile) }

$remoteRootQuoted = ConvertTo-BashSingleQuoted -Value $remoteLogRoot
$predicateText = ($predicates -join " -o ")
$remoteListCommand = "root=$remoteRootQuoted; if [ ! -d `"`$root`" ]; then echo `"remote log root not found: `$root`" >&2; exit 3; fi; cd `"`$root`"; find . -type f \( $predicateText \) -print | sed 's#^\./##' | sort"

Write-Host "HA-CTSE remote log SSH sync"
Write-Host "timestamp=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "config=$($configPath.Path)"
Write-Host "remote=$remote"
Write-Host "remote_log_root=$remoteLogRoot"
Write-Host "local_log_root=$localLogRoot"
Write-Host "interval_minutes=$intervalMinutes"
Write-Host "include_patterns=$($includePatterns -join ',')"
Write-Host "ssh list command:"
Write-Host "  $(Format-CommandLine -Command (@($sshExe) + $sshArgs + @($remoteListCommand)))"

if ($DryRun) {
    Write-Host "DryRun requested; not connecting to remote host."
    exit 0
}

New-Item -ItemType Directory -Path $localLogRoot -Force | Out-Null

$listOutput = & $sshExe @sshArgs $remoteListCommand 2>&1
$listExitCode = $LASTEXITCODE
if ($listExitCode -ne 0) {
    throw "Remote log listing failed with exit code $listExitCode. Output: $($listOutput -join [Environment]::NewLine)"
}

$remoteFiles = @(
    $listOutput |
        ForEach-Object { "$_".Trim() } |
        Where-Object { $_ }
)

$copied = 0
$failed = 0
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$summaryLines = New-Object System.Collections.Generic.List[string]
$summaryLines.Add("HA-CTSE remote log SSH sync")
$summaryLines.Add("timestamp=$stamp")
$summaryLines.Add("config=$($configPath.Path)")
$summaryLines.Add("remote=$remote")
$summaryLines.Add("remote_log_root=$remoteLogRoot")
$summaryLines.Add("local_log_root=$localLogRoot")
$summaryLines.Add("include_patterns=$($includePatterns -join ',')")
$summaryLines.Add("files_found=$($remoteFiles.Count)")

foreach ($relPath in $remoteFiles) {
    if (-not (Test-SafeRelativePath -Path $relPath)) {
        $failed += 1
        $summaryLines.Add("skip_unsafe=$relPath")
        continue
    }

    $localRelPath = $relPath -replace '/', [System.IO.Path]::DirectorySeparatorChar
    $localPath = Join-Path $localLogRoot $localRelPath
    $localDir = Split-Path -Parent $localPath
    New-Item -ItemType Directory -Path $localDir -Force | Out-Null

    $remoteFile = "$remoteLogRoot/$relPath"
    $source = "${remote}:$remoteFile"
    $scpArgs = $scpBaseArgs + @($source, $localPath)
    Write-Host "copy: $relPath"

    & $scpExe @scpArgs
    if ($LASTEXITCODE -eq 0) {
        $copied += 1
    } else {
        $failed += 1
        $summaryLines.Add("copy_failed=$relPath")
    }
}

$summaryLines.Add("files_copied=$copied")
$summaryLines.Add("files_failed=$failed")

$latestPath = Join-Path $localLogRoot "_last_sync.txt"
$logPath = Join-Path $localLogRoot "_sync.log"
$summaryLines | Set-Content -Path $latestPath -Encoding UTF8
Add-Content -Path $logPath -Value ($summaryLines -join [Environment]::NewLine) -Encoding UTF8
Add-Content -Path $logPath -Value "" -Encoding UTF8

Write-Host ""
Write-Host ($summaryLines -join [Environment]::NewLine)
Write-Host "Wrote sync summary:"
Write-Host "  $latestPath"
Write-Host "  $logPath"

if ($failed -gt 0) {
    exit 1
}
