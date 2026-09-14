#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/vnfc-b03-credit-20260912-01/pid"
START_TS=$(date +%s)
echo "=== Task 'vnfc-b03-credit-20260912-01' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/vnfc-b03-credit-20260912-01/task.log"

# Execute command capturing output
set +e
eval $'cd /home/wu/hmasd-worktrees/vnfc-b03-credit-20260912-01 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/variable_n_fleet_churn/exp/b03_credit_20260912_01_memory.json && /usr/bin/time -f \'elapsed_seconds=%e\npeak_rss_kib=%M\nexit_status=%x\' -o temp/directions/variable_n_fleet_churn/exp/b03_credit_20260912_01_outer_time.txt /usr/bin/timeout --signal=TERM --kill-after=1s 600s /home/wu/.venvs/hmasd/bin/python scripts/run_vnfc_native_service_credit_b03.py --seed 2026091201 --eval-seed 2026091202 --out temp/directions/variable_n_fleet_churn/exp/b03_credit_20260912_01 --launch-sha b93329b3c44ea9d0cf5622c00f5ca6eea0740dac' >> "/home/wu/.agent-tasks/vnfc-b03-credit-20260912-01/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/vnfc-b03-credit-20260912-01/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/vnfc-b03-credit-20260912-01/status"
else
    echo "failed" > "/home/wu/.agent-tasks/vnfc-b03-credit-20260912-01/status"
fi
echo "=== Task 'vnfc-b03-credit-20260912-01' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/vnfc-b03-credit-20260912-01/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
