#!/usr/bin/env bash
# HA-CTSE P3-4 forcing-reward cloud sweep.
#
# Purpose:
#   Test the first active HMASD-like forcing loop under decoupled per-agent
#   skill lifetimes.  This runner keeps process/posterior/topology-role
#   semantic rewards off and varies only the P3-4 forcing components.
#
# Examples:
#   bash scripts/run_p3_4_forcing_cloud_32env.sh --dry-run
#   bash scripts/run_p3_4_forcing_cloud_32env.sh
#   EXPERIMENTS=all SEEDS=1 TOTAL_TIMESTEPS=1280000 bash scripts/run_p3_4_forcing_cloud_32env.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_EXE="${PYTHON_EXE:-python}"
EXPERIMENTS="${EXPERIMENTS:-core}"        # core, all, or CSV names
SEEDS="${SEEDS:-1}"
TOTAL_TIMESTEPS="${TOTAL_TIMESTEPS:-1280000}"
EVAL_INTERVAL="${EVAL_INTERVAL:-160000}"
EVAL_EPISODES="${EVAL_EPISODES:-20}"
NUM_ENVS="${NUM_ENVS:-32}"
ROLLOUT_LENGTH="${ROLLOUT_LENGTH:-500}"
SKILL_INTERVAL="${SKILL_INTERVAL:-10}"
N_AGENTS="${N_AGENTS:-6}"
PRESET="${PRESET:-S7-S1}"
SCENARIO="${SCENARIO:-energy}"
COLLECTOR_BACKEND="${COLLECTOR_BACKEND:-subproc}"
COLLECTOR_START_METHOD="${COLLECTOR_START_METHOD:-spawn}"
SKILL_LIFETIME_CANDIDATES="${SKILL_LIFETIME_CANDIDATES:-1,2,3}"
SKILL_EFFECT_HORIZONS="${SKILL_EFFECT_HORIZONS:-3,5,10,20}"
SKILL_EFFECT_STRIDE="${SKILL_EFFECT_STRIDE:-5}"
SKILL_EFFECT_MAX_WINDOWS="${SKILL_EFFECT_MAX_WINDOWS:-8192}"
SMDP_BOOTSTRAP_COEF="${SMDP_BOOTSTRAP_COEF:-0.25}"
FORCE_WARMUP_STEPS="${FORCE_WARMUP_STEPS:-80000}"
FORCE_CLIP="${FORCE_CLIP:-0.05}"
FORCE_DISC_COEF="${FORCE_DISC_COEF:-0.02}"
FORCE_EFFECT_COEF="${FORCE_EFFECT_COEF:-0.01}"
LOG_ROOT="${LOG_ROOT:-logs_cloud_p3_4_forcing_32env}"
DEVICE="${DEVICE:-cpu}"
SAVE_INTERVAL="${SAVE_INTERVAL:-20}"
CHECKPOINT_KEEP_LAST="${CHECKPOINT_KEEP_LAST:-4}"
PLOT_INTERVAL="${PLOT_INTERVAL:-10}"
DRY_RUN="${DRY_RUN:-0}"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run_p3_4_forcing_cloud_32env.sh [--dry-run]

Environment variables:
  PYTHON_EXE                 Python executable. Default: python
  EXPERIMENTS                core, all, or CSV.
                             Core: reward_pure,force_probe,force_disc_only,force_disc_effect
                             All:  core + force_effect_only,force_disc_effect_no_gate
  SEEDS                      CSV seeds. Default: 1
  TOTAL_TIMESTEPS            Default: 1280000
  EVAL_INTERVAL              Default: 160000
  EVAL_EPISODES              Default: 20
  NUM_ENVS                   Default: 32
  DEVICE                     Default: cpu
  LOG_ROOT                   Default: logs_cloud_p3_4_forcing_32env
  SKILL_LIFETIME_CANDIDATES  Default: 1,2,3
  SKILL_EFFECT_HORIZONS      Default: 3,5,10,20
  SKILL_EFFECT_STRIDE        Default: 5
  FORCE_WARMUP_STEPS         Default: 80000
  FORCE_CLIP                 Default: 0.05
  FORCE_DISC_COEF            Default: 0.02
  FORCE_EFFECT_COEF          Default: 0.01

