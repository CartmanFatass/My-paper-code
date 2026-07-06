#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "ha_ctse_process/train.py" ]]; then
  echo "Run this script from the HMASD repo root or keep scripts/ under the repo root." >&2
  exit 2
fi

PYTHON_BIN="${PYTHON:-python}"
EXPERIMENTS="${EXPERIMENTS:-core}"
SEEDS="${SEEDS:-1}"
TOTAL_TIMESTEPS="${TOTAL_TIMESTEPS:-960000}"
NUM_ENVS="${NUM_ENVS:-64}"
DEVICE="${DEVICE:-cuda}"
LOG_ROOT="${LOG_ROOT:-logs_cloud_r19_team_transition_64env}"
COLLECTOR_BACKEND="${COLLECTOR_BACKEND:-subproc}"
COLLECTOR_START_METHOD="${COLLECTOR_START_METHOD:-spawn}"
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
  bash scripts/run_r19_team_transition_64env.sh --dry-run
  EXPERIMENTS=a2_plus_t SEEDS=1 bash scripts/run_r19_team_transition_64env.sh

Environment variables:
  PYTHON=/path/to/python
  EXPERIMENTS=core|all|a2_baseline,a2_plus_t_probe,a2_plus_t
  SEEDS=1,2
  TOTAL_TIMESTEPS=960000
  NUM_ENVS=64
  DEVICE=cuda
  LOG_ROOT=logs_cloud_r19_team_transition_64env
  COLLECTOR_BACKEND=subproc
  COLLECTOR_START_METHOD=spawn
  DRY_RUN=1
  CONTINUE_ON_ERROR=1

Recommended R19-only split:
  server 1: EXPERIMENTS=a2_plus_t_probe
  server 2: EXPERIMENTS=a2_plus_t
  optional control server, only if no matched A2 same-check run exists:
            EXPERIMENTS=a2_baseline

Arm meaning:
  a2_baseline     = matched R15 A2 same-check coordinator-residual baseline.
  a2_plus_t_probe = R19 team-transition heads trained/logged; team reward off.
  a2_plus_t       = R19 team-transition reward on, one variable vs A2 baseline.
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

if [[ "$EXPERIMENTS" == "core" ]]; then
  EXPERIMENTS="a2_plus_t_probe,a2_plus_t"
elif [[ "$EXPERIMENTS" == "all" ]]; then
  EXPERIMENTS="a2_baseline,a2_plus_t_probe,a2_plus_t"
fi

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
  --enable_situation_diagnostics
  --enable_prototype_response_skills
  --enable_high_omega_conditioning
  --enable_agent_prototype_relevance
  --enable_per_agent_kappa
  --enable_prototype_disc_probe
  --prototype_disc_condition kappa
  --disable_process_reward
  --disable_process_posterior_mi
  --disable_outcome_residual_probe
  --disable_topology_role_probe
  --disable_transition_skill_discriminator
)

print_header() {
  cat <<EOF
HA-CTSE R19 team-transition remote runner
  root:              $ROOT
  experiments:       $EXPERIMENTS
  seeds:             $SEEDS
  num_envs:          $NUM_ENVS
  total_timesteps:   $TOTAL_TIMESTEPS
  device:            $DEVICE
  collector:         $COLLECTOR_BACKEND/$COLLECTOR_START_METHOD
  log_root:          $LOG_ROOT
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
    a2_baseline)
      name="a2_baseline_samecheck_reward_coef01"
      extra_args=(
        --ar_prefix_mode same_check
        --enable_prototype_disc_reward
        --prototype_disc_reward_coef 0.1
        --prototype_disc_clip 2.0
        --prototype_disc_warmup_steps 20000
      )
      ;;
    a2_plus_t_probe)
      name="a2_plus_t_probe_reward_off"
      extra_args=(
        --ar_prefix_mode same_check
        --enable_prototype_disc_reward
        --prototype_disc_reward_coef 0.1
        --prototype_disc_clip 2.0
        --prototype_disc_warmup_steps 20000
        --enable_team_transition_probe
        --team_transition_coef 0.05
        --team_transition_clip 2.0
        --team_transition_warmup_steps 20000
      )
      ;;
    a2_plus_t)
      name="a2_plus_t_reward_coef005"
      extra_args=(
        --ar_prefix_mode same_check
        --enable_prototype_disc_reward
        --prototype_disc_reward_coef 0.1
        --prototype_disc_clip 2.0
        --prototype_disc_warmup_steps 20000
        --enable_team_transition_probe
        --enable_team_transition_reward
        --team_transition_coef 0.05
        --team_transition_clip 2.0
        --team_transition_warmup_steps 20000
      )
      ;;
    *)
      echo "Unknown experiment '$exp'. Use core, all, a2_baseline, a2_plus_t_probe, or a2_plus_t." >&2
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
  echo "===== HA-CTSE R19 team-transition: $name seed=$seed ====="
  printf '%q ' "${cmd[@]}"
  echo

  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi

  mkdir -p "$log_dir"
  printf '%q ' "${cmd[@]}" > "$log_dir/command.txt"
  echo >> "$log_dir/command.txt"
  {
    echo "started=$(date --iso-8601=seconds)"
    echo "state=running"
    echo "output_file=$log_dir/runner_output.log"
    echo "command_file=$log_dir/command.txt"
  } > "$log_dir/runner_status.txt"

  set +e
  "${cmd[@]}" > "$log_dir/runner_output.log" 2>&1
  local exit_code=$?
  set -e

  {
    echo "finished=$(date --iso-8601=seconds)"
    echo "state=finished"
    echo "exit_code=$exit_code"
    echo "output_file=$log_dir/runner_output.log"
    echo "command_file=$log_dir/command.txt"
  } > "$log_dir/runner_status.txt"

  if [[ "$exit_code" -ne 0 ]]; then
    echo "Experiment $name seed=$seed failed with exit code $exit_code; see $log_dir/runner_output.log" >&2
    return "$exit_code"
  fi
}

print_header

for seed in "${SEED_LIST[@]}"; do
  seed="$(echo "$seed" | xargs)"
  [[ -z "$seed" ]] && continue
  for exp in "${EXP_LIST[@]}"; do
    exp="$(echo "$exp" | xargs)"
    [[ -z "$exp" ]] && continue
    if ! run_one "$exp" "$seed"; then
      if [[ "$CONTINUE_ON_ERROR" == "1" ]]; then
        echo "Continuing after failure because CONTINUE_ON_ERROR=1" >&2
      else
        exit 1
      fi
    fi
  done
done
