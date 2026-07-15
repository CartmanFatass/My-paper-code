[CmdletBinding()]
param(
    [string]$SourceRoot = "",
    [string]$OutputRoot = "",
    [string]$BundleName = ""
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

if ([string]::IsNullOrWhiteSpace($BundleName)) {
    $BundleName = "imod_workspace_bundle_{0}" -f (Get-Date -Format "yyyyMMdd_HHmmss")
}

$bundleRoot = Join-Path $OutputRoot $BundleName
$zipPath = "$bundleRoot.zip"

if (Test-Path -LiteralPath $bundleRoot) {
    throw "Bundle directory already exists: $bundleRoot"
}
if (Test-Path -LiteralPath $zipPath) {
    throw "Bundle archive already exists: $zipPath"
}

$sourceBranch = (& git -C $SourceRoot branch --show-current).Trim()
if ([string]::IsNullOrWhiteSpace($sourceBranch)) {
    throw "IMOD workspace bundles must be built from a named Git branch"
}
$sourceChanges = @(& git -C $SourceRoot status --porcelain)
if ($sourceChanges.Count -gt 0) {
    throw "IMOD workspace bundles must be built from a clean Git worktree"
}
$sourceStatus = & git -C $SourceRoot status --short --branch

New-Item -ItemType Directory -Path $bundleRoot -Force | Out-Null

$directoryIncludes = @(
    ".codex",
    "configs",
    "docs",
    "envs",
    "ha_ctse_process",
    "hmasd",
    "manifold_hmasd",
    "memory",
    "scripts",
    "tests"
)

$rootFileIncludes = @(
    "AGENTS.md",
    "advice_sol.md",
    "config.py",
    "config_1.py",
    "config_test.py",
    "logger.py",
    "requirements_server.txt",
    "routing_protocols.py",
    "train_multiproc_config_1.py",
    "visualization.py"
)

$referenceFilePatterns = @(
    "*Interaction Pattern Disentangling for Multi-Agent Reinforcement Learning.pdf",
    "*Hierarchical Multi-Agent Skill Discovery.pdf"
)

$excludedDirectoryNames = @(
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "logs",
    "runs"
)

$excludedExtensions = @(
    ".avi",
    ".ckpt",
    ".db",
    ".err",
    ".gif",
    ".jpeg",
    ".jpg",
    ".log",
    ".mp4",
    ".npy",
    ".npz",
    ".out",
    ".pth",
    ".pt",
    ".pyc",
    ".pyo",
    ".sqlite",
    ".sqlite3",
    ".zip"
)

function Test-ExcludedRelativePath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)

    $normalized = $RelativePath.Replace("/", "\")
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

    return $false
}

function Get-CompatibleRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$BasePath,
        [Parameter(Mandatory = $true)][string]$FullPath
    )

    $base = [System.IO.Path]::GetFullPath($BasePath).TrimEnd("\", "/")
    $full = [System.IO.Path]::GetFullPath($FullPath)
    $baseWithSeparator = $base + [System.IO.Path]::DirectorySeparatorChar
    $baseUri = [System.Uri]::new($baseWithSeparator)
    $fullUri = [System.Uri]::new($full)
    return [System.Uri]::UnescapeDataString(
        $baseUri.MakeRelativeUri($fullUri).ToString()
    ).Replace("/", [System.IO.Path]::DirectorySeparatorChar)
}

function Copy-WorkspaceFile {
    param(
        [Parameter(Mandatory = $true)][string]$SourcePath,
        [Parameter(Mandatory = $true)][string]$DestinationRelativePath
    )

    if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
        throw "Required file is missing: $SourcePath"
    }

    $destinationPath = Join-Path $bundleRoot $DestinationRelativePath
    $destinationParent = Split-Path -Parent $destinationPath
    if (-not (Test-Path -LiteralPath $destinationParent)) {
        New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
    }
    Copy-Item -LiteralPath $SourcePath -Destination $destinationPath
}