Recommended:
  bash scripts/run_p3_4_forcing_cloud_32env.sh --dry-run
  bash scripts/run_p3_4_forcing_cloud_32env.sh

Run only the main reward arms:
  EXPERIMENTS=force_disc_only,force_disc_effect bash scripts/run_p3_4_forcing_cloud_32env.sh

Run every arm:
  EXPERIMENTS=all bash scripts/run_p3_4_forcing_cloud_32env.sh
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

split_csv() {
  local input="$1"
  local -n out_ref="$2"
  IFS=',' read -r -a out_ref <<< "$input"
}

case "$EXPERIMENTS" in
  core)
    EXPERIMENT_CSV="reward_pure,force_probe,force_disc_only,force_disc_effect"
    ;;
  all)
    EXPERIMENT_CSV="reward_pure,force_probe,force_disc_only,force_disc_effect,force_effect_only,force_disc_effect_no_gate"
    ;;
  *)
    EXPERIMENT_CSV="$EXPERIMENTS"
    ;;
esac

split_csv "$EXPERIMENT_CSV" EXPERIMENT_LIST
split_csv "$SEEDS" SEED_LIST

join_command() { printf '%q ' "$@"; }

base_semantic_off=(
  --process_reward_injection none
  --process_reward_coef 0.0
  --process_contrast_coef 0.0
  --process_outcome_coef 0.0
  --process_prior_coef 0.0
  --process_shortcut_coef 0.0
  --context_shortcut_coef 0.0
  --process_shortcut_margin_coef 0.0
  --disable_process_posterior_mi
  --disable_outcome_residual_probe
  --disable_process_reward
  --disable_transition_skill_discriminator
  --disable_topology_role_probe
)

skill_effect_common=(
  --skill_effect_horizons "$SKILL_EFFECT_HORIZONS"
  --skill_effect_stride "$SKILL_EFFECT_STRIDE"
  --skill_effect_max_windows "$SKILL_EFFECT_MAX_WINDOWS"
)

run_ha_ctse() {
  local name="$1"
  local seed="$2"
  shift 2

  local steps_k=$((TOTAL_TIMESTEPS / 1000))
  local log_dir="${LOG_ROOT}/ha_ctse_process_s7s1_${name}_${NUM_ENVS}env_seed${seed}_${steps_k}k"
  local common=(
    -m ha_ctse_process.train
    --config ha_ctse_process.config
    --scenario "$SCENARIO"
    --preset "$PRESET"
    --seed "$seed"
    --n_agents "$N_AGENTS"
    --collector_backend "$COLLECTOR_BACKEND"
    --collector_start_method "$COLLECTOR_START_METHOD"
    --num_envs "$NUM_ENVS"
    --rollout_length "$ROLLOUT_LENGTH"
    --skill_interval "$SKILL_INTERVAL"
    --skill_lifetime_candidates "$SKILL_LIFETIME_CANDIDATES"
    --total_timesteps "$TOTAL_TIMESTEPS"
    --eval_interval "$EVAL_INTERVAL"
    --eval_episodes "$EVAL_EPISODES"
    --save_interval "$SAVE_INTERVAL"
    --checkpoint_keep_last "$CHECKPOINT_KEEP_LAST"
    --plot_interval "$PLOT_INTERVAL"
    --low_clip_epsilon 0.1
    --smdp_bootstrap_coef "$SMDP_BOOTSTRAP_COEF"
    --device "$DEVICE"
    --log_dir "$log_dir"
  )
  local cmd=("$PYTHON_EXE" "${common[@]}" "$@")

  echo
  echo "===== HA-CTSE P3-4 forcing: ${name} seed=${seed} ====="
  join_command "${cmd[@]}"
  echo
  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi
  mkdir -p "$log_dir"
  "${cmd[@]}"
}

