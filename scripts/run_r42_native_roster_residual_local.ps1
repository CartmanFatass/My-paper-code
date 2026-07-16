[CmdletBinding()]
param(
    [string]$PythonPath = $(
        if ($env:R42_PYTHON) {
            $env:R42_PYTHON
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
        $RunRoot = Join-Path $LogsRoot 'r42_irr_native_roster_residual_320k_DRY_RUN'
    } else {
        $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
        $RunRoot = Join-Path $LogsRoot "r42_irr_native_roster_residual_320k_$stamp"
    }
}
$RunRoot = [IO.Path]::GetFullPath($RunRoot)
$logsPrefix = $LogsRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $RunRoot.StartsWith($logsPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "RunRoot must stay under $LogsRoot"
}

$SourceArchive = Join-Path $ProjectRoot 'ref\hmasd.tar'
$SourceRoot = Join-Path $RunRoot 'source'
$StatusPath = Join-Path $RunRoot 'runner_status.txt'
$ResultPath = Join-Path $RunRoot 'result\r42_irr_native_roster_residual.json'
$Modes = @('fixed_refresh', 'incumbent_roster_residual')
$Seed = 42041

if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "R42 Python is missing: $PythonPath"
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
        [string]$ErrorMessage = '',
        [string]$ProcessRows = ''
    )
    $lines = @(
        "updated=$((Get-Date).ToString('o'))"
        "state=$State"
        "phase=$Phase"
        'experiment=EXP-20260716-r42-irr-native-roster-residual'
        "run_root=$RunRoot"
        'execution_target=local'
        'device=cuda'
        'source_archive=ref/hmasd.tar'
        "source_checkpoint=$SourceCheckpoint"
        'seed=42041'
        'arms=fixed_refresh,incumbent_roster_residual'
        'parallel_arm_workers=2'
        'rollout_envs_per_arm=16'
        'concurrent_rollout_envs=32'
        'declared_env_steps_per_arm=320000'
        'outer_updates_per_arm=200'
        'optimizer_steps_per_path_per_arm=3000'
        "progress_glob=$RunRoot\arms\*\progress.json"
        "result_path=$ResultPath"
    )
    if ($ProcessRows) {
        $lines += "processes=$ProcessRows"
    }
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

function Arm-Arguments {
    param([string]$Mode)
    $armRoot = Join-Path $RunRoot "arms\$Mode"
    return @(
        'scripts/run_r42_native_roster_residual_arm.py'
        '--source-archive', $SourceArchive
        '--source-root', $SourceRoot
        '--source-checkpoint', $SourceCheckpoint
        '--output-root', $armRoot
        '--seed', [string]$Seed
        '--mode', $Mode
    )
}

$analysisArguments = @(
    'scripts/analyze_r42_native_roster_residual.py'
    '--run-root', $RunRoot
)

if ($DryRun) {
    Write-Output 'R42 topology: 2 concurrent arms x 16 rollout envs; 320K steps and 3,000 optimizer steps/path/arm.'
    Write-Output "Source: $SourceArchive"
    Write-Output "Checkpoint: $SourceCheckpoint"
    foreach ($mode in $Modes) {
        Write-Output (Format-Command $PythonPath (Arm-Arguments $mode))
    }
    Write-Output (Format-Command $PythonPath $analysisArguments)
    exit 0
}

if (Test-Path -LiteralPath $RunRoot) {
    throw "RunRoot already exists; use a new timestamped path: $RunRoot"
}
New-Item -ItemType Directory -Path $SourceRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $RunRoot 'arms') -Force | Out-Null
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

    $processes = @()
    foreach ($mode in $Modes) {
        $armRoot = Join-Path $RunRoot "arms\$mode"
        New-Item -ItemType Directory -Path $armRoot -Force | Out-Null
        $arguments = Arm-Arguments $mode
        [IO.File]::WriteAllText(
            (Join-Path $armRoot 'command.txt'),
            (Format-Command $PythonPath $arguments) + [Environment]::NewLine
        )
        $process = Start-Process `
            -FilePath $PythonPath `
            -ArgumentList $arguments `
            -WorkingDirectory $ProjectRoot `
            -RedirectStandardOutput (Join-Path $armRoot 'runner_stdout.log') `
            -RedirectStandardError (Join-Path $armRoot 'runner_stderr.log') `
            -WindowStyle Hidden `
            -PassThru
        $processes += [pscustomobject]@{ Mode = $mode; Process = $process }
    }
    $processRows = ($processes | ForEach-Object { "$($_.Mode):$($_.Process.Id)" }) -join ','
    Write-Status -State 'running' -Phase 'training' -ProcessRows $processRows
    foreach ($entry in $processes) {
        $entry.Process.WaitForExit()
    }
    # Windows PowerShell can expose a null ExitCode after Start-Process with
    # redirected streams even though WaitForExit() has returned.  The arm
    # writes seed_status.json only after its complete result is durable, so use
    # that state when the process object cannot report an exit code.  A real
    # non-zero exit code still wins and is never masked by the status file.
    $failed = @()
    foreach ($entry in $processes) {
        $entry.Process.Refresh()
        $exitCode = $entry.Process.ExitCode
        $seedStatusPath = Join-Path $RunRoot "arms\$($entry.Mode)\seed_status.json"
        $workerState = ''
        if (Test-Path -LiteralPath $seedStatusPath -PathType Leaf) {
            $workerState = (Get-Content -Raw -LiteralPath $seedStatusPath | ConvertFrom-Json).state
        }
        if (($null -ne $exitCode -and $exitCode -ne 0) -or $workerState -ne 'completed') {
            $failed += [pscustomobject]@{
                Mode = $entry.Mode
                ExitCode = $exitCode
                WorkerState = $workerState
            }
        }
    }
    if ($failed.Count -gt 0) {
        $failureRows = ($failed | ForEach-Object {
            "$($_.Mode):exit=$($_.ExitCode):state=$($_.WorkerState)"
        }) -join ','
        throw "training arm failure: $failureRows"
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
        throw 'analyzer did not produce the registered R42 result JSON'
    }
    $result = Get-Content -Raw -LiteralPath $ResultPath | ConvertFrom-Json
    Write-Status -State 'completed' -Phase 'result'
    Write-Output "R42 completed: status=$($result.status); result=$ResultPath"
} catch {
    if (Test-Path -LiteralPath $RunRoot) {
        Write-Status -State 'failed' -Phase 'runner' -ErrorMessage $_.Exception.Message
    }
    throw
}
