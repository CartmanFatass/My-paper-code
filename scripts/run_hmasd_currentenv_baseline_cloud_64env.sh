#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "train_multiproc_config_1.py" ]]; then
  echo "Run this script from the HMASD repo root or keep scripts/ under the repo root." >&2
  exit 2
fi

PYTHON_BIN="${PYTHON:-python}"
SEEDS="${SEEDS:-1,2}"
TOTAL_TIMESTEPS="${TOTAL_TIMESTEPS:-1000000}"
NUM_ENVS="${NUM_ENVS:-64}"
NUM_WORKERS="${NUM_WORKERS:-16}"
ENVS_PER_WORKER="${ENVS_PER_WORKER:-4}"
DEVICE="${DEVICE:-cuda}"
LOG_ROOT="${LOG_ROOT:-logs_cloud_hmasd_s7s1_6agent_baseline_64env}"
COLLECTOR_BACKEND="${COLLECTOR_BACKEND:-sharded}"
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
  SEEDS=1,2 bash scripts/run_hmasd_currentenv_baseline_cloud_64env.sh

Environment variables:
  PYTHON=python
  SEEDS=1,2
  TOTAL_TIMESTEPS=1000000
  NUM_ENVS=64
  NUM_WORKERS=16
  ENVS_PER_WORKER=4
  DEVICE=cuda
  LOG_ROOT=logs_cloud_hmasd_s7s1_6agent_baseline_64env
  COLLECTOR_BACKEND=sharded
  DRY_RUN=1
  CONTINUE_ON_ERROR=1

This is the HMASD current-environment baseline:
  algorithm=hmasd_original, scenario=energy, preset=S7-S1, n_agents=6.
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

IFS=',' read -r -a SEED_LIST <<< "$SEEDS"

print_header() {
  cat <<EOF
HMASD current-env baseline cloud runner
  root:              $ROOT
  seeds:             $SEEDS
  num_envs:          $NUM_ENVS
  workers:           $NUM_WORKERS x $ENVS_PER_WORKER
  total_timesteps:   $TOTAL_TIMESTEPS
  device:            $DEVICE
  collector:         $COLLECTOR_BACKEND
  log_root:          $LOG_ROOT
  n_agents:          6
  dry_run:           $DRY_RUN
  continue_on_error: $CONTINUE_ON_ERROR
  eval read:         coverage_eq1_step_fraction / zero_throughput_episode_fraction / throughput_gt5_step_fraction
EOF
}

run_one() {
  local seed="$1"
  local name="hmasd_original_s7s1_6agent_seed${seed}"
  local log_dir="$LOG_ROOT/$name"
  local -a cmd=(
    "$PYTHON_BIN"
    train_multiproc_config_1.py
    --config config_1
    --algorithm hmasd_original
    --scenario energy
    --preset S7-S1
    --seed "$seed"
    --n_agents 6
    --collector_backend "$COLLECTOR_BACKEND"
    --num_envs "$NUM_ENVS"
    --num_workers "$NUM_WORKERS"
    --envs_per_worker "$ENVS_PER_WORKER"
    --rollout_length 500
    --skill_interval 10
    --total_timesteps "$TOTAL_TIMESTEPS"
    --eval_interval 160000
    --eval_episodes 20
    --metrics_mode light
    --training_metrics_level light
    --device "$DEVICE"
    --console_log_level info
    --log_dir "$LOG_ROOT"
  )

  echo
  echo "===== HMASD baseline cloud: seed=$seed ====="
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
    local message="HMASD baseline seed=$seed failed with exit code $exit_code; see $log_dir/runner_output.log"
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
  run_one "$seed"
done

