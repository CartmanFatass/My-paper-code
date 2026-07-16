[CmdletBinding()]
param(
    [string]$PythonPath = $(
        if ($env:R47_PYTHON) {
            $env:R47_PYTHON
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
        $RunRoot = Join-Path $LogsRoot 'r47_nsopm_DRY_RUN'
    } else {
        $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
        $RunRoot = Join-Path $LogsRoot "r47_nsopm_$stamp"
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
    Join-Path $ResultRoot 'r47_nsopm.json'
}

if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "R47 Python is missing: $PythonPath"
}
if (-not (Test-Path -LiteralPath $Checkpoint -PathType Leaf)) {
    throw "R47 source checkpoint is missing: $Checkpoint"
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
        'experiment=EXP-20260716-r47-nsopm-g0'
        "scope=$(if ($DryRun) { 'dry_run' } else { 'formal' })"
        "run_root=$RunRoot"
        'execution_target=local'
        'device=cuda'
        'source_seed=47041'
        "natural_groups=$(if ($DryRun) { 2 } else { 64 })"
        "natural_windows=$(if ($DryRun) { 16 } else { 512 })"
        "causal_contexts=$(if ($DryRun) { 1 } else { 64 })"
        'skills=4'
        'replicas=2'
        'branch_horizon=40'
        "forced_steps=$(if ($DryRun) { 320 } else { 20480 })"
        "temporal_nulls=$(if ($DryRun) { 2 } else { 256 })"
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

function Invoke-LoggedProcess {
    param(
        [string]$Executable,
        [string[]]$Arguments,
        [string]$StdoutPath,
        [string]$StderrPath
    )
    Push-Location $ProjectRoot
    try {
        $savedErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        & $Executable @Arguments 1> $StdoutPath 2> $StderrPath
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $savedErrorActionPreference
        Pop-Location
    }
    if ($exitCode -ne 0) {
        throw "process exited with code $exitCode`: $(Format-Command $Executable $Arguments)"
    }
}

$workerArguments = @(
    'scripts/run_r47_nsopm_gate.py'
    '--checkpoint', $Checkpoint
    '--output-root', $SeedRoot
    '--device', 'cuda'
)
$analysisArguments = @(
    'scripts/analyze_r47_nsopm.py'
    '--run-root', $RunRoot
)
if ($DryRun) {
    $workerArguments += '--dry-run'
    $analysisArguments += '--dry-run'
}

if ($DryRun -and (Test-Path -LiteralPath $RunRoot)) {
    $resolvedExisting = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $RunRoot).Path)
    if ($resolvedExisting -ne [IO.Path]::GetFullPath((Join-Path $LogsRoot 'r47_nsopm_DRY_RUN'))) {
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
        (Format-Command $PythonPath $workerArguments) + [Environment]::NewLine
    )
    Write-Status -State 'running' -Phase 'natural_and_forced_collection'
    Invoke-LoggedProcess `
        -Executable $PythonPath `
        -Arguments $workerArguments `
        -StdoutPath (Join-Path $SeedRoot 'runner_stdout.log') `
        -StderrPath (Join-Path $SeedRoot 'runner_stderr.log')
    $seedStatusPath = Join-Path $SeedRoot 'seed_result.json'
    if (-not (Test-Path -LiteralPath $seedStatusPath -PathType Leaf)) {
        throw 'R47 worker did not produce seed_result.json'
    }
    $seedStatus = Get-Content -Raw -LiteralPath $seedStatusPath | ConvertFrom-Json
    if ($seedStatus.state -ne 'completed') {
        throw "R47 worker state is $($seedStatus.state)"
    }

    [IO.File]::WriteAllText(
        (Join-Path $ResultRoot 'command.txt'),
        (Format-Command $PythonPath $analysisArguments) + [Environment]::NewLine
    )
    Write-Status -State 'running' -Phase 'spectral_analysis'
    Invoke-LoggedProcess `
        -Executable $PythonPath `
        -Arguments $analysisArguments `
        -StdoutPath (Join-Path $ResultRoot 'analyzer_stdout.log') `
        -StderrPath (Join-Path $ResultRoot 'analyzer_stderr.log')
    if (-not (Test-Path -LiteralPath $ResultPath -PathType Leaf)) {
        throw 'R47 analyzer did not produce the registered result JSON'
    }
    if ($DryRun) {
        $dry = Get-Content -Raw -LiteralPath $ResultPath | ConvertFrom-Json
        if (-not $dry.dry_run_valid) {
            throw 'R47 focused dry-run checks failed'
        }
        $verified = [IO.Path]::GetFullPath($RunRoot)
        if ($verified -ne [IO.Path]::GetFullPath((Join-Path $LogsRoot 'r47_nsopm_DRY_RUN'))) {
            throw "Refusing to remove unexpected dry-run output: $verified"
        }
        Write-Output 'R47 focused dry run passed; transient output removed.'
        Remove-Item -LiteralPath $verified -Recurse -Force
        exit 0
    }
    $result = Get-Content -Raw -LiteralPath $ResultPath | ConvertFrom-Json
    Write-Status -State 'completed' -Phase 'result'
    Write-Output "R47 completed: status=$($result.status); result=$ResultPath"
} catch {
    if (Test-Path -LiteralPath $RunRoot) {
        Write-Status -State 'failed' -Phase 'runner' -ErrorMessage $_.Exception.Message
    }
    throw
}
