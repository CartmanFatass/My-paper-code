#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_EXE="${PYTHON_EXE:-python}"
TOTAL_TIMESTEPS="${TOTAL_TIMESTEPS:-480000}"
EVAL_INTERVAL="${EVAL_INTERVAL:-160000}"
EVAL_EPISODES="${EVAL_EPISODES:-20}"
NUM_ENVS="${NUM_ENVS:-32}"
ROLLOUT_LENGTH="${ROLLOUT_LENGTH:-500}"
SKILL_INTERVAL="${SKILL_INTERVAL:-10}"
N_AGENTS="${N_AGENTS:-6}"
SEEDS="${SEEDS:-1}"
PRESET="${PRESET:-S7-S1}"
SCENARIO="${SCENARIO:-energy}"
COLLECTOR_BACKEND="${COLLECTOR_BACKEND:-subproc}"
COLLECTOR_START_METHOD="${COLLECTOR_START_METHOD:-spawn}"
SMDP_BOOTSTRAP_COEF="${SMDP_BOOTSTRAP_COEF:-0.25}"
LOG_ROOT="${LOG_ROOT:-logs_cloud_overnight_32env}"
DEVICE="${DEVICE:-cpu}"
SAVE_INTERVAL="${SAVE_INTERVAL:-20}"
CHECKPOINT_KEEP_LAST="${CHECKPOINT_KEEP_LAST:-4}"
PLOT_INTERVAL="${PLOT_INTERVAL:-10}"
INCLUDE_RISKY_SEMANTIC="${INCLUDE_RISKY_SEMANTIC:-0}"
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run_ha_ctse_overnight_32env.sh [options]

Purpose:
  Overnight HA-CTSE sweep for the current P1/P1-adjacent ideas.
  Default is breadth-first: seed=1, 32 envs, 480k steps per arm.

Default arms:
  1. short_reward_pure baseline, candidates=(1,2,3)
  2. topology potential low_only, coef=1.0
  3. topology potential high_only, coef=1.0
  4. topology potential high_and_low, coef=0.5
  5. topology potential low_only positive_only, coef=1.0

Optional risky tail:
  Set INCLUDE_RISKY_SEMANTIC=1 to also run topology_role_low_reward.
  This is not part of the clean P1 gate; it is included only as a HMASD-spirit
  exploratory tail after the clean topology-potential arms.

Options:
  --python PATH
  --seeds CSV
  --total-timesteps N
  --eval-interval N
  --eval-episodes N
  --num-envs N
  --rollout-length N
  --skill-interval N
  --n-agents N
  --preset NAME
  --scenario NAME
  --log-root DIR
  --device cpu|cuda
  --include-risky-semantic
  --dry-run

Examples:
  bash scripts/run_ha_ctse_overnight_32env.sh --dry-run
  bash scripts/run_ha_ctse_overnight_32env.sh
  SEEDS=1,2 TOTAL_TIMESTEPS=640000 bash scripts/run_ha_ctse_overnight_32env.sh
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      PYTHON_EXE="$2"; shift 2 ;;
    --seeds)
      SEEDS="$2"; shift 2 ;;
    --total-timesteps)
      TOTAL_TIMESTEPS="$2"; shift 2 ;;
    --eval-interval)
      EVAL_INTERVAL="$2"; shift 2 ;;
    --eval-episodes)
      EVAL_EPISODES="$2"; shift 2 ;;
    --num-envs)
      NUM_ENVS="$2"; shift 2 ;;
    --rollout-length)
      ROLLOUT_LENGTH="$2"; shift 2 ;;
    --skill-interval)
      SKILL_INTERVAL="$2"; shift 2 ;;
    --n-agents)
      N_AGENTS="$2"; shift 2 ;;
    --preset)
      PRESET="$2"; shift 2 ;;
    --scenario)
      SCENARIO="$2"; shift 2 ;;
    --log-root)
      LOG_ROOT="$2"; shift 2 ;;
    --device)
      DEVICE="$2"; shift 2 ;;
    --include-risky-semantic)
      INCLUDE_RISKY_SEMANTIC=1; shift ;;
    --dry-run)
      DRY_RUN=1; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2 ;;
  esac
