#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/ucope-shared-return-b05-seed6702-p12-lf-20260907/pid"
START_TS=$(date +%s)
echo "=== Task 'ucope-shared-return-b05-seed6702-p12-lf-20260907' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/ucope-shared-return-b05-seed6702-p12-lf-20260907/task.log"

# Execute command capturing output
set +e
eval '/bin/bash /home/wu/hmasd-inputs/ucope-b05-seed6702-command-20260907.sh' >> "/home/wu/.agent-tasks/ucope-shared-return-b05-seed6702-p12-lf-20260907/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/ucope-shared-return-b05-seed6702-p12-lf-20260907/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/ucope-shared-return-b05-seed6702-p12-lf-20260907/status"
else
    echo "failed" > "/home/wu/.agent-tasks/ucope-shared-return-b05-seed6702-p12-lf-20260907/status"
fi
echo "=== Task 'ucope-shared-return-b05-seed6702-p12-lf-20260907' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/ucope-shared-return-b05-seed6702-p12-lf-20260907/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
