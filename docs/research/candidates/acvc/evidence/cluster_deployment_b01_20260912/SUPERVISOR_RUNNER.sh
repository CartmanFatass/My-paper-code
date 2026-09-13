#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/acvc-cluster-b01-e06b3d63f/pid"
START_TS=$(date +%s)
echo "=== Task 'acvc-cluster-b01-e06b3d63f' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/acvc-cluster-b01-e06b3d63f/task.log"

# Execute command capturing output
set +e
eval 'cd /home/wu/hmasd-worktrees/acvc-cluster-b01-e06b3d63f && export HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= && /usr/bin/time -f '\''whole_command_wall_s=%e\npeak_rss_kib=%M\nexit_code=%x'\'' -o temp/directions/acvc/cluster_deployment_b01_task_time.txt timeout --signal=TERM --kill-after=1 595 bash experiments/candidates/acvc/cluster_deployment_b01/launch.sh e06b3d63f7e9f77c13fd327dba0270d80e74d819' >> "/home/wu/.agent-tasks/acvc-cluster-b01-e06b3d63f/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/acvc-cluster-b01-e06b3d63f/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/acvc-cluster-b01-e06b3d63f/status"
else
    echo "failed" > "/home/wu/.agent-tasks/acvc-cluster-b01-e06b3d63f/status"
fi
echo "=== Task 'acvc-cluster-b01-e06b3d63f' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/acvc-cluster-b01-e06b3d63f/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
