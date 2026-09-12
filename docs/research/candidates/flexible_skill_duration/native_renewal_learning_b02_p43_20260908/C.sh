#!/usr/bin/env bash
set -euo pipefail
cd /home/wu/hmasd-worktrees/fsd-native-renewal-b02-p43-d961c5826
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b02_770303/C/admission.json && \
exec /home/wu/.venvs/hmasd/bin/python scripts/run_fsd_native_renewal_learning_b02.py --policy C --seed 770303 --launch-sha d961c58268353f215d3ffddf0d83927e6318541d --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b02_770303/C