done

IFS=',' read -r -a SEED_LIST <<< "$SEEDS"

join_command() {
  printf '%q ' "$@"
}

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
  local cmd=("$PYTHON_EXE" "${common[@]}" "$@")

  echo
  echo "===== HA-CTSE overnight: ${name} seed=${seed} candidates=${candidates} ====="
  join_command "${cmd[@]}"
  echo
  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi
  mkdir -p "$log_dir"
  "${cmd[@]}"
}

isolated_process_off=(
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

echo "HA-CTSE overnight cloud sweep"
echo "  root:              $ROOT_DIR"
echo "  seeds:             $SEEDS"
echo "  num_envs:          $NUM_ENVS"
echo "  total_timesteps:   $TOTAL_TIMESTEPS"
echo "  eval_interval:     $EVAL_INTERVAL"
echo "  log_root:          $LOG_ROOT"
echo "  device:            $DEVICE"
echo "  risky_semantic:    $INCLUDE_RISKY_SEMANTIC"

for seed in "${SEED_LIST[@]}"; do
  run_ha_ctse "s7s1_short_reward_pure" "$seed" "1,2,3" \
    "${isolated_process_off[@]}"

  run_ha_ctse "s7s1_topopot_low_coef1" "$seed" "1,2,3" \
    "${isolated_process_off[@]}" \
    --enable_topology_potential_shaping \
    --topology_potential_injection low_only \
    --topology_potential_coef 1.0 \
    --topology_potential_clip 0.05 \
    --topology_potential_discount_mode delta \
    --topology_potential_warmup_steps 0

  run_ha_ctse "s7s1_topopot_high_coef1" "$seed" "1,2,3" \
    "${isolated_process_off[@]}" \
    --enable_topology_potential_shaping \
    --topology_potential_injection high_only \
    --topology_potential_coef 1.0 \
    --topology_potential_clip 0.05 \
    --topology_potential_discount_mode delta \
    --topology_potential_warmup_steps 0

  run_ha_ctse "s7s1_topopot_highlow_coef05" "$seed" "1,2,3" \
    "${isolated_process_off[@]}" \
    --enable_topology_potential_shaping \
    --topology_potential_injection high_and_low \
    --topology_potential_coef 0.5 \
    --topology_potential_clip 0.05 \
    --topology_potential_discount_mode delta \
    --topology_potential_warmup_steps 0

  run_ha_ctse "s7s1_topopot_low_pos_coef1" "$seed" "1,2,3" \
    "${isolated_process_off[@]}" \
    --enable_topology_potential_shaping \
    --topology_potential_injection low_only \
    --topology_potential_coef 1.0 \
    --topology_potential_clip 0.05 \
    --topology_potential_discount_mode delta \
    --topology_potential_positive_only \
    --topology_potential_warmup_steps 0

  if [[ "$INCLUDE_RISKY_SEMANTIC" == "1" ]]; then
    run_ha_ctse "s7s1_topology_role_low_reward_tail" "$seed" "1,2,3" \
      --process_reward_injection none \
      --process_reward_coef 0.0 \
      --process_contrast_coef 0.0 \
      --process_outcome_coef 0.0 \
      --process_prior_coef 0.0 \
      --process_shortcut_coef 0.0 \
      --context_shortcut_coef 0.0 \
      --process_shortcut_margin_coef 0.0 \
      --disable_process_posterior_mi \
      --disable_outcome_residual_probe \
      --disable_transition_skill_discriminator \
      --topology_role_coef 1.0 \
      --topology_role_injection low_only \
      --topology_role_reward_coef 0.02 \
      --topology_role_reward_clip 0.03
  fi
done
