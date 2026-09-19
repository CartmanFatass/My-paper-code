#!/usr/bin/env bash
# FSD matched-information baseline B01: one fit through the admission kernel.
#
# The kernel (scripts/hmasd_launch.py) owns interpreter selection, the published-source and
# pause/lead checks, the fresh actual-node memory admission, detachment and the native
# manifest; this script only composes one invocation of it, so there is no per-run wrapper to
# maintain and the scientific runner is never called directly.
#
#   launch_fit.sh <node> <lead> <launch_sha> <tag> <arm> <seed> <stage> [lr_multiplier] [selection_json]
#
#   node           executing node in .codex/hmasd-compute.toml (e.g. wsl_4070)
#   lead           the direction's exact current Lead runtime cell from docs/research/RESEARCH.md
#   launch_sha     full published SHA; the snapshot worktree is prepared from it
#   tag            fresh output tag; the run root is runs/flexible_skill_duration/<tag>
#   arm            D1280 | CF
#   seed           training block seed (772603/772703 at stage 0, 772803..773203 at stage 1)
#   stage          0 (CF tuning) | 1 (confirmation)
#   lr_multiplier  CF only: 0.5 | 1 | 2 at stage 0, the selected value at stage 1
#   selection_json required for stage-1 CF: the repository-relative path of the completed stage-0
#                  SELECTION.json, COMMITTED at <launch_sha>
#                  (runs/flexible_skill_duration/<selection-tag>/SELECTION.json).  The kernel
#                  runs the fit inside a snapshot worktree of <launch_sha> and refuses an author
#                  input that is absent from it, so an uncommitted selection cannot be read;
#                  committing it also pins the selected multiplier before any stage-1 fit.
#
# Fixed by the card and the runner, not by this script: CPU FP32, torch four threads, 16
# training lanes, 45 rollouts, panels after 5,10,...,45, 32 evaluation worlds.
set -euo pipefail

if [ "$#" -lt 7 ] || [ "$#" -gt 9 ]; then
  echo "usage: launch_fit.sh <node> <lead> <launch_sha> <tag> <arm> <seed> <stage> [lr_multiplier] [selection_json]" >&2
  exit 2
fi

node=$1; lead=$2; launch_sha=$3; tag=$4; arm=$5; seed=$6; stage=$7
multiplier=${8:-}; selection=${9:-}

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
runner_args=(scripts/run_fsd_matched_information_baseline_b01.py fit
             --arm "$arm" --seed "$seed" --stage "$stage"
             --launch-sha "$launch_sha" --output-root "$output")
if [ -n "$multiplier" ]; then
  runner_args+=(--lr-multiplier "$multiplier")
fi
if [ -n "$selection" ]; then
  runner_args+=(--selection "$selection")
fi

cd -- "$source_root"
exec "$control_python" scripts/hmasd_launch.py launch \
  --node "$node" --source-root "$source_root" --snapshot \
  --direction flexible_skill_duration --lead "$lead" --sha "$launch_sha" \
  --output "$output" \
  -- "${runner_args[@]}"
