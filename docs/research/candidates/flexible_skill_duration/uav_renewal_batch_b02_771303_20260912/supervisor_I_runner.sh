#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/fsd-uav-renewal-batch-b02-771303-I-20260912/pid"
START_TS=$(date +%s)
echo "=== Task 'fsd-uav-renewal-batch-b02-771303-I-20260912' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/fsd-uav-renewal-batch-b02-771303-I-20260912/task.log"

# Execute command capturing output
set +e
eval '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,user_seconds=%U,system_seconds=%S,exit_status=%x -o /home/wu/hmasd-inputs/fsd-uav-renewal-batch-b02-771303-20260912/I_process_time.txt /usr/bin/timeout --signal=KILL 1800s /bin/bash /home/wu/hmasd-worktrees/fsd-uav-renewal-batch-b02-771303-20260912/docs/research/candidates/flexible_skill_duration/uav_renewal_batch_b02_771303_20260912/I.sh' >> "/home/wu/.agent-tasks/fsd-uav-renewal-batch-b02-771303-I-20260912/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/fsd-uav-renewal-batch-b02-771303-I-20260912/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/fsd-uav-renewal-batch-b02-771303-I-20260912/status"
else
    echo "failed" > "/home/wu/.agent-tasks/fsd-uav-renewal-batch-b02-771303-I-20260912/status"
fi
echo "=== Task 'fsd-uav-renewal-batch-b02-771303-I-20260912' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/fsd-uav-renewal-batch-b02-771303-I-20260912/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
