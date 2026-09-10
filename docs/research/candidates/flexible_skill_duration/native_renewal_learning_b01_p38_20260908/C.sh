#!/usr/bin/env bash
set -euo pipefail
cd /home/wu/hmasd-worktrees/fsd-native-renewal-b01-p38-b3f86bb28
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b01_770203/C/admission.json && \
exec /home/wu/.venvs/hmasd/bin/python scripts/run_fsd_native_renewal_learning_b01.py --policy C --seed 770203 --launch-sha b3f86bb28879db239b07291c39d93a1c494abe50 --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b01_770203/C
