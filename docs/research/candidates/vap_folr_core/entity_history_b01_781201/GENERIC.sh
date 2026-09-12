#!/usr/bin/env bash
# Args are the committed source SHA, exact detached checkout and prepared empty output.
set -euo pipefail
exec /usr/bin/time -q -f '{"wall_seconds":%e,"user_seconds":%U,"system_seconds":%S,"peak_rss_kib":%M,"exit_code":%x}' \
  -o "$3/INVOCATION_TIME.json" timeout --signal=TERM --kill-after=5s 1794s \
  bash -c 'set -euo pipefail
    cd "$1"
    /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out "$3/ADMISSION.json" &&
    exec /home/wu/.venvs/hmasd/bin/python scripts/run_folr_entity_history_b01.py \
      --arm GENERIC_RETAIN --seed 781201 --evaluation-seed 1781201 --cap-seconds 1800 \
      --launch-sha "$2" --out "$3"
  ' -- "$2" "$1" "$3"
