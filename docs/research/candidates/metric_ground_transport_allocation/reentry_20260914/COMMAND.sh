#!/usr/bin/env bash
# Exact published detached worktree; no retry or scientific endpoint extension.
set -u
if [ "${1:-}" != native ]; then
  exec /usr/bin/time -f 'MGTAP_COMPLETE_COMMAND_WALL_SECONDS=%e\nMGTAP_COMPLETE_COMMAND_PEAK_RSS_KIB=%M\nMGTAP_COMPLETE_COMMAND_EXIT=%x' /usr/bin/timeout 14400 bash "$0" native
fi
cd /home/wu/hmasd-worktrees/mgtap-lr-selection-8251-8252-20260914 || exit 1
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=''
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/metric_ground_transport_allocation/exp/lr_selection_b01_8251_8252_20260914/admission.json &&
/home/wu/.venvs/hmasd/bin/python -u -m experiments.candidates.metric_ground_transport_allocation.mgtap_lr_selection_b01.study --selection-master 8251 --holdout-master 8252 --launch-sha "$(git rev-parse HEAD)" --out temp/directions/metric_ground_transport_allocation/exp/lr_selection_b01_8251_8252_20260914
