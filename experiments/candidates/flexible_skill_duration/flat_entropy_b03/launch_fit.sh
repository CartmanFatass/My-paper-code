#!/usr/bin/env bash
# FSD flat entropy B03: one fit through the admission kernel.
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
#   arm         CF_E005 (lambda_l 0.005) | CF_E0005 (lambda_l 0.0005)
#   seed        training block seed: 772803, 772903 or 773003
#
# Fixed by the notebook entry and the runner, not by this script: CPU FP32, torch four threads,
# 16 training lanes, 45 rollouts, panels after 5,10,...,45, 32 evaluation worlds.
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
  -- scripts/run_fsd_flat_entropy_b03.py fit \
     --arm "$arm" --seed "$seed" --launch-sha "$launch_sha" --output-root "$output"
