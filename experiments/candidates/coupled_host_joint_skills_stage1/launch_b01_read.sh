#!/usr/bin/env bash
# Admission launch of one P3 interaction reading (T4 reader) on wsl_4070 at a published SHA.
# Issued FROM the WSL host; same mechanics as launch_b01_collect.sh. The table path is passed
# RELATIVE to the checkout (runs/...); the reader resolves it against the checkout holding runs/.
# Usage:  launch_b01_read.sh <full sha> <collection tag> [tag]
#   tag default: <collection tag with p3_collect -> p3_read>
set -u
SHA="$1"; COL="$2"; TAG="${3:-${COL/p3_collect/p3_read}}"
RUNNER=experiments/candidates/coupled_host_joint_skills_stage1/interaction_reader.py
TABLE=runs/coupled_host_joint_skills_stage1/$COL/commitments.npz
OUT=runs/coupled_host_joint_skills_stage1/$TAG
ssh -o BatchMode=yes -o ConnectTimeout=20 hmasd-wsl-node "zsh -lic 'cd /home/wu/projects/HMASD && test -f $TABLE || { echo TABLE_ABSENT $TABLE; exit 4; }; sha256sum $TABLE; timeout 120 git fetch -q --no-tags origin main $SHA 2>&1 | grep -v \"garbage found\|bad tree\|failed to run repack\"; git cat-file -e $SHA^{commit} || { echo SHA_NOT_FETCHED; exit 3; }; echo HEAD=\$(git rev-parse HEAD) LOAD=\$(cut -d\" \" -f1-3 /proc/loadavg); echo ---LAUNCH---; /home/wu/.venvs/hmasd/bin/python scripts/hmasd_launch.py launch --node wsl_4070 --source-root /home/wu/projects/HMASD --snapshot --direction coupled_host_joint_skills_stage1 --lead \"Claude DM (WSL session)\" --sha $SHA --output $OUT -- $RUNNER --table $TABLE --launch-sha $SHA --out $OUT 2>&1'" 2>&1 | grep -v "zle\|monitor\|gitstatus\|GITSTATUS\|exec zsh\|Add the following\|Restart Zsh\|^$"
