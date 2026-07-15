[CmdletBinding()]
param(
    [string]$SourceRoot = "",
    [string]$OutputRoot = "",
    [string]$BundleName = "",
    [string]$ManifestPath = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([string]::IsNullOrWhiteSpace($SourceRoot)) {
    $SourceRoot = Split-Path -Parent $PSScriptRoot
}
$SourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $SourceRoot "dist"
}
$OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)

if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
    $ManifestPath = Join-Path $SourceRoot "scripts\r27_g2_runtime_package_manifest.txt"
}
$ManifestPath = (Resolve-Path -LiteralPath $ManifestPath).Path

if ([string]::IsNullOrWhiteSpace($BundleName)) {
    $BundleName = "r27_g2_runtime_{0}" -f (Get-Date -Format "yyyyMMdd_HHmmss")
}
if ([System.IO.Path]::GetFileName($BundleName) -ne $BundleName) {
    throw "BundleName must be a single path segment: $BundleName"
}

$bundleRoot = Join-Path $OutputRoot $BundleName
$zipPath = "$bundleRoot.zip"
if (Test-Path -LiteralPath $bundleRoot) {
    throw "Bundle directory already exists: $bundleRoot"
}
if (Test-Path -LiteralPath $zipPath) {
    throw "Bundle archive already exists: $zipPath"
}

$excludedDirectoryNames = @(
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".pytest_tmp",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "dist",
    "logs",
    "node_modules",
    "runs",
    "venv"
)
$excludedExtensions = @(
    ".ckpt",
    ".err",
    ".log",
    ".npy",
    ".npz",
    ".out",
    ".pth",
    ".pt",
    ".pyc",
    ".pyo",
    ".zip"
)

function Get-CompatibleRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$BasePath,
        [Parameter(Mandatory = $true)][string]$FullPath
    )

    $base = [System.IO.Path]::GetFullPath($BasePath).TrimEnd("\", "/")
    $full = [System.IO.Path]::GetFullPath($FullPath)
    $baseUri = [System.Uri]::new($base + [System.IO.Path]::DirectorySeparatorChar)
    $fullUri = [System.Uri]::new($full)
    return [System.Uri]::UnescapeDataString(
        $baseUri.MakeRelativeUri($fullUri).ToString()
    ).Replace("/", [System.IO.Path]::DirectorySeparatorChar)
}

