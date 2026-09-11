#!/bin/bash
export PATH=/home/wu/.venvs/hmasd/bin:$PATH
export PYTHONPATH=/home/wu/hmasd-worktrees/n3-b03-20260906
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
cd /home/wu/hmasd-worktrees/n3-b03-20260906
mkdir -p temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906_r3
exec /usr/bin/timeout --signal=ALRM 1794.13s bash -c 'python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906_r3/admission_control.json && /usr/bin/time -v -o temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906_r3/control_time.txt python scripts/run_dish_forecast_package_b03.py run --arm CONTROL --seed 73 --shared-preparation-seconds 4.94 --admission temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906_r3/admission_control.json --out temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906_r3/control'
