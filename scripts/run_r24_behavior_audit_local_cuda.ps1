param(
    [string]$Checkpoint = "logs_r23_next_mechanism_matrix_local\seed1\arm2_qA_reward_coef002\standalone_process_core_update_40.pt",
    [string]$OutDir = "logs_r24_behavior_audit_local",
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$Device = "cuda",
    [int]$Seed = 1,
    [int]$NResets = 16
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Checkpoint)) {
    throw "R24 behavior-audit checkpoint not found: $Checkpoint"
}

& $Python scripts\r24_forced_behavior_audit.py `
    --checkpoint $Checkpoint `
    --out_dir $OutDir `
    --config ha_ctse_process.config `
    --scenario energy `
    --preset S7-S1 `
    --seed $Seed `
    --n_agents 6 `
    --device $Device `
    --horizons 10,20,50 `
    --n_resets $NResets
