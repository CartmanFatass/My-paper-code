#!/usr/bin/env bash
set -euo pipefail
cd /home/wu/hmasd-worktrees/fsd-uav-renewal-batch-b01-770703-20260911
export PYTHONDONTWRITEBYTECODE=1
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-inputs/fsd-uav-renewal-batch-b01-770703-20260911/I_admission.json && \
exec /home/wu/.venvs/hmasd/bin/python scripts/run_fsd_uav_renewal_batch_b01.py --arm I --output-root temp/directions/flexible_skill_duration/exp/uav_renewal_batch_b01_770703/I --d0-summary temp/directions/flexible_skill_duration/exp/uav_renewal_batch_b01_770703/D0/summary.json
