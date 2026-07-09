#!/usr/bin/env bash
set -euo pipefail

# HA-CTSE R25 q_A verification cloud runner (Linux / CUDA / 64 env, 1M steps).
#
# Purpose:
#   Verification tier for q_A actionability residual reward variant, scaled to
#   1M steps on 64-env cloud infrastructure. Two-arm matched comparison:
#   arm0_arch_only (control: team-intent baseline, no q_A reward)
#   arm2_qA_reward (treatment: team-intent + q_A actionability residual reward)
#
# Explore-short/verify-long doctrine:
#   R23 (320k, 16env local) demonstrated q_A mechanism signal (residual_gain +0.222).
#   R25 (1M, 64env cloud) validates at scale with mature checkpoints for downstream
#   diagnostics (G1 gates, skill differentiation probes).
#
# Read:
#   - Eval trajectory: coverage_ratio, qos_satisfaction_ratio, system_throughput_mbps,
#     zero_throughput_step_fraction, coverage_eq1_step_fraction
#   - Mechanism fields: z_usage_entropy, duration_usage_entropy, z_assignment_itv
#     (forced-Z KL stability), assignment_actionability_gain
#   - Checkpoint maturity: matched-arm reach at HMASD milestones (0.7@480k, 0.9@800k, plateau 0.964)
#
# Gate:
#   q_A reward remains in place (per R23 validation). No q_d/q_D reward paths enabled.
#   Gate criteria deferred to downstream G1 diagnostics on mature checkpoints.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "ha_ctse_process/train.py" ]]; then
  echo "Run this script from the HMASD repo root or keep scripts/ under the repo root." >&2
  exit 2
fi

PYTHON_BIN="${PYTHON:-python}"
SEEDS="${SEEDS:-1}"
ARMS="${ARMS:-arm0_arch_only,arm2_qA_reward}"
TOTAL_TIMESTEPS="${TOTAL_TIMESTEPS:-1000000}"
NUM_ENVS="${NUM_ENVS:-64}"
DEVICE="${DEVICE:-cuda}"
LOG_ROOT="${LOG_ROOT:-logs_cloud_r25_qa_verification_1m}"
COLLECTOR_BACKEND="${COLLECTOR_BACKEND:-subproc}"
COLLECTOR_START_METHOD="${COLLECTOR_START_METHOD:-spawn}"

TEAM_INTENT_K="${TEAM_INTENT_K:-8}"
DURATIONS="${DURATIONS:-1,2,3,4}"
Z_GAIN="${Z_GAIN:-0.5}"
QA_COEF="${QA_COEF:-0.02}"
QA_CLIP="${QA_CLIP:-1.0}"
QA_WARMUP="${QA_WARMUP:-20000}"
DRY_RUN="${DRY_RUN:-0}"
CONTINUE_ON_ERROR="${CONTINUE_ON_ERROR:-0}"

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --continue-on-error) CONTINUE_ON_ERROR=1 ;;
    --help|-h)
      cat <<'EOF'
Usage:
  bash scripts/run_r25_qa_verification_cloud_64env_1m.sh [--dry-run] [--continue-on-error]

Environment overrides:
  PYTHON=python
  SEEDS=1                          (default: "1"; e.g., "1,2" for multi-seed)
  ARMS=arm0_arch_only,arm2_qA_reward (default: both; e.g., "arm2_qA_reward" for single arm)
  TOTAL_TIMESTEPS=1000000
  NUM_ENVS=64
  DEVICE=cuda
  LOG_ROOT=logs_cloud_r25_qa_verification_1m
  TEAM_INTENT_K=8
  DURATIONS=1,2,3,4
  Z_GAIN=0.5
  QA_COEF=0.02
  QA_CLIP=1.0
  QA_WARMUP=20000

This is a q_A verification run (R23 validated mechanism at scale). q_A reward is ON
for arm2 only. q_d/q_D rewards are OFF. Mature checkpoints reserved for G1 diagnostics.
EOF
      exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

IFS=',' read -r -a SEED_LIST <<< "$SEEDS"
IFS=',' read -r -a ARMS_LIST <<< "$ARMS"

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
  --save_interval 5
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
  --prototype_disc_reward_coef 0.05
  --prototype_disc_clip 2.0
  --prototype_disc_warmup_steps 20000
  --reward_ratio_guard_mode kill
  --disable_process_reward
  --disable_process_posterior_mi
  --disable_outcome_residual_probe
  --disable_topology_role_probe
  --disable_transition_skill_discriminator
)

