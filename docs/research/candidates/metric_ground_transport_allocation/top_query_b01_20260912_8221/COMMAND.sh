#!/usr/bin/env bash
# Exact source SHA is bound in LAUNCH.md before this committed command is staged.
set -u
if [ "${1:-}" != native ]; then
  exec /usr/bin/time -f 'MGTAP_NATIVE_WALL_SECONDS=%e\nMGTAP_NATIVE_PEAK_RSS_KIB=%M\nMGTAP_NATIVE_EXIT=%x' bash "$0" native
fi
cd /home/wu/hmasd-worktrees/mgtap-top-b01-8221-20260912 || exit 1
export MGTAP_CHAIN_STARTED_UNIX="$(date +%s.%N)"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=''
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/metric_ground_transport_allocation/exp/top_query_b01_20260912_8221/admission.json &&
/home/wu/.venvs/hmasd/bin/python scripts/run_mgtap_top_query_b01.py --seed 8221 --out temp/directions/metric_ground_transport_allocation/exp/top_query_b01_20260912_8221
