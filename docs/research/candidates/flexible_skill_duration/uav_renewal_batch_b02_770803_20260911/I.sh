#!/usr/bin/env bash
set -euo pipefail
cd /home/wu/hmasd-worktrees/fsd-uav-renewal-batch-b02-770803-20260911
export PYTHONDONTWRITEBYTECODE=1
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-inputs/fsd-uav-renewal-batch-b02-770803-20260911/I_admission.json && \
exec /home/wu/.venvs/hmasd/bin/python scripts/run_fsd_uav_renewal_batch_b02.py --arm I --output-root temp/directions/flexible_skill_duration/exp/uav_renewal_batch_b02_770803/I --d0-summary temp/directions/flexible_skill_duration/exp/uav_renewal_batch_b02_770803/D0/summary.json
