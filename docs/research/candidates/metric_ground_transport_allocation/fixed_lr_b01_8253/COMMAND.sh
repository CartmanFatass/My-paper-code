#!/usr/bin/env bash
# One fixed-rate pair at the exact published detached source; no retry.
set -u
if [ "${1:-}" != native ]; then
  exec /usr/bin/time -f 'MGTAP_COMPLETE_COMMAND_WALL_SECONDS=%e\nMGTAP_COMPLETE_COMMAND_PEAK_RSS_KIB=%M\nMGTAP_COMPLETE_COMMAND_EXIT=%x' /usr/bin/timeout 14400 bash "$0" native
fi
cd /home/wu/hmasd-worktrees/mgtap-fixed-lr-b01-8253-20260914 || exit 1
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=''
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/metric_ground_transport_allocation/exp/fixed_lr_b01_8253_20260914/admission.json &&
/home/wu/.venvs/hmasd/bin/python -u -m experiments.candidates.metric_ground_transport_allocation.mgtap_fixed_lr_b01.study --master 8253 --launch-sha "$(git rev-parse HEAD)" --out temp/directions/metric_ground_transport_allocation/exp/fixed_lr_b01_8253_20260914
