#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/vspc1_b01_generic_s2_e2f00991f_01/pid"
START_TS=$(date +%s)
echo "=== Task 'vspc1_b01_generic_s2_e2f00991f_01' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/vspc1_b01_generic_s2_e2f00991f_01/task.log"

# Execute command capturing output
set +e
eval 'cd /home/wu/hmasd-worktrees/vspc1-b01-e2f00991f && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/vspc1-b01-e2f00991f/temp/directions/vsp_c1/exp/k4_b01_generic_seed2_e2f00991f_01/admission.json && /usr/bin/time -v -o /home/wu/hmasd-worktrees/vspc1-b01-e2f00991f/temp/directions/vsp_c1/exp/k4_b01_generic_seed2_e2f00991f_01/invocation.time timeout --signal=TERM 2700s /home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_k4_factor_value_b01.py --arm GENERIC --seed 2 --out /home/wu/hmasd-worktrees/vspc1-b01-e2f00991f/temp/directions/vsp_c1/exp/k4_b01_generic_seed2_e2f00991f_01' >> "/home/wu/.agent-tasks/vspc1_b01_generic_s2_e2f00991f_01/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/vspc1_b01_generic_s2_e2f00991f_01/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/vspc1_b01_generic_s2_e2f00991f_01/status"
else
    echo "failed" > "/home/wu/.agent-tasks/vspc1_b01_generic_s2_e2f00991f_01/status"
fi
echo "=== Task 'vspc1_b01_generic_s2_e2f00991f_01' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/vspc1_b01_generic_s2_e2f00991f_01/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
