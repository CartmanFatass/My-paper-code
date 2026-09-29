#!/usr/bin/env bash
# Admission launch of one P3 commitment collection (T4 collector) on wsl_4070 at a published SHA.
# Issued FROM the WSL host. Same mechanics as launch_b01_fits.sh (fetch-only, --snapshot).
# The checkpoint is passed RELATIVE to the checkout (runs/...): the collector resolves it against
# the checkout that holds runs/ (its docstring), records its sha256; frozen weights, zero optimizer steps.
#
# Usage:  launch_b01_collect.sh <full sha> <fit tag> <fit seed> [checkpoint index=45] [tag]
#   tag default: b01_p3_collect_<fit tag minus b01_fit_>_c<idx> ; output runs/coupled_host_joint_skills_stage1/<tag>
set -u
SHA="$1"; FIT="$2"; SEED="$3"; IDX="${4:-45}"; TAG="${5:-b01_p3_collect_${FIT#b01_fit_}_c${IDX}}"
RUNNER=experiments/candidates/coupled_host_joint_skills_stage1/collect_commitments.py
CKPT=runs/coupled_host_joint_skills_stage1/$FIT/checkpoint_$IDX.pt
OUT=runs/coupled_host_joint_skills_stage1/$TAG
ssh -o BatchMode=yes -o ConnectTimeout=20 hmasd-wsl-node "zsh -lic 'cd /home/wu/projects/HMASD && test -f $CKPT || { echo CHECKPOINT_ABSENT $CKPT; exit 4; }; sha256sum $CKPT; timeout 120 git fetch -q --no-tags origin main $SHA 2>&1 | grep -v \"garbage found\|bad tree\|failed to run repack\"; git cat-file -e $SHA^{commit} || { echo SHA_NOT_FETCHED; exit 3; }; echo HEAD=\$(git rev-parse HEAD) LOAD=\$(cut -d\" \" -f1-3 /proc/loadavg); echo ---LAUNCH---; /home/wu/.venvs/hmasd/bin/python scripts/hmasd_launch.py launch --node wsl_4070 --source-root /home/wu/projects/HMASD --snapshot --direction coupled_host_joint_skills_stage1 --lead \"Claude DM (WSL session)\" --sha $SHA --output $OUT -- $RUNNER --checkpoint $CKPT --seed $SEED --area-size 5000 --launch-sha $SHA --out $OUT 2>&1'" 2>&1 | grep -v "zle\|monitor\|gitstatus\|GITSTATUS\|exec zsh\|Add the following\|Restart Zsh\|^$"
