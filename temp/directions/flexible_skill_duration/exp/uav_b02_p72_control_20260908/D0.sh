#!/usr/bin/env bash
set -euo pipefail
cd /home/wu/hmasd-worktrees/fsd-uav-b02-p72-08199a932
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-inputs/fsd-uav-b02-p72-20260908/D0_admission.json && \
exec /home/wu/.venvs/hmasd/bin/python scripts/run_fsd_uav_individual_renewal_b02.py --arm D0 --output-root temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b02_770603/D0
