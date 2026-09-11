#!/usr/bin/env bash
# P76's sole submission; the caller supplies its accepted exact-SHA detached cwd.
set -eu
cwd=$1
exec bash "$cwd/experiments/candidates/vsp_03/vsp03_b04/launch.sh" \
    vsp03-b05-p76-20260909 "$cwd" vsp03-b05-p76-20260909 \
    /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b05_seed7_p76_20260909_terminal.json \
    120 10 -- bash -c '/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b05_seed7_p76_20260909_admission.json && exec /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b05.py --seed 7 --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b05_seed7_p76_20260909 --started-monotonic "$VSP03_B04_STARTED" --node wsl_4070'
