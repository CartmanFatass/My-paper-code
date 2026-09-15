#!/usr/bin/env bash
# Args: exact source SHA, detached checkout, new current increment B01 current-only output directory, collected current increment B01 Generic summary.
set -euo pipefail
exec /usr/bin/time -q -f '{"wall_seconds":%e,"user_seconds":%U,"system_seconds":%S,"peak_rss_kib":%M,"exit_code":%x}' \
  -o "$3/INVOCATION_TIME.json" \
  bash -c 'set -euo pipefail
    cd "$1"
    /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out "$3/ADMISSION.json" &&
    exec /home/wu/.venvs/hmasd/bin/python -u scripts/run_folr_entity_current_increment_b01.py \
      --arm AUGMENTED_CURRENT_ONLY --seed 781801 --evaluation-seed 1781801 \
      --launch-sha "$2" --out "$3" --generic-summary "$4"
  ' -- "$2" "$1" "$3" "$4"
