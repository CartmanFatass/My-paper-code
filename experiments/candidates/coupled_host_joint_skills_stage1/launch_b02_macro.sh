#!/usr/bin/env bash
# Admission launch of a b02 macro-step fit or probe (T-W contracts) on wsl_4070 at a published SHA.
# Same mechanics as launch_b01_fits.sh (issued FROM the WSL host; node checkout only fetches;
# --snapshot worktree). The bounded action head (tanh_gaussian, init -1, clamp [-5, 0]) is fixed here:
# every b02 arm uses it. Menus are cached under runs/<direction>/menus on the node (target contract
# needs none).
#
# Usage:  launch_b02_macro.sh <full sha> <arm H|SET> <seed> <contract target|slot|offset> <fit|probe> [tag]
#   tag default: b02_<fit|probe>_<ARM>T_<seed>_a01 (T for target; S for slot; O for offset)
#   EXTRA_FLAGS (env, default empty) is appended to the runner argv, e.g. EXTRA_FLAGS="--lambda-l 0".
set -u
SHA="$1"; ARM="$2"; SEED="$3"; CONTRACT="$4"; MODE="$5"
case "$CONTRACT" in target) C=T;; slot) C=S;; offset) C=O;; *) echo "bad contract"; exit 2;; esac
TAG="${6:-b02_${MODE}_${ARM}${C}_${SEED}_a01}"
PROBE=""; [ "$MODE" = probe ] && PROBE="--probe"
RUNNER=experiments/candidates/coupled_host_joint_skills_stage1/runner.py
OUT=runs/coupled_host_joint_skills_stage1/$TAG
HEAD_FLAGS="--continuous-action-distribution tanh_gaussian --continuous-logstd-init -1.0 --continuous-logstd-min -5.0 --continuous-logstd-max 0.0"
EXTRA_FLAGS="${EXTRA_FLAGS:-}"
ssh -o BatchMode=yes -o ConnectTimeout=20 hmasd-wsl-node "zsh -lic 'cd /home/wu/projects/HMASD && timeout 120 git fetch -q --no-tags origin main $SHA 2>&1 | grep -v \"garbage found\|bad tree\|failed to run repack\"; git cat-file -e $SHA^{commit} || { echo SHA_NOT_FETCHED; exit 3; }; echo HEAD=\$(git rev-parse HEAD) LOAD=\$(cut -d\" \" -f1-3 /proc/loadavg); echo ---LAUNCH---; /home/wu/.venvs/hmasd/bin/python scripts/hmasd_launch.py launch --node wsl_4070 --source-root /home/wu/projects/HMASD --snapshot --direction coupled_host_joint_skills_stage1 --lead \"Claude DM (WSL session)\" --sha $SHA --output $OUT -- $RUNNER --arm $ARM --seed $SEED --launch-sha $SHA --area-size 5000 --contract $CONTRACT $HEAD_FLAGS $EXTRA_FLAGS $PROBE --menu-dir runs/coupled_host_joint_skills_stage1/menus --out $OUT 2>&1'" 2>&1 | grep -v "zle\|monitor\|gitstatus\|GITSTATUS\|exec zsh\|Add the following\|Restart Zsh\|^$"
