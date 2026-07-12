#!/usr/bin/env bash

set -Eeuo pipefail

# This must be fixed before the first Python process can initialize CUDA.
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"
REQUESTED_DEVICE="${DEVICE:-cuda}"
MAX_WORKERS="${MAX_WORKERS:-1}"
CONTINUE_ON_ERROR="${CONTINUE_ON_ERROR:-0}"
R27_G2_CONCURRENCY_VALIDATED="${R27_G2_CONCURRENCY_VALIDATED:-0}"
CHECKPOINT_DIST_ROOT="${CHECKPOINT_DIST_ROOT:-$ROOT/dist}"
RUN_ROOT="${RUN_ROOT:-logs/r27_g2_forced_z_trajectory_effect_$(date +%Y%m%d_%H%M%S)}"
DRY_RUN="${DRY_RUN:-0}"

for argument in "$@"; do
  case "$argument" in
    --dry-run) DRY_RUN=1 ;;
    *) echo "Unknown argument: $argument" >&2; exit 2 ;;
  esac
done

if [[ "$REQUESTED_DEVICE" != "cuda" ]]; then
  echo "R27-G2 requires DEVICE=cuda; CPU fallback and alternate device flags are forbidden." >&2
  exit 2
fi
readonly DEVICE=cuda

if [[ ! "$MAX_WORKERS" =~ ^[0-9]+$ ]]; then
  echo "MAX_WORKERS must be an integer from 1 through 64; reset support remains exactly 64." >&2
  exit 2
fi
MAX_WORKERS=$((10#$MAX_WORKERS))
if (( MAX_WORKERS < 1 || MAX_WORKERS > 64 )); then
  echo "MAX_WORKERS must be an integer from 1 through 64; reset support remains exactly 64." >&2
  exit 2
fi
for binary_flag in DRY_RUN CONTINUE_ON_ERROR R27_G2_CONCURRENCY_VALIDATED; do
  value="${!binary_flag}"
  if [[ "$value" != "0" && "$value" != "1" ]]; then
    echo "$binary_flag must be 0 or 1." >&2
    exit 2
  fi
done
if [[ "$DRY_RUN" == "0" ]] && (( MAX_WORKERS > 1 )) && \
  [[ "$R27_G2_CONCURRENCY_VALIDATED" != "1" ]]; then
  echo "MAX_WORKERS>1 requires R27_G2_CONCURRENCY_VALIDATED=1 after a separate safe GPU/process topology check." >&2
  echo "No R27-G2 work was started." >&2
  exit 2
fi

AUDIT_SCRIPT="scripts/audit_r27_forced_trajectory_effect.py"
CHECKPOINT_DIR="$CHECKPOINT_DIST_ROOT/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1"
CHECKPOINT_IDS=(arm0_update25 arm0_update30 arm0_final)
CHECKPOINT_UPDATES=(25 30 32)
CHECKPOINT_FILES=(
  standalone_process_core_update_25.pt
  standalone_process_core_update_30.pt
  standalone_process_core_final.pt
)
RESET_BATCHES_PER_CHECKPOINT=$(((64 + MAX_WORKERS - 1) / MAX_WORKERS))
COLLECTOR_BATCHES=$((3 * RESET_BATCHES_PER_CHECKPOINT))
CONFIGURED_LOW_HOURS=$((3 * COLLECTOR_BATCHES))
CONFIGURED_HIGH_HOURS=$((5 * COLLECTOR_BATCHES))

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

checkpoint_path() {
  local index="$1"
  printf '%s/%s\n' "$CHECKPOINT_DIR" "${CHECKPOINT_FILES[$index]}"
}

reset_output_dir() {
  local checkpoint_id="$1"
  local reset_id="$2"
  printf '%s/%s/resets/reset_%02d\n' "$RUN_ROOT" "$checkpoint_id" "$reset_id"
}

collect_command() {
  local index="$1"
  local reset_id="$2"
  local output_dir="$3"
  COLLECT_COMMAND=(
    "$PYTHON_BIN" "$AUDIT_SCRIPT" collect-reset
    --checkpoint "$(checkpoint_path "$index")"
    --checkpoint-id "${CHECKPOINT_IDS[$index]}"
    --checkpoint-update "${CHECKPOINT_UPDATES[$index]}"
    --reset-id "$reset_id"
    --output-dir "$output_dir"
    --device cuda
  )
}

aggregate_command() {
  AGGREGATE_COMMAND=(
    "$PYTHON_BIN" "$AUDIT_SCRIPT" aggregate
    --run-root "$RUN_ROOT"
    --checkpoint-ids arm0_update25 arm0_update30 arm0_final
  )
}

json_string_field() {
  local key="$1"
  sed -n "s/.*\"${key}\": \"\([^\"]*\)\".*/\1/p" | tail -n 1
}

RESET_SCIENTIFIC_STATUS=""
validate_reset_output() {
  local index="$1"
  local reset_id="$2"
  local checkpoint_id="${CHECKPOINT_IDS[$index]}"
  local output_dir manifest_path validation_path validation_output
  output_dir="$(reset_output_dir "$checkpoint_id" "$reset_id")"
  manifest_path="$output_dir/reset_manifest.json"
  validation_path="$output_dir/validation_output.log"
  RESET_SCIENTIFIC_STATUS=""
  [[ -s "$manifest_path" ]] || return 1
  if validation_output="$(
    "$PYTHON_BIN" "$AUDIT_SCRIPT" validate-reset \
      --manifest "$manifest_path" \
      --checkpoint-id "$checkpoint_id" \
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

AGGREGATE_SCIENTIFIC_STATUS=""
AGGREGATE_CLASSIFICATION=""
validate_aggregate_output() {
  local validation_output validation_path
  validation_path="$RUN_ROOT/aggregate_validation_output.log"
  AGGREGATE_SCIENTIFIC_STATUS=""
  AGGREGATE_CLASSIFICATION=""
  if validation_output="$(
    "$PYTHON_BIN" "$AUDIT_SCRIPT" validate-aggregate --run-root "$RUN_ROOT" 2>&1
  )"; then
    printf '%s\n' "$validation_output" > "$validation_path"
  else
    printf '%s\n' "$validation_output" > "$validation_path"
    return 1
  fi
  AGGREGATE_SCIENTIFIC_STATUS="$(
    printf '%s\n' "$validation_output" | json_string_field scientific_status
  )"
  AGGREGATE_CLASSIFICATION="$(
    printf '%s\n' "$validation_output" | json_string_field classification
  )"
  [[ -n "$AGGREGATE_SCIENTIFIC_STATUS" && -n "$AGGREGATE_CLASSIFICATION" ]]
}

