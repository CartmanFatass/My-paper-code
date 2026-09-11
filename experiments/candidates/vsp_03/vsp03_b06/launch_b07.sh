#!/usr/bin/env bash
# One new B07 fit; unchanged inherited whole-task adapter.
set -eu
cwd=$1
fit=10804
base=/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b07_${fit}_20260910
name=vsp03-b07-${fit}-20260910
exec bash "$cwd/experiments/candidates/vsp_03/vsp03_b04/launch.sh" "$name" "$cwd" "$name" "${base}_terminal.json" 60 10 -- bash -c '/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out "$1" && /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b06.py --seed "$2" --out "$3" --node wsl_4070 --started-monotonic "$VSP03_B04_STARTED"' bash "${base}_admission.json" "$fit" "$base"
