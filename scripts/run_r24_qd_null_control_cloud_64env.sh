#!/usr/bin/env bash
set -euo pipefail

# HA-CTSE R24 q_d null-control cloud runner (Linux / CUDA / 64 env).
#
# Purpose:
#   Complete the R24 reward-off behavior-window q_d diagnostic after the local
#   runs were interrupted before 320k by the unrelated prototype-disc ratio
#   guard. This script keeps the current R24 context (S-base + q_A actionability
#   reward + q_d probe), but does NOT enable q_d/q_D reward.
#
# Read:
#   r24_qd_acc_full / r24_qd_acc_prior / r24_qd_residual_gain
#   r24_qd_positive_frac
#   r24_qd_acc_behavior / r24_qd_acc_pre
#   r24_qd_full_minus_behavior_acc / r24_qd_full_minus_pre_acc
#   r24_qd_shuffle_acc_gap / r24_qd_fake_acc_gap
#
# Gate:
#   q_d reward remains blocked unless the residual is seed-consistent and beats
#   behavior/pre/null controls. The default guard mode is WARN so this diagnostic
#   can reach 320k even if the unrelated prototype-disc ratio spikes; would-have
#   killed counters are still logged.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "ha_ctse_process/train.py" ]]; then
  echo "Run this script from the HMASD repo root or keep scripts/ under the repo root." >&2
  exit 2
fi

PYTHON_BIN="${PYTHON:-python}"
SEEDS="${SEEDS:-1,2}"
TOTAL_TIMESTEPS="${TOTAL_TIMESTEPS:-320000}"
NUM_ENVS="${NUM_ENVS:-64}"
DEVICE="${DEVICE:-cuda}"
LOG_ROOT="${LOG_ROOT:-logs_cloud_r24_qd_null_control_64env}"
COLLECTOR_BACKEND="${COLLECTOR_BACKEND:-subproc}"
COLLECTOR_START_METHOD="${COLLECTOR_START_METHOD:-spawn}"
GUARD_MODE="${GUARD_MODE:-warn}"
DRY_RUN="${DRY_RUN:-0}"
CONTINUE_ON_ERROR="${CONTINUE_ON_ERROR:-0}"

TEAM_INTENT_K="${TEAM_INTENT_K:-48}"
DURATIONS="${DURATIONS:-3,7,13,24}"
Z_GAIN="${Z_GAIN:-1.0}"
QA_COEF="${QA_COEF:-0.05}"
QA_CLIP="${QA_CLIP:-1.0}"
QA_WARMUP="${QA_WARMUP:-20000}"
PROTO_DISC_COEF="${PROTO_DISC_COEF:-0.05}"
PROTO_DISC_CLIP="${PROTO_DISC_CLIP:-2.0}"
PROTO_DISC_WARMUP="${PROTO_DISC_WARMUP:-20000}"
QD_MIN_SAMPLES="${QD_MIN_SAMPLES:-64}"
EXPORT_QD_WINDOWS="${EXPORT_QD_WINDOWS:-0}"
QD_EXPORT_MAX_ROWS="${QD_EXPORT_MAX_ROWS:-4096}"
QD_EXPORT_SEED="${QD_EXPORT_SEED:-17}"
RUN_FROZEN_NULL_ANALYSIS="${RUN_FROZEN_NULL_ANALYSIS:-0}"
FROZEN_NULL_STEPS="${FROZEN_NULL_STEPS:-300}"
FROZEN_NULL_HIDDEN_DIM="${FROZEN_NULL_HIDDEN_DIM:-128}"
FROZEN_NULL_LR="${FROZEN_NULL_LR:-0.003}"
FROZEN_NULL_MAX_ROWS="${FROZEN_NULL_MAX_ROWS:-0}"

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --continue-on-error) CONTINUE_ON_ERROR=1 ;;
    --help|-h)
      cat <<'EOF'
Usage:
  bash scripts/run_r24_qd_null_control_cloud_64env.sh [--dry-run] [--continue-on-error]

Environment overrides:
  PYTHON=python
  SEEDS=1,2
  TOTAL_TIMESTEPS=320000
  NUM_ENVS=64
  DEVICE=cuda
  LOG_ROOT=logs_cloud_r24_qd_null_control_64env
  GUARD_MODE=warn
  TEAM_INTENT_K=48
  DURATIONS=3,7,13,24
  Z_GAIN=1.0
  QA_COEF=0.05
  QD_MIN_SAMPLES=64
  EXPORT_QD_WINDOWS=0
  QD_EXPORT_MAX_ROWS=4096
  QD_EXPORT_SEED=17
  RUN_FROZEN_NULL_ANALYSIS=0
  FROZEN_NULL_STEPS=300
  FROZEN_NULL_HIDDEN_DIM=128
  FROZEN_NULL_LR=0.003
  FROZEN_NULL_MAX_ROWS=0

