#!/usr/bin/env bash

set -Eeuo pipefail

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"
REQUESTED_DEVICE="${DEVICE:-cuda}"
MAX_WORKERS="${MAX_WORKERS:-8}"
R27_G2_CONCURRENCY_VALIDATED="${R27_G2_CONCURRENCY_VALIDATED:-0}"
CHECKPOINT_DIST_ROOT="${CHECKPOINT_DIST_ROOT:-$ROOT/dist}"
RUN_ROOT="${RUN_ROOT:-logs/r27_g2_forced_z_trajectory_effect_pilot_$(date +%Y%m%d_%H%M%S)}"
DRY_RUN="${DRY_RUN:-0}"

for argument in "$@"; do
  case "$argument" in
    --dry-run) DRY_RUN=1 ;;
    *) echo "Unknown argument: $argument" >&2; exit 2 ;;
  esac
done

if [[ "$REQUESTED_DEVICE" != "cuda" ]]; then
  echo "R27-G2 wiring pilot requires DEVICE=cuda; CPU fallback is forbidden." >&2
  exit 2
fi
readonly DEVICE=cuda

if [[ ! "$MAX_WORKERS" =~ ^[0-9]+$ ]]; then
  echo "MAX_WORKERS must be an integer from 1 through 8; pilot support is exactly 8 resets." >&2
  exit 2
fi
MAX_WORKERS=$((10#$MAX_WORKERS))
if (( MAX_WORKERS < 1 || MAX_WORKERS > 8 )); then
  echo "MAX_WORKERS must be an integer from 1 through 8; pilot support is exactly 8 resets." >&2
  exit 2
fi
for binary_flag in DRY_RUN R27_G2_CONCURRENCY_VALIDATED; do
  value="${!binary_flag}"
  if [[ "$value" != "0" && "$value" != "1" ]]; then
    echo "$binary_flag must be 0 or 1." >&2
    exit 2
  fi
done
if [[ "$DRY_RUN" == "0" ]] && (( MAX_WORKERS == 1 )); then
  echo "Serial R27-G2 pilot launch is disabled; use a validated parallel topology." >&2
  echo "No R27-G2 work was started." >&2
  exit 2
fi
if [[ "$DRY_RUN" == "0" ]] && \
  [[ "$R27_G2_CONCURRENCY_VALIDATED" != "1" ]]; then
  echo "Pilot launch requires R27_G2_CONCURRENCY_VALIDATED=1 after a bounded topology check." >&2
  echo "No R27-G2 work was started." >&2
  exit 2
fi

AUDIT_SCRIPT="scripts/audit_r27_forced_trajectory_effect.py"
SUMMARY_SCRIPT="scripts/r27_g2_pilot_summary.py"
CHECKPOINT_ID=arm0_final
CHECKPOINT_UPDATE=32
CHECKPOINT_DIR="$CHECKPOINT_DIST_ROOT/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1"
CHECKPOINT_PATH="$CHECKPOINT_DIR/standalone_process_core_final.pt"
RESET_IDS=(0 1 2 3 4 5 6 7)
EXPECTED_ENVIRONMENT_STEPS=83600
RESET_BATCHES=$(((8 + MAX_WORKERS - 1) / MAX_WORKERS))
CONFIGURED_LOW_HOURS=$((3 * RESET_BATCHES))
CONFIGURED_HIGH_HOURS=$((5 * RESET_BATCHES))

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

status_succeeded() {
  local path="$1"
  [[ -f "$path" ]] && grep -qx 'state=succeeded' "$path"
}

reset_output_dir() {
  local reset_id="$1"
  printf '%s/%s/resets/reset_%02d\n' "$RUN_ROOT" "$CHECKPOINT_ID" "$reset_id"
}

collect_command() {
  local reset_id="$1"
  local output_dir="$2"
  COLLECT_COMMAND=(
    "$PYTHON_BIN" "$AUDIT_SCRIPT" collect-reset
    --checkpoint "$CHECKPOINT_PATH"
    --checkpoint-id "$CHECKPOINT_ID"
    --checkpoint-update "$CHECKPOINT_UPDATE"
    --reset-id "$reset_id"
    --output-dir "$output_dir"
    --device cuda
  )
}

summary_command() {
  SUMMARY_COMMAND=(
    "$PYTHON_BIN" "$SUMMARY_SCRIPT"
    --run-root "$RUN_ROOT"
    --audit-script "$AUDIT_SCRIPT"
    --python-bin "$PYTHON_BIN"
  )
}

json_string_field() {
  local key="$1"
  sed -n "s/.*\"${key}\": \"\([^\"]*\)\".*/\1/p" | tail -n 1
}

RESET_SCIENTIFIC_STATUS=""
validate_reset_output() {
  local reset_id="$1"
  local output_dir manifest_path validation_path validation_output
  output_dir="$(reset_output_dir "$reset_id")"
  manifest_path="$output_dir/reset_manifest.json"
  validation_path="$output_dir/validation_output.log"
  RESET_SCIENTIFIC_STATUS=""
  [[ -s "$manifest_path" ]] || return 1
  if validation_output="$(
    "$PYTHON_BIN" "$AUDIT_SCRIPT" validate-reset \
      --manifest "$manifest_path" \
      --checkpoint-id "$CHECKPOINT_ID" \
      --reset-id "$reset_id" 2>&1
  )"; then
    printf '%s\n' "$validation_output" > "$validation_path"
  else
    printf '%s\n' "$validation_output" > "$validation_path"
    return 1
  fi
  RESET_SCIENTIFIC_STATUS="$(
    printf '%s\n' "$validation_output" | json_string_field scientific_status
  )"
  case "$RESET_SCIENTIFIC_STATUS" in
    OK|EXCLUDED|INVALID) return 0 ;;
    *) return 1 ;;
  esac
}

