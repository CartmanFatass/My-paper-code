#!/usr/bin/env bash
# P67's sole submission; the caller supplies its accepted exact-SHA detached cwd.
set -eu
cwd=$1
exec bash "$cwd/experiments/candidates/vsp_03/vsp03_b04/launch.sh" \
    vsp03-b04-p67-20260908 "$cwd" vsp03-b04-p67-20260908 \
    /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p67_20260908_terminal.json \
    120 10 -- bash -c '/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p67_20260908_admission.json && exec /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b04.py --seed 6 --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p67_20260908 --started-monotonic "$VSP03_B04_STARTED" --node wsl_4070'