This is a reward-off q_d diagnostic. It enables q_A actionability reward as the
current R24 bridge context, but does not enable q_d/q_D reward.
EOF
      exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

if [[ "$RUN_FROZEN_NULL_ANALYSIS" == "1" && "$EXPORT_QD_WINDOWS" != "1" ]]; then
  echo "RUN_FROZEN_NULL_ANALYSIS=1 requires EXPORT_QD_WINDOWS=1 so r24_qd_windows inputs exist." >&2
  exit 2
fi

IFS=',' read -r -a SEED_LIST <<< "$SEEDS"

COMMON_ARGS=(
  -m ha_ctse_process.train
  --config ha_ctse_process.config
  --scenario energy
  --preset S7-S1
  --n_agents 6
  --collector_backend "$COLLECTOR_BACKEND"
  --collector_start_method "$COLLECTOR_START_METHOD"
  --num_envs "$NUM_ENVS"
  --rollout_length 500
  --skill_interval 10
  --skill_lifetime_candidates "$DURATIONS"
  --total_timesteps "$TOTAL_TIMESTEPS"
  --eval_interval 160000
  --eval_episodes 20
  --save_interval 20
  --checkpoint_keep_last 4
  --plot_interval 10
  --low_clip_epsilon 0.1
  --smdp_bootstrap_coef 0.25
  --device "$DEVICE"
  --opt_num_prototypes 4
  --prototype_skill_extra_codes 0
  --team_bridge_type stochastic
  --enable_situation_diagnostics
  --enable_prototype_response_skills
  --enable_high_omega_conditioning
  --enable_agent_prototype_relevance
  --enable_per_agent_kappa
  --enable_prototype_disc_probe
  --prototype_disc_condition kappa
  --enable_prototype_disc_reward
  --prototype_disc_reward_coef "$PROTO_DISC_COEF"
  --prototype_disc_clip "$PROTO_DISC_CLIP"
  --prototype_disc_warmup_steps "$PROTO_DISC_WARMUP"
  --reward_ratio_guard_mode "$GUARD_MODE"
  --disable_process_reward
  --disable_process_posterior_mi
  --disable_outcome_residual_probe
  --disable_topology_role_probe
  --disable_transition_skill_discriminator
  --enable_team_intent
  --team_intent_k "$TEAM_INTENT_K"
  --z_assignment_residual_gain "$Z_GAIN"
  --enable_assignment_actionability_probe
  --enable_assignment_actionability_reward
  --assignment_actionability_coef "$QA_COEF"
  --assignment_actionability_clip "$QA_CLIP"
  --assignment_actionability_warmup_steps "$QA_WARMUP"
  --enable_team_conditioned_qd_probe
  --team_conditioned_qd_min_samples "$QD_MIN_SAMPLES"
)

print_header() {
  cat <<EOF
HA-CTSE R24 q_d null-control cloud runner
  root:              $ROOT
  seeds:             $SEEDS
  num_envs:          $NUM_ENVS
  total_timesteps:   $TOTAL_TIMESTEPS
  device:            $DEVICE
  collector:         $COLLECTOR_BACKEND/$COLLECTOR_START_METHOD
  log_root:          $LOG_ROOT
  guard_mode:        $GUARD_MODE (diagnostic completion; would-have-killed metrics still log)
  team_intent_k:     $TEAM_INTENT_K
  durations:         $DURATIONS
  z_gain:            $Z_GAIN
  qA coef/clip/warm: $QA_COEF / $QA_CLIP / $QA_WARMUP
  qd_min_samples:    $QD_MIN_SAMPLES
  export_qd_windows: $EXPORT_QD_WINDOWS
  qd_export_max_rows: $QD_EXPORT_MAX_ROWS
  qd_export_seed:    $QD_EXPORT_SEED
  run_frozen_null_analysis: $RUN_FROZEN_NULL_ANALYSIS
  frozen_null_steps:  $FROZEN_NULL_STEPS
  frozen_null_hidden_dim: $FROZEN_NULL_HIDDEN_DIM
  frozen_null_lr:     $FROZEN_NULL_LR
  frozen_null_max_rows: $FROZEN_NULL_MAX_ROWS
  qd_reward:         OFF
  dry_run:           $DRY_RUN
  continue_on_error: $CONTINUE_ON_ERROR
EOF
}

