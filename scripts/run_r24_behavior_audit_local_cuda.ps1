param(
    [string]$Checkpoint = "logs_r23_next_mechanism_matrix_local\arm2_qA_reward\standalone_process_core_update_40.pt",
    [string]$OutDir = "logs_r24_behavior_audit_local",
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$Device = "cuda",
    [int]$Seed = 1,
    [int]$NResets = 16
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

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

if ($LASTEXITCODE -ne 0) {
    throw "R24 behavior audit failed with exit code $LASTEXITCODE"
}
