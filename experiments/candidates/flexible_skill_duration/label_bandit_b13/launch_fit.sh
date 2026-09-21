#!/usr/bin/env bash
# FSD label bandit B13: one fit through the admission kernel.
#
# The kernel (scripts/hmasd_launch.py) owns interpreter selection, the published-source and
# pause/lead checks, the fresh actual-node memory admission, detachment and the native
# manifest; this script only composes one invocation of it, and the scientific runner is never
# called directly.
#
#   launch_fit.sh <node> <lead> <launch_sha> <tag> <arm> <seed>
#
#   node        executing node in .codex/hmasd-compute.toml (e.g. wsl_4070)
#   lead        the direction's exact current Lead runtime cell from docs/research/RESEARCH.md
#   launch_sha  full published SHA; the snapshot worktree is prepared from it
#   tag         fresh output tag; the run root is runs/flexible_skill_duration/<tag>
#   arm         BANDIT (q = .7 softmax(z) + .3 uniform, rollout 1 uniform) or UNIFORM (q uniform
#               throughout, the estimator passive; the coordinator-off control)
#   seed        training block seed: 772803, 772903 or 773003
#
# Fixed by the notebook entry and the runner, not by this script: the recorded stage-1 D1280
# construction with the one declared configuration difference `disable_high_level_training = True`,
# CPU FP32, torch four threads, 16 training lanes, 45 rollouts, 32 evaluation worlds, caps
# k_max = k_Z = config.k = 10, coordinator batch 1280, the standing D1280 learning rates, the
# count-regression estimator after every rollout, and the panels at 5,10,...,45 - `best_estimate`
# in the frozen schedule slot and `uniform_every_10` beside it, with the six constant-label panels
# added at rollout 45. The final weights are written with the agent's own save_model after the fit
# has returned (runs/flexible_skill_duration/<tag>/final_weights.pt, with its weights.json
# sidecar; *.pt is gitignored, so the checkpoint stays on the executing node's run root).
#
# Ordinary wall plan (recorded, never a deadline): 8,300 s, the notebook entry's own ~2.3 h.
set -euo pipefail

if [ "$#" -ne 6 ]; then
  echo "usage: launch_fit.sh <node> <lead> <launch_sha> <tag> <arm> <seed>" >&2
  exit 2
fi

node=$1; lead=$2; launch_sha=$3; tag=$4; arm=$5; seed=$6

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
  -- scripts/run_fsd_label_bandit_b13.py fit \
     --arm "$arm" --seed "$seed" --launch-sha "$launch_sha" --output-root "$output"
