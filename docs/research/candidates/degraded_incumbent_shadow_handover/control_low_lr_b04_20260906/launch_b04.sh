#!/bin/bash
# DISH-CONTROL-LOW-LR-B04 complete chain: shared item S (focused check + initializer + four-row
# raw reference), then CONTROL, then LOW_LR. Launch sha ef23d927045e449a0aa831e6a94a99d976e91924.
set -u
WT=/home/wu/hmasd-worktrees/dish-b04-ef23d92
ROOT=$WT/temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b04_20260906
PY=/home/wu/.venvs/hmasd/bin/python
export PATH=/home/wu/.venvs/hmasd/bin:$PATH
export PYTHONPATH="$WT"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
cd "$WT"
mkdir -p "$ROOT/shared" "$ROOT/control" "$ROOT/low_lr"

echo "=== shared item S ==="
T0=$(date +%s.%N)
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/admission_shared.json" && \
/usr/bin/time -v -o "$ROOT/focused.time" $PY -m pytest -q -p no:cacheprovider tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04 > "$ROOT/focused.log" 2>&1 && \
/usr/bin/time -v -o "$ROOT/shared.time" $PY scripts/run_dish_control_low_lr_b04.py shared --admission "$ROOT/admission_shared.json" --out "$ROOT/shared" > "$ROOT/shared.stdout" 2> "$ROOT/shared.stderr"
SHARED_EXIT=$?
T1=$(date +%s.%N)
S=$(python3 -c "print(round($T1 - $T0, 3))")
echo "shared_exit=$SHARED_EXIT shared_wall_seconds=$S" | tee "$ROOT/shared_wall.txt"
if [ "$SHARED_EXIT" -ne 0 ] || [ ! -f "$ROOT/shared/summary.json" ]; then echo "shared item failed; not launching arms"; exit 10; fi
TIMEOUT=$(python3 -c "print(round(1800 - $S/2 - 3.4, 2))")
echo "arm_timeout_seconds=$TIMEOUT" | tee -a "$ROOT/shared_wall.txt"

echo "=== arm CONTROL ==="
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/admission_control.json" && \
/usr/bin/timeout --signal=ALRM "${TIMEOUT}s" /usr/bin/time -v -o "$ROOT/control_time.txt" \
$PY scripts/run_dish_control_low_lr_b04.py run --arm CONTROL --seed 89 --shared "$ROOT/shared" --shared-preparation-seconds "$S" --admission "$ROOT/admission_control.json" --out "$ROOT/control" > "$ROOT/control.stdout" 2> "$ROOT/control.stderr"
echo "control_exit=$?" | tee "$ROOT/control_exit.txt"

echo "=== arm LOW_LR ==="
if [ -f "$ROOT/control/summary.json" ]; then
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/admission_low_lr.json" && \
/usr/bin/timeout --signal=ALRM "${TIMEOUT}s" /usr/bin/time -v -o "$ROOT/low_lr_time.txt" \
$PY scripts/run_dish_control_low_lr_b04.py run --arm LOW_LR --seed 89 --shared "$ROOT/shared" --shared-preparation-seconds "$S" --admission "$ROOT/admission_low_lr.json" --out "$ROOT/low_lr" --control-summary "$ROOT/control/summary.json" > "$ROOT/low_lr.stdout" 2> "$ROOT/low_lr.stderr"
echo "low_lr_exit=$?" | tee "$ROOT/low_lr_exit.txt"
else
echo "SKIP_LOW_LR_no_control_summary" | tee "$ROOT/low_lr_exit.txt"
fi
echo "=== chain done ==="