foreach ($relativeDirectory in $directoryIncludes) {
    $sourceDirectory = Join-Path $SourceRoot $relativeDirectory
    if (-not (Test-Path -LiteralPath $sourceDirectory -PathType Container)) {
        throw "Required directory is missing: $sourceDirectory"
    }

    Get-ChildItem -LiteralPath $sourceDirectory -Recurse -File -Force | ForEach-Object {
        $relativePath = Get-CompatibleRelativePath -BasePath $SourceRoot -FullPath $_.FullName
        if (-not (Test-ExcludedRelativePath -RelativePath $relativePath)) {
            Copy-WorkspaceFile -SourcePath $_.FullName -DestinationRelativePath $relativePath
        }
    }
}

foreach ($relativeFile in $rootFileIncludes) {
    $sourceFile = Join-Path $SourceRoot $relativeFile
    Copy-WorkspaceFile -SourcePath $sourceFile -DestinationRelativePath $relativeFile
}

$copiedReferenceNames = @()
foreach ($referencePattern in $referenceFilePatterns) {
    $referenceFiles = @(Get-ChildItem -LiteralPath $SourceRoot -File -Filter $referencePattern)
    if ($referenceFiles.Count -ne 1) {
        throw "Expected exactly one reference matching '$referencePattern'; found $($referenceFiles.Count)"
    }
    $referenceName = $referenceFiles[0].Name
    Copy-WorkspaceFile -SourcePath $referenceFiles[0].FullName -DestinationRelativePath $referenceName
    $copiedReferenceNames += $referenceName
}

$readme = @"
# IMOD Standalone Workspace

This directory is a clean working-tree snapshot migrated from the HMASD
repository for the IMOD-Direct research line.

## Active Design

Read in this order:

1. `AGENTS.md`
2. `memory/CURRENT_WORK.md`
3. `memory/ALGORITHM_PRINCIPLES.md`
4. `memory/IMPLEMENTATION_PLAN.md`
5. `memory/ExpRecord.md`
6. `docs/archive/legacy-memory/IMOD_DIRECT_DESIGN_20260710.md`

The written IMOD spec is awaiting user review and independent cross-family
MARL review. No replacement implementation plan is authorized yet.

## Runtime Boundary

`ha_ctse_process/`, `hmasd/`, and the R23/R24 scripts are migration support for
environment construction, frozen-policy/checkpoint loading, collectors, and
diagnostic reference. New IMOD algorithm code must not inherit their reward or
algorithm semantics by default.

## Environment

Install the CUDA-compatible PyTorch build separately, then install:

```powershell
python -m pip install -r requirements_imod.txt
```

No checkpoint or runtime log is included. Supply source-policy checkpoints as
external inputs under a run-local path when a reviewed execution plan requires
them.

## Snapshot

- Source repository: `$SourceRoot`
- Source branch: `$sourceBranch`
- Bundle: `$BundleName`

See `MIGRATION_MANIFEST.md`, `SOURCE_GIT_BRANCH.txt`, and
`SOURCE_GIT_STATUS.txt` for the Git-managed source boundary. The ZIP is
verified by opening every entry and checking required paths.
"@
Set-Content -LiteralPath (Join-Path $bundleRoot "README.md") -Value $readme -Encoding UTF8

$requirements = @"
-r requirements_server.txt
pytest
scikit-learn
tqdm
"@
Set-Content -LiteralPath (Join-Path $bundleRoot "requirements_imod.txt") -Value $requirements -Encoding ASCII

$gitignore = @"
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.venv/
venv/
logs/
logs_*/
runs/
dist/
*.pt
*.pth
*.ckpt
*.npz
*.npy
*.log
*.out
*.err
events.out.tfevents*
"@
Set-Content -LiteralPath (Join-Path $bundleRoot ".gitignore") -Value $gitignore -Encoding ASCII

$progressDirectory = Join-Path $bundleRoot ".superpowers\sdd"
New-Item -ItemType Directory -Path $progressDirectory -Force | Out-Null
$progress = @"
# IMOD SDD Progress

- 2026-07-10: standalone workspace migrated from Git branch `$sourceBranch`.
- Current gate: user review of the IMOD written spec, followed by independent
  Claude/Gemini MARL review.
- No IMOD implementation task has been authorized or started.
"@
Set-Content -LiteralPath (Join-Path $progressDirectory "progress.md") -Value $progress -Encoding UTF8

