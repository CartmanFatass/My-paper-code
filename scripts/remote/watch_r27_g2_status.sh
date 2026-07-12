#!/usr/bin/env bash

set -uo pipefail

CONTROLLER_ROOT="${CONTROLLER_ROOT:-/root/autodl-tmp/HMASD/r27_g2_remote/controller}"
REFRESH_SECONDS="${REFRESH_SECONDS:-10}"
RUN_ROOT="${RUN_ROOT:-}"
ONCE=0

while (( $# > 0 )); do
  case "$1" in
    --once) ONCE=1; shift ;;
    --run-root)
      [[ $# -ge 2 ]] || { echo "--run-root requires a path" >&2; exit 2; }
      RUN_ROOT="$2"; shift 2 ;;
    --controller-root)
      [[ $# -ge 2 ]] || { echo "--controller-root requires a path" >&2; exit 2; }
      CONTROLLER_ROOT="$2"; shift 2 ;;
    --refresh)
      [[ $# -ge 2 && "$2" =~ ^[0-9]+$ && "$2" -ge 1 ]] || {
        echo "--refresh requires a positive integer" >&2; exit 2;
      }
      REFRESH_SECONDS="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

CHECKPOINT_IDS=(arm0_update25 arm0_update30 arm0_final)

status_value() {
  local path="$1"
  local key="$2"
  [[ -f "$path" ]] || return 0
  sed -n "s/^${key}=//p" "$path" | tail -n 1
}

count_status() {
  local checkpoint_id="$1"
  local key="$2"
  local value="$3"
  local count=0 reset_id status_path actual
  for reset_id in $(seq 0 63); do
    status_path="$RUN_ROOT/$checkpoint_id/resets/reset_$(printf '%02d' "$reset_id")/runner_status.txt"
    actual="$(status_value "$status_path" "$key")"
    [[ "$actual" == "$value" ]] && count=$((count + 1))
  done
  printf '%d' "$count"
}

progress_bar() {
  local completed="$1"
  local width=32
  local filled=$((completed * width / 64))
  local empty=$((width - filled))
  printf '['
  printf '%*s' "$filled" '' | tr ' ' '#'
  printf '%*s' "$empty" '' | tr ' ' '-'
  printf ']'
}

render() {
  local state_file="$CONTROLLER_ROOT/current_run.env"
  local package_dir="" launcher_log="" screen_session=""
  if [[ -z "$RUN_ROOT" && -f "$state_file" ]]; then
    # The controller writes only fixed, single-quoted absolute paths.
    # shellcheck disable=SC1090
    . "$state_file"
  fi

  if [[ -t 1 ]]; then
    printf '\033[2J\033[H'
  fi
  echo "R27-G2 remote status — $(date -Is)"
  echo "Status source: runner_status.txt / batch_status.txt (read-only view)"
  echo
  if [[ -z "$RUN_ROOT" ]]; then
    echo "state=not_started (no current_run.env and no --run-root)"
    return
  fi

  echo "Run root:    $RUN_ROOT"
  [[ -n "${PACKAGE_DIR:-}" ]] && echo "Package:     $PACKAGE_DIR"
  if [[ -n "${SCREEN_SESSION:-}" ]] && \
    screen -ls 2>/dev/null | grep -Eq "[.]${SCREEN_SESSION}[[:space:]]"; then
    echo "Process:     alive (screen=$SCREEN_SESSION)"
  else
    echo "Process:     not alive"
  fi
  if command -v nvidia-smi >/dev/null 2>&1; then
    gpu_line="$(nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null | head -n 1)"
    [[ -n "$gpu_line" ]] && echo "GPU:         $gpu_line (name, util%, used MiB, total MiB)"
  fi
  storage_line="$(df -hP "$RUN_ROOT" 2>/dev/null | awk 'NR==2 {print $2 " total, " $3 " used, " $4 " free (" $5 ")"}')"
  [[ -n "$storage_line" ]] && echo "Data disk:   $storage_line"
  echo
  printf '%-15s %-35s %8s %8s %8s %8s %8s\n' \
    "checkpoint" "progress" "success" "failed" "running" "excluded" "invalid"
  for checkpoint_id in "${CHECKPOINT_IDS[@]}"; do
    succeeded="$(count_status "$checkpoint_id" state succeeded)"
    failed="$(count_status "$checkpoint_id" state failed)"
    running="$(count_status "$checkpoint_id" state running)"
    excluded="$(count_status "$checkpoint_id" scientific_status EXCLUDED)"
    invalid="$(count_status "$checkpoint_id" scientific_status INVALID)"
    printf '%-15s ' "$checkpoint_id"
    progress_bar "$succeeded"
    printf ' %8d %8d %8d %8d %8d\n' \
      "$succeeded" "$failed" "$running" "$excluded" "$invalid"
  done

  batch_status="$RUN_ROOT/batch_status.txt"
  aggregate_status="$RUN_ROOT/aggregate_status.txt"
  echo
  echo "Batch operational state:   $(status_value "$batch_status" state || true)"
  echo "Aggregate state:           $(status_value "$aggregate_status" state || true)"
  echo "Scientific status:         $(status_value "$batch_status" scientific_status || true)"
  echo "Classification:            $(status_value "$batch_status" classification || true)"
  echo "Failed reset shards:       $(status_value "$batch_status" failed_reset_shards || true)"

  active_lines="$(find "$RUN_ROOT" -path '*/resets/reset_*/runner_status.txt' -type f -print 2>/dev/null |
    while IFS= read -r status_path; do
      if grep -qx 'state=running' "$status_path" 2>/dev/null; then
        printf '%s\n' "${status_path%/runner_status.txt}"
      fi
    done | head -n 8)"
  if [[ -n "$active_lines" ]]; then
    echo
    echo "Active reset workers (up to 8):"
    printf '%s\n' "$active_lines"
  fi

  if [[ -n "${LAUNCHER_LOG:-}" && -f "$LAUNCHER_LOG" ]]; then
    echo
    echo "Launcher tail:"
    tail -n 8 "$LAUNCHER_LOG"
  fi
}

while true; do
  render
  (( ONCE == 1 )) && break
  sleep "$REFRESH_SECONDS"
done
