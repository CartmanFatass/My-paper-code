#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_ROOT="${DATA_ROOT:-/root/autodl-tmp/HMASD}"
RUN_ROOT="${RUN_ROOT:-$DATA_ROOT/logs/r41_official_hmasd_$(date +%Y%m%d_%H%M%S)}"
SOURCE_ARCHIVE="$ROOT/ref/hmasd.tar"
SOURCE_ROOT="$RUN_ROOT/source"
PYTHON_BIN="${R41_PYTHON:-$DATA_ROOT/runtime/r41_official_hmasd/bin/python}"
STATUS_PATH="$RUN_ROOT/runner_status.txt"
STATUS_OWNED=0

if [[ "$RUN_ROOT" != "$DATA_ROOT"/logs/* ]]; then
  echo "RUN_ROOT must be under $DATA_ROOT/logs so all large artifacts remain on the data disk." >&2
  exit 2
fi
if [[ ! -d /root/autodl-tmp ]]; then
  echo "/root/autodl-tmp is unavailable." >&2
  exit 2
fi
mkdir -p "$RUN_ROOT/seeds" "$RUN_ROOT/result" "$RUN_ROOT/source"

write_status() {
  local state="$1"
  local phase="$2"
  shift 2
  {
    echo "updated=$(date -Is)"
    echo "state=$state"
    echo "phase=$phase"
    echo "experiment=EXP-20260716-r41-official-hmasd-alice-bob-anchor"
    echo "run_root=$RUN_ROOT"
    echo "source_archive=ref/hmasd.tar"
    echo "seeds=1,2,3,4,5"
    echo "parallel_seed_workers=5"
    echo "rollout_envs_per_seed=32"
    echo "declared_env_steps_per_seed=3000000"
    echo "actual_env_steps_per_seed=2998400"
    echo "outer_updates_per_seed=937"
    echo "optimizer_steps_per_path_per_seed=14055"
    echo "progress_glob=$RUN_ROOT/seeds/seed*/progress.json"
    echo "result_path=$RUN_ROOT/result/r41_official_hmasd_alice_bob.json"
    for line in "$@"; do echo "$line"; done
  } > "$STATUS_PATH"
  STATUS_OWNED=1
}

on_error() {
  local exit_code=$?
  if [[ "$STATUS_OWNED" -eq 1 ]]; then
    write_status failed runner "error=cloud runner exited with code $exit_code"
  fi
  exit "$exit_code"
}
trap on_error ERR

write_status running source_extract
if [[ ! -f "$SOURCE_ARCHIVE" ]]; then
  write_status failed source_extract "error=tracked HMASD source archive is missing: $SOURCE_ARCHIVE"
  exit 1
fi
tar -xf "$SOURCE_ARCHIVE" -C "$SOURCE_ROOT"
if [[ ! -f "$SOURCE_ROOT/hmasd/scripts/train/train_alice_and_bob.py" ]]; then
  write_status failed source_extract "error=ref/hmasd.tar did not produce the expected HMASD source tree"
  exit 1
fi

if [[ ! -x "$PYTHON_BIN" ]] || ! "$PYTHON_BIN" -c 'import torch, numpy, gym, tensorboardX, wandb, cv2, matplotlib, absl, setproctitle; assert torch.cuda.is_available()'; then
  write_status failed runtime "error=R41_PYTHON lacks a required official-source runtime dependency or CUDA"
  exit 1
fi

export MPLBACKEND=Agg
export WANDB_MODE=disabled
export PYTHONUNBUFFERED=1
write_status running training

declare -a pids=()
for seed in 1 2 3 4 5; do
  seed_root="$RUN_ROOT/seeds/seed${seed}"
  mkdir -p "$seed_root"
  (
    cd "$ROOT"
    CUDA_VISIBLE_DEVICES=0 "$PYTHON_BIN" scripts/run_r41_official_hmasd_seed.py \
      --source-archive "$SOURCE_ARCHIVE" \
      --source-root "$SOURCE_ROOT" \
      --output-root "$seed_root" \
      --seed "$seed" \
      > "$seed_root/runner_stdout.log" \
      2> "$seed_root/runner_stderr.log"
  ) &
  pids+=("$!")
done

failed=0
for index in "${!pids[@]}"; do
  seed=$((index + 1))
  if ! wait "${pids[$index]}"; then
    echo "seed $seed failed" >&2
    failed=1
  fi
done
if [[ "$failed" -ne 0 ]]; then
  write_status failed training "error=one or more seed workers failed"
  exit 1
fi

write_status running analysis
cd "$ROOT"
"$PYTHON_BIN" scripts/analyze_r41_official_hmasd_anchor.py \
  --run-root "$RUN_ROOT" \
  > "$RUN_ROOT/result/analyzer_stdout.log" \
  2> "$RUN_ROOT/result/analyzer_stderr.log"

if [[ ! -f "$RUN_ROOT/result/r41_official_hmasd_alice_bob.json" ]]; then
  write_status failed analysis "error=analyzer did not produce the registered result JSON"
  exit 1
fi
result_status="$($PYTHON_BIN -c 'import json,sys; print(json.load(open(sys.argv[1]))["status"])' "$RUN_ROOT/result/r41_official_hmasd_alice_bob.json")"
implementation_valid="$($PYTHON_BIN -c 'import json,sys; print(json.load(open(sys.argv[1]))["implementation_valid"])' "$RUN_ROOT/result/r41_official_hmasd_alice_bob.json")"
write_status completed result \
  "result_status=$result_status" \
  "implementation_valid=$implementation_valid"
trap - ERR
