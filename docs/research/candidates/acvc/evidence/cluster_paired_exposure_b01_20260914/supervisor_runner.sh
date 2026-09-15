#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/acvc-paired-exposure-b01-8fd41b61f/pid"
START_TS=$(date +%s)
echo "=== Task 'acvc-paired-exposure-b01-8fd41b61f' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/acvc-paired-exposure-b01-8fd41b61f/task.log"

# Execute command capturing output
set +e
eval 'env HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 bash /home/wu/hmasd-worktrees/acvc-paired-exposure-b01-8fd41b61f/experiments/candidates/acvc/cluster_paired_exposure_b01/launch.sh 8fd41b61f3c8d3c70057492a18e619ef0faeda78 /home/wu/hmasd-worktrees/acvc-paired-exposure-b01-8fd41b61f/temp/directions/acvc/exp/cluster_paired_exposure_b01_20260914' >> "/home/wu/.agent-tasks/acvc-paired-exposure-b01-8fd41b61f/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/acvc-paired-exposure-b01-8fd41b61f/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/acvc-paired-exposure-b01-8fd41b61f/status"
else
    echo "failed" > "/home/wu/.agent-tasks/acvc-paired-exposure-b01-8fd41b61f/status"
fi
echo "=== Task 'acvc-paired-exposure-b01-8fd41b61f' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/acvc-paired-exposure-b01-8fd41b61f/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
