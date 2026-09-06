#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/vspc1_b01_factor_s0_e7e574b44_01/pid"
START_TS=$(date +%s)
echo "=== Task 'vspc1_b01_factor_s0_e7e574b44_01' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/vspc1_b01_factor_s0_e7e574b44_01/task.log"

# Execute command capturing output
set +e
eval 'cd /home/wu/hmasd-worktrees/vspc1-b01-e7e574b44 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/vspc1-b01-e7e574b44/temp/directions/vsp_c1/exp/k4_b01_factor_seed0_e7e574b44_01/admission.json && /usr/bin/time -v -o /home/wu/hmasd-worktrees/vspc1-b01-e7e574b44/temp/directions/vsp_c1/exp/k4_b01_factor_seed0_e7e574b44_01/invocation.time timeout --signal=TERM 2700s /home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_k4_factor_value_b01.py --arm FACTOR --seed 0 --out /home/wu/hmasd-worktrees/vspc1-b01-e7e574b44/temp/directions/vsp_c1/exp/k4_b01_factor_seed0_e7e574b44_01' >> "/home/wu/.agent-tasks/vspc1_b01_factor_s0_e7e574b44_01/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/vspc1_b01_factor_s0_e7e574b44_01/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/vspc1_b01_factor_s0_e7e574b44_01/status"
else
    echo "failed" > "/home/wu/.agent-tasks/vspc1_b01_factor_s0_e7e574b44_01/status"
fi
echo "=== Task 'vspc1_b01_factor_s0_e7e574b44_01' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/vspc1_b01_factor_s0_e7e574b44_01/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
