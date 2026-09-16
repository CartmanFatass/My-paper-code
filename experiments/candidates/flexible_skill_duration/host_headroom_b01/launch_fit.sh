#!/usr/bin/env bash
# FSD host headroom B01: one fit, admission immediately before the runner, both under one agent-task command.
# Usage: launch_fit.sh <launch_sha> <output_dir> <arm> <seed> <stage> <lr_multiplier>
set -euo pipefail
launch_sha=$1; output=$2; arm=$3; seed=$4; stage=$5; mult=$6
PY=/home/wu/.venvs/hmasd/bin/python
cd "/home/wu/hmasd-worktrees/fsd-headroom-b01-${launch_sha:0:9}"
[ "$(git rev-parse HEAD)" = "$launch_sha" ] || { echo "worktree is not at $launch_sha" >&2; exit 3; }
mkdir -p -- "$(dirname -- "$output")"
mkdir -- "$output"
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$output/admission_receipt.json" \
  && /usr/bin/time -v -o "$output/gnu_time.txt" \
     $PY scripts/run_fsd_host_headroom_b01.py fit --arm "$arm" --seed "$seed" --stage "$stage" \
        --lr-multiplier "$mult" --output-root "$output"
