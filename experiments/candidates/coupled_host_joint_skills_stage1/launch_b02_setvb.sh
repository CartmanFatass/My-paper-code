#!/usr/bin/env bash
# Admission launch of the declared b02 SET-V-b fit (coupled_host_bounded_head_substrate, NOTES
# 2026-09-29 16:12 UTC) on wsl_4070 at a published SHA. Same mechanics as launch_b01_fits.sh
# (issued FROM the WSL host; the node checkout only fetches; --snapshot worktree). Recipe = the b01
# SET per-step recipe with only the native bounded action head changed (tanh_gaussian, log-std
# init -1, clamp [-5, 0]); seed 932201; 360k team steps; cap 5.0 CPU-h.
#
# Usage:  launch_b02_setvb.sh <full sha> [tag]      tag default: b02_fit_SETVb_932201_a01
set -u
SHA="$1"; TAG="${2:-b02_fit_SETVb_932201_a01}"; ARM=SET; SEED=932201
RUNNER=experiments/candidates/coupled_host_joint_skills_stage1/runner.py
OUT=runs/coupled_host_joint_skills_stage1/$TAG
HEAD_FLAGS="--continuous-action-distribution tanh_gaussian --continuous-logstd-init -1.0 --continuous-logstd-min -5.0 --continuous-logstd-max 0.0"
ssh -o BatchMode=yes -o ConnectTimeout=20 hmasd-wsl-node "zsh -lic 'cd /home/wu/projects/HMASD && timeout 120 git fetch -q --no-tags origin main $SHA 2>&1 | grep -v \"garbage found\|bad tree\|failed to run repack\"; git cat-file -e $SHA^{commit} || { echo SHA_NOT_FETCHED; exit 3; }; echo HEAD=\$(git rev-parse HEAD) LOAD=\$(cut -d\" \" -f1-3 /proc/loadavg); echo ---LAUNCH---; /home/wu/.venvs/hmasd/bin/python scripts/hmasd_launch.py launch --node wsl_4070 --source-root /home/wu/projects/HMASD --snapshot --direction coupled_host_joint_skills_stage1 --lead \"Claude DM (WSL session)\" --sha $SHA --output $OUT -- $RUNNER --arm $ARM --seed $SEED --launch-sha $SHA --area-size 5000 --contract step $HEAD_FLAGS --out $OUT 2>&1'" 2>&1 | grep -v "zle\|monitor\|gitstatus\|GITSTATUS\|exec zsh\|Add the following\|Restart Zsh\|^$"
