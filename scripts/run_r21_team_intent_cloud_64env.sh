#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "ha_ctse_process/train.py" ]]; then
  echo "Run this script from the HMASD repo root or keep scripts/ under the repo root." >&2
  exit 2
fi

PYTHON_BIN="${PYTHON:-python}"
EXPERIMENTS="${EXPERIMENTS:-r21_z_probe,r21_z_reward}"
SEEDS="${SEEDS:-1}"
TOTAL_TIMESTEPS="${TOTAL_TIMESTEPS:-960000}"
NUM_ENVS="${NUM_ENVS:-64}"
DEVICE="${DEVICE:-cuda}"
LOG_ROOT="${LOG_ROOT:-logs_cloud_r21_team_intent_64env}"
COLLECTOR_BACKEND="${COLLECTOR_BACKEND:-subproc}"
COLLECTOR_START_METHOD="${COLLECTOR_START_METHOD:-spawn}"
TEAM_INTENT_K="${TEAM_INTENT_K:-48}"
TEAM_DISC_COEF="${TEAM_DISC_COEF:-0.05}"
TEAM_DISC_CLIP="${TEAM_DISC_CLIP:-2.0}"
TEAM_DISC_WARMUP_STEPS="${TEAM_DISC_WARMUP_STEPS:-20000}"
GUARD_MODE="${GUARD_MODE:-kill}"
DRY_RUN="${DRY_RUN:-0}"
CONTINUE_ON_ERROR="${CONTINUE_ON_ERROR:-0}"

for arg in "$@"; do
  case "$arg" in
    --dry-run)
      DRY_RUN=1
      ;;
    --continue-on-error)
      CONTINUE_ON_ERROR=1
      ;;
    --help|-h)
      cat <<'EOF'
Usage:
  EXPERIMENTS=r21_z_probe,r21_z_reward SEEDS=1 bash scripts/run_r21_team_intent_cloud_64env.sh

Environment variables:
  PYTHON=python
  EXPERIMENTS=r21_z_probe,r21_z_reward
  SEEDS=1,2
  TOTAL_TIMESTEPS=960000
  NUM_ENVS=64
  DEVICE=cuda
  LOG_ROOT=logs_cloud_r21_team_intent_64env
  COLLECTOR_BACKEND=subproc
  COLLECTOR_START_METHOD=spawn
  TEAM_INTENT_K=48
  TEAM_DISC_COEF=0.05
  GUARD_MODE=kill
  DRY_RUN=1
  CONTINUE_ON_ERROR=1

This runner uses the S-base matched control configuration:
  prototype response skills ON,
  prototype discriminator reward ON with coef=0.05,
  duration entropy floor OFF.
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
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
  --skill_lifetime_candidates 3,7,13,24
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
HA-CTSE R21 team-intent cloud runner
  root:              $ROOT
  experiments:       $EXPERIMENTS
  seeds:             $SEEDS
  num_envs:          $NUM_ENVS
  total_timesteps:   $TOTAL_TIMESTEPS
  device:            $DEVICE
  collector:         $COLLECTOR_BACKEND/$COLLECTOR_START_METHOD
  log_root:          $LOG_ROOT
  team_intent_k:     $TEAM_INTENT_K
  team_disc_coef:    $TEAM_DISC_COEF
  guard_mode:        $GUARD_MODE
  base:              coef005 prototype reward, duration floor OFF
  dry_run:           $DRY_RUN
  continue_on_error: $CONTINUE_ON_ERROR
EOF
}

run_one() {
  local exp="$1"
  local seed="$2"
  local name
  local -a extra_args

  case "$exp" in
    r21_z_probe)
      name="r21_z_probe"
      extra_args=(
        --enable_team_intent
        --enable_team_disc_probe
        --team_intent_k "$TEAM_INTENT_K"
      )
      ;;
    r21_z_reward)
      name="r21_z_reward_coef$(printf '%s' "$TEAM_DISC_COEF" | tr -d '.')"
      extra_args=(
        --enable_team_intent
        --enable_team_disc_reward
        --team_intent_k "$TEAM_INTENT_K"
        --team_disc_coef "$TEAM_DISC_COEF"
        --team_disc_clip "$TEAM_DISC_CLIP"
        --team_disc_warmup_steps "$TEAM_DISC_WARMUP_STEPS"
      )
      ;;
    *)
      echo "Unknown experiment '$exp'. Use r21_z_probe or r21_z_reward." >&2
      return 2
      ;;
  esac

  local log_dir="$LOG_ROOT/seed${seed}/${name}"
  local -a cmd=(
    "$PYTHON_BIN"
    "${COMMON_ARGS[@]}"
    --seed "$seed"
    "${extra_args[@]}"
    --log_dir "$log_dir"
  )

  echo
  echo "===== R21 cloud: $name seed=$seed ====="
  printf '%q ' "${cmd[@]}"
  echo

  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi

  mkdir -p "$log_dir"
  printf '%q ' "${cmd[@]}" > "$log_dir/command.txt"
  echo >> "$log_dir/command.txt"
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
  seed="$(echo "$seed" | xargs)"
  [[ -z "$seed" ]] && continue
  for exp in "${EXP_LIST[@]}"; do
    exp="$(echo "$exp" | xargs)"
    [[ -z "$exp" ]] && continue
    run_one "$exp" "$seed"
  done
done

