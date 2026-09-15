#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/acvc-cluster-b02-be76f696c-launch2/pid"
START_TS=$(date +%s)
echo "=== Task 'acvc-cluster-b02-be76f696c-launch2' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/acvc-cluster-b02-be76f696c-launch2/task.log"

# Execute command capturing output
set +e
eval 'cd /home/wu/hmasd-worktrees/acvc-cluster-b02-be76f696c && export HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= && /usr/bin/time -f '\''whole_command_wall_s=%e\npeak_rss_kib=%M\nexit_code=%x'\'' -o temp/directions/acvc/cluster_deployment_b02_task_time.txt timeout --signal=TERM --kill-after=1 595 bash experiments/candidates/acvc/cluster_deployment_b02/launch.sh be76f696cb773f2e5db8f4d55ebff1f3b6335ae6' >> "/home/wu/.agent-tasks/acvc-cluster-b02-be76f696c-launch2/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/acvc-cluster-b02-be76f696c-launch2/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/acvc-cluster-b02-be76f696c-launch2/status"
else
    echo "failed" > "/home/wu/.agent-tasks/acvc-cluster-b02-be76f696c-launch2/status"
fi
echo "=== Task 'acvc-cluster-b02-be76f696c-launch2' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/acvc-cluster-b02-be76f696c-launch2/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
