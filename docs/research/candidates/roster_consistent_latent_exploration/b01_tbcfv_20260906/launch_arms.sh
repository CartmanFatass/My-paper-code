WT=/home/wu/hmasd-worktrees/rcle-b01-4d40621
ROOT=$WT/temp/directions/roster_consistent_latent_exploration/exp/tbcfv_b01_20260906
PY=/home/wu/.venvs/hmasd/bin/python
export PYTHONPATH="$WT"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PATH="/home/wu/.venvs/hmasd/bin:$PATH"
cd "$WT"

echo "=== step (4) ==="
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/c1p1.json" && \
/usr/bin/timeout --signal=ALRM 2696s \
/usr/bin/time -v -o "$ROOT/timings/c1p1.time" \
$PY scripts/run_rcle_tbcfv_b01.py arm --arm C1P1 \
  --out "$ROOT/c1p1" --wall-cap 2600 \
  --admission-receipt "$ROOT/receipts/c1p1.json" \
  --launch-sha 4d40621e0a9abd26e783e8c8aeeaf2653e49cf6a --updates 200 --eval-episodes 256
echo "STEP4_EXIT=$?"

echo "=== step (5) ==="
if [ -f "$ROOT/c1p1/summary.json" ]; then
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/flex.json" && \
/usr/bin/timeout --signal=ALRM 2696s \
/usr/bin/time -v -o "$ROOT/timings/flex.time" \
$PY scripts/run_rcle_tbcfv_b01.py arm --arm FLEX \
  --out "$ROOT/flex" --wall-cap 2600 \
  --admission-receipt "$ROOT/receipts/flex.json" \
  --control-summary "$ROOT/c1p1/summary.json" \
  --launch-sha 4d40621e0a9abd26e783e8c8aeeaf2653e49cf6a --updates 200 --eval-episodes 256
echo "STEP5_EXIT=$?"
else
echo "SKIP5_no_control_summary"
fi

echo "=== step (6) ==="
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/reference.json" && \
/usr/bin/time -v -o "$ROOT/timings/reference.time" \
$PY scripts/run_rcle_tbcfv_b01.py reference \
  --out "$ROOT/reference" \
  --admission-receipt "$ROOT/receipts/reference.json" \
  --launch-sha 4d40621e0a9abd26e783e8c8aeeaf2653e49cf6a --eval-episodes 256
echo "STEP6_EXIT=$?"
