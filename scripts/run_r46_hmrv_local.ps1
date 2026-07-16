[CmdletBinding()]
param(
    [string]$PythonPath = $(
        if ($env:R46_PYTHON) {
            $env:R46_PYTHON
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
        $RunRoot = Join-Path $LogsRoot 'r46_hmrv_64k_DRY_RUN'
    } else {
        $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
        $RunRoot = Join-Path $LogsRoot "r46_hmrv_64k_$stamp"
    }
}
$RunRoot = [IO.Path]::GetFullPath($RunRoot)
$logsPrefix = $LogsRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $RunRoot.StartsWith($logsPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "RunRoot must stay under $LogsRoot"
}

$SeedRoot = Join-Path $RunRoot 'seed'
$StatusPath = Join-Path $RunRoot 'runner_status.txt'
$ResultPath = Join-Path $RunRoot 'result\r46_hmrv_identifiability.json'

if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "R46 Python is missing: $PythonPath"
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
        'experiment=EXP-20260716-r46-hmrv-g0'
        "run_root=$RunRoot"
        'execution_target=local'
        'device=cuda'
        'environment_seed=46041'
        'behavior_action_seed=46041'
        'evaluation_action_seed=56041'
        'rollout_envs=16'
        'episodes_per_env=100'
        'declared_env_steps=64000'
        'k0=5'
        'horizon=40'
        'usable_event_rows=9600'
        'focal_rows=19200'
        'policy_low_skill_intrinsic_optimizer_steps=0'
        'critic_models=4'
        'critic_steps_per_model=570'
        'critic_optimizer_steps_total=2280'
        'bootstrap_cluster=(env_rank,episode_index)'
        'bootstrap_repetitions=10000'
        'bootstrap_seed=62046'
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
    'scripts/run_r46_hmrv_gate.py'
    '--output-root', $SeedRoot
    '--device', 'cuda'
)
$analysisArguments = @(
    'scripts/analyze_r46_hmrv.py'
    '--run-root', $RunRoot
)

if ($DryRun) {
    Write-Output 'R46 topology: one local CUDA worker; no source archive or policy process.'
    Write-Output 'Collection: 16 envs x 100 episodes x 40 steps = 64,000 steps.'
    Write-Output 'Evidence: 9,600 usable checks and 19,200 focal rows.'
    Write-Output 'Learning: four 6->32 GELU->2 critics, 570 steps/model, 2,280 total.'
    Write-Output 'No policy, low, skill, intrinsic, shaping, or task-specific reward path.'
    Write-Output (Format-Command $PythonPath $workerArguments)
    Write-Output (Format-Command $PythonPath $analysisArguments)
    exit 0
}

if (Test-Path -LiteralPath $RunRoot) {
    throw "RunRoot already exists; use a new timestamped path: $RunRoot"
}
New-Item -ItemType Directory -Path $SeedRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $RunRoot 'result') -Force | Out-Null

$env:CUDA_VISIBLE_DEVICES = '0'
$env:MPLBACKEND = 'Agg'
$env:WANDB_MODE = 'disabled'
$env:PYTHONUNBUFFERED = '1'

try {
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
    $seedStatusPath = Join-Path $SeedRoot 'seed_result.json'
    if (-not (Test-Path -LiteralPath $seedStatusPath -PathType Leaf)) {
        throw 'R46 worker did not produce seed_result.json'
    }
    $seedStatus = Get-Content -Raw -LiteralPath $seedStatusPath | ConvertFrom-Json
    if ($seedStatus.state -ne 'completed') {
        throw "R46 worker state is $($seedStatus.state)"
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
        throw 'analyzer did not produce the registered R46 result JSON'
    }
    $result = Get-Content -Raw -LiteralPath $ResultPath | ConvertFrom-Json
    Write-Status -State 'completed' -Phase 'result'
    Write-Output "R46 completed: status=$($result.status); result=$ResultPath"
} catch {
    Write-Status -State 'failed' -Phase 'runner' -ErrorMessage $_.Exception.Message
    throw
}