function Assert-SafeRelativePath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)

    if ([System.IO.Path]::IsPathRooted($RelativePath)) {
        throw "Manifest path must be relative: $RelativePath"
    }
    $sourcePrefix = $SourceRoot.TrimEnd("\", "/") + [System.IO.Path]::DirectorySeparatorChar
    $candidate = [System.IO.Path]::GetFullPath((Join-Path $SourceRoot $RelativePath))
    if (-not $candidate.StartsWith($sourcePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Manifest path escapes SourceRoot: $RelativePath"
    }
}

function Test-ExcludedRelativePath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)

    $normalized = $RelativePath.Replace("/", "\")
    $allowedGeneratedMetadata = @(
        "PACKAGE_BUILD_INFO.txt",
        "scripts\r27_g2_runtime_package_manifest.txt"
    )
    if ($allowedGeneratedMetadata -contains $normalized) {
        return $false
    }
    if ($normalized -like "memory\backup_*" -or $normalized -like "memory\tmp\*") {
        return $true
    }
    $segments = $normalized.Split("\", [System.StringSplitOptions]::RemoveEmptyEntries)
    foreach ($segment in $segments) {
        if ($excludedDirectoryNames -contains $segment) {
            return $true
        }
        if ($segment -like "logs_*") {
            return $true
        }
    }

    $extension = [System.IO.Path]::GetExtension($normalized).ToLowerInvariant()
    if ($excludedExtensions -contains $extension) {
        return $true
    }
    if ([System.IO.Path]::GetFileName($normalized) -like "events.out.tfevents*") {
        return $true
    }
    if ([System.IO.Path]::GetFileName($normalized) -like "test_*.py") {
        return $true
    }
    return $false
}

$manifestEntries = @()
$lineNumber = 0
foreach ($rawLine in Get-Content -LiteralPath $ManifestPath) {
    $lineNumber += 1
    $line = $rawLine.Trim()
    if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
        continue
    }
    if ($line -notmatch '^(directory|file)\s+(.+)$') {
        throw "Invalid manifest line ${lineNumber}: $rawLine"
    }
    $kind = $matches[1]
    $relativePath = $matches[2].Trim().Replace("/", "\")
    Assert-SafeRelativePath -RelativePath $relativePath
    $manifestEntries += [pscustomobject]@{
        Kind = $kind
        RelativePath = $relativePath
    }
}
if ($manifestEntries.Count -eq 0) {
    throw "Runtime manifest contains no package entries: $ManifestPath"
}

$packageFiles = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::OrdinalIgnoreCase
)
foreach ($entry in $manifestEntries) {
    $sourcePath = Join-Path $SourceRoot $entry.RelativePath
    if ($entry.Kind -eq "file") {
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
            throw "Required manifest file is missing: $sourcePath"
        }
        if (Test-ExcludedRelativePath -RelativePath $entry.RelativePath) {
            throw "Required manifest file is forbidden by package policy: $($entry.RelativePath)"
        }
        [void]$packageFiles.Add($entry.RelativePath)
        continue
    }

    if (-not (Test-Path -LiteralPath $sourcePath -PathType Container)) {
        throw "Required manifest directory is missing: $sourcePath"
    }
    Get-ChildItem -LiteralPath $sourcePath -Recurse -File -Force | ForEach-Object {
        $relativePath = Get-CompatibleRelativePath -BasePath $SourceRoot -FullPath $_.FullName
        if (-not (Test-ExcludedRelativePath -RelativePath $relativePath)) {
            [void]$packageFiles.Add($relativePath)
        }
    }
}