$manifest = @"
# IMOD Workspace Migration Manifest

- Created: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss K")
- Source: `$SourceRoot`
- Branch: `$sourceBranch`
- Snapshot mode: clean Git working tree on the named branch

## Included Directories

$($directoryIncludes | ForEach-Object { "- " + $_ } | Out-String)

## Included Root Files

$(($rootFileIncludes + $copiedReferenceNames) | ForEach-Object { "- " + $_ } | Out-String)

Generated migration files are `README.md`, `.gitignore`,
`requirements_imod.txt`, `.superpowers/sdd/progress.md`,
`SOURCE_GIT_BRANCH.txt`, and `SOURCE_GIT_STATUS.txt`.

## Excluded

- source `.git/` history and repository-local IDE state;
- all logs, `logs_*`, runs, TensorBoard events, and generated experiment data;
- checkpoints and arrays: `*.pt`, `*.pth`, `*.ckpt`, `*.npy`, `*.npz`;
- caches and compiled files;
- prior bundles and archives;
- generated images, videos, databases, and transient stdout/stderr files.

## Maintenance Rule

Future execution bundles should be built from this standalone repository and
must update their own explicit manifest. Do not silently copy additional HMASD
mechanisms into IMOD; every runtime dependency must have an environment,
checkpoint-reader, diagnostic-reference, or independently reviewed IMOD role.
"@
Set-Content -LiteralPath (Join-Path $bundleRoot "MIGRATION_MANIFEST.md") -Value $manifest -Encoding UTF8
Set-Content -LiteralPath (Join-Path $bundleRoot "SOURCE_GIT_BRANCH.txt") -Value $sourceBranch -Encoding ASCII
Set-Content -LiteralPath (Join-Path $bundleRoot "SOURCE_GIT_STATUS.txt") -Value $sourceStatus -Encoding UTF8

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $bundleRoot,
    $zipPath,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)

$forbidden = Get-ChildItem -LiteralPath $bundleRoot -Recurse -Force | Where-Object {
    $relativePath = Get-CompatibleRelativePath -BasePath $bundleRoot -FullPath $_.FullName
    Test-ExcludedRelativePath -RelativePath $relativePath
}
if ($forbidden) {
    $paths = ($forbidden | ForEach-Object FullName) -join [Environment]::NewLine
    throw "Forbidden files entered the bundle:$([Environment]::NewLine)$paths"
}

$requiredPaths = @(
    "AGENTS.md",
    ".codex\config.toml",
    "docs\superpowers\specs\2026-07-10-imod-direct-design.md",
    "memory\CURRENT_WORK.md",
    "ha_ctse_process\env_factory.py",
    "ha_ctse_process\collectors.py",
    "ha_ctse_process\standalone_agent.py",
    "envs\pettingzoo\scenario7_energy_aware.py",
    "hmasd\r_mappo_utils.py",
    "scripts\r24_forced_behavior_audit.py",
    "tests\r24_behavior_audit_test.py",
    "requirements_imod.txt",
    "README.md",
    "MIGRATION_MANIFEST.md",
    "SOURCE_GIT_BRANCH.txt",
    "SOURCE_GIT_STATUS.txt"
)
foreach ($requiredPath in $requiredPaths) {
    if (-not (Test-Path -LiteralPath (Join-Path $bundleRoot $requiredPath) -PathType Leaf)) {
        throw "Bundle verification failed; missing $requiredPath"
    }
}

$archive = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
try {
    $archiveNames = @($archive.Entries | ForEach-Object { $_.FullName.Replace("/", "\") })
    foreach ($requiredPath in $requiredPaths) {
        if ($archiveNames -notcontains $requiredPath) {
            throw "ZIP verification failed; missing $requiredPath"
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

$zipSize = (Get-Item -LiteralPath $zipPath).Length
[pscustomobject]@{
    BundleRoot = $bundleRoot
    ZipPath = $zipPath
    ZipBytes = $zipSize
    FileCount = (Get-ChildItem -LiteralPath $bundleRoot -Recurse -File -Force).Count
    SourceBranch = $sourceBranch
} | ConvertTo-Json -Depth 3
