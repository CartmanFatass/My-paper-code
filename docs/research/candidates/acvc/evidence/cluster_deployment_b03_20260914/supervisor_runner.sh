#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/acvc-cluster-b03-091c6725b/pid"
START_TS=$(date +%s)
echo "=== Task 'acvc-cluster-b03-091c6725b' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/acvc-cluster-b03-091c6725b/task.log"

# Execute command capturing output
set +e
eval 'env HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 bash /home/wu/hmasd-worktrees/acvc-cluster-b03-091c6725b/experiments/candidates/acvc/cluster_deployment_b03/launch.sh 091c6725b149cd2dfa9665408cabee17b8f958e3 /home/wu/hmasd-worktrees/acvc-cluster-b03-091c6725b/temp/directions/acvc/exp/cluster_deployment_b03_20260914' >> "/home/wu/.agent-tasks/acvc-cluster-b03-091c6725b/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/acvc-cluster-b03-091c6725b/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/acvc-cluster-b03-091c6725b/status"
else
    echo "failed" > "/home/wu/.agent-tasks/acvc-cluster-b03-091c6725b/status"
fi
echo "=== Task 'acvc-cluster-b03-091c6725b' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/acvc-cluster-b03-091c6725b/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
