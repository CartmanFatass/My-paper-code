#!/usr/bin/env bash

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"
DEVICE="${DEVICE:-cuda}"
NUM_ENVS="${NUM_ENVS:-64}"
N_RESETS="${N_RESETS:-64}"
COLLECTOR_BACKEND="${COLLECTOR_BACKEND:-subproc}"
COLLECTOR_START_METHOD="${COLLECTOR_START_METHOD:-spawn}"
CHECKPOINT_DIST_ROOT="${CHECKPOINT_DIST_ROOT:-$ROOT/dist}"
RUN_ROOT="${RUN_ROOT:-logs/r27_g1_capacity_autopsy_cloud64_$(date +%Y%m%d_%H%M%S)}"
SHA256_BIN="${SHA256_BIN:-sha256sum}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"

DRY_RUN=0
CONTINUE_ON_ERROR=0
for argument in "$@"; do
  case "$argument" in
    --dry-run) DRY_RUN=1 ;;
    --continue-on-error) CONTINUE_ON_ERROR=1 ;;
    *) echo "Unknown argument: $argument" >&2; exit 2 ;;
  esac
done

if [[ ! "$DEVICE" =~ ^cuda(:[0-9]+)?$ ]]; then
  echo "R27-G1 cloud audit requires DEVICE=cuda; CPU fallback is forbidden." >&2
  exit 2
fi
if [[ "$NUM_ENVS" != "64" || "$N_RESETS" != "64" ]]; then
  echo "R27-G1 scientific contract requires NUM_ENVS=64 and N_RESETS=64." >&2
  exit 2
fi
if [[ "$COLLECTOR_BACKEND" != "subproc" || "$COLLECTOR_START_METHOD" != "spawn" ]]; then
  echo "R27-G1 scientific contract requires subproc/spawn." >&2
  exit 2
fi
if [[ ! -f scripts/audit_r27_low_actor_capacity.py ]]; then
  echo "Run this script from an HMASD checkout containing the R27 audit." >&2
  exit 2
fi

ARM_NAMES=(arm0_update25 arm0_update30 arm0_final)
ARM_UPDATES=(25 30 32)
ARM_FILES=(
  standalone_process_core_update_25.pt
  standalone_process_core_update_30.pt
  standalone_process_core_final.pt
)
ARM_HASHES=(
  3f6404cd54e75f3f39af0cffb56c444dda78acd05993f1b6efd9cdc77ad9ca54
  6553e97c032e54f0a19cf801e451298d6b56232720d82a8e26abbdb7171acabc
  eeaa4f7ec32314d47be818f20c76758c47a97b7881aa997511a2660bb5632c36
)
CHECKPOINT_DIR="$CHECKPOINT_DIST_ROOT/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1"

format_command() {
  printf '%q ' "$@"
  printf '\n'
}

write_status() {
  local path="$1"
  shift
  printf '%s\n' "$@" > "$path"
}

run_phase() {
  local log_path="$1"
  shift
  set +e
  "$@" 2>&1 | tee "$log_path"
  local exit_code=${PIPESTATUS[0]}
  set -e
  return "$exit_code"
}

echo "R27-G1 cloud 64-environment capacity autopsy"
echo "  root:                    $ROOT"
echo "  python:                  $PYTHON_BIN"
echo "  run_root:                $RUN_ROOT"
echo "  checkpoint_dist_root:    $CHECKPOINT_DIST_ROOT"
echo "  device:                  $DEVICE"
echo "  num_envs:                $NUM_ENVS"
echo "  n_resets:                $N_RESETS"
echo "  collector:               $COLLECTOR_BACKEND/$COLLECTOR_START_METHOD"
echo "  schedule:                step_major_env_id_ascending"
echo "  dry_run:                 $DRY_RUN"

if [[ "$DRY_RUN" -eq 0 ]]; then
  if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 && [[ ! -x "$PYTHON_BIN" ]]; then
    echo "Python executable not found: $PYTHON_BIN" >&2
    exit 2
  fi
  for index in 0 1 2; do
    checkpoint="$CHECKPOINT_DIR/${ARM_FILES[$index]}"
    if [[ ! -f "$checkpoint" ]]; then
      echo "Required checkpoint not found: $checkpoint" >&2
      exit 2
    fi
    actual_hash="$("$SHA256_BIN" "$checkpoint" | awk '{print tolower($1)}')"
    if [[ "$actual_hash" != "${ARM_HASHES[$index]}" ]]; then
      echo "Checkpoint SHA256 mismatch: $checkpoint" >&2
      echo "expected=${ARM_HASHES[$index]} actual=$actual_hash" >&2
      exit 2
    fi
  done
  mkdir -p "$RUN_ROOT"
  write_status "$RUN_ROOT/batch_status.txt" \
    "started=$(date -Is)" \
    "state=running" \
    "phase=collect-static" \
    "device=$DEVICE" \
    "num_envs=$NUM_ENVS" \
    "n_resets=$N_RESETS" \
    "schedule=step_major_env_id_ascending"
