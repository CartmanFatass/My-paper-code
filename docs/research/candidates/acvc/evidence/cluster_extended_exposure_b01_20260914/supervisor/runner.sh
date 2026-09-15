#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/acvc-extended-b01-27457-66ea85e01/pid"
START_TS=$(date +%s)
echo "=== Task 'acvc-extended-b01-27457-66ea85e01' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/acvc-extended-b01-27457-66ea85e01/task.log"

# Execute command capturing output
set +e
eval 'env HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 bash /home/wu/hmasd-worktrees/acvc-extended-b01-66ea85e01/experiments/candidates/acvc/cluster_extended_exposure_b01/launch.sh 66ea85e0154e838ccb570eab81e2fecea8ff5973 /home/wu/hmasd-worktrees/acvc-extended-b01-66ea85e01/temp/directions/acvc/exp/cluster_extended_exposure_b01_27457' >> "/home/wu/.agent-tasks/acvc-extended-b01-27457-66ea85e01/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/acvc-extended-b01-27457-66ea85e01/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/acvc-extended-b01-27457-66ea85e01/status"
else
    echo "failed" > "/home/wu/.agent-tasks/acvc-extended-b01-27457-66ea85e01/status"
fi
echo "=== Task 'acvc-extended-b01-27457-66ea85e01' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/acvc-extended-b01-27457-66ea85e01/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
