[CmdletBinding()]
param(
    [string]$PythonPath = $(
        if ($env:R48_PYTHON) {
            $env:R48_PYTHON
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
$Checkpoint = Join-Path $ProjectRoot 'logs\r30_alice_bob_paired_64k_20260714_163908\runs\adaptive_keep_set\seed30031\standalone_process_core_final.pt'
if (-not $RunRoot) {
    if ($DryRun) {
        $RunRoot = Join-Path $LogsRoot 'r48_sbrs_DRY_RUN'
    } else {
        $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
        $RunRoot = Join-Path $LogsRoot "r48_sbrs_$stamp"
    }
}
$RunRoot = [IO.Path]::GetFullPath($RunRoot)
$logsPrefix = $LogsRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $RunRoot.StartsWith($logsPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "RunRoot must stay under $LogsRoot"
}

$SeedRoot = Join-Path $RunRoot 'seed'
$ResultRoot = Join-Path $RunRoot 'result'
$StatusPath = Join-Path $RunRoot 'runner_status.txt'
$ResultPath = if ($DryRun) {
    Join-Path $ResultRoot 'dry_run_check.json'
} else {
    Join-Path $ResultRoot 'r48_sbrs.json'
}

if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "R48 Python is missing: $PythonPath"
}
if (-not (Test-Path -LiteralPath $Checkpoint -PathType Leaf)) {
    throw "R48 source checkpoint is missing: $Checkpoint"
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
        [string]$ErrorMessage = ''
    )
    $lines = @(
        "updated=$((Get-Date).ToString('o'))"
        "state=$State"
        "phase=$Phase"
        'experiment=EXP-20260716-r48-sbrs-g0'
        "scope=$(if ($DryRun) { 'dry_run' } else { 'formal' })"
        "run_root=$RunRoot"
        'execution_target=local'
        'device=cuda'
        'source_seed=47041'
        'innovation_seed=68041'
        "contexts=$(if ($DryRun) { 2 } else { 64 })"
        'targets_per_context=3'
        'replicas_per_target=2'
        'arms=carry_hidden,reset_on_set'
        'branch_horizon=40'
        "forced_steps=$(if ($DryRun) { 960 } else { 30720 })"
        'all_optimizer_steps=0'
        'external_reward_used=false'
        "progress_path=$SeedRoot\progress.json"
        "result_path=$ResultPath"
    )
    if ($ErrorMessage) {
        $lines += "error=$ErrorMessage"
    }
    [IO.File]::WriteAllLines($StatusPath, $lines)
}

$arguments = @(
    'scripts/run_r48_sbrs_gate.py'
    '--checkpoint', $Checkpoint
    '--run-root', $RunRoot
    '--device', 'cuda'
)
if ($DryRun) {
    $arguments += '--dry-run'
}

if ($DryRun -and (Test-Path -LiteralPath $RunRoot)) {
    $resolvedExisting = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $RunRoot).Path)
    if ($resolvedExisting -ne [IO.Path]::GetFullPath((Join-Path $LogsRoot 'r48_sbrs_DRY_RUN'))) {
        throw "Refusing to remove unexpected dry-run path: $resolvedExisting"
    }
    Remove-Item -LiteralPath $resolvedExisting -Recurse -Force
} elseif (Test-Path -LiteralPath $RunRoot) {
    throw "RunRoot already exists; use a new timestamped path: $RunRoot"
}
New-Item -ItemType Directory -Path $SeedRoot -Force | Out-Null
New-Item -ItemType Directory -Path $ResultRoot -Force | Out-Null

$env:CUDA_VISIBLE_DEVICES = '0'
$env:MPLBACKEND = 'Agg'
$env:WANDB_MODE = 'disabled'
$env:PYTHONUNBUFFERED = '1'

try {
    [IO.File]::WriteAllText(
        (Join-Path $SeedRoot 'command.txt'),
        (Format-Command $PythonPath $arguments) + [Environment]::NewLine
    )
    Write-Status -State 'running' -Phase 'natural_and_paired_forced_collection'
    Push-Location $ProjectRoot
    try {
        $savedErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        & $PythonPath @arguments `
            1> (Join-Path $SeedRoot 'runner_stdout.log') `
            2> (Join-Path $SeedRoot 'runner_stderr.log')
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $savedErrorActionPreference
        Pop-Location
    }
    if ($exitCode -ne 0) {
        throw "R48 worker exited with code $exitCode"
    }
    if (-not (Test-Path -LiteralPath $ResultPath -PathType Leaf)) {
        throw 'R48 worker did not produce the registered result JSON'
    }
    $result = Get-Content -Raw -LiteralPath $ResultPath | ConvertFrom-Json
    if ($DryRun) {
        if (-not $result.dry_run_valid) {
            throw 'R48 focused dry-run checks failed'
        }
        $verified = [IO.Path]::GetFullPath($RunRoot)
        if ($verified -ne [IO.Path]::GetFullPath((Join-Path $LogsRoot 'r48_sbrs_DRY_RUN'))) {
            throw "Refusing to remove unexpected dry-run output: $verified"
        }
        Write-Output 'R48 focused dry run passed; transient output removed.'
        Remove-Item -LiteralPath $verified -Recurse -Force
        exit 0
    }
    Write-Status -State 'completed' -Phase 'result'
    Write-Output "R48 completed: status=$($result.status); result=$ResultPath"
} catch {
    if (Test-Path -LiteralPath $RunRoot) {
        Write-Status -State 'failed' -Phase 'runner' -ErrorMessage $_.Exception.Message
    }
    throw
}
