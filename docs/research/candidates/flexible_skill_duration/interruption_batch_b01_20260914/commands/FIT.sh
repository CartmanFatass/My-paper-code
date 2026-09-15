#!/bin/bash
# One selected original; the committed execution table supplies arm and seed.
set -u
cd /home/wu/hmasd-worktrees/fsd-interruption-batch-b01-20260914 || exit 1
arm="$1"
seed="$2"
out="temp/directions/flexible_skill_duration/exp/interruption_batch_b01_20260914/${seed}_${arm}"
mkdir -p "$out"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4
export PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
/usr/bin/time -q -f '{"wall_seconds":%e,"user_seconds":%U,"system_seconds":%S,"peak_rss_kib":%M,"exit_code":%x}' \
  -o "$out/whole_command_resources.json" /bin/bash -c '
  /home/wu/.venvs/hmasd/bin/python -B scripts/hmasd_resource_preflight.py admit-memory --out "$1/admission.json" &&
  /home/wu/.venvs/hmasd/bin/python -B scripts/run_fsd_interruption_batch_b01.py fit --arm "$2" --seed "$3" --output-root "$1"
  ' fsd-original "$out" "$arm" "$seed"
