#!/usr/bin/env bash
# Admission launches of the declared six-fit batch (cell 1, b01) on wsl_4070 at a published SHA.
# Issued FROM the WSL host (the script hops to the node; never run it on the node itself).
# The node control checkout only FETCHES origin/main (its HEAD and its foreign local edits are
# untouched): scripts/hmasd_launch.py --snapshot needs the published control head and the
# launch SHA as objects, then runs the runner from a locked worktree under .git/hmasd-launch-sources.
# Fresh node memory preflight (result_memory_floor_gib = 4), occupancy and duplicate-claim checks,
# detached supervisor. Recipe unchanged from the declaration: CPU float32, torch_threads 4,
# 45 rollouts, area 5000 m, declared dev/hold-out panels inside the runner.
#
# Usage:  launch_b01_fits.sh <full sha> <arm H|SET> <seed> [tag]
#   tag default: b01_fit_<arm>_<seed>_a01 ; output runs/coupled_host_joint_skills_stage1/<tag>
set -u
SHA="$1"; ARM="$2"; SEED="$3"; TAG="${4:-b01_fit_${ARM}_${SEED}_a01}"
RUNNER=experiments/candidates/coupled_host_joint_skills_stage1/runner.py
OUT=runs/coupled_host_joint_skills_stage1/$TAG
ssh -o BatchMode=yes -o ConnectTimeout=20 hmasd-wsl-node "zsh -lic 'cd /home/wu/projects/HMASD && timeout 120 git fetch -q --no-tags origin main $SHA 2>&1 | grep -v \"garbage found\|bad tree\|failed to run repack\"; git cat-file -e $SHA^{commit} || { echo SHA_NOT_FETCHED; exit 3; }; echo HEAD=\$(git rev-parse HEAD) LOAD=\$(cut -d\" \" -f1-3 /proc/loadavg); echo ---LAUNCH---; /home/wu/.venvs/hmasd/bin/python scripts/hmasd_launch.py launch --node wsl_4070 --source-root /home/wu/projects/HMASD --snapshot --direction coupled_host_joint_skills_stage1 --lead \"Claude DM (WSL session)\" --sha $SHA --output $OUT -- $RUNNER --arm $ARM --seed $SEED --launch-sha $SHA --area-size 5000 --out $OUT 2>&1'" 2>&1 | grep -v "zle\|monitor\|gitstatus\|GITSTATUS\|exec zsh\|Add the following\|Restart Zsh\|^$"
