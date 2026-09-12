#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/acvc-fresh-dense-c01-18150-3fd9062d5/pid"
START_TS=$(date +%s)
echo "=== Task 'acvc-fresh-dense-c01-18150-3fd9062d5' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/acvc-fresh-dense-c01-18150-3fd9062d5/task.log"

# Execute command capturing output
set +e
eval 'cd /home/wu/hmasd-worktrees/acvc-fresh-dense-c01-3fd9062d5 && export HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= && /usr/bin/time -f '\''whole_command_wall_s=%e\npeak_rss_kib=%M\nexit_code=%x'\'' -o temp/directions/acvc/fresh_dense_package_c01_18150_task_time.txt timeout --signal=TERM --kill-after=1 267 bash experiments/candidates/acvc/fresh_dense_package_c01/launch.sh 3fd9062d5456a6b61a132a16ebd33a7099810143 18150' >> "/home/wu/.agent-tasks/acvc-fresh-dense-c01-18150-3fd9062d5/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/acvc-fresh-dense-c01-18150-3fd9062d5/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/acvc-fresh-dense-c01-18150-3fd9062d5/status"
else
    echo "failed" > "/home/wu/.agent-tasks/acvc-fresh-dense-c01-18150-3fd9062d5/status"
fi
echo "=== Task 'acvc-fresh-dense-c01-18150-3fd9062d5' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/acvc-fresh-dense-c01-18150-3fd9062d5/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
