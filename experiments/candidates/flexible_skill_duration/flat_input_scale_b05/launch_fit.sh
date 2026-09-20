#!/usr/bin/env bash
# FSD flat input scale B05: one fit through the admission kernel.
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
#   arm         CF_S (B03's CF_E0005 construction plus the state affine on the appended state)
#   seed        training block seed: 772803, 772903 or 773003
#
# Fixed by the notebook entry and the runner, not by this script: CPU FP32, torch four threads,
# 16 training lanes, 45 rollouts, panels after 5,10,...,45, 32 evaluation worlds, rate multiplier
# 0.5, lambda_l 0.0005, the learner's default sequence minibatch.
#
# The `probe` command of the same runner is a zero-update forward measurement, not a fit; it is
# not admitted and has no launch script here (see the runner's docstring).
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
  -- scripts/run_fsd_flat_input_scale_b05.py fit \
     --arm "$arm" --seed "$seed" --launch-sha "$launch_sha" --output-root "$output"
