#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/mgtap-cond-b01-8213-20260911/pid"
START_TS=$(date +%s)
echo "=== Task 'mgtap-cond-b01-8213-20260911' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/mgtap-cond-b01-8213-20260911/task.log"

# Execute command capturing output
set +e
eval 'bash /home/wu/hmasd-inputs/mgtap-cond-b01-8213-20260911/COMMAND.sh' >> "/home/wu/.agent-tasks/mgtap-cond-b01-8213-20260911/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/mgtap-cond-b01-8213-20260911/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/mgtap-cond-b01-8213-20260911/status"
else
    echo "failed" > "/home/wu/.agent-tasks/mgtap-cond-b01-8213-20260911/status"
fi
echo "=== Task 'mgtap-cond-b01-8213-20260911' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/mgtap-cond-b01-8213-20260911/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
