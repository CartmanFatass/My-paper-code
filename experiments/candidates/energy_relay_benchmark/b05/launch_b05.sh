#!/usr/bin/env bash
# Admission launches of b05_canonical_frame_a01 on wsl_4070 at a published SHA (DO NOT run before
# the engineering review and the launch record).  Mirrors the admitted B02 Stage 1 scripts
# (temp/directions/energy_relay_benchmark/scratch/launch_b02_{train,eval,eval_final,resume}.sh):
# the node control checkout fast-forwards to origin/main, refuses a SHA that is not an ancestor of
# its HEAD, and runs scripts/hmasd_launch.py --snapshot (fresh node memory preflight >= the
# node's result_memory_floor_gib = 4 GiB, occupancy/duplicate-claim checks, detached supervisor).
#
# Usage:
#   launch_b05.sh train  <full sha> <tag> [threads=4]                       B fit, CUDA
#   launch_b05.sh resume <full sha> <tag> <ckpt node path> <source sha> [threads=4]
#   launch_b05.sh panel  <full sha> <tag> <arm> <ckpt node path> [modes] [workers=8] [threads=2]
#   launch_b05.sh final  <full sha> <tag> <arm> <ckpt node path> [modes] [workers=8] [threads=2]
# arm: B | C_SW | C_SW_FULL.  panel = development 955001-955032; final = hold-out 957001-957032
# (--final).  Checkpoint paths must be outside the node's author root (B02 convention: copy
# checkpoints/cNN unchanged to /home/wu/hmasd-artifacts/energy_relay_benchmark/<fit tag>/checkpoints/cNN).
set -u
MODE="$1"; SHA="$2"; TAG="$3"; shift 3
RUNNER=experiments/candidates/energy_relay_benchmark/b05/run_b05.py
case "$MODE" in
  train)  T="${1:-4}"
          ARGS="train --seed 925031 --launch-sha $SHA --out runs/energy_relay_benchmark/$TAG --device cuda --threads $T" ;;
  resume) CK="$1"; SRC="$2"; T="${3:-4}"
          ARGS="train --seed 925031 --launch-sha $SHA --out runs/energy_relay_benchmark/$TAG --device cuda --threads $T --resume-from $CK --resume-source-sha $SRC" ;;
  panel|final)
          ARM="$1"; CK="$2"; M="${3:-deterministic,stochastic}"; W="${4:-8}"; T="${5:-2}"
          WORLDS=955001-955032; FINAL=""
          if [ "$MODE" = final ]; then WORLDS=957001-957032; FINAL="--final"; fi
          ARGS="panel --arm $ARM --checkpoint $CK --out runs/energy_relay_benchmark/$TAG --worlds $WORLDS $FINAL --modes $M --launch-sha $SHA --workers $W --threads $T --device cpu" ;;
  *) echo "unknown mode $MODE" >&2; exit 2 ;;
esac
ssh -o BatchMode=yes -o ConnectTimeout=20 hmasd-wsl-node "zsh -lic 'cd /home/wu/projects/HMASD && git pull --ff-only origin main 2>&1 | grep -v \"garbage found\|bad tree\|failed to run repack\" | tail -1; H=\$(git rev-parse HEAD); echo HEAD=\$H; git merge-base --is-ancestor $SHA \$H || { echo PUBLISHED_SHA_NOT_IN_HEAD; exit 3; }; echo ---LAUNCH---; /home/wu/.venvs/hmasd/bin/python scripts/hmasd_launch.py launch --node wsl_4070 --source-root /home/wu/projects/HMASD --snapshot --direction energy_relay_benchmark --lead \"Claude DM (WSL session)\" --sha $SHA --output runs/energy_relay_benchmark/$TAG -- $RUNNER $ARGS 2>&1'" 2>&1 | grep -v "zle\|monitor\|gitstatus\|GITSTATUS\|exec zsh\|Add the following\|Restart Zsh\|^$"
