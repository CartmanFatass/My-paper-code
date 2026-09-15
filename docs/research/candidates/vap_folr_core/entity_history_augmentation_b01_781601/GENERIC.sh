#!/usr/bin/env bash
# Args: exact source SHA, detached checkout, new augmentation B01 Generic output directory.
set -euo pipefail
exec /usr/bin/time -q -f '{"wall_seconds":%e,"user_seconds":%U,"system_seconds":%S,"peak_rss_kib":%M,"exit_code":%x}' \
  -o "$3/INVOCATION_TIME.json" \
  bash -c 'set -euo pipefail
    cd "$1"
    /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out "$3/ADMISSION.json" &&
    exec /home/wu/.venvs/hmasd/bin/python -u scripts/run_folr_entity_history_augmentation_b01.py \
      --arm GENERIC_RETAIN --seed 781601 --evaluation-seed 1781601 \
      --launch-sha "$2" --out "$3"
  ' -- "$2" "$1" "$3"
