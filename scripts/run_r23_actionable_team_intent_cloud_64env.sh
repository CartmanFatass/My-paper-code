#!/usr/bin/env bash
set -euo pipefail

# HA-CTSE R23 "Actionable Team Intent" cloud runner (Linux / CUDA / 64 env).
#
# Staged, actionability-first (see memory/R23_ACTIONABLE_TEAM_INTENT.md):
#   r23_arch_only : Z gets the R23-0 residual capacity path, NO actionability
#                   objective, NO q_D reward. Isolates "does capacity alone matter?".
#   r23_1_action  : + g-info actionability objective I(Z;skill|c,w). q_D probe only,
#                   NO q_D reward. The R23-1 mechanism read.
#   r23_3_reward  : + q_D(Z|s_next) reward, HARD-GATED behind the forced-Z KL floor
#                   (team_disc_actionability_floor). The R23-3 read.
#
# Timing is Choice-1 (K_team << episode, short durations) so the two-clock does
# not degenerate the way R21 (K=48 ~= episode) did:  K_team=8, durations {1,2,3,4}.
#
# Base matches the S-base control (prototype response + prototype-disc reward 0.05)
# for comparability with R21.  q_D reward defaults OFF unless the r23_3_reward arm
# is selected, and even then it only applies once Z is measurably actionable.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "ha_ctse_process/train.py" ]]; then
  echo "Run this script from the HMASD repo root or keep scripts/ under the repo root." >&2
  exit 2
fi

PYTHON_BIN="${PYTHON:-python}"
EXPERIMENTS="${EXPERIMENTS:-r23_arch_only,r23_1_action,r23_3_reward}"
SEEDS="${SEEDS:-1}"
TOTAL_TIMESTEPS="${TOTAL_TIMESTEPS:-960000}"
NUM_ENVS="${NUM_ENVS:-64}"
DEVICE="${DEVICE:-cuda}"
LOG_ROOT="${LOG_ROOT:-logs_cloud_r23_actionable_team_intent_64env}"
COLLECTOR_BACKEND="${COLLECTOR_BACKEND:-subproc}"
COLLECTOR_START_METHOD="${COLLECTOR_START_METHOD:-spawn}"

# R23 knobs.
Z_GAIN="${Z_GAIN:-0.5}"                          # R23-0 residual gain (small; annealing optional)
TEAM_INTENT_K="${TEAM_INTENT_K:-8}"              # Choice-1: K_team << episode
DURATIONS="${DURATIONS:-1,2,3,4}"                # Choice-1: short individual lifetimes
G_INFO_COEF="${G_INFO_COEF:-0.02}"              # actionability objective coef on I(Z;skill)
G_INFO_WARMUP="${G_INFO_WARMUP:-20000}"
G_INFO_ANNEAL="${G_INFO_ANNEAL:-0}"
ACTIONABILITY_FLOOR="${ACTIONABILITY_FLOOR:-0.05}"   # R23-3 q_D reward gate on forced-Z skill KL
TEAM_DISC_COEF="${TEAM_DISC_COEF:-0.05}"
TEAM_DISC_CLIP="${TEAM_DISC_CLIP:-2.0}"
TEAM_DISC_WARMUP_STEPS="${TEAM_DISC_WARMUP_STEPS:-20000}"
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
  EXPERIMENTS=r23_arch_only,r23_1_action,r23_3_reward SEEDS=1 \
    bash scripts/run_r23_actionable_team_intent_cloud_64env.sh [--dry-run] [--continue-on-error]

Env vars (defaults): PYTHON=python EXPERIMENTS=r23_arch_only,r23_1_action,r23_3_reward
  SEEDS=1 TOTAL_TIMESTEPS=960000 NUM_ENVS=64 DEVICE=cuda
  LOG_ROOT=logs_cloud_r23_actionable_team_intent_64env
  Z_GAIN=0.5 TEAM_INTENT_K=8 DURATIONS=1,2,3,4
  G_INFO_COEF=0.02 G_INFO_WARMUP=20000 G_INFO_ANNEAL=0
  ACTIONABILITY_FLOOR=0.05 TEAM_DISC_COEF=0.05 TEAM_DISC_WARMUP_STEPS=20000 GUARD_MODE=kill

