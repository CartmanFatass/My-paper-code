[CmdletBinding()]
param(
    [string]$PythonPath = $(
        if ($env:R41_PYTHON) {
            $env:R41_PYTHON
        } else {
            'C:\Users\wu\.conda\envs\SB3\python.exe'
        }
    ),
    [string]$RunRoot = '',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$LogsRoot = [IO.Path]::GetFullPath((Join-Path $ProjectRoot 'logs'))
if (-not $RunRoot) {
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $RunRoot = Join-Path $LogsRoot "r41_official_hmasd_$stamp"
}
$RunRoot = [IO.Path]::GetFullPath($RunRoot)
$logsPrefix = $LogsRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $RunRoot.StartsWith($logsPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "RunRoot must stay under $LogsRoot"
}

$SourceArchive = Join-Path $ProjectRoot 'ref\hmasd.tar'
$SourceRoot = Join-Path $RunRoot 'source'
$StatusPath = Join-Path $RunRoot 'runner_status.txt'
$ResultPath = Join-Path $RunRoot 'result\r41_official_hmasd_alice_bob.json'
$Seeds = @(1, 2, 3, 4, 5)

if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "R41 Python is missing: $PythonPath"
}
if (-not (Test-Path -LiteralPath $SourceArchive -PathType Leaf)) {
    throw "Original HMASD source archive is missing: $SourceArchive"
}

function Format-Command {
    param([string]$Executable, [string[]]$Arguments)
    $rendered = foreach ($argument in $Arguments) {
        if ($argument -match '[\s"]') {
            '"' + $argument.Replace('"', '\"') + '"'
        } else {
            $argument
        }
    }
    return (@($Executable) + $rendered) -join ' '
}

function Write-Status {
    param(
        [string]$State,
        [string]$Phase,
        [int]$ActiveSeed = 0,
        [string]$ErrorMessage = ''
    )
    $lines = @(
        "updated=$((Get-Date).ToString('o'))"
        "state=$State"
        "phase=$Phase"
        'experiment=EXP-20260716-r41-official-hmasd-alice-bob-anchor'
        "run_root=$RunRoot"
        'execution_target=local'
        'device=cuda'
        'source_archive=ref/hmasd.tar'
        'seeds=1,2,3,4,5'
        'parallel_seed_workers=1'
        'rollout_envs_per_seed=32'
        'concurrent_rollout_envs=32'
        'declared_env_steps_per_seed=3000000'
        'actual_env_steps_per_seed=2998400'
        'outer_updates_per_seed=937'
        'optimizer_steps_per_path_per_seed=14055'
        "active_seed=$ActiveSeed"
        "progress_glob=$RunRoot\seeds\seed*\progress.json"
        "result_path=$ResultPath"
    )
    if ($ErrorMessage) {
        $lines += "error=$ErrorMessage"
    }
    [IO.File]::WriteAllLines($StatusPath, $lines)
}

function Invoke-LoggedProcess {
    param(
        [string]$Executable,
        [string[]]$Arguments,
        [string]$StdoutPath,
        [string]$StderrPath
    )
    $process = Start-Process `
        -FilePath $Executable `
        -ArgumentList $Arguments `
        -WorkingDirectory $ProjectRoot `
        -NoNewWindow `
        -Wait `
        -PassThru `
        -RedirectStandardOutput $StdoutPath `
        -RedirectStandardError $StderrPath
    if ($process.ExitCode -ne 0) {
        throw "process exited with code $($process.ExitCode): $(Format-Command $Executable $Arguments)"
    }
}

$seedCommands = foreach ($seed in $Seeds) {
    $seedRoot = Join-Path $RunRoot "seeds\seed$seed"
    $arguments = @(
        'scripts/run_r41_official_hmasd_seed.py'
        '--source-archive', $SourceArchive
        '--source-root', $SourceRoot
        '--output-root', $seedRoot
        '--seed', [string]$seed
    )
    Format-Command $PythonPath $arguments
}
$analysisArguments = @(
    'scripts/analyze_r41_official_hmasd_anchor.py'
    '--run-root', $RunRoot
)
$analysisCommand = Format-Command $PythonPath $analysisArguments

if ($DryRun) {
    Write-Output 'R41 local topology: 1 seed worker x 32 rollout envs; seeds 1..5 sequential.'
    Write-Output "Source: $SourceArchive"
    $seedCommands | ForEach-Object { Write-Output $_ }
    Write-Output $analysisCommand
    exit 0
}

if (Test-Path -LiteralPath $RunRoot) {
    throw "RunRoot already exists; use a new timestamped path: $RunRoot"
}
New-Item -ItemType Directory -Path $SourceRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $RunRoot 'seeds') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $RunRoot 'result') -Force | Out-Null

$env:CUDA_VISIBLE_DEVICES = '0'
$env:MPLBACKEND = 'Agg'
$env:WANDB_MODE = 'disabled'
$env:PYTHONUNBUFFERED = '1'

try {
    Write-Status -State 'running' -Phase 'source_extract'
    & tar.exe -xf $SourceArchive -C $SourceRoot
    if ($LASTEXITCODE -ne 0) {
        throw "tar extraction failed with exit code $LASTEXITCODE"
    }
    $expectedEntry = Join-Path $SourceRoot 'hmasd\scripts\train\train_alice_and_bob.py'
    if (-not (Test-Path -LiteralPath $expectedEntry -PathType Leaf)) {
        throw 'ref/hmasd.tar did not produce the expected HMASD source tree'
    }

    foreach ($seed in $Seeds) {
        $seedRoot = Join-Path $RunRoot "seeds\seed$seed"
        New-Item -ItemType Directory -Path $seedRoot -Force | Out-Null
        $arguments = @(
            'scripts/run_r41_official_hmasd_seed.py'
            '--source-archive', $SourceArchive
            '--source-root', $SourceRoot
            '--output-root', $seedRoot
            '--seed', [string]$seed
        )
        [IO.File]::WriteAllText(
            (Join-Path $seedRoot 'command.txt'),
            (Format-Command $PythonPath $arguments) + [Environment]::NewLine
        )
        Write-Status -State 'running' -Phase 'training' -ActiveSeed $seed
        Invoke-LoggedProcess `
            -Executable $PythonPath `
            -Arguments $arguments `
            -StdoutPath (Join-Path $seedRoot 'runner_stdout.log') `
            -StderrPath (Join-Path $seedRoot 'runner_stderr.log')
    }

    [IO.File]::WriteAllText(
        (Join-Path $RunRoot 'result\command.txt'),
        $analysisCommand + [Environment]::NewLine
    )
    Write-Status -State 'running' -Phase 'analysis'
    Invoke-LoggedProcess `
        -Executable $PythonPath `
        -Arguments $analysisArguments `
        -StdoutPath (Join-Path $RunRoot 'result\analyzer_stdout.log') `
        -StderrPath (Join-Path $RunRoot 'result\analyzer_stderr.log')

    if (-not (Test-Path -LiteralPath $ResultPath -PathType Leaf)) {
        throw 'analyzer did not produce the registered result JSON'
    }
    $result = Get-Content -Raw -LiteralPath $ResultPath | ConvertFrom-Json
    Write-Status -State 'completed' -Phase 'result'
    Write-Output "R41 completed: status=$($result.status); result=$ResultPath"
} catch {
    if (Test-Path -LiteralPath $RunRoot) {
        Write-Status -State 'failed' -Phase 'runner' -ErrorMessage $_.Exception.Message
    }
    throw
}