echo "HA-CTSE P3-4 forcing cloud sweep"
echo "  root:              $ROOT_DIR"
echo "  experiments:       $EXPERIMENT_CSV"
echo "  seeds:             $SEEDS"
echo "  num_envs:          $NUM_ENVS"
echo "  total_timesteps:   $TOTAL_TIMESTEPS"
echo "  eval_interval:     $EVAL_INTERVAL"
echo "  duration_set:      $SKILL_LIFETIME_CANDIDATES"
echo "  effect_horizons:   $SKILL_EFFECT_HORIZONS"
echo "  log_root:          $LOG_ROOT"
echo "  device:            $DEVICE"

for seed in "${SEED_LIST[@]}"; do
  for experiment in "${EXPERIMENT_LIST[@]}"; do
    case "$experiment" in
      reward_pure)
        run_ha_ctse "reward_pure" "$seed" \
          "${base_semantic_off[@]}"
        ;;
      force_probe)
        run_ha_ctse "force_probe" "$seed" \
          "${base_semantic_off[@]}" \
          "${skill_effect_common[@]}" \
          --enable_skill_forcing_probe \
          --skill_force_reward_injection none \
          --skill_force_disc_coef "$FORCE_DISC_COEF" \
          --skill_force_effect_coef "$FORCE_EFFECT_COEF" \
          --skill_force_warmup_steps "$FORCE_WARMUP_STEPS" \
          --skill_force_clip "$FORCE_CLIP"
        ;;
      force_disc_only)
        run_ha_ctse "force_disc_only" "$seed" \
          "${base_semantic_off[@]}" \
          "${skill_effect_common[@]}" \
          --enable_skill_forcing_reward \
          --skill_force_disc_coef "$FORCE_DISC_COEF" \
          --skill_force_effect_coef 0.0 \
          --skill_force_warmup_steps "$FORCE_WARMUP_STEPS" \
          --skill_force_clip "$FORCE_CLIP"
        ;;
      force_disc_effect)
        run_ha_ctse "force_disc_effect" "$seed" \
          "${base_semantic_off[@]}" \
          "${skill_effect_common[@]}" \
          --enable_skill_forcing_reward \
          --skill_force_disc_coef "$FORCE_DISC_COEF" \
          --skill_force_effect_coef "$FORCE_EFFECT_COEF" \
          --skill_force_warmup_steps "$FORCE_WARMUP_STEPS" \
          --skill_force_clip "$FORCE_CLIP"
        ;;
      force_effect_only)
        run_ha_ctse "force_effect_only" "$seed" \
          "${base_semantic_off[@]}" \
          "${skill_effect_common[@]}" \
          --enable_skill_forcing_reward \
          --skill_force_disc_coef 0.0 \
          --skill_force_effect_coef "$FORCE_EFFECT_COEF" \
          --skill_force_warmup_steps "$FORCE_WARMUP_STEPS" \
          --skill_force_clip "$FORCE_CLIP"
        ;;
      force_disc_effect_no_gate)
        run_ha_ctse "force_disc_effect_no_gate" "$seed" \
          "${base_semantic_off[@]}" \
          "${skill_effect_common[@]}" \
          --enable_skill_forcing_reward \
          --skill_force_disc_coef "$FORCE_DISC_COEF" \
          --skill_force_effect_coef "$FORCE_EFFECT_COEF" \
          --skill_force_warmup_steps "$FORCE_WARMUP_STEPS" \
          --skill_force_clip "$FORCE_CLIP" \
          --disable_skill_force_shortcut_gate
        ;;
      *)
        echo "Unknown experiment: $experiment" >&2
        exit 2
        ;;
    esac
  done
done

echo
echo "HA-CTSE P3-4 forcing sweep complete."
