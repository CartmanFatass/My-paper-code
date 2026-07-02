#!/usr/bin/env bash
# HA-CTSE S7-S1 parity sweep for HMASD-level comparison.
#
# Purpose:
#   S7-S1 is the near-term parity gate.  Run isolated P1/P2-lite variants first,
#   then optional P1+P2 combinations.  Do not treat a combination result as a
#   clean mechanism verdict unless the isolated arms are also available.
#
# Default core arms:
#   reward_pure     : short-duration reward-pure baseline
#   p1_low_pos      : strongest P1 service baseline from 640k cloud sweep
#   p2_h0           : P2-lite high-level shared recovery credit
#   p2_h1           : P2-lite high-level per-agent recovery credit
#   p2_l1           : P2-lite low-level positive-only recovery ablation
#
# Optional combination arms:
#   p1_p2_h0, p1_p2_h1, p1_p2_l1
#
# Examples:
#   bash scripts/run_s7s1_p1_p2_parity_32env.sh --dry-run
#   bash scripts/run_s7s1_p1_p2_parity_32env.sh
#   EXPERIMENTS=core SEEDS=1 TOTAL_TIMESTEPS=1280000 bash scripts/run_s7s1_p1_p2_parity_32env.sh
#   EXPERIMENTS=combo bash scripts/run_s7s1_p1_p2_parity_32env.sh
#   EXPERIMENTS=all SEEDS=1,2 bash scripts/run_s7s1_p1_p2_parity_32env.sh
set -euo pipefail

PYTHON_EXE="${PYTHON_EXE:-python}"
EXPERIMENTS="${EXPERIMENTS:-core}"        # core, combo, all, or CSV names
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
SMDP_BOOTSTRAP_COEF="${SMDP_BOOTSTRAP_COEF:-0.25}"
P2_REWARD_COEF="${P2_REWARD_COEF:-0.05}"
P2_REWARD_CLIP="${P2_REWARD_CLIP:-0.5}"
P1_TOPO_COEF="${P1_TOPO_COEF:-1.0}"
P1_TOPO_CLIP="${P1_TOPO_CLIP:-0.05}"
LOG_ROOT="${LOG_ROOT:-logs_cloud_s7s1_p1p2_32env}"
DEVICE="${DEVICE:-cpu}"
SAVE_INTERVAL="${SAVE_INTERVAL:-20}"
CHECKPOINT_KEEP_LAST="${CHECKPOINT_KEEP_LAST:-4}"
PLOT_INTERVAL="${PLOT_INTERVAL:-10}"
DRY_RUN="${DRY_RUN:-0}"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run_s7s1_p1_p2_parity_32env.sh [--dry-run]

Environment variables:
  PYTHON_EXE                 Python executable. Default: python
  EXPERIMENTS                core, combo, all, or CSV.
                             Names: reward_pure,p1_low_pos,p2_h0,p2_h1,p2_l1,
                                    p1_p2_h0,p1_p2_h1,p1_p2_l1
                             Default: core
  SEEDS                      CSV seeds. Default: 1
  TOTAL_TIMESTEPS            Default: 1280000
  EVAL_INTERVAL              Default: 160000
  EVAL_EPISODES              Default: 20
  NUM_ENVS                   Default: 32
  DEVICE                     Default: cpu
  LOG_ROOT                   Default: logs_cloud_s7s1_p1p2_32env
  SKILL_LIFETIME_CANDIDATES  Default: 1,2,3
  P2_REWARD_COEF             Default: 0.05
  P2_REWARD_CLIP             Default: 0.5
  P1_TOPO_COEF               Default: 1.0
  P1_TOPO_CLIP               Default: 0.05

Recommended first server command:
  bash scripts/run_s7s1_p1_p2_parity_32env.sh --dry-run
  bash scripts/run_s7s1_p1_p2_parity_32env.sh

Combination arms:
  EXPERIMENTS=combo bash scripts/run_s7s1_p1_p2_parity_32env.sh
  EXPERIMENTS=all   bash scripts/run_s7s1_p1_p2_parity_32env.sh
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
    EXPERIMENT_CSV="reward_pure,p1_low_pos,p2_h0,p2_h1,p2_l1"
    ;;
  combo)
    EXPERIMENT_CSV="p1_p2_h0,p1_p2_h1,p1_p2_l1"
    ;;
  all)
    EXPERIMENT_CSV="reward_pure,p1_low_pos,p2_h0,p2_h1,p2_l1,p1_p2_h0,p1_p2_h1,p1_p2_l1"
    ;;
  *)
    EXPERIMENT_CSV="$EXPERIMENTS"
    ;;
