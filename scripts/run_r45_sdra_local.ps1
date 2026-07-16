[CmdletBinding()]
param(
    [string]$PythonPath = $(
        if ($env:R45_PYTHON) {
            $env:R45_PYTHON
        } else {
            'C:\Users\wu\.conda\envs\SB3\python.exe'
        }
    ),
    [string]$SourceCheckpoint = 'C:\project\HMASD\logs\r41b_hmasd_full_source_20260716_035300_retry2\seeds\seed1\checkpoints\exact_final.pt',
    [string]$RunRoot = '',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$LogsRoot = [IO.Path]::GetFullPath((Join-Path $ProjectRoot 'logs'))
if (-not $RunRoot) {
    if ($DryRun) {
        $RunRoot = Join-Path $LogsRoot 'r45_sdra_160k_DRY_RUN'
    } else {
        $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
        $RunRoot = Join-Path $LogsRoot "r45_sdra_160k_$stamp"
    }
}
$RunRoot = [IO.Path]::GetFullPath($RunRoot)
$logsPrefix = $LogsRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $RunRoot.StartsWith($logsPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "RunRoot must stay under $LogsRoot"
}

$SourceArchive = Join-Path $ProjectRoot 'ref\hmasd.tar'
$SourceRoot = Join-Path $RunRoot 'source'
$SeedRoot = Join-Path $RunRoot 'seed'
$StatusPath = Join-Path $RunRoot 'runner_status.txt'
$ResultPath = Join-Path $RunRoot 'result\r45_sdra_identifiability.json'
$Seed = 43041

if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "R45 Python is missing: $PythonPath"
}
if (-not (Test-Path -LiteralPath $SourceArchive -PathType Leaf)) {
    throw "Original HMASD source archive is missing: $SourceArchive"
}
if (-not (Test-Path -LiteralPath $SourceCheckpoint -PathType Leaf)) {
    throw "R41B source checkpoint is missing: $SourceCheckpoint"
}
$SourceCheckpoint = [IO.Path]::GetFullPath($SourceCheckpoint)

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
        [string]$ErrorMessage = ''
    )
    $lines = @(
        "updated=$((Get-Date).ToString('o'))"
        "state=$State"
        "phase=$Phase"
        'experiment=EXP-20260716-r45-sdra-g0'
        "run_root=$RunRoot"
        'execution_target=local'
        'device=cuda'
        'source_archive=ref/hmasd.tar'
        "source_checkpoint=$SourceCheckpoint"
        'seed=43041'
        'rollout_envs=16'
        'declared_env_steps=160000'
        'outer_updates=100'
        'env_check_rows=3200'
        'structural_rows=16'
        'normal_env_check_rows=3184'
        'normal_agent_factor_rows=6368'
        'source_optimizer_steps_per_path=0'
        'renewal_actor_optimizer_steps=0'
        'critic_models=4'
        'critic_steps_per_model=195'
        'critic_optimizer_steps_total=780'
        'controller_clock=source_global_k50_reset_censored'
        'credit=sequential_crossfit_doubly_robust'
        'comparator=true_Q_vs_action_blind_sham'
        'm2_threshold=LCB95(WMSE_sham_over_true_minus_1)>0'
        "progress_path=$SeedRoot\progress.json"
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
    Push-Location $ProjectRoot
    try {
        & $Executable @Arguments 1> $StdoutPath 2> $StderrPath
        $exitCode = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    if ($exitCode -ne 0) {
        throw "process exited with code $exitCode`: $(Format-Command $Executable $Arguments)"
    }
}

$workerArguments = @(
    'scripts/run_r45_sdra_gate.py'
    '--source-archive', $SourceArchive
    '--source-root', $SourceRoot
    '--source-checkpoint', $SourceCheckpoint
    '--output-root', $SeedRoot
    '--seed', [string]$Seed
)
$analysisArguments = @(
    'scripts/analyze_r45_sdra.py'
    '--run-root', $RunRoot
)

if ($DryRun) {
    Write-Output 'R45 topology: one frozen-source collection worker with 16 rollout envs.'
    Write-Output 'Collection: 160K steps, 100 updates, 6,368 natural normal factor rows.'
    Write-Output 'Offline fitting: fold-A/B true-Q and action-blind sham, 195 steps/model.'
    Write-Output 'No source or renewal-actor optimizer step; no forced branch or new reward.'
    Write-Output 'M2 uses the nontrivial interpretation LCB95(WMSE ratio - 1) > 0.'
    Write-Output "Source: $SourceArchive"
    Write-Output "Checkpoint: $SourceCheckpoint"
    Write-Output (Format-Command $PythonPath $workerArguments)
    Write-Output (Format-Command $PythonPath $analysisArguments)
    exit 0
}

if (Test-Path -LiteralPath $RunRoot) {
    throw "RunRoot already exists; use a new timestamped path: $RunRoot"
}
New-Item -ItemType Directory -Path $SourceRoot -Force | Out-Null
New-Item -ItemType Directory -Path $SeedRoot -Force | Out-Null
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

    [IO.File]::WriteAllText(
        (Join-Path $SeedRoot 'command.txt'),
        (Format-Command $PythonPath $workerArguments) + [Environment]::NewLine
    )
    Write-Status -State 'running' -Phase 'collection_and_critic_fit'
    Invoke-LoggedProcess `
        -Executable $PythonPath `
        -Arguments $workerArguments `
        -StdoutPath (Join-Path $SeedRoot 'runner_stdout.log') `
        -StderrPath (Join-Path $SeedRoot 'runner_stderr.log')
    $seedStatusPath = Join-Path $SeedRoot 'seed_status.json'
    if (-not (Test-Path -LiteralPath $seedStatusPath -PathType Leaf)) {
        throw 'R45 worker did not produce seed_status.json'
    }
    $seedStatus = Get-Content -Raw -LiteralPath $seedStatusPath | ConvertFrom-Json
    if ($seedStatus.state -ne 'completed') {
        throw "R45 worker state is $($seedStatus.state)"
    }

    [IO.File]::WriteAllText(
        (Join-Path $RunRoot 'result\command.txt'),
        (Format-Command $PythonPath $analysisArguments) + [Environment]::NewLine
    )
    Write-Status -State 'running' -Phase 'analysis'
    Invoke-LoggedProcess `
        -Executable $PythonPath `
        -Arguments $analysisArguments `
        -StdoutPath (Join-Path $RunRoot 'result\analyzer_stdout.log') `
        -StderrPath (Join-Path $RunRoot 'result\analyzer_stderr.log')
    if (-not (Test-Path -LiteralPath $ResultPath -PathType Leaf)) {
        throw 'analyzer did not produce the registered R45 result JSON'
    }
    $result = Get-Content -Raw -LiteralPath $ResultPath | ConvertFrom-Json
    Write-Status -State 'completed' -Phase 'result'
    Write-Output "R45 completed: status=$($result.status); result=$ResultPath"
} catch {
    Write-Status -State 'failed' -Phase 'runner' -ErrorMessage $_.Exception.Message
    throw
}
