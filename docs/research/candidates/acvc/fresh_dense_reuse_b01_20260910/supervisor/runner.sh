#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/acvc-fresh-dense-b01-8921-60d42dd73/pid"
START_TS=$(date +%s)
echo "=== Task 'acvc-fresh-dense-b01-8921-60d42dd73' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/acvc-fresh-dense-b01-8921-60d42dd73/task.log"

# Execute command capturing output
set +e
eval 'cd /home/wu/hmasd-worktrees/acvc-fresh-dense-b01-60d42dd73 && export HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= && /usr/bin/time -f '\''whole_command_wall_s=%e\npeak_rss_kib=%M\nexit_code=%x'\'' -o temp/directions/acvc/fresh_dense_reuse_b01_8921_task_time.txt timeout --signal=TERM --kill-after=1 327 bash scripts/run_acvc_fresh_dense_reuse_b01.sh 60d42dd739ef125a505772f2b1d698b099b43a16' >> "/home/wu/.agent-tasks/acvc-fresh-dense-b01-8921-60d42dd73/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/acvc-fresh-dense-b01-8921-60d42dd73/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/acvc-fresh-dense-b01-8921-60d42dd73/status"
else
    echo "failed" > "/home/wu/.agent-tasks/acvc-fresh-dense-b01-8921-60d42dd73/status"
fi
echo "=== Task 'acvc-fresh-dense-b01-8921-60d42dd73' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/acvc-fresh-dense-b01-8921-60d42dd73/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
