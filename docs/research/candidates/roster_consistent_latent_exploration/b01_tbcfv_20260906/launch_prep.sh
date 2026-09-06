#!/bin/bash
set -e
WT=/home/wu/hmasd-worktrees/rcle-b01-4d40621
ROOT=$WT/temp/directions/roster_consistent_latent_exploration/exp/tbcfv_b01_20260906
PY=/home/wu/.venvs/hmasd/bin/python
export PYTHONPATH="$WT"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PATH="/home/wu/.venvs/hmasd/bin:$PATH"
cd "$WT"
mkdir -p "$ROOT/receipts" "$ROOT/timings" "$ROOT/build" "$ROOT/executability" "$ROOT/c1p1" "$ROOT/flex" "$ROOT/reference"

echo "=== step (1) build ==="
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/build.json" && \
/usr/bin/time -v -o "$ROOT/timings/build.time" \
$PY scripts/run_rcle_tbcfv_b01.py build --build-root "$ROOT/build"
echo "STEP1_EXIT=$?"

echo "=== step (2) pytest ==="
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/pytest.json" && \
/usr/bin/time -v -o "$ROOT/timings/pytest.time" \
$PY -m pytest -q -p no:cacheprovider \
  tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv/test_native_host.py \
  tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01
echo "STEP2_EXIT=$?"

echo "=== step (3) executability ==="
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/executability.json" && \
/usr/bin/timeout --signal=TERM 300s \
/usr/bin/time -v -o "$ROOT/timings/executability.time" \
$PY scripts/run_rcle_tbcfv_b01.py executability --out "$ROOT/executability" --wall-cap 300
echo "STEP3_EXIT=$?"

echo "=== prep chain complete ==="