if (Test-Path -LiteralPath (Join-Path $SourceRoot ".git")) {
    $closureArgs = @(
        "-C",
        $SourceRoot,
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "--"
    ) + @($manifestEntries | ForEach-Object { $_.RelativePath })
    $eligibleFiles = @(& git @closureArgs 2>$null)
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to establish Git package-file closure"
    }
    $eligibleSet = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::OrdinalIgnoreCase
    )
    foreach ($eligible in $eligibleFiles) {
        [void]$eligibleSet.Add($eligible.Replace("/", "\"))
    }
    $outsideClosure = @(
        $packageFiles |
            Where-Object { -not $eligibleSet.Contains($_) } |
            Sort-Object
    )
    if ($outsideClosure.Count -gt 0) {
        throw "Package contains ignored or unaccounted source files:$([Environment]::NewLine)$($outsideClosure -join [Environment]::NewLine)"
    }
}

New-Item -ItemType Directory -Path $bundleRoot -Force | Out-Null
foreach ($relativePath in ($packageFiles | Sort-Object)) {
    $sourcePath = Join-Path $SourceRoot $relativePath
    $destinationPath = Join-Path $bundleRoot $relativePath
    $destinationParent = Split-Path -Parent $destinationPath
    if (-not (Test-Path -LiteralPath $destinationParent)) {
        New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
    }
    Copy-Item -LiteralPath $sourcePath -Destination $destinationPath
}

$manifestRelativePath = "scripts\r27_g2_runtime_package_manifest.txt"
if (-not (Test-Path -LiteralPath (Join-Path $bundleRoot $manifestRelativePath) -PathType Leaf)) {
    $manifestDestination = Join-Path $bundleRoot $manifestRelativePath
    New-Item -ItemType Directory -Path (Split-Path -Parent $manifestDestination) -Force | Out-Null
    Copy-Item -LiteralPath $ManifestPath -Destination $manifestDestination
}

$buildInfo = @(
    "experiment=R27-G2 forced-z trajectory/effect intervention",
    "purpose=optional structural review artifact only; remote launch authority is the clean Git checkout",
    "created=$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')",
    "source_root=$SourceRoot",
    "manifest=$ManifestPath",
    "device=cuda",
    "checkpoint_ids=arm0_update25,arm0_update30,arm0_final",
    "reset_ids=0..63",
    "environments_per_reset_worker=1",
    "default_parallel_reset_worker_limit=64",
    "default_parallel_collect_cost_hours=9-15",
    "registered_decision_grade_cost_hours=12-20",
    "decision_grade_concurrency=blocked_pending_separate safe GPU/process topology validation",
    "branches_per_reset=55",
    "runner=scripts/run_r27_g2_forced_trajectory_effect_cloud_64env.sh",
    "dry_run_command=MAX_WORKERS=64 bash scripts/run_r27_g2_forced_trajectory_effect_cloud_64env.sh --dry-run",
    "serial_launch=disabled",
    "parallel_launch_command=MAX_WORKERS=64 R27_G2_CONCURRENCY_VALIDATED=1 bash scripts/run_r27_g2_forced_trajectory_effect_cloud_64env.sh",
    "launch_authorization=blocked; pilot and decision-grade launch require separate user approval",
    "remote_prepare_command=pwsh -File scripts/remote/run_hmasd_r27_g2.ps1 -Action prepare; fast-forward updates the clean Git branch on the data disk",
    "remote_launch_command=blocked; requires exact experiment authorization plus clean local and remote Git worktrees and a validated parallel worker topology",
    "remote_storage_root=/root/autodl-tmp/HMASD; system disk is prohibited for source checkouts, checkpoints, logs, and results",
    "remote_checkpoint_cache=/root/autodl-tmp/HMASD/checkpoint_dist; checkpoints are staged by registered filename and required to be nonempty; model metadata is validated when loaded",
    "remote_daemon=GNU screen; current_run.env binds the exact screen session and launch script",
    "expected_run_root=logs/r27_g2_forced_z_trajectory_effect_<timestamp>",
    "expected_reset_artifacts=command.txt,runner_status.txt,runner_output.log,reset_manifest.json,reset_<id>.npz when calibration exists",
    "expected_aggregate_artifacts=aggregate_command.txt,aggregate_status.txt,aggregate_output.log,r27_g2_forced_trajectory_effect.json,r27_g2_forced_trajectory_effect.md,batch_status.txt",
    "checkpoints_included=false"
)
Set-Content -LiteralPath (Join-Path $bundleRoot "PACKAGE_BUILD_INFO.txt") -Value $buildInfo -Encoding UTF8

$sourceStatusPath = Join-Path $bundleRoot "PACKAGE_SOURCE_STATUS.txt"
$sourceStatus = @(
    "source_management=unavailable",
    "git_branch=unavailable",
    "worktree_status=unavailable",
    "package_scope_dirty=True"
)
if (Test-Path -LiteralPath (Join-Path $SourceRoot ".git")) {
    $gitBranch = ((& git -C $SourceRoot branch --show-current 2>$null) | Select-Object -First 1).Trim()
    if ([string]::IsNullOrWhiteSpace($gitBranch)) {
        $gitBranch = "detached"
    }
    $gitStatus = @(& git -C $SourceRoot status --short 2>$null)
    $scopeArgs = @("-C", $SourceRoot, "status", "--short", "--") + @(
        $manifestEntries | ForEach-Object { $_.RelativePath }
    )
    $packageScopeStatus = @(& git @scopeArgs 2>$null)
    if ($LASTEXITCODE -eq 0) {
        $sourceStatus = @(
            "source_management=git",
            "git_branch=$gitBranch",
            "worktree_dirty=$([bool]($gitStatus.Count -gt 0))",
            "package_scope_dirty=$([bool]($packageScopeStatus.Count -gt 0))",
            "package_scope_status_begin"
        ) + $packageScopeStatus + @(
            "package_scope_status_end",
            "worktree_status_begin"
        ) + $gitStatus + @("worktree_status_end")
    }
}
Set-Content -LiteralPath $sourceStatusPath -Value $sourceStatus -Encoding UTF8

$requiredPaths = @(
    "AGENTS.md",
    "config_1.py",
    "logger.py",
    "requirements_server.txt",
    "routing_protocols.py",
    "ha_ctse_process\env_factory.py",
    "envs\pettingzoo\scenario7_energy_aware.py",
    "hmasd\r_mappo_utils.py",
    "ha_ctse_process\r27_g2_analysis.py",
    "ha_ctse_process\r27_g2_collector.py",
    "ha_ctse_process\r27_g2_runtime.py",
    "scripts\audit_r27_forced_trajectory_effect.py",
    "scripts\run_r27_g2_forced_trajectory_effect_cloud_64env.sh",
    "scripts\package_r27_g2_runtime.ps1",
    "scripts\r27_g2_runtime_package_manifest.txt",
    "scripts\remote\hmasd_autodl_ssh_config",
    "scripts\remote\run_hmasd_r27_g2.ps1",
    "scripts\remote\watch_r27_g2_status.sh",
    "docs\research\designs\R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md",
    "docs\external-review\R27_G2_design_review_20260712_Claude.md",
    "docs\operations\R27_G2_REMOTE_AUTOMATION_20260712.md",
    "memory\CURRENT_WORK.md",
    "memory\ALGORITHM_PRINCIPLES.md",
    "memory\IMPLEMENTATION_PLAN.md",
    "memory\ExpRecord.md",
    "tests\r27_g2_cloud_runner_test.py",
    "tests\r27_g2_cli_test.py",
    "tests\r27_g2_collector_test.py",
    "tests\r27_g2_live_hook_test.py",
    "tests\r27_g2_package_test.py",
    "tests\r27_g2_runtime_test.py",
    "tests\r27_g2_analysis_test.py",
    "tests\r27_g2_remote_workflow_test.py",
    "PACKAGE_BUILD_INFO.txt",
    "PACKAGE_SOURCE_STATUS.txt"
)
foreach ($requiredPath in $requiredPaths) {
    if (-not (Test-Path -LiteralPath (Join-Path $bundleRoot $requiredPath) -PathType Leaf)) {
        throw "Bundle verification failed; missing $requiredPath"
    }
}

$forbidden = Get-ChildItem -LiteralPath $bundleRoot -Recurse -Force | Where-Object {
    $relativePath = Get-CompatibleRelativePath -BasePath $bundleRoot -FullPath $_.FullName
    Test-ExcludedRelativePath -RelativePath $relativePath
}
if ($forbidden) {
    $paths = ($forbidden | ForEach-Object FullName) -join [Environment]::NewLine
    throw "Forbidden paths entered the bundle:$([Environment]::NewLine)$paths"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $bundleRoot,
    $zipPath,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)

$archive = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
try {
    $archiveNames = @($archive.Entries | ForEach-Object { $_.FullName.Replace("/", "\") })
    foreach ($requiredPath in $requiredPaths) {
        if ($archiveNames -notcontains $requiredPath) {
            throw "ZIP verification failed; missing $requiredPath"
        }
    }
    foreach ($archiveName in $archiveNames) {
        if (-not [string]::IsNullOrWhiteSpace($archiveName) -and
            (Test-ExcludedRelativePath -RelativePath $archiveName)) {
            throw "ZIP verification failed; forbidden path present: $archiveName"
        }
    }
    foreach ($entry in $archive.Entries) {
        if ([string]::IsNullOrEmpty($entry.Name)) {
            continue
        }
        $entryStream = $entry.Open()
        try {
            $entryStream.CopyTo([System.IO.Stream]::Null)
        }
        finally {
            $entryStream.Dispose()
        }
    }
}
finally {
    $archive.Dispose()
}

[pscustomobject]@{
    BundleRoot = $bundleRoot
    ZipPath = $zipPath
    ZipBytes = (Get-Item -LiteralPath $zipPath).Length
    FileCount = (Get-ChildItem -LiteralPath $bundleRoot -Recurse -File -Force).Count
    ManifestPath = $ManifestPath
} | ConvertTo-Json -Depth 3
