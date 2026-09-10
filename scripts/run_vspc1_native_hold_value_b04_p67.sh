#!/usr/bin/env bash
# P67 only; scientific surface accepted at a33a3820fe9d4a46a3231bcf267afc956554b6c5.
set -euo pipefail
exec /usr/bin/time -f 'whole_wall_seconds=%e,peak_rss_kib=%M' /bin/bash --noprofile --norc -c '
cd /home/wu/hmasd-worktrees/vspc1-native-hold-value-b04-p67-8202 &&
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b04_p67_8202_admission.json &&
/home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_native_hold_value_b04.py --seed 8202 --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b04_p67_8202
'