run_one() {
  local seed="$1"
  local name="r24_qd_null_control_seed${seed}"
  local log_dir="$LOG_ROOT/seed${seed}/${name}"
  local -a cmd=("$PYTHON_BIN" "${COMMON_ARGS[@]}" --seed "$seed" --log_dir "$log_dir")
  if [[ "$EXPORT_QD_WINDOWS" == "1" ]]; then
    cmd+=(
      --r24_qd_export_windows
      --r24_qd_export_max_rows_per_update "$QD_EXPORT_MAX_ROWS"
      --r24_qd_export_seed "$QD_EXPORT_SEED"
    )
  fi

  local -a frozen_null_cmd=(
    "$PYTHON_BIN"
    scripts/analyze_r24_qd_frozen_nulls.py
    --input_dir "$log_dir/r24_qd_windows"
    --output_dir "$log_dir/r24_qd_frozen_nulls"
    --num_skills 6
    --hidden_dim "$FROZEN_NULL_HIDDEN_DIM"
    --steps "$FROZEN_NULL_STEPS"
    --lr "$FROZEN_NULL_LR"
    --seed "$QD_EXPORT_SEED"
    --max_rows "$FROZEN_NULL_MAX_ROWS"
  )

  echo
  echo "===== R24 q_d null-control: seed=$seed ====="
  printf '%q ' "${cmd[@]}"; echo

  if [[ "$DRY_RUN" == "1" ]]; then
    if [[ "$RUN_FROZEN_NULL_ANALYSIS" == "1" ]]; then
      echo "would run:"
      printf '%q ' "${frozen_null_cmd[@]}"; echo
    fi
    return 0
  fi

  mkdir -p "$log_dir"
  printf '%q ' "${cmd[@]}" > "$log_dir/command.txt"; echo >> "$log_dir/command.txt"
  {
    echo "started=$(date -Is)"
    echo "state=running"
    echo "seed=$seed"
    echo "command_file=$log_dir/command.txt"
    echo "output_file=$log_dir/runner_output.log"
  } > "$log_dir/runner_status.txt"

  set +e
  "${cmd[@]}" > "$log_dir/runner_output.log" 2>&1
  local exit_code=$?
  set -e

  local training_succeeded=1

  {
    echo "finished=$(date -Is)"
    echo "state=finished"
    echo "seed=$seed"
    echo "exit_code=$exit_code"
    echo "command_file=$log_dir/command.txt"
    echo "output_file=$log_dir/runner_output.log"
  } > "$log_dir/runner_status.txt"

  if [[ "$exit_code" -ne 0 ]]; then
    training_succeeded=0
    local message="R24 q_d null-control seed=$seed failed with exit code $exit_code; see $log_dir/runner_output.log"
    if [[ "$CONTINUE_ON_ERROR" == "1" ]]; then
      echo "WARNING: $message" >&2
    else
      echo "$message" >&2
      return "$exit_code"
    fi
  fi

  if [[ "$training_succeeded" == "1" && "$RUN_FROZEN_NULL_ANALYSIS" == "1" ]]; then
    printf '%q ' "${frozen_null_cmd[@]}" > "$log_dir/frozen_null_command.txt"
    echo >> "$log_dir/frozen_null_command.txt"

    echo "===== R24 q_d frozen-null analyzer: seed=$seed ====="
    printf '%q ' "${frozen_null_cmd[@]}"
    echo

    set +e
    "${frozen_null_cmd[@]}" > "$log_dir/frozen_null_output.log" 2>&1
    local frozen_exit_code=$?
    set -e

    if [[ "$frozen_exit_code" -ne 0 ]]; then
      local frozen_message="R24 frozen-null analyzer seed=$seed failed with exit code $frozen_exit_code; see $log_dir/frozen_null_output.log"
      if [[ "$CONTINUE_ON_ERROR" == "1" ]]; then
        echo "WARNING: $frozen_message" >&2
      else
        echo "$frozen_message" >&2
        return "$frozen_exit_code"
      fi
    fi
  fi
}

print_header
for seed in "${SEED_LIST[@]}"; do
  seed="$(echo "$seed" | xargs)"
  [[ -z "$seed" ]] && continue
  run_one "$seed"
done

echo
echo "R24 q_d null-control cloud runner complete."
