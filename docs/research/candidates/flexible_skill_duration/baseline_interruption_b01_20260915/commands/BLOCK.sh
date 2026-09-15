#!/bin/bash
# One training block of FSD_BASELINE_INTERRUPTION_B01: the three arms in order, each its own queue
# element with an adjacent memory admission joined by &&. A failed arm records its exit and the
# queue continues; nothing is retried. Usage: BLOCK.sh WORKTREE SEED
set -u
worktree="$1"
seed="$2"
cd "$worktree" || exit 1
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4
export PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
status=0
for arm in D1280 I1280 FLAT; do
  out="temp/directions/flexible_skill_duration/exp/baseline_interruption_b01_20260915/${seed}_${arm}"
  mkdir -p "$out"
  date -u +%FT%TZ > "$out/queue_element_start.txt"
  /usr/bin/time -q -f '{"wall_seconds":%e,"user_seconds":%U,"system_seconds":%S,"peak_rss_kib":%M,"exit_code":%x}' \
    -o "$out/whole_command_resources.json" /bin/bash -c '
    /home/wu/.venvs/hmasd/bin/python -B scripts/hmasd_resource_preflight.py admit-memory --out "$1/admission.json" &&
    /home/wu/.venvs/hmasd/bin/python -B scripts/run_fsd_baseline_interruption_b01.py fit --arm "$2" --seed "$3" --output-root "$1"
    ' fsd-original "$out" "$arm" "$seed"
  code=$?
  date -u +%FT%TZ > "$out/queue_element_end.txt"
  echo "{\"seed\":$seed,\"arm\":\"$arm\",\"exit_code\":$code}" >> "temp/directions/flexible_skill_duration/exp/baseline_interruption_b01_20260915/block_${seed}_queue.jsonl"
  if [ "$code" -ne 0 ]; then status=1; fi
done
exit $status
