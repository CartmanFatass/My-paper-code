param(
    [Parameter(Mandatory = $true)]
    [string]$Root,
    [string]$Output = "",
    [switch]$IncludeCheckpoints,
    [switch]$IncludePlots,
    [int]$MaxDepth = 6
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

if (-not (Test-Path -LiteralPath $Root)) {
    throw "Log root does not exist: $Root"
}

if ($MaxDepth -lt 1) {
    throw "MaxDepth must be >= 1"
}

function Get-RelativePath {
    param([string]$Path)
    $full = [System.IO.Path]::GetFullPath($Path)
    $base = [System.IO.Path]::GetFullPath((Get-Location).Path)
    if (-not $base.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
        $base += [System.IO.Path]::DirectorySeparatorChar
    }
    $baseUri = [System.Uri]::new($base)
    $fullUri = [System.Uri]::new($full)
    return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($fullUri).ToString()).Replace('/', [System.IO.Path]::DirectorySeparatorChar)
}

function Get-DepthFromRoot {
    param(
        [string]$Base,
        [string]$Path
    )
    $baseFull = [System.IO.Path]::GetFullPath($Base).TrimEnd('\', '/')
    $pathFull = [System.IO.Path]::GetFullPath($Path)
    if (-not $baseFull.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
        $baseFull += [System.IO.Path]::DirectorySeparatorChar
    }
    $baseUri = [System.Uri]::new($baseFull)
    $pathUri = [System.Uri]::new($pathFull)
    $rel = [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($pathUri).ToString()).Replace('/', [System.IO.Path]::DirectorySeparatorChar)
    if ($rel -eq "." -or [string]::IsNullOrWhiteSpace($rel)) {
        return 0
    }
    return ($rel -split '[\\/]').Count
}

function Add-ExistingFile {
    param(
        [System.Collections.Generic.HashSet[string]]$Set,
        [string]$Path
    )
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        [void]$Set.Add((Get-RelativePath $Path))
    }
}

function Add-FilteredFiles {
    param(
        [System.Collections.Generic.HashSet[string]]$Set,
        [string]$Base,
        [scriptblock]$Predicate
    )
    Get-ChildItem -LiteralPath $Base -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { (Get-DepthFromRoot -Base $Base -Path $_.FullName) -le $MaxDepth } |
        Where-Object $Predicate |
        ForEach-Object { [void]$Set.Add((Get-RelativePath $_.FullName)) }
}

$files = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

Add-FilteredFiles -Set $files -Base $Root -Predicate {
    $full = $_.FullName
    $name = $_.Name
    $dir = $_.DirectoryName
    (
        $full -like "*\metadata\run_manifest.json" -or
        $full -like "*\metrics\*.csv" -or
        $full -like "*\metrics\*.json" -or
        $name -in @("standalone_train.log", "runner_status.txt", "runner_output.log", "command.txt") -or
        ($_.Extension -eq ".json" -and (Get-DepthFromRoot -Base $Root -Path $full) -le 2)
    )
}

if ($IncludeCheckpoints) {
    Add-FilteredFiles -Set $files -Base $Root -Predicate {
        $_.Name -like "standalone_process_core_update_*.pt" -or $_.Name -eq "best_model.pt"
    }
}

if ($IncludePlots) {
    Add-FilteredFiles -Set $files -Base $Root -Predicate {
        $_.FullName -like "*\plots\*.png" -or
        $_.FullName -like "*\plots\*.pdf" -or
        $_.FullName -like "*\paper_data\*"
    }
}

if ($files.Count -eq 0) {
    throw "No matching result files found under: $Root"
}

if ([string]::IsNullOrWhiteSpace($Output)) {
    $safeRoot = ($Root -replace '[:\\/\s]+', '_').Trim('_')
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $Output = "dist/${safeRoot}_results_${timestamp}.zip"
}

$outDir = Split-Path -Parent $Output
if (-not [string]::IsNullOrWhiteSpace($outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$staging = Join-Path ([System.IO.Path]::GetTempPath()) ("ha_ctse_results_" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $staging | Out-Null

try {
    foreach ($rel in ($files | Sort-Object)) {
        $src = Join-Path (Get-Location) $rel
        $dst = Join-Path $staging $rel
        New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force | Out-Null
        Copy-Item -LiteralPath $src -Destination $dst -Force
    }

    if (Test-Path -LiteralPath $Output) {
        Remove-Item -LiteralPath $Output -Force
    }
    Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $Output -Force
}
finally {
    Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "HA-CTSE result package created"
Write-Host "  root:                $Root"
Write-Host "  output:              $Output"
Write-Host "  files:               $($files.Count)"
Write-Host "  include_checkpoints: $($IncludeCheckpoints.IsPresent)"
Write-Host "  include_plots:       $($IncludePlots.IsPresent)"
Write-Host ""
Write-Host "Included file preview:"
$files | Sort-Object | Select-Object -First 30 | ForEach-Object { Write-Host "  $_" }
if ($files.Count -gt 30) {
    Write-Host "  ... ($($files.Count - 30) more)"
}
