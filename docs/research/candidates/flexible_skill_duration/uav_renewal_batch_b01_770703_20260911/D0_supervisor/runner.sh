#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/fsd-uav-renewal-batch-b01-770703-D0-20260911/pid"
START_TS=$(date +%s)
echo "=== Task 'fsd-uav-renewal-batch-b01-770703-D0-20260911' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/fsd-uav-renewal-batch-b01-770703-D0-20260911/task.log"

# Execute command capturing output
set +e
eval '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,user_seconds=%U,system_seconds=%S,exit_status=%x -o /home/wu/hmasd-inputs/fsd-uav-renewal-batch-b01-770703-20260911/D0_process_time.txt /usr/bin/timeout --signal=KILL 900s /bin/bash /home/wu/hmasd-worktrees/fsd-uav-renewal-batch-b01-770703-20260911/docs/research/candidates/flexible_skill_duration/uav_renewal_batch_b01_770703_20260911/D0.sh' >> "/home/wu/.agent-tasks/fsd-uav-renewal-batch-b01-770703-D0-20260911/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/fsd-uav-renewal-batch-b01-770703-D0-20260911/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/fsd-uav-renewal-batch-b01-770703-D0-20260911/status"
else
    echo "failed" > "/home/wu/.agent-tasks/fsd-uav-renewal-batch-b01-770703-D0-20260911/status"
fi
echo "=== Task 'fsd-uav-renewal-batch-b01-770703-D0-20260911' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/fsd-uav-renewal-batch-b01-770703-D0-20260911/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
