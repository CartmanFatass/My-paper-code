#!/usr/bin/env bash
# FSD label content B08: one fit through the admission kernel.
#
# The kernel (scripts/hmasd_launch.py) owns interpreter selection, the published-source and
# pause/lead checks, the fresh actual-node memory admission, detachment and the native
# manifest; this script only composes one invocation of it, and the scientific runner is never
# called directly.
#
#   launch_fit.sh <node> <lead> <launch_sha> <tag> <seed>
#
#   node        executing node in .codex/hmasd-compute.toml (e.g. wsl_4070)
#   lead        the direction's exact current Lead runtime cell from docs/research/RESEARCH.md
#   launch_sha  full published SHA; the snapshot worktree is prepared from it
#   tag         fresh output tag; the run root is runs/flexible_skill_duration/<tag>
#   seed        training block seed: 772803, 772903 or 773003
#
# This object has one arm, D_SAVE: the recorded stage-1 D1280 construction with no configuration
# difference at all. Fixed by the notebook entry and the runner, not by this script: CPU FP32,
# torch four threads, 16 training lanes, 45 rollouts, panels after 5,10,...,45, 32 evaluation
# worlds, caps k_max = k_Z = config.k = 10, coordinator batch 1280, the standing D1280 learning
# rates, and the final weights written with the agent's own save_model after the fit has returned
# (runs/flexible_skill_duration/<tag>/final_weights.pt, with its weights.json sidecar; *.pt is
# gitignored, so the checkpoint stays on the executing node's run root).
#
# The probe is a separate, zero-fit command of the same runner and is not launched from here:
# it takes no optimizer step, carries no admission and is recorded as exposure.
#
# Ordinary wall plan (recorded, never a deadline): 10,300 s, the D1280 plan.
set -euo pipefail

if [ "$#" -ne 5 ]; then
  echo "usage: launch_fit.sh <node> <lead> <launch_sha> <tag> <seed>" >&2
  exit 2
fi

node=$1; lead=$2; launch_sha=$3; tag=$4; seed=$5

source_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)
cd -- "$source_root"

# The kernel itself runs under this checkout's control-plane interpreter (3.11+, tomllib);
# tools/research_support/interpreters.py resolves it for the running host.
control_python=$(
  python3 - <<'PY'
import sys
sys.path.insert(0, "tools")
from research_support.interpreters import control_plane_interpreter
print(control_plane_interpreter())
PY
)

output="runs/flexible_skill_duration/${tag}"
exec "$control_python" scripts/hmasd_launch.py launch \
  --node "$node" --source-root "$source_root" --snapshot \
  --direction flexible_skill_duration --lead "$lead" --sha "$launch_sha" \
  --output "$output" \
  -- scripts/run_fsd_label_content_b08.py fit \
     --arm D_SAVE --seed "$seed" --launch-sha "$launch_sha" --output-root "$output"
