#!/usr/bin/env bash
set -euo pipefail
cd /home/wu/hmasd-worktrees/fsd-uav-b01-p70-ca36e2f94
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-inputs/fsd-uav-b01-p70-20260908/I_admission.json && \
exec /home/wu/.venvs/hmasd/bin/python scripts/run_fsd_uav_individual_renewal_b01.py --arm I --output-root temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b01_770503/I --d0-summary temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b01_770503/D0/summary.json