echo "R27-G2 final-checkpoint eight-reset wiring pilot"
echo "  repository_root:         $ROOT"
echo "  python:                  $PYTHON_BIN"
echo "  run_root:                $RUN_ROOT"
echo "  checkpoint:              $CHECKPOINT_PATH"
echo "  checkpoint_id:           $CHECKPOINT_ID"
echo "  reset_ids:               0..7"
echo "  reset_seeds:             1..8"
echo "  prefix_steps:            50,150,250,50,150,250,50,150"
echo "  branches_per_reset:      55"
echo "  branch_steps:            50"
echo "  environment_steps:       $EXPECTED_ENVIRONMENT_STEPS"
echo "  reset_worker_limit:      $MAX_WORKERS"
echo "  environments_per_worker: 1"
echo "  expected_wall_clock:     ${CONFIGURED_LOW_HOURS}-${CONFIGURED_HIGH_HOURS}h rough queue estimate on cloud CUDA"
echo "  scientific_gate:         NOT_EVALUATED; pilot evidence is quarantined"
echo "  concurrency_validated:   $R27_G2_CONCURRENCY_VALIDATED"
echo "  dry_run:                 $DRY_RUN"

if [[ "$DRY_RUN" == "1" ]]; then
  for reset_id in "${RESET_IDS[@]}"; do
    output_dir="$(reset_output_dir "$reset_id")"
    collect_command "$reset_id" "$output_dir"
    printf 'PHASE pilot-collect-reset checkpoint=%s reset_id=%d\n' \
      "$CHECKPOINT_ID" "$reset_id"
    format_command "${COLLECT_COMMAND[@]}"
  done
  summary_command
  echo "PHASE pilot-summary"
  format_command "${SUMMARY_COMMAND[@]}"
  echo "Pilot dry run complete; no directories, commands, logs, or statuses were written."
  exit 0
fi

for required_file in "$AUDIT_SCRIPT" "$SUMMARY_SCRIPT"; do
  if [[ ! -f "$required_file" ]]; then
    echo "Required R27-G2 pilot file is missing: $required_file" >&2
    exit 2
  fi
