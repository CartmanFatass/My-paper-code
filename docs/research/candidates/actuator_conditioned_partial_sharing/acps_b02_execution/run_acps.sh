#!/usr/bin/env bash
set -euo pipefail
cd /home/wu/hmasd-worktrees/acps-b02-9102-20260912
export ACPS_ARM_WALL_START="$(date +%s.%N)"
export PYTHONDONTWRITEBYTECODE=1
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/actuator_conditioned_partial_sharing/exp/acps_b02_9102/ACPS/admission.json && exec /home/wu/.venvs/hmasd/bin/python scripts/run_acps_b02.py --arm ACPS --seed 9102 --output temp/directions/actuator_conditioned_partial_sharing/exp/acps_b02_9102/ACPS
