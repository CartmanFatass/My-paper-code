#!/usr/bin/env bash
set -uo pipefail
cd /home/wu/hmasd-worktrees/cadc-b01-9302-20260912
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=''
export CADC_CHAIN_STARTED_UNIX="$(date +%s.%N)"
/usr/bin/time -q -f '{"elapsed_seconds":%e,"peak_rss_kib":%M,"exit_code":%x}' -o /home/wu/hmasd-inputs/cadc-b01-9302-20260912/RR_WALL.json timeout --signal=TERM --kill-after=1s 595s bash -c '
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-inputs/cadc-b01-9302-20260912/RR_MEMORY.json &&
/home/wu/.venvs/hmasd/bin/python scripts/run_cadc_b01.py --seed 9302 --arm RR --out temp/directions/contention_aware_decentralized_communication/exp/cadc_b01_9302/RR
'
cadc_exit=$?
exit "$cadc_exit"