done
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 && [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python executable not found: $PYTHON_BIN" >&2
  exit 2
fi
if [[ ! -s "$CHECKPOINT_PATH" ]]; then
  echo "Required final checkpoint is missing or empty: $CHECKPOINT_PATH" >&2
  exit 2
fi
if ! "$PYTHON_BIN" -c \
  'import torch; raise SystemExit(0 if torch.cuda.is_available() else "CUDA unavailable; R27-G2 forbids CPU fallback")'; then
  echo "CUDA preflight failed; the R27-G2 pilot was not started." >&2
  exit 2
fi
mkdir -p "$RUN_ROOT/$CHECKPOINT_ID/resets"
printf '%s\n' \
  '{' \
  '  "experiment_id": "EXP-20260712-r27-g2-forced-z-trajectory-effect",' \
  '  "run_kind": "wiring_pilot",' \
  '  "scientific_status": "NOT_EVALUATED",' \
  '  "eligible_for_scientific_gate": false,' \
  '  "checkpoint_ids": ["arm0_final"],' \
  '  "checkpoint_update": 32,' \
  '  "reset_ids": [0, 1, 2, 3, 4, 5, 6, 7],' \
  '  "reset_seeds": [1, 2, 3, 4, 5, 6, 7, 8],' \
  '  "prefix_policy_seeds": [27100, 27101, 27102, 27103, 27104, 27105, 27106, 27107],' \
  '  "prefix_steps": [50, 150, 250, 50, 150, 250, 50, 150],' \
  '  "branches_per_reset": 55,' \
  '  "branch_steps": 50,' \
  '  "environment_steps": 83600' \
  '}' \
  > "$RUN_ROOT/pilot_contract.json"
write_status "$RUN_ROOT/batch_status.txt" \
  "started=$(date -Is)" \
  "state=running" \
  "phase=pilot-collect-reset" \
  "run_kind=wiring_pilot" \
  "device=cuda" \
  "checkpoint_id=$CHECKPOINT_ID" \
  "reset_ids=0..7" \
  "expected_resets=8" \
  "branches_per_reset=55" \
  "environment_steps=$EXPECTED_ENVIRONMENT_STEPS" \
  "reset_worker_limit=$MAX_WORKERS" \
  "concurrency_validated=$R27_G2_CONCURRENCY_VALIDATED" \
  "scientific_status=NOT_EVALUATED" \
  "eligible_for_scientific_gate=false"

RUNNER_PID="$BASHPID"
pids=()
finished=0

cleanup_children() {
  local pid
  for pid in "${pids[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill -TERM "$pid" 2>/dev/null || true
    fi
  done
  for pid in "${pids[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
  pids=()
}

write_crash_state() {
  local reason="$1"
  write_status "$RUN_ROOT/pilot_status.txt" \
    "state=crash" \
    "scientific_status=NOT_EVALUATED" \
    "eligible_for_scientific_gate=false" \
    "reason=$reason" \
    "expected_resets=8" \
    "environment_steps=partial_unknown"
  write_status "$RUN_ROOT/batch_status.txt" \
    "finished=$(date -Is)" \
    "state=crash" \
    "phase=pilot-collect-reset" \
    "reason=$reason" \
    "scientific_status=NOT_EVALUATED" \
    "eligible_for_scientific_gate=false"
}

on_signal() {
  local signal_name="$1"
  trap - INT TERM
  cleanup_children
  write_crash_state "signal_$signal_name"
  finished=1
  exit 130
}

on_exit() {
  local exit_code=$?
  if [[ "$BASHPID" != "$RUNNER_PID" ]]; then
    return
  fi
  if (( exit_code != 0 && finished == 0 )); then
    cleanup_children
    write_crash_state "runner_exit_$exit_code"
  fi
}

trap 'on_signal INT' INT
trap 'on_signal TERM' TERM
trap on_exit EXIT

run_reset() {
  local reset_id="$1"
  local output_dir status_path command_exit failure_reason
  output_dir="$(reset_output_dir "$reset_id")"
  status_path="$output_dir/runner_status.txt"
  mkdir -p "$output_dir"
  collect_command "$reset_id" "$output_dir"
  format_command "${COLLECT_COMMAND[@]}" > "$output_dir/command.txt"
  write_status "$status_path" \
    "started=$(date -Is)" \
    "state=running" \
    "phase=pilot-collect-reset" \
    "checkpoint_id=$CHECKPOINT_ID" \
    "checkpoint_update=$CHECKPOINT_UPDATE" \
    "reset_id=$reset_id" \
    "device=cuda"

  local command_pid=""
  cleanup_reset_child() {
    if [[ -n "$command_pid" ]] && kill -0 "$command_pid" 2>/dev/null; then
      kill -TERM "$command_pid" 2>/dev/null || true
      wait "$command_pid" 2>/dev/null || true
    fi
  }
  trap cleanup_reset_child INT TERM EXIT
  "${COLLECT_COMMAND[@]}" > "$output_dir/runner_output.log" 2>&1 &
  command_pid="$!"
  if wait "$command_pid"; then
    command_exit=0
  else
    command_exit=$?
  fi
  command_pid=""
  trap - INT TERM EXIT
  if (( command_exit == 0 )) && validate_reset_output "$reset_id"; then
    write_status "$status_path" \
      "finished=$(date -Is)" \
      "state=succeeded" \
      "phase=pilot-collect-reset" \
      "checkpoint_id=$CHECKPOINT_ID" \
      "checkpoint_update=$CHECKPOINT_UPDATE" \
      "reset_id=$reset_id" \
      "scientific_status=$RESET_SCIENTIFIC_STATUS" \
      "exit_code=0"
    return 0
  fi

  failure_reason=collect_command_failed
  if (( command_exit == 0 )); then
    command_exit=3
    failure_reason=output_validation_failed
  fi
  write_status "$status_path" \
    "finished=$(date -Is)" \
    "state=failed" \
    "phase=pilot-collect-reset" \
    "checkpoint_id=$CHECKPOINT_ID" \
    "checkpoint_update=$CHECKPOINT_UPDATE" \
    "reset_id=$reset_id" \
    "reason=$failure_reason" \
    "exit_code=$command_exit"
  return "$command_exit"
}

wait_for_batch() {
  local completed_pid="" wait_exit=0 pid
  local -a new_pids=()
  while (( ${#pids[@]} > 0 )); do
    completed_pid=""
    if wait -n -p completed_pid "${pids[@]}"; then
      wait_exit=0
    else
      wait_exit=$?
    fi
    new_pids=()
    for pid in "${pids[@]}"; do
      [[ "$pid" == "$completed_pid" ]] || new_pids+=("$pid")
    done
    pids=("${new_pids[@]}")
    if (( wait_exit != 0 )); then
      cleanup_children
      return "$wait_exit"
    fi
  done
  return 0
}

for reset_id in "${RESET_IDS[@]}"; do
  status_path="$(reset_output_dir "$reset_id")/runner_status.txt"
  if status_succeeded "$status_path" && validate_reset_output "$reset_id"; then
    printf 'SKIP pilot-collect-reset checkpoint=%s reset_id=%d state=succeeded scientific_status=%s\n' \
      "$CHECKPOINT_ID" "$reset_id" "$RESET_SCIENTIFIC_STATUS"
    continue
  fi
  printf 'START pilot-collect-reset checkpoint=%s reset_id=%d\n' \
    "$CHECKPOINT_ID" "$reset_id"
  run_reset "$reset_id" &
  pids+=("$!")
  if (( ${#pids[@]} >= MAX_WORKERS )); then
    if ! wait_for_batch; then
      write_crash_state "reset_worker_failed"
      finished=1
      exit 6
    fi
  fi
done
if (( ${#pids[@]} > 0 )); then
  if ! wait_for_batch; then
    write_crash_state "reset_worker_failed"
    finished=1
    exit 6
  fi
fi

summary_command
echo "PHASE pilot-summary"
format_command "${SUMMARY_COMMAND[@]}"
set +e
"${SUMMARY_COMMAND[@]}" > "$RUN_ROOT/pilot_summary_output.log" 2>&1
summary_exit=$?
set -e

pilot_state="$(sed -n 's/^state=//p' "$RUN_ROOT/pilot_status.txt" 2>/dev/null | tail -n 1)"
case "$pilot_state" in
  WIRING_PASS|INCOMPLETE|INVALID|crash) ;;
  *)
    write_crash_state "missing_or_invalid_pilot_summary"
    finished=1
    exit 5
    ;;
esac

batch_state=failed
if [[ "$pilot_state" == "WIRING_PASS" && "$summary_exit" == "0" ]]; then
  batch_state=succeeded
fi
write_status "$RUN_ROOT/batch_status.txt" \
  "finished=$(date -Is)" \
  "state=$batch_state" \
  "phase=pilot-complete" \
  "pilot_state=$pilot_state" \
  "run_kind=wiring_pilot" \
  "device=cuda" \
  "checkpoint_id=$CHECKPOINT_ID" \
  "expected_resets=8" \
  "branches_per_reset=55" \
  "environment_steps=$EXPECTED_ENVIRONMENT_STEPS" \
  "reset_worker_limit=$MAX_WORKERS" \
  "scientific_status=NOT_EVALUATED" \
  "eligible_for_scientific_gate=false"
finished=1

if [[ "$pilot_state" != "WIRING_PASS" || "$summary_exit" != "0" ]]; then
  echo "R27-G2 pilot did not pass wiring: state=$pilot_state summary_exit=$summary_exit" >&2
  exit "$summary_exit"
fi

echo "R27-G2 pilot completed: state=WIRING_PASS run_root=$RUN_ROOT"
echo "Scientific status: NOT_EVALUATED; pilot artifacts are quarantined."
