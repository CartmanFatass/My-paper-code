#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/fsd_native_b03_p47_D0_f09aa00ba/pid"
START_TS=$(date +%s)
echo "=== Task 'fsd_native_b03_p47_D0_f09aa00ba' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/fsd_native_b03_p47_D0_f09aa00ba/task.log"

# Execute command capturing output
set +e
eval '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,exit_status=%x -o /home/wu/hmasd-inputs/fsd-native-renewal-b03-p47-20260908/D0_process_time.txt /usr/bin/timeout --signal=KILL 1200s /bin/bash /home/wu/hmasd-inputs/fsd-native-renewal-b03-p47-20260908/D0.sh' >> "/home/wu/.agent-tasks/fsd_native_b03_p47_D0_f09aa00ba/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/fsd_native_b03_p47_D0_f09aa00ba/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/fsd_native_b03_p47_D0_f09aa00ba/status"
else
    echo "failed" > "/home/wu/.agent-tasks/fsd_native_b03_p47_D0_f09aa00ba/status"
fi
echo "=== Task 'fsd_native_b03_p47_D0_f09aa00ba' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/fsd_native_b03_p47_D0_f09aa00ba/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
