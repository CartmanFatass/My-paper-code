[CmdletBinding()]
param(
    [string]$PythonPath = $(
        if ($env:R50_PYTHON) {
            $env:R50_PYTHON
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
    if ($DryRun) {
        $RunRoot = Join-Path $LogsRoot 'r50_vnsl_DRY_RUN'
    } else {
        $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
        $RunRoot = Join-Path $LogsRoot "r50_vnsl_$stamp"
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
    Join-Path $ResultRoot 'r50_vnsl.json'
}

if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "R50 Python is missing: $PythonPath"
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
        'experiment=EXP-20260716-r50-vnsl-g0'
        "scope=$(if ($DryRun) { 'dry_run' } else { 'formal' })"
        "run_root=$RunRoot"
        'execution_target=local'
        'device=cuda'
        'deterministic=true'
        'model_seed=50050'
        'train_data_seed=60050'
        'eval_data_seed=70050'
        'action_uniform_seed=80050'
        'active_sizes=2,3,4,6,8,12,16'
        "updates=$(if ($DryRun) { 4 } else { 512 })"
        "batch_per_size=$(if ($DryRun) { 8 } else { 64 })"
        "eval_per_size=$(if ($DryRun) { 32 } else { 512 })"
        'environment_steps=0'
        'intrinsic_reward_reads=0'
        'low_level_policy_calls=0'
        'checkpoint_exposure=0'
        "progress_path=$SeedRoot\progress.json"
        "updates_path=$SeedRoot\train_updates.csv"
        "result_path=$ResultPath"
    )
    if ($ErrorMessage) {
        $lines += "error=$ErrorMessage"
    }
    [IO.File]::WriteAllLines($StatusPath, $lines)
}

$arguments = @(
    'scripts/run_r50_vnsl_gate.py'
    '--run-root', $RunRoot
    '--device', 'cuda'
)
if ($DryRun) {
    $arguments += '--dry-run'
}

$ExpectedDryRoot = [IO.Path]::GetFullPath((Join-Path $LogsRoot 'r50_vnsl_DRY_RUN'))
if ($DryRun -and (Test-Path -LiteralPath $RunRoot)) {
    $resolvedExisting = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $RunRoot).Path)
    if ($resolvedExisting -ne $ExpectedDryRoot) {
        throw "Refusing to remove unexpected dry-run path: $resolvedExisting"
    }
    Remove-Item -LiteralPath $resolvedExisting -Recurse -Force
} elseif (Test-Path -LiteralPath $RunRoot) {
    throw "RunRoot already exists; use a new timestamped path: $RunRoot"
}
New-Item -ItemType Directory -Path $SeedRoot -Force | Out-Null
New-Item -ItemType Directory -Path $ResultRoot -Force | Out-Null

$env:CUDA_VISIBLE_DEVICES = '0'
$env:CUBLAS_WORKSPACE_CONFIG = ':4096:8'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:NUMEXPR_NUM_THREADS = '1'
$env:PYTHONHASHSEED = '0'
$env:PYTHONUNBUFFERED = '1'
$env:WANDB_MODE = 'disabled'

try {
    [IO.File]::WriteAllText(
        (Join-Path $SeedRoot 'command.txt'),
        (Format-Command $PythonPath $arguments) + [Environment]::NewLine
    )
    Write-Status -State 'running' -Phase 'training'
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
        throw "R50 worker exited with code $exitCode"
    }
    if (-not (Test-Path -LiteralPath $ResultPath -PathType Leaf)) {
        throw 'R50 worker did not produce the registered result JSON'
    }
    $result = Get-Content -Raw -LiteralPath $ResultPath | ConvertFrom-Json
    if ($DryRun) {
        if (-not $result.dry_run_valid) {
            throw 'R50 focused dry-run checks failed'
        }
        $verified = [IO.Path]::GetFullPath($RunRoot)
        if ($verified -ne $ExpectedDryRoot) {
            throw "Refusing to remove unexpected dry-run output: $verified"
        }
        Write-Output 'R50 focused dry run passed; transient output removed.'
        Remove-Item -LiteralPath $verified -Recurse -Force
        exit 0
    }
    Write-Status -State 'completed' -Phase 'result'
    Write-Output "R50 completed: status=$($result.status); result=$ResultPath"
} catch {
    if (Test-Path -LiteralPath $RunRoot) {
        Write-Status -State 'failed' -Phase 'runner' -ErrorMessage $_.Exception.Message
    }
    throw
}
