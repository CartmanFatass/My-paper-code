#!/usr/bin/env bash
# Args: exact source SHA, detached checkout, new output; BANK additionally accepted Generic summary and fixed final.pt.
set -euo pipefail
exec /usr/bin/time -q -f '{"wall_seconds":%e,"user_seconds":%U,"system_seconds":%S,"peak_rss_kib":%M,"exit_code":%x}' \
  -o "$3/INVOCATION_TIME.json" timeout --signal=TERM --kill-after=5s 294s \
  bash -c 'set -euo pipefail
    cd "$1"
    /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out "$3/ADMISSION.json" &&
    exec /home/wu/.venvs/hmasd/bin/python scripts/run_folr_entity_history_b01.py \
      --reference-use --arm BANK --seed 781201 --evaluation-seed 2781301 --cap-seconds 300 \
      --launch-sha "$2" --out "$3" --generic-summary "$4" --retained-checkpoint "$5"
  ' -- "$2" "$1" "$3" "$4" "$5"
