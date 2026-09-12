#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/acvc-training-use-b01-f-a4c24e4ee/pid"
START_TS=$(date +%s)
echo "=== Task 'acvc-training-use-b01-f-a4c24e4ee' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/acvc-training-use-b01-f-a4c24e4ee/task.log"

# Execute command capturing output
set +e
eval 'cd /home/wu/hmasd-worktrees/acvc-training-use-b01-a4c24e4ee && export HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= && /usr/bin/time -f '\''whole_command_wall_s=%e\npeak_rss_kib=%M\nexit_code=%x'\'' -o temp/directions/acvc/training_use_b01_F_task_time.txt timeout --signal=TERM --kill-after=1 267 bash experiments/candidates/acvc/training_use_b01/launch.sh a4c24e4eef4eb290d5026596a0a49ba4f4f9ce4f F' >> "/home/wu/.agent-tasks/acvc-training-use-b01-f-a4c24e4ee/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/acvc-training-use-b01-f-a4c24e4ee/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/acvc-training-use-b01-f-a4c24e4ee/status"
else
    echo "failed" > "/home/wu/.agent-tasks/acvc-training-use-b01-f-a4c24e4ee/status"
fi
echo "=== Task 'acvc-training-use-b01-f-a4c24e4ee' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/acvc-training-use-b01-f-a4c24e4ee/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
