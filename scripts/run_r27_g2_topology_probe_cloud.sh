#!/usr/bin/env bash

set -Eeuo pipefail

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"
DEVICE="${DEVICE:-cuda}"
PROBE_WORKERS="${PROBE_WORKERS:-8}"
CHECKPOINT_DIST_ROOT="${CHECKPOINT_DIST_ROOT:-$ROOT/dist}"
RUN_ROOT="${RUN_ROOT:-logs/r27_g2_topology_probe_$(date +%Y%m%d_%H%M%S)}"
RESIDENCY_SECONDS="${RESIDENCY_SECONDS:-300}"
STARTUP_TIMEOUT_SECONDS="${STARTUP_TIMEOUT_SECONDS:-480}"
SHUTDOWN_TIMEOUT_SECONDS="${SHUTDOWN_TIMEOUT_SECONDS:-60}"
MAX_WALL_SECONDS="${MAX_WALL_SECONDS:-900}"
MIN_FREE_GPU_MIB="${MIN_FREE_GPU_MIB:-4096}"
MIN_FREE_HOST_MIB="${MIN_FREE_HOST_MIB:-8192}"
MIN_FREE_HOST_FRACTION="${MIN_FREE_HOST_FRACTION:-0.15}"
MIN_START_FREE_GPU_MIB="${MIN_START_FREE_GPU_MIB:-22000}"
DRY_RUN=0

for argument in "$@"; do
  case "$argument" in
    --dry-run) DRY_RUN=1 ;;
    *) echo "Unknown argument: $argument" >&2; exit 2 ;;
  esac
done

if [[ "$DEVICE" != "cuda" ]]; then
  echo "R27-G2 topology probing requires DEVICE=cuda; CPU fallback is forbidden." >&2
  exit 2
fi
if [[ ! "$PROBE_WORKERS" =~ ^[0-9]+$ ]]; then
  echo "PROBE_WORKERS must be an integer from 2 through 64." >&2
  exit 2
