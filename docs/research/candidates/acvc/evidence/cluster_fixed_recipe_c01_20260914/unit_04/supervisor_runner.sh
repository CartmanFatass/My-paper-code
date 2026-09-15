#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/acvc-fixed-recipe-c01-u04-6e8d1b894/pid"
START_TS=$(date +%s)
echo "=== Task 'acvc-fixed-recipe-c01-u04-6e8d1b894' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/acvc-fixed-recipe-c01-u04-6e8d1b894/task.log"

# Execute command capturing output
set +e
eval 'env HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 bash /home/wu/hmasd-worktrees/acvc-fixed-recipe-c01-6e8d1b894/experiments/candidates/acvc/cluster_fixed_recipe_c01/launch.sh 6e8d1b8946e1b2eb0e4207cbc9cc9d006ad2abda 4' >> "/home/wu/.agent-tasks/acvc-fixed-recipe-c01-u04-6e8d1b894/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/acvc-fixed-recipe-c01-u04-6e8d1b894/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/acvc-fixed-recipe-c01-u04-6e8d1b894/status"
else
    echo "failed" > "/home/wu/.agent-tasks/acvc-fixed-recipe-c01-u04-6e8d1b894/status"
fi
echo "=== Task 'acvc-fixed-recipe-c01-u04-6e8d1b894' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/acvc-fixed-recipe-c01-u04-6e8d1b894/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
