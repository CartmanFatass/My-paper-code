#!/usr/bin/env bash
# HA-CTSE S7-S1 reward-pure K/T_i matrix.
#
# Falsifiable mechanism question:
#   Under the same global high-level check interval k, does per-agent realized
#   lifetime T_i improve cooperative MARL versus full-sync/shared fixed lifetime?
#
# This runner intentionally keeps all process/P1/P2/semantic auxiliary rewards OFF.
# Run HMASD original separately with the legacy training entry point as the
# external strong baseline.
set -euo pipefail

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
SMDP_BOOTSTRAP_COEF="${SMDP_BOOTSTRAP_COEF:-0.25}"
LOG_ROOT="${LOG_ROOT:-logs_cloud_s7s1_k_matrix_32env}"
DEVICE="${DEVICE:-cpu}"
SAVE_INTERVAL="${SAVE_INTERVAL:-20}"
CHECKPOINT_KEEP_LAST="${CHECKPOINT_KEEP_LAST:-4}"
PLOT_INTERVAL="${PLOT_INTERVAL:-10}"
DRY_RUN="${DRY_RUN:-0}"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run_s7s1_k_matrix_32env.sh [--dry-run]

Environment variables:
  EXPERIMENTS   core, all, or CSV.
                Names:
                  full_sync_k1
                  shared_fixed_d7
                  decoupled_short
                  decoupled_mixed
                  decoupled_prime
                Default: core
  SEEDS         CSV seeds. Default: 1
  NUM_ENVS      Default: 32
  DEVICE        Default: cpu
  TOTAL_TIMESTEPS Default: 1280000
  EVAL_INTERVAL Default: 160000
  LOG_ROOT      Default: logs_cloud_s7s1_k_matrix_32env

Recommended:
  bash scripts/run_s7s1_k_matrix_32env.sh --dry-run
  bash scripts/run_s7s1_k_matrix_32env.sh

Run all candidate sets:
  EXPERIMENTS=all bash scripts/run_s7s1_k_matrix_32env.sh
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
    EXPERIMENT_CSV="full_sync_k1,shared_fixed_d7,decoupled_short,decoupled_mixed"
    ;;
  all)
    EXPERIMENT_CSV="full_sync_k1,shared_fixed_d7,decoupled_short,decoupled_mixed,decoupled_prime"
    ;;
  *)
    EXPERIMENT_CSV="$EXPERIMENTS"
    ;;
esac

split_csv "$EXPERIMENT_CSV" EXPERIMENT_LIST
split_csv "$SEEDS" SEED_LIST

join_command() { printf '%q ' "$@"; }

process_off=(
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

run_ha_ctse() {
  local name="$1"
  local seed="$2"
  local candidates="$3"
  shift 3

  local steps_k=$((TOTAL_TIMESTEPS / 1000))
  local log_dir="${LOG_ROOT}/ha_ctse_process_${name}_${NUM_ENVS}env_seed${seed}_${steps_k}k"
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
    --skill_lifetime_candidates "$candidates"
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
  local cmd=("$PYTHON_EXE" "${common[@]}" "${process_off[@]}" "$@")

  echo
  echo "===== HA-CTSE S7-S1 K-matrix: ${name} seed=${seed} candidates=${candidates} ====="
  join_command "${cmd[@]}"
  echo
  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi
  mkdir -p "$log_dir"
  "${cmd[@]}"
}

echo "HA-CTSE S7-S1 reward-pure K/T_i matrix"
echo "  experiments:       $EXPERIMENT_CSV"
echo "  seeds:             $SEEDS"
echo "  num_envs:          $NUM_ENVS"
echo "  total_timesteps:   $TOTAL_TIMESTEPS"
echo "  eval_interval:     $EVAL_INTERVAL"
echo "  skill_interval k:  $SKILL_INTERVAL"
echo "  log_root:          $LOG_ROOT"
echo "  device:            $DEVICE"
echo "  dry_run:           $DRY_RUN"
echo "  note: HMASD original baseline must be run separately via train_multiproc_config_1.py"

for seed in "${SEED_LIST[@]}"; do
  for experiment in "${EXPERIMENT_LIST[@]}"; do
    case "$experiment" in
      full_sync_k1)
        run_ha_ctse "s7s1_full_sync_k1_reward_pure" "$seed" "1"
        ;;
      shared_fixed_d7)
        run_ha_ctse "s7s1_shared_fixed_d7_reward_pure" "$seed" "7"
        ;;
      decoupled_short)
        run_ha_ctse "s7s1_decoupled_short_1_2_3_reward_pure" "$seed" "1,2,3"
        ;;
      decoupled_mixed)
        run_ha_ctse "s7s1_decoupled_mixed_1_2_4_8_reward_pure" "$seed" "1,2,4,8"
        ;;
      decoupled_prime)
        run_ha_ctse "s7s1_decoupled_prime_3_7_13_reward_pure" "$seed" "3,7,13"
        ;;
      *)
        echo "Unknown experiment: ${experiment}" >&2
        exit 2
        ;;
    esac
  done
done