fi

set -e
failures=()
successful_arms=0
results=()

for index in 0 1 2; do
  arm="${ARM_NAMES[$index]}"
  checkpoint="$CHECKPOINT_DIR/${ARM_FILES[$index]}"
  arm_root="$RUN_ROOT/$arm"
  command=(
    "$PYTHON_BIN" scripts/audit_r27_low_actor_capacity.py collect-static
    --checkpoint "$checkpoint"
    --output-dir "$arm_root"
    --checkpoint-id "$arm"
    --checkpoint-update "${ARM_UPDATES[$index]}"
    --device "$DEVICE"
    --num-envs "$NUM_ENVS"
    --n-resets "$N_RESETS"
    --collector-backend "$COLLECTOR_BACKEND"
    --collector-start-method "$COLLECTOR_START_METHOD"
  )
  echo
  echo "PHASE collect-static $arm"
  format_command "${command[@]}"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    continue
  fi

  mkdir -p "$arm_root"
  format_command "${command[@]}" > "$arm_root/command.txt"
  write_status "$arm_root/runner_status.txt" \
    "started=$(date -Is)" "state=running" "phase=collect-static" "arm=$arm"
  if run_phase "$arm_root/collector_static_output.log" "${command[@]}"; then
    if [[ -f "$arm_root/collector_manifest.json" && -f "$arm_root/static_capacity.json" ]]; then
      write_status "$arm_root/runner_status.txt" \
        "finished=$(date -Is)" "state=succeeded" "phase=collect-static" "arm=$arm"
      results+=("$arm=succeeded")
      successful_arms=$((successful_arms + 1))
    else
      failures+=("$arm")
      results+=("$arm=failed: required artifact missing")
      write_status "$arm_root/runner_status.txt" \
        "finished=$(date -Is)" "state=failed" "phase=collect-static" \
        "arm=$arm" "error=required artifact missing"
    fi
  else
    exit_code=$?
    failures+=("$arm")
    results+=("$arm=failed: exit_code=$exit_code")
    write_status "$arm_root/runner_status.txt" \
      "finished=$(date -Is)" "state=failed" "phase=collect-static" \
      "arm=$arm" "exit_code=$exit_code"
  fi
  if [[ ${#failures[@]} -gt 0 && "$CONTINUE_ON_ERROR" -eq 0 ]]; then
    break
  fi
done

final_checkpoint="$CHECKPOINT_DIR/${ARM_FILES[2]}"
synthetic_command=(
  "$PYTHON_BIN" scripts/audit_r27_low_actor_capacity.py synthetic
  --checkpoint "$final_checkpoint"
  --snapshot-dir "$RUN_ROOT/arm0_final/capacity_snapshots"
  --output-dir "$RUN_ROOT"
  --device "$DEVICE"
)
echo
echo "PHASE synthetic"
format_command "${synthetic_command[@]}"
if [[ "$DRY_RUN" -eq 0 ]]; then
  if [[ "$successful_arms" -eq 3 ]]; then
    format_command "${synthetic_command[@]}" > "$RUN_ROOT/synthetic_command.txt"
    if run_phase "$RUN_ROOT/synthetic_output.log" "${synthetic_command[@]}" \
      && [[ -f "$RUN_ROOT/synthetic_control.json" ]]; then
      results+=("synthetic=succeeded")
    else
      failures+=("synthetic")
      results+=("synthetic=failed")
    fi
  else
    failures+=("synthetic")
    results+=("synthetic=skipped: collect-static incomplete")
  fi
fi

aggregate_command=(
  "$PYTHON_BIN" scripts/audit_r27_low_actor_capacity.py aggregate
  --run-root "$RUN_ROOT"
  --checkpoint-ids arm0_update25 arm0_update30 arm0_final
)
echo
echo "PHASE aggregate"
format_command "${aggregate_command[@]}"
if [[ "$DRY_RUN" -eq 0 ]]; then
  if [[ ${#failures[@]} -eq 0 ]]; then
    format_command "${aggregate_command[@]}" > "$RUN_ROOT/aggregate_command.txt"
    if run_phase "$RUN_ROOT/aggregate_output.log" "${aggregate_command[@]}" \
      && [[ -f "$RUN_ROOT/r27_capacity_autopsy.json" ]]; then
      results+=("aggregate=succeeded")
    else
      failures+=("aggregate")
      results+=("aggregate=failed")
    fi
  else
    results+=("aggregate=skipped: required phase failed")
  fi

  state=succeeded
  if [[ ${#failures[@]} -gt 0 ]]; then
    state=failed
  fi
  write_status "$RUN_ROOT/batch_status.txt" \
    "finished=$(date -Is)" \
    "state=$state" \
    "failed_phases=$(IFS=,; echo "${failures[*]}")" \
    "${results[@]}"
  if [[ "$state" == failed ]]; then
    exit 1
  fi
fi

echo
echo "R27-G1 cloud capacity autopsy runner completed."
