#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/fsd_native_b01_p38_C_b3f86bb28/pid"
START_TS=$(date +%s)
echo "=== Task 'fsd_native_b01_p38_C_b3f86bb28' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/fsd_native_b01_p38_C_b3f86bb28/task.log"

# Execute command capturing output
set +e
eval '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,exit_status=%x -o /home/wu/hmasd-inputs/fsd-native-renewal-b01-p38-20260908/C_process_time.txt /usr/bin/timeout --signal=KILL 900s /bin/bash /home/wu/hmasd-inputs/fsd-native-renewal-b01-p38-20260908/C.sh' >> "/home/wu/.agent-tasks/fsd_native_b01_p38_C_b3f86bb28/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/fsd_native_b01_p38_C_b3f86bb28/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/fsd_native_b01_p38_C_b3f86bb28/status"
else
    echo "failed" > "/home/wu/.agent-tasks/fsd_native_b01_p38_C_b3f86bb28/status"
fi
echo "=== Task 'fsd_native_b01_p38_C_b3f86bb28' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/fsd_native_b01_p38_C_b3f86bb28/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
