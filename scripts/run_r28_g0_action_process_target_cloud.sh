#!/usr/bin/env bash

set -Eeuo pipefail

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"
REQUESTED_DEVICE="${DEVICE:-cuda}"
R27_RUN_ROOT="${R27_RUN_ROOT:-}"
CHECKPOINT_ROOT="${CHECKPOINT_ROOT:-$ROOT/dist}"
LOG_ROOT="${LOG_ROOT:-logs}"
RUN_ROOT="${RUN_ROOT:-$LOG_ROOT/r28_g0_action_process_target_$(date +%Y%m%d_%H%M%S)}"
DRY_RUN="${DRY_RUN:-0}"

for argument in "$@"; do
  case "$argument" in
    --dry-run) DRY_RUN=1 ;;
    *) echo "Unknown argument: $argument" >&2; exit 2 ;;
  esac
done

if [[ "$REQUESTED_DEVICE" != "cuda" ]]; then
  echo "R28-G0 requires DEVICE=cuda; CPU fallback is forbidden." >&2
  exit 2
fi
readonly DEVICE=cuda

if [[ "$DRY_RUN" != "0" && "$DRY_RUN" != "1" ]]; then
  echo "DRY_RUN must be 0 or 1." >&2
  exit 2
fi

ANALYZER="scripts/analyze_r28_g0_action_process_target.py"
CHECKPOINT_DIR="$CHECKPOINT_ROOT/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1"
CHECKPOINT_FILES=(
  standalone_process_core_update_25.pt
  standalone_process_core_update_30.pt
  standalone_process_core_final.pt
)

format_command() {
  printf '%q ' "$@"
  printf '\n'
}

write_status() {
  local path="$1"
  shift
  local temporary="${path}.tmp.${BASHPID:-$$}"
  printf '%s\n' "$@" > "$temporary"
  mv -f "$temporary" "$path"
}

json_string_field() {
  local key="$1"
  sed -n "s/.*\"${key}\": \"\([^\"]*\)\".*/\1/p" | tail -n 1
}

ANALYZE_COMMAND=(
  "$PYTHON_BIN" "$ANALYZER" analyze
  --r27-run-root "$R27_RUN_ROOT"
  --checkpoint-root "$CHECKPOINT_ROOT"
  --output-dir "$RUN_ROOT"
  --device cuda
)
VALIDATE_COMMAND=(
  "$PYTHON_BIN" "$ANALYZER" validate-result
  --output-dir "$RUN_ROOT"
)

echo "R28-G0 action-process target cloud runner"
echo "  repository_root:         $ROOT"
echo "  python:                  $PYTHON_BIN"
echo "  r27_run_root:            ${R27_RUN_ROOT:-<required>}"
echo "  checkpoint_root:         $CHECKPOINT_ROOT"
echo "  run_root:                $RUN_ROOT"
echo "  device:                  $DEVICE"
echo "  cublas_workspace_config: $CUBLAS_WORKSPACE_CONFIG"
echo "  expected_cost:           <30 minutes, offline CUDA diagnostic"
echo "  execution_topology:      single CUDA analysis process, zero env steps"
echo "  dry_run:                 $DRY_RUN"
for checkpoint in "${CHECKPOINT_FILES[@]}"; do
  echo "  checkpoint:              $CHECKPOINT_DIR/$checkpoint"
done

if [[ "$DRY_RUN" == "1" ]]; then
  echo "PHASE analyze"
  format_command "${ANALYZE_COMMAND[@]}"
  echo "PHASE validate-result"
  format_command "${VALIDATE_COMMAND[@]}"
  echo "Dry run complete; no directories, commands, logs, or statuses were written."
  exit 0
fi

if [[ -z "$R27_RUN_ROOT" ]]; then
  echo "R27_RUN_ROOT is required and must point at the R27-G2 decision shard run root." >&2
  exit 2
fi
if [[ ! -d "$R27_RUN_ROOT" ]]; then
  echo "R27_RUN_ROOT does not exist: $R27_RUN_ROOT" >&2
  exit 2
fi
if [[ ! -f "$ANALYZER" ]]; then
  echo "Required analyzer is missing: $ANALYZER" >&2
  exit 2
fi
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 && [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python executable not found: $PYTHON_BIN" >&2
  exit 2
fi
for checkpoint in "${CHECKPOINT_FILES[@]}"; do
  if [[ ! -s "$CHECKPOINT_DIR/$checkpoint" ]]; then
    echo "Required checkpoint is missing or empty: $CHECKPOINT_DIR/$checkpoint" >&2
    exit 2
  fi
done
if ! "$PYTHON_BIN" -c 'import torch; raise SystemExit(0 if torch.cuda.is_available() else "CUDA unavailable; R28-G0 forbids CPU fallback")'; then
  echo "CUDA preflight failed; R28-G0 was not started." >&2
  exit 2
fi

mkdir -p "$RUN_ROOT"
format_command "${ANALYZE_COMMAND[@]}" > "$RUN_ROOT/command.txt"
write_status "$RUN_ROOT/runner_status.txt" \
  "started=$(date -Is)" \
  "state=running" \
  "phase=analyze" \
  "device=cuda" \
  "r27_run_root=$R27_RUN_ROOT" \
  "checkpoint_root=$CHECKPOINT_ROOT" \
  "expected_cost_minutes=<30" \
  "zero_environment_steps=true" \
  "zero_policy_updates=true"

if "${ANALYZE_COMMAND[@]}" > "$RUN_ROOT/runner_output.log" 2>&1; then
  analyze_exit=0
else
  analyze_exit=$?
  write_status "$RUN_ROOT/runner_status.txt" \
    "finished=$(date -Is)" \
    "state=failed" \
    "phase=analyze" \
    "reason=analyzer_command_failed" \
    "exit_code=$analyze_exit"
  exit "$analyze_exit"
fi

format_command "${VALIDATE_COMMAND[@]}" > "$RUN_ROOT/validate_command.txt"
if validation_output="$("${VALIDATE_COMMAND[@]}" 2>&1)"; then
  printf '%s\n' "$validation_output" > "$RUN_ROOT/validation_output.log"
else
  printf '%s\n' "$validation_output" > "$RUN_ROOT/validation_output.log"
  write_status "$RUN_ROOT/runner_status.txt" \
    "finished=$(date -Is)" \
    "state=failed" \
    "phase=validate-result" \
    "reason=output_validation_failed" \
    "exit_code=3"
  exit 3
fi

scientific_status="$(printf '%s\n' "$validation_output" | json_string_field scientific_status)"
classification="$(printf '%s\n' "$validation_output" | json_string_field classification)"

write_status "$RUN_ROOT/runner_status.txt" \
  "finished=$(date -Is)" \
  "state=succeeded" \
  "phase=complete" \
  "device=cuda" \
  "scientific_status=$scientific_status" \
  "classification=$classification" \
  "exit_code=0"

echo "R28-G0 runner completed operationally: $RUN_ROOT"
echo "Scientific status: $scientific_status / $classification"
