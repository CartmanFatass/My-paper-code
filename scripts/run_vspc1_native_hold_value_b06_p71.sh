#!/usr/bin/env bash
set -euo pipefail
exec /usr/bin/time -f 'whole_wall_seconds=%e,peak_rss_kib=%M' /bin/bash --noprofile --norc -c '
cd /home/wu/hmasd-worktrees/vspc1-native-hold-value-b06-8302-fd4c9f4a65c7 &&
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b06_8302_fd4c9f4a65c7_admission.json &&
/home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_native_hold_value_b06.py --seed 8302 --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b06_8302_fd4c9f4a65c7
'
