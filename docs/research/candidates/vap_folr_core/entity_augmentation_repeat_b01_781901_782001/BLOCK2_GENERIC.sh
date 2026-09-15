#!/usr/bin/env bash
# Args: exact source SHA, detached checkout, fixed block 2 generic output.
set -euo pipefail
exec /usr/bin/time -q -f '{"wall_seconds":%e,"user_seconds":%U,"system_seconds":%S,"peak_rss_kib":%M,"exit_code":%x}' \
  -o "$3/INVOCATION_TIME.json" \
  bash -c 'set -euo pipefail
    cd "$1"
    /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out "$3/ADMISSION.json" &&
    exec /home/wu/.venvs/hmasd/bin/python -u scripts/run_folr_entity_augmentation_repeat_b01.py \
      --block 2 --arm GENERIC_RETAIN --seed 782001 --evaluation-seed 1782001 \
      --launch-sha "$2" --out "$3"
  ' -- "$2" "$1" "$3"
