#!/bin/bash
# RCLE-TBCFV-B02-NORM-0p02 complete chain: build (charged once), focused check (Linux oracle + B02
# tests), arm C1P1 (with the shared init panel), arm FLEX, reference. Launch sha
# 8ad01cb9ea69b77a2e907947bef59bf716a8b45a. Object cap 1,500 s; per-arm 600 s external ALRM.
set -u
SHA=8ad01cb9ea69b77a2e907947bef59bf716a8b45a
WT=/home/wu/hmasd-worktrees/rcle-b02-8ad01cb
ROOT=$WT/temp/directions/roster_consistent_latent_exploration/exp/tbcfv_b02_20260906
PY=/home/wu/.venvs/hmasd/bin/python
export PYTHONPATH="$WT"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PATH="/home/wu/.venvs/hmasd/bin:$PATH"
cd "$WT"
mkdir -p "$ROOT/receipts" "$ROOT/timings" "$ROOT/build" "$ROOT/c1p1" "$ROOT/flex" "$ROOT/reference"
T0=$(date +%s.%N)

echo "=== step (1) build ==="
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/build.json" && \
/usr/bin/time -v -o "$ROOT/timings/build.time" \
$PY scripts/run_rcle_tbcfv_b02.py build --build-root "$ROOT/build" > "$ROOT/build.stdout" 2> "$ROOT/build.stderr"
echo "STEP1_EXIT=$?" | tee "$ROOT/step1_exit.txt"

echo "=== step (2) focused check ==="
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/pytest.json" && \
/usr/bin/time -v -o "$ROOT/timings/pytest.time" \
$PY -m pytest -q -p no:cacheprovider \
  tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv/test_native_host.py \
  tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02 > "$ROOT/pytest.log" 2>&1
STEP2=$?
echo "STEP2_EXIT=$STEP2" | tee "$ROOT/step2_exit.txt"
T1=$(date +%s.%N)
echo "prep_wall_seconds=$(python3 -c "print(round($T1 - $T0, 3))")" | tee "$ROOT/prep_wall.txt"
if [ "$STEP2" -ne 0 ]; then echo "focused check failed; not launching arms"; exit 10; fi

echo "=== step (3) arm C1P1 ==="
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/c1p1.json" && \
/usr/bin/timeout --signal=ALRM 600s \
/usr/bin/time -v -o "$ROOT/timings/c1p1.time" \
$PY scripts/run_rcle_tbcfv_b02.py arm --arm C1P1 \
  --out "$ROOT/c1p1" --wall-cap 580 \
  --admission-receipt "$ROOT/receipts/c1p1.json" \
  --launch-sha $SHA --updates 200 --eval-episodes 256 > "$ROOT/c1p1.stdout" 2> "$ROOT/c1p1.stderr"
echo "STEP3_EXIT=$?" | tee "$ROOT/step3_exit.txt"

echo "=== step (4) arm FLEX ==="
if [ -f "$ROOT/c1p1/summary.json" ]; then
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/flex.json" && \
/usr/bin/timeout --signal=ALRM 600s \
/usr/bin/time -v -o "$ROOT/timings/flex.time" \
$PY scripts/run_rcle_tbcfv_b02.py arm --arm FLEX \
  --out "$ROOT/flex" --wall-cap 580 \
  --admission-receipt "$ROOT/receipts/flex.json" \
  --control-summary "$ROOT/c1p1/summary.json" \
  --launch-sha $SHA --updates 200 --eval-episodes 256 > "$ROOT/flex.stdout" 2> "$ROOT/flex.stderr"
echo "STEP4_EXIT=$?" | tee "$ROOT/step4_exit.txt"
else
echo "SKIP4_no_control_summary" | tee "$ROOT/step4_exit.txt"
fi

echo "=== step (5) reference ==="
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/reference.json" && \
/usr/bin/time -v -o "$ROOT/timings/reference.time" \
$PY scripts/run_rcle_tbcfv_b02.py reference \
  --out "$ROOT/reference" \
  --admission-receipt "$ROOT/receipts/reference.json" \
  --launch-sha $SHA --eval-episodes 256 > "$ROOT/reference.stdout" 2> "$ROOT/reference.stderr"
echo "STEP5_EXIT=$?" | tee "$ROOT/step5_exit.txt"
T2=$(date +%s.%N)
echo "chain_wall_seconds=$(python3 -c "print(round($T2 - $T0, 3))")" | tee "$ROOT/chain_wall.txt"
echo "=== chain done ==="
