[CmdletBinding()]
param(
    [string]$PythonPath = $(
        if ($env:R54_PYTHON) {
            $env:R54_PYTHON
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
        $RunRoot = Join-Path $LogsRoot 'r54_hfsr_DRY_RUN'
    } else {
        $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
        $RunRoot = Join-Path $LogsRoot "r54_hfsr_$stamp"
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
    Join-Path $ResultRoot 'r54_hfsr.json'
}

if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "R54 Python is missing: $PythonPath"
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
        'experiment=EXP-20260717-r54-hfsr-g0'
        "scope=$(if ($DryRun) { 'dry_run' } else { 'formal' })"
        "run_root=$RunRoot"
        'execution_target=local'
        'device=cuda'
        'train_team_sizes=8,16,32'
        'heldout_team_sizes=8,16,32,64'
        'representation_arms=full_active_set_reference,hybrid_m8_l2'
        'slot_count=8'
        'exact_residual_count=2'
        'parameters_per_arm=49576'
        "updates_per_arm=$(if ($DryRun) { 6 } else { 600 })"
        "batch_size=$(if ($DryRun) { 16 } else { 64 })"
        "case_exposures_per_arm=$(if ($DryRun) { 96 } else { 38400 })"
        'environment_reward_terms=0'
        'ppo_steps=0'
        'intrinsic_reward_terms=0'
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
    'scripts/run_r54_hfsr_gate.py'
    '--run-root', $RunRoot
    '--device', 'cuda'
)
if ($DryRun) {
    $arguments += '--dry-run'
}

$ExpectedDryRoot = [IO.Path]::GetFullPath((Join-Path $LogsRoot 'r54_hfsr_DRY_RUN'))
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
$env:PYTHONDONTWRITEBYTECODE = '1'
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
        throw "R54 worker exited with code $exitCode"
    }
    if (-not (Test-Path -LiteralPath $ResultPath -PathType Leaf)) {
        throw 'R54 worker did not produce the registered result JSON'
    }
    $result = Get-Content -Raw -LiteralPath $ResultPath | ConvertFrom-Json
    if ($DryRun) {
        if (-not $result.dry_run_valid) {
            throw 'R54 focused dry-run checks failed'
        }
        $verified = [IO.Path]::GetFullPath($RunRoot)
        if ($verified -ne $ExpectedDryRoot) {
            throw "Refusing to remove unexpected dry-run output: $verified"
        }
        Write-Output 'R54 focused dry run passed; transient output removed.'
        Remove-Item -LiteralPath $verified -Recurse -Force
        exit 0
    }
    Write-Status -State 'completed' -Phase 'result'
    Write-Output "R54 completed: status=$($result.status); result=$ResultPath"
} catch {
    if (Test-Path -LiteralPath $RunRoot) {
        Write-Status -State 'failed' -Phase 'runner' -ErrorMessage $_.Exception.Message
    }
    throw
}
