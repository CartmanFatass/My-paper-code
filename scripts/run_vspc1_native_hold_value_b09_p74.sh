#!/usr/bin/env bash
set -euo pipefail
exec /usr/bin/time -f 'whole_wall_seconds=%e,peak_rss_kib=%M' /bin/bash --noprofile --norc -c '
cd /home/wu/hmasd-worktrees/vspc1-native-hold-value-b09-8402-4c9dc8b3de9b &&
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b09_8402_4c9dc8b3de9b_admission.json &&
/home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_native_hold_value_b09.py --seed 8402 --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b09_8402_4c9dc8b3de9b
'
