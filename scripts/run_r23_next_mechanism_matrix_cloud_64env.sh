#!/usr/bin/env bash
set -euo pipefail

# HA-CTSE R23-next mechanism matrix cloud runner (Linux / CUDA / 64 env, 320k).
#
# Follows the 2026-07-06 GPT post-R23-read plan (memory/R23_ACTIONABLE_TEAM_INTENT.md
# section 11; cross_validation "2026-07-06 GPT R23-result advice"). The g-info gradient
# audit (scripts/r23_ginfo_grad_audit.py) showed g-info's grad into the Z path is <2%
# of PPO and self-stalling, so the actionability main line switches to the q_A residual
# discriminator. This matrix is a 320k MECHANISM read (NOT a 960k parity run):
#
#   arm0_arch_only : Z gets the R23-0 residual capacity path only (known-pass control).
#   arm1_qA_probe  : + q_A residual actionability PROBE (reward off). Read: does q_A
#                    recover Z from executed xi beyond the context prior (residual_gain>0)?
#   arm2_qA_reward : + small q_A residual REWARD (high-level only, gated on residual_gain>0).
#                    Read: does actionability learning raise/stabilize forced-Z KL?
#   arm3_qD_audit  : arm0 + reward-off q_D effect-target/timescale audit over
#                    {s_next, joint_action, joint_effect, delta_omega} x H{10,20,50}.
#                    Read: which target (if any) recovers Z above chance -> where the
#                    Z->joint-effect signature lives. q_D reward stays OFF (amplifier only).
#
# Timing is Choice-1: K_team=8, durations {1,2,3,4}. q_D reward is NOT enabled anywhere
# in this matrix (per the stop list); enable it only after arm3 finds a non-chance target.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "ha_ctse_process/train.py" ]]; then
  echo "Run this script from the HMASD repo root or keep scripts/ under the repo root." >&2
  exit 2
fi

PYTHON_BIN="${PYTHON:-python}"
EXPERIMENTS="${EXPERIMENTS:-arm0_arch_only,arm1_qA_probe,arm2_qA_reward,arm3_qD_audit}"
SEEDS="${SEEDS:-1}"
TOTAL_TIMESTEPS="${TOTAL_TIMESTEPS:-320000}"
NUM_ENVS="${NUM_ENVS:-64}"
DEVICE="${DEVICE:-cuda}"
LOG_ROOT="${LOG_ROOT:-logs_cloud_r23_next_mechanism_matrix_64env}"
COLLECTOR_BACKEND="${COLLECTOR_BACKEND:-subproc}"
COLLECTOR_START_METHOD="${COLLECTOR_START_METHOD:-spawn}"

Z_GAIN="${Z_GAIN:-0.5}"
TEAM_INTENT_K="${TEAM_INTENT_K:-8}"
DURATIONS="${DURATIONS:-1,2,3,4}"
QA_COEF="${QA_COEF:-0.02}"
QA_CLIP="${QA_CLIP:-1.0}"
QA_WARMUP="${QA_WARMUP:-20000}"
QD_AUDIT_HORIZONS="${QD_AUDIT_HORIZONS:-10,20,50}"
QD_AUDIT_TARGETS="${QD_AUDIT_TARGETS:-s_next,joint_action,joint_effect,delta_omega}"
GUARD_MODE="${GUARD_MODE:-kill}"
DRY_RUN="${DRY_RUN:-0}"
CONTINUE_ON_ERROR="${CONTINUE_ON_ERROR:-0}"

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --continue-on-error) CONTINUE_ON_ERROR=1 ;;
    --help|-h)
      cat <<'EOF'
Usage:
  EXPERIMENTS=arm0_arch_only,arm1_qA_probe,arm2_qA_reward,arm3_qD_audit SEEDS=1 \
    bash scripts/run_r23_next_mechanism_matrix_cloud_64env.sh [--dry-run] [--continue-on-error]

Env vars (defaults): PYTHON=python
  EXPERIMENTS=arm0_arch_only,arm1_qA_probe,arm2_qA_reward,arm3_qD_audit SEEDS=1
  TOTAL_TIMESTEPS=320000 NUM_ENVS=64 DEVICE=cuda
  LOG_ROOT=logs_cloud_r23_next_mechanism_matrix_64env
  Z_GAIN=0.5 TEAM_INTENT_K=8 DURATIONS=1,2,3,4
  QA_COEF=0.02 QA_CLIP=1.0 QA_WARMUP=20000
  QD_AUDIT_HORIZONS=10,20,50 QD_AUDIT_TARGETS=s_next,joint_action,joint_effect,delta_omega
  GUARD_MODE=kill

