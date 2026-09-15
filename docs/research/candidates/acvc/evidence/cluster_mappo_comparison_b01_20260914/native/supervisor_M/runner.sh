#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/acvc-mappo-m-b01-28331-e4d3f324/pid"
START_TS=$(date +%s)
echo "=== Task 'acvc-mappo-m-b01-28331-e4d3f324' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/acvc-mappo-m-b01-28331-e4d3f324/task.log"

# Execute command capturing output
set +e
eval 'env HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 bash /home/wu/hmasd-worktrees/acvc-mappo-b01-e4d3f324e/experiments/candidates/acvc/cluster_mappo_comparison_b01/launch.sh e4d3f324ef2b233d0e97b347a5b94c9061ac6f52 /home/wu/hmasd-worktrees/acvc-mappo-b01-e4d3f324e/temp/directions/acvc/exp/cluster_mappo_comparison_b01_28331_M M /home/wu/hmasd-inputs/acvc-mappo-b01-28331/on-policy' >> "/home/wu/.agent-tasks/acvc-mappo-m-b01-28331-e4d3f324/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/acvc-mappo-m-b01-28331-e4d3f324/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/acvc-mappo-m-b01-28331-e4d3f324/status"
else
    echo "failed" > "/home/wu/.agent-tasks/acvc-mappo-m-b01-28331-e4d3f324/status"
fi
echo "=== Task 'acvc-mappo-m-b01-28331-e4d3f324' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/acvc-mappo-m-b01-28331-e4d3f324/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
