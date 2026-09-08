#!/usr/bin/env bash
set -euo pipefail
cd /home/wu/hmasd-worktrees/fsd-native-renewal-b03-p47-f09aa00ba
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403/H/admission.json && \
exec /home/wu/.venvs/hmasd/bin/python scripts/run_fsd_native_renewal_learning_b03.py --policy H --seed 770403 --launch-sha f09aa00ba0e6f7c709af188b61be6ff8e7e6bc96 --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403/H --d0-summary temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403/D0/summary.json --g-summary temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403/G/summary.json
