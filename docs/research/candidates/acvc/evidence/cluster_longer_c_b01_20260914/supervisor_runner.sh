#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/acvc-longer-c-b01-914a3d0e7/pid"
START_TS=$(date +%s)
echo "=== Task 'acvc-longer-c-b01-914a3d0e7' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/acvc-longer-c-b01-914a3d0e7/task.log"

# Execute command capturing output
set +e
eval 'env HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 bash /home/wu/hmasd-worktrees/acvc-longer-c-b01-914a3d0e7/experiments/candidates/acvc/cluster_longer_c_b01/launch.sh 914a3d0e78d49d385c54aaec0776ead63712b624 /home/wu/hmasd-worktrees/acvc-longer-c-b01-914a3d0e7/temp/directions/acvc/exp/cluster_longer_c_b01_20260914' >> "/home/wu/.agent-tasks/acvc-longer-c-b01-914a3d0e7/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/acvc-longer-c-b01-914a3d0e7/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/acvc-longer-c-b01-914a3d0e7/status"
else
    echo "failed" > "/home/wu/.agent-tasks/acvc-longer-c-b01-914a3d0e7/status"
fi
echo "=== Task 'acvc-longer-c-b01-914a3d0e7' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/acvc-longer-c-b01-914a3d0e7/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
