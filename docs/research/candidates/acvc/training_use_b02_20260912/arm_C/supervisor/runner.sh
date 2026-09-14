#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/acvc-training-use-b02-c-ac64769f6/pid"
START_TS=$(date +%s)
echo "=== Task 'acvc-training-use-b02-c-ac64769f6' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/acvc-training-use-b02-c-ac64769f6/task.log"

# Execute command capturing output
set +e
eval 'cd /home/wu/hmasd-worktrees/acvc-training-use-b02-ac64769f6 && export HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= && /usr/bin/time -f '\''whole_command_wall_s=%e\npeak_rss_kib=%M\nexit_code=%x'\'' -o temp/directions/acvc/training_use_b02_C_task_time.txt timeout --signal=TERM --kill-after=1 267 bash experiments/candidates/acvc/training_use_b02/launch.sh ac64769f6403e4495a00673e2230d100edb7a02b C' >> "/home/wu/.agent-tasks/acvc-training-use-b02-c-ac64769f6/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/acvc-training-use-b02-c-ac64769f6/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/acvc-training-use-b02-c-ac64769f6/status"
else
    echo "failed" > "/home/wu/.agent-tasks/acvc-training-use-b02-c-ac64769f6/status"
fi
echo "=== Task 'acvc-training-use-b02-c-ac64769f6' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/acvc-training-use-b02-c-ac64769f6/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
