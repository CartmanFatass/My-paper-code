#!/bin/bash
set -u
WT=/home/wu/hmasd-worktrees/dish-witness-3c0ed5c
ROOT=$WT/temp/directions/degraded_incumbent_shadow_handover/exp/init_witness_a01_20260906_r2
PY=/home/wu/.venvs/hmasd/bin/python
export PATH=/home/wu/.venvs/hmasd/bin:$PATH
export PYTHONPATH="$WT"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
cd "$WT"
mkdir -p "$ROOT/receipts" "$ROOT/witness"
T0=$(date +%s.%N)
/usr/bin/time -v -o "$ROOT/focused.time" $PY -m pytest -q -p no:cacheprovider tests/experiments/candidates/degraded_incumbent_shadow_handover/init_witness_a01 > "$ROOT/focused.log" 2>&1
FOCUSED_EXIT=$?
T1=$(date +%s.%N)
C=$(python3 -c "print(round($T1 - $T0, 3))")
echo "focused_exit=$FOCUSED_EXIT focused_wall_seconds=$C" | tee "$ROOT/focused_wall.txt"
if [ "$FOCUSED_EXIT" -ne 0 ]; then echo "focused check failed; not launching"; exit 10; fi
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/witness.json" && \
/usr/bin/timeout --signal=ALRM 118s /usr/bin/time -v -o "$ROOT/witness.time" \
$PY scripts/run_dish_init_witness_a01.py run --out "$ROOT/witness" --admission "$ROOT/receipts/witness.json" --shared-preparation-seconds "$C" > "$ROOT/witness.stdout" 2> "$ROOT/witness.stderr"
echo "witness_exit=$?" | tee "$ROOT/witness_exit.txt"
