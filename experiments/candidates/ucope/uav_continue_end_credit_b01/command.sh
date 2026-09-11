#!/bin/bash
# Native chain; outer /usr/bin/time and timeout include this shell through exit.
set -eu
cd /home/wu/hmasd-worktrees/ucope-continue-end-credit-b01-8801-20260911
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
admission_start=$(date +%s.%N)
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-inputs/ucope-continue-end-credit-b01-8801-20260911-memory.json &&
exec /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_uav_continue_end_credit_b01.py --seed 8801 --admission-start-unix "$admission_start" --out temp/directions/ucope/exp/uav_continue_end_credit_b01_8801
