#!/usr/bin/env bash
# Launch only in the exact published-SHA worktree bound in LAUNCH.md.
set -u
if [ "${1:-}" != native ]; then
  exec /usr/bin/time -f 'MGTAP_NATIVE_WALL_SECONDS=%e\nMGTAP_NATIVE_PEAK_RSS_KIB=%M\nMGTAP_NATIVE_EXIT=%x' /usr/bin/timeout 900 bash "$0" native
fi
cd /home/wu/hmasd-worktrees/mgtap-early-8241-20260913 || exit 1
export MGTAP_CHAIN_STARTED_UNIX="$(date +%s.%N)"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=''
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/metric_ground_transport_allocation/exp/early_exposure_b01_8241_20260913/admission.json &&
/home/wu/.venvs/hmasd/bin/python -u scripts/run_mgtap_early_exposure_b01.py --seed 8241 --out temp/directions/metric_ground_transport_allocation/exp/early_exposure_b01_8241_20260913