Read order (320k, mechanism not parity):
  arm1  -> q_a_acc_full vs q_a_acc_prior, q_a_residual_gain (>0 == Z recoverable from xi)
  arm2  -> q_a_reward_active, g_itv_kl_skill / z_assignment_itv (rise/stable?), z_usage_entropy healthy,
           coverage/qos not collapsing
  arm3  -> q_d_acc_* per target/horizon vs chance (1/num_team_codes), q_d_best_target_*,
           q_d_residual_gain_* (which observation space carries the Z signature)
q_D reward stays OFF in every arm.
EOF
      exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

IFS=',' read -r -a EXP_LIST <<< "$EXPERIMENTS"
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
  --prototype_disc_reward_coef 0.05
  --prototype_disc_clip 2.0
  --prototype_disc_warmup_steps 20000
  --reward_ratio_guard_mode "$GUARD_MODE"
  --disable_process_reward
  --disable_process_posterior_mi
  --disable_outcome_residual_probe
  --disable_topology_role_probe
  --disable_transition_skill_discriminator
)

print_header() {
  cat <<EOF
HA-CTSE R23-next mechanism matrix cloud runner
  root:              $ROOT
  experiments:       $EXPERIMENTS
  seeds:             $SEEDS
  num_envs:          $NUM_ENVS
  total_timesteps:   $TOTAL_TIMESTEPS   (mechanism read, NOT 960k parity)
  device:            $DEVICE
  collector:         $COLLECTOR_BACKEND/$COLLECTOR_START_METHOD
  log_root:          $LOG_ROOT
  z_gain:            $Z_GAIN
  team_intent_k:     $TEAM_INTENT_K   (Choice-1)
  durations:         $DURATIONS       (Choice-1)
  qA_coef/clip/warm: $QA_COEF / $QA_CLIP / $QA_WARMUP
  qD_audit:          targets=$QD_AUDIT_TARGETS horizons=$QD_AUDIT_HORIZONS (reward OFF)
  guard_mode:        $GUARD_MODE
  dry_run:           $DRY_RUN
  continue_on_error: $CONTINUE_ON_ERROR
EOF
}

run_one() {
  local exp="$1"; local seed="$2"; local name; local -a extra_args
  local -a base=(
    --enable_team_intent --enable_team_disc_probe
    --team_intent_k "$TEAM_INTENT_K"
    --z_assignment_residual_gain "$Z_GAIN"
  )

  case "$exp" in
    arm0_arch_only)
      name="arm0_arch_only"
      extra_args=("${base[@]}") ;;
    arm1_qA_probe)
      name="arm1_qA_probe"
      extra_args=("${base[@]}" --enable_assignment_actionability_probe) ;;
    arm2_qA_reward)
      name="arm2_qA_reward_coef$(printf '%s' "$QA_COEF" | tr -d '.')"
      extra_args=(
        "${base[@]}"
        --enable_assignment_actionability_reward
        --assignment_actionability_coef "$QA_COEF"
        --assignment_actionability_clip "$QA_CLIP"
        --assignment_actionability_warmup_steps "$QA_WARMUP"
      ) ;;
    arm3_qD_audit)
      name="arm3_qD_audit"
      extra_args=(
        "${base[@]}"
        --enable_team_effect_target_audit
        --team_effect_audit_targets "$QD_AUDIT_TARGETS"
        --team_effect_audit_horizons "$QD_AUDIT_HORIZONS"
      ) ;;
    *)
      echo "Unknown experiment '$exp'. Use arm0_arch_only, arm1_qA_probe, arm2_qA_reward, or arm3_qD_audit." >&2
      return 2 ;;
  esac

  local log_dir="$LOG_ROOT/seed${seed}/${name}"
  local -a cmd=("$PYTHON_BIN" "${COMMON_ARGS[@]}" --seed "$seed" "${extra_args[@]}" --log_dir "$log_dir")

  echo
  echo "===== R23-next matrix: $name seed=$seed ====="
  printf '%q ' "${cmd[@]}"; echo

  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi

  mkdir -p "$log_dir"
  printf '%q ' "${cmd[@]}" > "$log_dir/command.txt"; echo >> "$log_dir/command.txt"
  {
    echo "started=$(date -Is)"
    echo "state=running"
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
    echo "exit_code=$exit_code"
    echo "command_file=$log_dir/command.txt"
    echo "output_file=$log_dir/runner_output.log"
  } > "$log_dir/runner_status.txt"

  if [[ "$exit_code" -ne 0 ]]; then
    local message="Experiment $name seed=$seed failed with exit code $exit_code; see $log_dir/runner_output.log"
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
  for exp in "${EXP_LIST[@]}"; do
    exp="$(echo "$exp" | xargs)"; [[ -z "$exp" ]] && continue
    run_one "$exp" "$seed"
  done
done