Read order: 160k forced-Z KL shape (g_itv_kl_skill), 320k actionability gate
(g_itv_kl_skill up, g_info_skill_mi up, Z-usage healthy, task not collapsing),
then 960k task gate. For r23_3_reward also watch team_disc_reward_gated_off and
team_disc_forced_z_kl (reward must stay gated until forced-Z KL >= floor).
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
HA-CTSE R23 Actionable Team Intent cloud runner
  root:              $ROOT
  experiments:       $EXPERIMENTS
  seeds:             $SEEDS
  num_envs:          $NUM_ENVS
  total_timesteps:   $TOTAL_TIMESTEPS
  device:            $DEVICE
  collector:         $COLLECTOR_BACKEND/$COLLECTOR_START_METHOD
  log_root:          $LOG_ROOT
  z_gain:            $Z_GAIN
  team_intent_k:     $TEAM_INTENT_K   (Choice-1)
  durations:         $DURATIONS       (Choice-1)
  g_info_coef:       $G_INFO_COEF (warmup=$G_INFO_WARMUP anneal=$G_INFO_ANNEAL)
  actionability_floor: $ACTIONABILITY_FLOOR (R23-3 q_D reward gate)
  team_disc_coef:    $TEAM_DISC_COEF (warmup=$TEAM_DISC_WARMUP_STEPS)
  guard_mode:        $GUARD_MODE
  dry_run:           $DRY_RUN
  continue_on_error: $CONTINUE_ON_ERROR
EOF
}

run_one() {
  local exp="$1"; local seed="$2"; local name; local -a extra_args

  case "$exp" in
    r23_arch_only)
      name="r23_arch_only"
      extra_args=(
        --enable_team_intent --enable_team_disc_probe
        --team_intent_k "$TEAM_INTENT_K"
        --z_assignment_residual_gain "$Z_GAIN"
      ) ;;
    r23_1_action)
      name="r23_1_action"
      extra_args=(
        --enable_team_intent --enable_team_disc_probe
        --team_intent_k "$TEAM_INTENT_K"
        --z_assignment_residual_gain "$Z_GAIN"
        --enable_g_info_objective
        --g_info_coef_skill "$G_INFO_COEF"
        --g_info_warmup_steps "$G_INFO_WARMUP"
        --g_info_anneal_steps "$G_INFO_ANNEAL"
      ) ;;
    r23_3_reward)
      name="r23_3_reward_coef$(printf '%s' "$TEAM_DISC_COEF" | tr -d '.')_floor$(printf '%s' "$ACTIONABILITY_FLOOR" | tr -d '.')"
      extra_args=(
        --enable_team_intent --enable_team_disc_reward
        --team_intent_k "$TEAM_INTENT_K"
        --z_assignment_residual_gain "$Z_GAIN"
        --enable_g_info_objective
        --g_info_coef_skill "$G_INFO_COEF"
        --g_info_warmup_steps "$G_INFO_WARMUP"
        --g_info_anneal_steps "$G_INFO_ANNEAL"
        --team_disc_coef "$TEAM_DISC_COEF"
        --team_disc_clip "$TEAM_DISC_CLIP"
        --team_disc_warmup_steps "$TEAM_DISC_WARMUP_STEPS"
        --team_disc_actionability_floor "$ACTIONABILITY_FLOOR"
      ) ;;
    *)
      echo "Unknown experiment '$exp'. Use r23_arch_only, r23_1_action, or r23_3_reward." >&2
      return 2 ;;
  esac

  local log_dir="$LOG_ROOT/seed${seed}/${name}"
  local -a cmd=("$PYTHON_BIN" "${COMMON_ARGS[@]}" --seed "$seed" "${extra_args[@]}" --log_dir "$log_dir")

  echo
  echo "===== R23 cloud: $name seed=$seed ====="
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
