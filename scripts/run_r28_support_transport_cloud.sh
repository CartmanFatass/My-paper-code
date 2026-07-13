#!/usr/bin/env bash

set -Eeuo pipefail

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="${REPO_DIR:-$SCRIPT_ROOT}"
DATA_ROOT="${DATA_ROOT:-/root/autodl-tmp/HMASD}"
RUN_ROOT="${RUN_ROOT:-$DATA_ROOT/logs/r28_support_transport_$(date +%Y%m%d_%H%M%S)}"
PYTHON_BIN="${PYTHON_BIN:-python}"
SOURCE_CHECKPOINT="${SOURCE_CHECKPOINT:-$REPO_DIR/dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_final.pt}"
SCORER_PATH="${SCORER_PATH:-$REPO_DIR/logs/r28_g0_action_process_target_20260713_175600/r28_g0_scorer_final.pt}"
MAX_WORKERS="${MAX_WORKERS:-8}"
REQUESTED_DEVICE="${DEVICE:-cuda}"
DRY_RUN="${DRY_RUN:-0}"

for argument in "$@"; do
  case "$argument" in
    --dry-run) DRY_RUN=1 ;;
    *) echo "Unknown argument: $argument" >&2; exit 2 ;;
  esac
done

if [[ "$REQUESTED_DEVICE" != "cuda" ]]; then
  echo "R28 support transport requires CUDA; CPU fallback is forbidden." >&2
  exit 2
fi
if [[ ! "$MAX_WORKERS" =~ ^[0-9]+$ ]] || (( 10#$MAX_WORKERS < 2 || 10#$MAX_WORKERS > 64 )); then
  echo "MAX_WORKERS must be an integer from 2 through 64." >&2
  exit 2
fi
MAX_WORKERS=$((10#$MAX_WORKERS))
if [[ "$DRY_RUN" != "0" && "$DRY_RUN" != "1" ]]; then
  echo "DRY_RUN must be 0 or 1." >&2
  exit 2
fi

readonly DEVICE=cuda
readonly AUDIT_SCRIPT="$REPO_DIR/scripts/audit_r28_support_transport.py"
readonly EXPECTED_ENVIRONMENT_STEPS=111100

format_command() {
  printf '%q ' "$@"
  printf '\n'
}

reset_output_dir() {
  printf '%s/resets/reset_%02d\n' "$RUN_ROOT" "$1"
}

collect_command() {
  local reset_id="$1"
  local output_dir="$2"
  COLLECT_COMMAND=(
    "$PYTHON_BIN" "$AUDIT_SCRIPT" collect-reset
    --checkpoint "$SOURCE_CHECKPOINT"
    --scorer "$SCORER_PATH"
    --reset-id "$reset_id"
    --output-dir "$output_dir"
    --device cuda
  )
}

AGGREGATE_COMMAND=(
  "$PYTHON_BIN" "$AUDIT_SCRIPT" aggregate
  --run-root "$RUN_ROOT"
)

echo "R28 reward-off support transport runner"
echo "  run_root:          $RUN_ROOT"
echo "  source_checkpoint: $SOURCE_CHECKPOINT"
echo "  scorer:            $SCORER_PATH"
echo "  device:            $DEVICE"
echo "  reset_ids:         0..63"
echo "  max_workers:       $MAX_WORKERS"
echo "  environment_steps: $EXPECTED_ENVIRONMENT_STEPS"
echo "  policy_updates:    0"
echo "  reward_steps:      0"
echo "  dry_run:           $DRY_RUN"

if [[ "$DRY_RUN" == "1" ]]; then
  for reset_id in $(seq 0 63); do
    output_dir="$(reset_output_dir "$reset_id")"
    collect_command "$reset_id" "$output_dir"
    format_command "${COLLECT_COMMAND[@]}"
  done
  format_command "${AGGREGATE_COMMAND[@]}"
  echo "Dry run complete; no directories or files were created."
  exit 0
fi

for required in "$AUDIT_SCRIPT" "$SOURCE_CHECKPOINT" "$SCORER_PATH"; do
  if [[ ! -s "$required" ]]; then
    echo "Required file is missing or empty: $required" >&2
    exit 2
  fi
done
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 && [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python executable not found: $PYTHON_BIN" >&2
  exit 2
fi
if ! "$PYTHON_BIN" -c \
  'import torch; raise SystemExit(0 if torch.cuda.is_available() else "CUDA unavailable")'; then
  echo "CUDA preflight failed; no reset was started." >&2
  exit 2
fi

mkdir -p "$RUN_ROOT/resets"
pids=()

cleanup_children() {
  local pid
  for pid in "${pids[@]}"; do
    kill -TERM "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup_children INT TERM

run_reset() {
  local reset_id="$1"
  local output_dir
  output_dir="$(reset_output_dir "$reset_id")"
  mkdir -p "$output_dir"
  collect_command "$reset_id" "$output_dir"
  format_command "${COLLECT_COMMAND[@]}" > "$output_dir/command.txt"
  "${COLLECT_COMMAND[@]}" > "$output_dir/runner_output.log" 2>&1
}

wait_batch() {
  local pid failed=0
  for pid in "${pids[@]}"; do
    if ! wait "$pid"; then
      failed=1
    fi
  done
  pids=()
  return "$failed"
}

for reset_id in $(seq 0 63); do
  run_reset "$reset_id" &
  pids+=("$!")
  if (( ${#pids[@]} >= MAX_WORKERS )); then
    if ! wait_batch; then
      echo "A collect-reset worker failed; aggregate was not run." >&2
      exit 1
    fi
  fi
done
if (( ${#pids[@]} > 0 )) && ! wait_batch; then
  echo "A collect-reset worker failed; aggregate was not run." >&2
  exit 1
fi

format_command "${AGGREGATE_COMMAND[@]}" > "$RUN_ROOT/aggregate_command.txt"
if ! "${AGGREGATE_COMMAND[@]}" > "$RUN_ROOT/aggregate_output.log" 2>&1; then
  echo "Aggregate failed; see $RUN_ROOT/aggregate_output.log" >&2
  exit 1
fi

echo "R28 support transport completed: $RUN_ROOT"
