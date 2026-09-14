#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/acvc-fresh-dense-b01-8961-62d7eae7d/pid"
START_TS=$(date +%s)
echo "=== Task 'acvc-fresh-dense-b01-8961-62d7eae7d' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/acvc-fresh-dense-b01-8961-62d7eae7d/task.log"

# Execute command capturing output
set +e
eval 'cd /home/wu/hmasd-worktrees/acvc-fresh-dense-b01-8961-62d7eae7d && export HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= && /usr/bin/time -f '\''whole_command_wall_s=%e\npeak_rss_kib=%M\nexit_code=%x'\'' -o temp/directions/acvc/fresh_dense_reuse_b01_8961_task_time.txt timeout --signal=TERM --kill-after=1 267 bash scripts/run_acvc_fresh_dense_reuse_b01.sh 62d7eae7dedf5560171d636e845286108a4bc528' >> "/home/wu/.agent-tasks/acvc-fresh-dense-b01-8961-62d7eae7d/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/acvc-fresh-dense-b01-8961-62d7eae7d/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/acvc-fresh-dense-b01-8961-62d7eae7d/status"
else
    echo "failed" > "/home/wu/.agent-tasks/acvc-fresh-dense-b01-8961-62d7eae7d/status"
fi
echo "=== Task 'acvc-fresh-dense-b01-8961-62d7eae7d' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/acvc-fresh-dense-b01-8961-62d7eae7d/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