esac

split_csv "$EXPERIMENT_CSV" EXPERIMENT_LIST
split_csv "$SEEDS" SEED_LIST

join_command() { printf '%q ' "$@"; }

run_ha_ctse() {
  local name="$1"
  local seed="$2"
  shift 2

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
  echo "===== HA-CTSE S7-S1 parity: ${name} seed=${seed} ====="
  join_command "${cmd[@]}"
  echo
  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi
  mkdir -p "$log_dir"
  "${cmd[@]}"
}

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

p1_low_pos=(
  --enable_topology_potential_shaping
  --topology_potential_injection low_only
  --topology_potential_coef "$P1_TOPO_COEF"
  --topology_potential_clip "$P1_TOPO_CLIP"
  --topology_potential_discount_mode delta
  --topology_potential_positive_only
  --topology_potential_warmup_steps 0
)

p2_h0=(
  --enable_p2_recovery_reward
  --p2_recovery_reward_level high_team
  --p2_recovery_reward_coef "$P2_REWARD_COEF"
  --p2_recovery_reward_clip "$P2_REWARD_CLIP"
)

p2_h1=(
  --enable_p2_recovery_reward
  --p2_recovery_reward_level high_per_agent
  --p2_recovery_reward_coef "$P2_REWARD_COEF"
  --p2_recovery_reward_clip "$P2_REWARD_CLIP"
)

p2_l1=(
  --enable_p2_recovery_reward
  --p2_recovery_reward_level low_only
  --p2_recovery_reward_coef "$P2_REWARD_COEF"
  --p2_recovery_reward_clip "$P2_REWARD_CLIP"
)

echo "HA-CTSE S7-S1 P1/P2 parity sweep"
echo "  root:              $(pwd)"
echo "  experiments:       $EXPERIMENT_CSV"
echo "  seeds:             $SEEDS"
echo "  num_envs:          $NUM_ENVS"
echo "  total_timesteps:   $TOTAL_TIMESTEPS"
echo "  eval_interval:     $EVAL_INTERVAL"
echo "  duration_set:      $SKILL_LIFETIME_CANDIDATES"
echo "  low_clip:          0.1"
echo "  log_root:          $LOG_ROOT"
echo "  device:            $DEVICE"
echo "  dry_run:           $DRY_RUN"

for seed in "${SEED_LIST[@]}"; do
  for experiment in "${EXPERIMENT_LIST[@]}"; do
    case "$experiment" in
      reward_pure)
        run_ha_ctse "s7s1_reward_pure_short" "$seed" \
          "${process_off[@]}"
        ;;
      p1_low_pos)
        run_ha_ctse "s7s1_p1_low_pos_coef${P1_TOPO_COEF}" "$seed" \
          "${process_off[@]}" \
          "${p1_low_pos[@]}"
        ;;
      p2_h0)
        run_ha_ctse "s7s1_p2_h0_high_team_coef${P2_REWARD_COEF}" "$seed" \
          "${process_off[@]}" \
          "${p2_h0[@]}"
        ;;
      p2_h1)
        run_ha_ctse "s7s1_p2_h1_per_agent_coef${P2_REWARD_COEF}" "$seed" \
          "${process_off[@]}" \
          "${p2_h1[@]}"
        ;;
      p2_l1)
        run_ha_ctse "s7s1_p2_l1_low_only_coef${P2_REWARD_COEF}" "$seed" \
          "${process_off[@]}" \
          "${p2_l1[@]}"
        ;;
      p1_p2_h0)
        run_ha_ctse "s7s1_p1_low_pos_p2_h0_coef${P2_REWARD_COEF}" "$seed" \
          "${process_off[@]}" \
          "${p1_low_pos[@]}" \
          "${p2_h0[@]}"
        ;;
      p1_p2_h1)
        run_ha_ctse "s7s1_p1_low_pos_p2_h1_coef${P2_REWARD_COEF}" "$seed" \
          "${process_off[@]}" \
          "${p1_low_pos[@]}" \
          "${p2_h1[@]}"
        ;;
      p1_p2_l1)
        run_ha_ctse "s7s1_p1_low_pos_p2_l1_coef${P2_REWARD_COEF}" "$seed" \
          "${process_off[@]}" \
          "${p1_low_pos[@]}" \
          "${p2_l1[@]}"
        ;;
      *)
        echo "Unknown experiment: ${experiment}" >&2
        exit 2
        ;;
    esac
  done
done