print_header() {
  cat <<EOF
HA-CTSE R25 q_A verification cloud runner
  root:              $ROOT
  seeds:             $SEEDS
  arms:              $ARMS
  num_envs:          $NUM_ENVS
  total_timesteps:   $TOTAL_TIMESTEPS
  device:            $DEVICE
  collector:         $COLLECTOR_BACKEND/$COLLECTOR_START_METHOD
  log_root:          $LOG_ROOT
  team_intent_k:     $TEAM_INTENT_K
  durations:         $DURATIONS
  z_gain:            $Z_GAIN
  qA coef/clip/warm: $QA_COEF / $QA_CLIP / $QA_WARMUP
  save_interval:     5 updates (~160k steps = eval cadence match)
  checkpoint_keep:   4 (mature checkpoints for G1 diagnostics)
  q_A reward:        ON (arm2 only, per R23 validation)
  q_d/q_D reward:    OFF
  dry_run:           $DRY_RUN
  continue_on_error: $CONTINUE_ON_ERROR
EOF
}

run_one() {
  local arm="$1"
  local seed="$2"
  local name
  local -a extra_args

  case "$arm" in
    arm0_arch_only)
      name="arm0_arch_only"
      extra_args=(
        --enable_team_intent
        --enable_team_disc_probe
        --team_intent_k "$TEAM_INTENT_K"
        --z_assignment_residual_gain "$Z_GAIN"
      ) ;;
    arm2_qA_reward)
      name="arm2_qA_reward"
      extra_args=(
        --enable_team_intent
        --enable_team_disc_probe
        --team_intent_k "$TEAM_INTENT_K"
        --z_assignment_residual_gain "$Z_GAIN"
        --enable_assignment_actionability_reward
        --assignment_actionability_coef "$QA_COEF"
        --assignment_actionability_clip "$QA_CLIP"
        --assignment_actionability_warmup_steps "$QA_WARMUP"
      ) ;;
    *)
      echo "Unknown arm '$arm'. Use arm0_arch_only or arm2_qA_reward." >&2
      return 2 ;;
  esac

  local log_dir="$LOG_ROOT/$arm/seed${seed}"
  local -a cmd=("$PYTHON_BIN" "${COMMON_ARGS[@]}" --seed "$seed" "${extra_args[@]}" --log_dir "$log_dir")

  echo
  echo "===== R25 q_A verification: $name seed=$seed ====="
  printf '%q ' "${cmd[@]}"; echo

  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi

  mkdir -p "$log_dir"
  printf '%q ' "${cmd[@]}" > "$log_dir/command.txt"; echo >> "$log_dir/command.txt"
  {
    echo "started=$(date -Is)"
    echo "state=running"
    echo "arm=$arm"
    echo "seed=$seed"
    echo "command_file=$log_dir/command.txt"
    echo "output_file=$log_dir/runner_output.log"
  } > "$log_dir/runner_status.txt"

  set +e
  "${cmd[@]}" > "$log_dir/runner_output.log" 2>&1
  local exit_code=$?
  set -e

  {
    echo "finished=$(date -Is)"
    echo "state=finished"
    echo "arm=$arm"
    echo "seed=$seed"
    echo "exit_code=$exit_code"
    echo "command_file=$log_dir/command.txt"
    echo "output_file=$log_dir/runner_output.log"
  } > "$log_dir/runner_status.txt"

  if [[ "$exit_code" -ne 0 ]]; then
    local message="R25 q_A verification $name seed=$seed failed with exit code $exit_code; see $log_dir/runner_output.log"
    if [[ "$CONTINUE_ON_ERROR" == "1" ]]; then
      echo "WARNING: $message" >&2
    else
      echo "$message" >&2
      return "$exit_code"
    fi
  fi
}

print_header
for seed in "${SEED_LIST[@]}"; do
  seed="$(echo "$seed" | xargs)"; [[ -z "$seed" ]] && continue
  for arm in "${ARMS_LIST[@]}"; do
    arm="$(echo "$arm" | xargs)"; [[ -z "$arm" ]] && continue
    run_one "$arm" "$seed"
  done
done

echo
echo "R25 q_A verification runner complete."