echo "R27-G2 forced-z trajectory/effect cloud runner"
echo "  repository_root:         $ROOT"
echo "  python:                  $PYTHON_BIN"
echo "  run_root:                $RUN_ROOT"
echo "  checkpoint_directory:    $CHECKPOINT_DIR"
echo "  device:                  $DEVICE"
echo "  cublas_workspace_config: $CUBLAS_WORKSPACE_CONFIG"
echo "  checkpoint_count:        3"
echo "  reset_ids:               0..63 per checkpoint"
echo "  branches_per_reset:      55"
echo "  reset_worker_limit:      $MAX_WORKERS"
echo "  environments_per_worker: 1"
echo "  continue_on_error:       $CONTINUE_ON_ERROR"
echo "  concurrency_validated:   $R27_G2_CONCURRENCY_VALIDATED"
echo "  configured_collect_cost: ${CONFIGURED_LOW_HOURS}-${CONFIGURED_HIGH_HOURS}h rough queue estimate"
echo "  registered_grade_cost:   12-20h only with a separately validated safe flattened queue"
echo "  dry_run:                 $DRY_RUN"
for index in 0 1 2; do
  echo "  checkpoint[${CHECKPOINT_IDS[$index]}]: $(checkpoint_path "$index")"
done

if [[ "$DRY_RUN" == "1" ]]; then
  for index in 0 1 2; do
    for reset_id in $(seq 0 63); do
      output_dir="$(reset_output_dir "${CHECKPOINT_IDS[$index]}" "$reset_id")"
      collect_command "$index" "$reset_id" "$output_dir"
      printf 'PHASE collect-reset checkpoint=%s reset_id=%d\n' \
        "${CHECKPOINT_IDS[$index]}" "$reset_id"
      format_command "${COLLECT_COMMAND[@]}"
    done
  done
  aggregate_command
  echo "PHASE aggregate"
  format_command "${AGGREGATE_COMMAND[@]}"
  echo "Dry run complete; no directories, commands, logs, or statuses were written."
  exit 0
fi

if [[ ! -f "$AUDIT_SCRIPT" ]]; then
  echo "Required R27-G2 audit is missing: $AUDIT_SCRIPT" >&2
  exit 2