fi
PROBE_WORKERS=$((10#$PROBE_WORKERS))
if (( PROBE_WORKERS < 2 || PROBE_WORKERS > 64 )); then
  echo "PROBE_WORKERS must be an integer from 2 through 64; serial probing is rejected." >&2
  exit 2
fi

PROBE_SCRIPT="scripts/r27_g2_topology_probe.py"
CHECKPOINT="$CHECKPOINT_DIST_ROOT/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_final.pt"
RESULT_JSON="$RUN_ROOT/topology_probe.json"

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

if ! command -v git >/dev/null 2>&1; then
  echo "git is required to bind topology validation to a source commit." >&2
  exit 2
fi
GIT_COMMIT="$(git rev-parse HEAD)"
if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "R27-G2 topology probing requires a clean tracked Git worktree." >&2
  exit 2
fi

COMMAND=(
  "$PYTHON_BIN" "$PROBE_SCRIPT"
  --checkpoint "$CHECKPOINT"
  --output "$RESULT_JSON"
  --workers "$PROBE_WORKERS"
  --device cuda
  --residency-seconds "$RESIDENCY_SECONDS"
  --startup-timeout-seconds "$STARTUP_TIMEOUT_SECONDS"
  --shutdown-timeout-seconds "$SHUTDOWN_TIMEOUT_SECONDS"
  --max-wall-seconds "$MAX_WALL_SECONDS"
  --min-free-gpu-mib "$MIN_FREE_GPU_MIB"
  --min-free-host-mib "$MIN_FREE_HOST_MIB"
  --min-free-host-fraction "$MIN_FREE_HOST_FRACTION"
  --git-commit "$GIT_COMMIT"
)

echo "R27-G2 independent CUDA-process topology probe"
echo "  repository_root:      $ROOT"
echo "  git_commit:           $GIT_COMMIT"
echo "  python:               $PYTHON_BIN"
echo "  checkpoint:           $CHECKPOINT"
echo "  run_root:             $RUN_ROOT"
echo "  device:               cuda"
echo "  workers:              $PROBE_WORKERS"
echo "  residency_seconds:    $RESIDENCY_SECONDS"
echo "  expected_wall_clock:  5-15 minutes (hard gate ${MAX_WALL_SECONDS}s)"
echo "  scientific_evidence:  false"
format_command "${COMMAND[@]}"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "Dry run complete; no probe directories, processes, or statuses were created."
  exit 0
fi

if [[ ! -f "$PROBE_SCRIPT" ]]; then
  echo "Required topology probe is missing: $PROBE_SCRIPT" >&2
  exit 2
fi
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 && [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python executable not found: $PYTHON_BIN" >&2
  exit 2
fi
if [[ ! -s "$CHECKPOINT" ]]; then
  echo "Registered final checkpoint is missing or empty: $CHECKPOINT" >&2
  exit 2
fi
if ! "$PYTHON_BIN" -c 'import torch; raise SystemExit(0 if torch.cuda.is_available() else 1)'; then
  echo "CUDA preflight failed; topology probe was not started." >&2
  exit 2
fi
compute_pids="$(
  nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null |
    awk '$1 ~ /^[0-9]+$/ {print $1}'
)"
if [[ -n "$compute_pids" ]]; then
  echo "GPU is occupied by compute PID(s): ${compute_pids//$'\n'/,}." >&2
  echo "Topology probe stopped; no CPU or shared-GPU fallback was selected." >&2
  exit 2
fi
start_free_gpu_mib="$(
  nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null |
    awk 'NR==1 {gsub(/^[[:space:]]+|[[:space:]]+$/, "", $0); print $0}'
)"
if [[ ! "$start_free_gpu_mib" =~ ^[0-9]+$ ]] || \
  (( start_free_gpu_mib < MIN_START_FREE_GPU_MIB )); then
  echo "GPU start-free memory ${start_free_gpu_mib:-unknown} MiB is below ${MIN_START_FREE_GPU_MIB} MiB." >&2
  echo "Topology probe stopped; no CPU or shared-GPU fallback was selected." >&2
  exit 2
fi

mkdir -p "$RUN_ROOT"
format_command "${COMMAND[@]}" > "$RUN_ROOT/command.txt"
write_status "$RUN_ROOT/runner_status.txt" \
  "started=$(date -Is)" \
  "state=running" \
  "probe_status=RUNNING" \
  "workers_requested=$PROBE_WORKERS" \
  "workers_passed=0" \
  "device=cuda" \
  "git_commit=$GIT_COMMIT" \
  "scientific_evidence=false" \
  "result_json=$RESULT_JSON"

set +e
"${COMMAND[@]}" 2>&1 | tee "$RUN_ROOT/runner_output.log"
probe_exit=${PIPESTATUS[0]}
set -e

if (( probe_exit == 0 )) && [[ -s "$RESULT_JSON" ]]; then
  write_status "$RUN_ROOT/runner_status.txt" \
    "finished=$(date -Is)" \
    "state=succeeded" \
    "probe_status=PASS" \
    "failure_class=NONE" \
    "workers_requested=$PROBE_WORKERS" \
    "workers_passed=$PROBE_WORKERS" \
    "device=cuda" \
    "git_commit=$GIT_COMMIT" \
    "scientific_evidence=false" \
    "result_json=$RESULT_JSON" \
    "exit_code=0"
  echo "R27-G2 topology probe operational PASS: $RESULT_JSON"
  exit 0
fi

failure_class=EXECUTION
if [[ -s "$RESULT_JSON" ]]; then
  set +e
  parsed_failure_class="$(
    "$PYTHON_BIN" -c \
      'import json, sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["failure_class"])' \
      "$RESULT_JSON" 2>/dev/null
  )"
  parse_exit=$?
  set -e
  if (( parse_exit == 0 )); then
    case "$parsed_failure_class" in
      RESOURCE_CAPACITY|EXECUTION) failure_class="$parsed_failure_class" ;;
    esac
  fi
fi

write_status "$RUN_ROOT/runner_status.txt" \
  "finished=$(date -Is)" \
  "state=failed" \
  "probe_status=FAIL" \
  "failure_class=$failure_class" \
  "workers_requested=$PROBE_WORKERS" \
  "workers_passed=0" \
  "device=cuda" \
  "git_commit=$GIT_COMMIT" \
  "scientific_evidence=false" \
  "result_json=$RESULT_JSON" \
  "exit_code=$probe_exit"
echo "R27-G2 topology probe failed; no scientific launch is authorized." >&2
exit 1
