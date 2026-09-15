#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/acvc-rate-ref-b01-27931-2bbaa99ad/pid"
START_TS=$(date +%s)
echo "=== Task 'acvc-rate-ref-b01-27931-2bbaa99ad' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/acvc-rate-ref-b01-27931-2bbaa99ad/task.log"

# Execute command capturing output
set +e
eval 'env HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 bash /home/wu/hmasd-worktrees/acvc-rate-pair-b01-2bbaa99ad/experiments/candidates/acvc/cluster_fixed_lr_pair_b01/launch.sh 2bbaa99ad9cc717d89e47a1f24d9acd76dce4f97 /home/wu/hmasd-worktrees/acvc-rate-pair-b01-2bbaa99ad/temp/directions/acvc/exp/cluster_fixed_lr_pair_b01_27931_reference reference' >> "/home/wu/.agent-tasks/acvc-rate-ref-b01-27931-2bbaa99ad/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/acvc-rate-ref-b01-27931-2bbaa99ad/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/acvc-rate-ref-b01-27931-2bbaa99ad/status"
else
    echo "failed" > "/home/wu/.agent-tasks/acvc-rate-ref-b01-27931-2bbaa99ad/status"
fi
echo "=== Task 'acvc-rate-ref-b01-27931-2bbaa99ad' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/acvc-rate-ref-b01-27931-2bbaa99ad/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