fi
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 && [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python executable not found: $PYTHON_BIN" >&2
  exit 2
fi
for index in 0 1 2; do
  checkpoint="$(checkpoint_path "$index")"
  if [[ ! -s "$checkpoint" ]]; then
    echo "Required checkpoint is missing or empty: $checkpoint" >&2
    exit 2
  fi
done

if ! "$PYTHON_BIN" -c \
  'import torch; raise SystemExit(0 if torch.cuda.is_available() else "CUDA unavailable; R27-G2 forbids CPU fallback")'; then
  echo "CUDA preflight failed; R27-G2 was not started." >&2
  exit 2
fi

RUNNER_PID="$BASHPID"
pids=()
batch_started=0

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

on_signal() {
  local signal_name="$1"
  trap - INT TERM
  cleanup_children
  if [[ -d "$RUN_ROOT" ]]; then
    write_status "$RUN_ROOT/batch_status.txt" \
      "finished=$(date -Is)" \
      "state=interrupted" \
      "phase=collect-reset" \
      "signal=$signal_name" \
      "device=cuda"
  fi
  exit 130
}

on_exit() {
  local exit_code=$?
  if [[ "$BASHPID" != "$RUNNER_PID" ]]; then
    return
  fi
  if (( exit_code != 0 )); then
    cleanup_children
    if (( batch_started == 1 )) && \
      grep -qx 'state=running' "$RUN_ROOT/batch_status.txt" 2>/dev/null; then
      write_status "$RUN_ROOT/batch_status.txt" \
        "finished=$(date -Is)" \
        "state=crashed" \
        "phase=collect-reset" \
        "exit_code=$exit_code" \
        "device=cuda"
    fi
  fi
}

trap 'on_signal INT' INT
trap 'on_signal TERM' TERM
trap on_exit EXIT

mkdir -p "$RUN_ROOT"
write_status "$RUN_ROOT/batch_status.txt" \
  "started=$(date -Is)" \
  "state=running" \
  "phase=collect-reset" \
  "device=cuda" \
  "cublas_workspace_config=$CUBLAS_WORKSPACE_CONFIG" \
  "checkpoint_ids=arm0_update25,arm0_update30,arm0_final" \
  "reset_ids=0..63" \
  "resets_per_checkpoint=64" \
  "branches_per_reset=55" \
  "reset_worker_limit=$MAX_WORKERS" \
  "environments_per_worker=1" \
  "continue_on_error=$CONTINUE_ON_ERROR" \
  "concurrency_validated=$R27_G2_CONCURRENCY_VALIDATED" \
  "configured_collect_cost_hours=${CONFIGURED_LOW_HOURS}-${CONFIGURED_HIGH_HOURS}" \
  "registered_decision_grade_cost_hours=12-20"
batch_started=1

run_reset() {
  local index="$1"
  local reset_id="$2"
  local checkpoint_id="${CHECKPOINT_IDS[$index]}"
  local output_dir
  output_dir="$(reset_output_dir "$checkpoint_id" "$reset_id")"
  local status_path="$output_dir/runner_status.txt"
  mkdir -p "$output_dir"
  collect_command "$index" "$reset_id" "$output_dir"
  format_command "${COLLECT_COMMAND[@]}" > "$output_dir/command.txt"
  write_status "$status_path" \
    "started=$(date -Is)" \
    "state=running" \
    "phase=collect-reset" \
    "checkpoint_id=$checkpoint_id" \
    "checkpoint_update=${CHECKPOINT_UPDATES[$index]}" \
    "reset_id=$reset_id" \
    "environments_per_worker=1" \
    "device=cuda"

  local command_pid=""
  local command_exit=0
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

  if (( command_exit == 0 )) && validate_reset_output "$index" "$reset_id"; then
    write_status "$status_path" \
      "finished=$(date -Is)" \
      "state=succeeded" \
      "phase=collect-reset" \
      "checkpoint_id=$checkpoint_id" \
      "checkpoint_update=${CHECKPOINT_UPDATES[$index]}" \
      "reset_id=$reset_id" \
      "scientific_status=$RESET_SCIENTIFIC_STATUS" \
      "environments_per_worker=1" \
      "exit_code=0"
    return 0
  fi

  local failure_reason="collect_command_failed"
  local exit_code="$command_exit"
  if (( command_exit == 0 )); then
    failure_reason="output_validation_failed"
    exit_code=3
  fi
  write_status "$status_path" \
    "finished=$(date -Is)" \
    "state=failed" \
    "phase=collect-reset" \
    "checkpoint_id=$checkpoint_id" \
    "checkpoint_update=${CHECKPOINT_UPDATES[$index]}" \
    "reset_id=$reset_id" \
    "reason=$failure_reason" \
    "environments_per_worker=1" \
    "exit_code=$exit_code"
  return "$exit_code"
}

failed_workers=0

wait_for_batch() {
  local pid batch_failed=0
  for pid in "${pids[@]}"; do
    if ! wait "$pid"; then
      failed_workers=$((failed_workers + 1))
      batch_failed=$((batch_failed + 1))
    fi
  done
  pids=()
  (( batch_failed == 0 ))
}

abort_scheduling=0
for index in 0 1 2; do
  checkpoint_id="${CHECKPOINT_IDS[$index]}"
  checkpoint_root="$RUN_ROOT/$checkpoint_id"
  mkdir -p "$checkpoint_root/resets"
  write_status "$checkpoint_root/runner_status.txt" \
    "started=$(date -Is)" \
    "state=running" \
    "phase=collect-reset" \
    "checkpoint_id=$checkpoint_id" \
    "reset_worker_limit=$MAX_WORKERS" \
    "environments_per_worker=1" \
    "reset_ids=0..63"

  for reset_id in $(seq 0 63); do
    output_dir="$(reset_output_dir "$checkpoint_id" "$reset_id")"
    status_path="$output_dir/runner_status.txt"
    if status_succeeded "$status_path" && validate_reset_output "$index" "$reset_id"; then
      printf 'SKIP collect-reset checkpoint=%s reset_id=%d state=succeeded scientific_status=%s\n' \
        "$checkpoint_id" "$reset_id" "$RESET_SCIENTIFIC_STATUS"
      continue
    fi
    if status_succeeded "$status_path"; then
      printf 'STALE collect-reset checkpoint=%s reset_id=%d; output validation failed, rerunning\n' \
        "$checkpoint_id" "$reset_id"
    fi

    printf 'START collect-reset checkpoint=%s reset_id=%d\n' \
      "$checkpoint_id" "$reset_id"
    run_reset "$index" "$reset_id" &
    pids+=("$!")
    if (( ${#pids[@]} >= MAX_WORKERS )); then
      if ! wait_for_batch && [[ "$CONTINUE_ON_ERROR" == "0" ]]; then
        abort_scheduling=1
        break
      fi
    fi
  done
  if (( ${#pids[@]} > 0 )); then
    if ! wait_for_batch && [[ "$CONTINUE_ON_ERROR" == "0" ]]; then
      abort_scheduling=1
    fi
  fi

  checkpoint_failed=0
  checkpoint_succeeded=0
  checkpoint_ok=0
  checkpoint_excluded=0
  checkpoint_invalid=0
  for reset_id in $(seq 0 63); do
    status_path="$(reset_output_dir "$checkpoint_id" "$reset_id")/runner_status.txt"
    if status_succeeded "$status_path" && validate_reset_output "$index" "$reset_id"; then
      checkpoint_succeeded=$((checkpoint_succeeded + 1))
      case "$RESET_SCIENTIFIC_STATUS" in
        OK) checkpoint_ok=$((checkpoint_ok + 1)) ;;
        EXCLUDED) checkpoint_excluded=$((checkpoint_excluded + 1)) ;;
        INVALID) checkpoint_invalid=$((checkpoint_invalid + 1)) ;;
      esac
    else
      checkpoint_failed=$((checkpoint_failed + 1))
    fi
  done
  checkpoint_state=succeeded
  if (( checkpoint_failed > 0 )); then
    checkpoint_state=failed
  fi
  write_status "$checkpoint_root/runner_status.txt" \
    "finished=$(date -Is)" \
    "state=$checkpoint_state" \
    "phase=collect-reset" \
    "checkpoint_id=$checkpoint_id" \
    "succeeded_resets=$checkpoint_succeeded" \
    "failed_resets=$checkpoint_failed" \
    "scientific_ok_resets=$checkpoint_ok" \
    "scientific_excluded_resets=$checkpoint_excluded" \
    "scientific_invalid_resets=$checkpoint_invalid" \
    "reset_worker_limit=$MAX_WORKERS" \
    "environments_per_worker=1" \
    "expected_resets=64"

  if (( abort_scheduling == 1 )); then
    echo "R27-G2 fail-fast: stopping after the current worker batch." >&2
    break
  fi
done

failed_shards=0
succeeded_shards=0
scientific_ok_shards=0
scientific_excluded_shards=0
scientific_invalid_shards=0
for index in 0 1 2; do
  checkpoint_id="${CHECKPOINT_IDS[$index]}"
  for reset_id in $(seq 0 63); do
    status_path="$(reset_output_dir "$checkpoint_id" "$reset_id")/runner_status.txt"
    if status_succeeded "$status_path" && validate_reset_output "$index" "$reset_id"; then
      succeeded_shards=$((succeeded_shards + 1))
      case "$RESET_SCIENTIFIC_STATUS" in
        OK) scientific_ok_shards=$((scientific_ok_shards + 1)) ;;
        EXCLUDED) scientific_excluded_shards=$((scientific_excluded_shards + 1)) ;;
        INVALID) scientific_invalid_shards=$((scientific_invalid_shards + 1)) ;;
      esac
    else
      failed_shards=$((failed_shards + 1))
    fi
  done
done

aggregate_state=skipped
aggregate_command
echo "PHASE aggregate"
format_command "${AGGREGATE_COMMAND[@]}"
if (( failed_shards == 0 )); then
  format_command "${AGGREGATE_COMMAND[@]}" > "$RUN_ROOT/aggregate_command.txt"
  write_status "$RUN_ROOT/aggregate_status.txt" \
    "started=$(date -Is)" "state=running" "phase=aggregate"
  if "${AGGREGATE_COMMAND[@]}" > "$RUN_ROOT/aggregate_output.log" 2>&1; then
    if validate_aggregate_output; then
      aggregate_state=succeeded
      write_status "$RUN_ROOT/aggregate_status.txt" \
        "finished=$(date -Is)" \
        "state=succeeded" \
        "phase=aggregate" \
        "scientific_status=$AGGREGATE_SCIENTIFIC_STATUS" \
        "classification=$AGGREGATE_CLASSIFICATION" \
        "exit_code=0"
    else
      aggregate_state=failed
      write_status "$RUN_ROOT/aggregate_status.txt" \
        "finished=$(date -Is)" \
        "state=failed" \
        "phase=aggregate" \
        "reason=output_validation_failed" \
        "exit_code=3"
    fi
  else
    aggregate_exit_code=$?
    aggregate_state=failed
    write_status "$RUN_ROOT/aggregate_status.txt" \
      "finished=$(date -Is)" "state=failed" "phase=aggregate" \
      "reason=aggregate_command_failed" \
      "exit_code=$aggregate_exit_code"
  fi
else
  write_status "$RUN_ROOT/aggregate_status.txt" \
    "finished=$(date -Is)" \
    "state=skipped" \
    "phase=aggregate" \
    "reason=failed reset shards" \
    "failed_reset_shards=$failed_shards"
fi

batch_state=succeeded
if (( failed_shards > 0 )) || [[ "$aggregate_state" != "succeeded" ]]; then
  batch_state=failed
fi
write_status "$RUN_ROOT/batch_status.txt" \
  "finished=$(date -Is)" \
  "state=$batch_state" \
  "phase=complete" \
  "device=cuda" \
  "checkpoint_ids=arm0_update25,arm0_update30,arm0_final" \
  "expected_reset_shards=192" \
  "succeeded_reset_shards=$succeeded_shards" \
  "failed_reset_shards=$failed_shards" \
  "scientific_ok_reset_shards=$scientific_ok_shards" \
  "scientific_excluded_reset_shards=$scientific_excluded_shards" \
  "scientific_invalid_reset_shards=$scientific_invalid_shards" \
  "failed_worker_attempts=$failed_workers" \
  "reset_worker_limit=$MAX_WORKERS" \
  "environments_per_worker=1" \
  "aggregate_state=$aggregate_state" \
  "scientific_status=$AGGREGATE_SCIENTIFIC_STATUS" \
  "classification=$AGGREGATE_CLASSIFICATION"

if [[ "$batch_state" != "succeeded" ]]; then
  echo "R27-G2 runner incomplete: failed_reset_shards=$failed_shards aggregate_state=$aggregate_state" >&2
  exit 1
fi

echo "R27-G2 runner completed operationally: $RUN_ROOT"
echo "Scientific status: $AGGREGATE_SCIENTIFIC_STATUS / $AGGREGATE_CLASSIFICATION"
