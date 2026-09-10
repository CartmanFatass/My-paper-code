#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/vsp03-b04-p64-20260908/pid"
START_TS=$(date +%s)
echo "=== Task 'vsp03-b04-p64-20260908' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/vsp03-b04-p64-20260908/task.log"

# Execute command capturing output
set +e
eval '/home/wu/.venvs/hmasd/bin/python /home/wu/hmasd-worktrees/vsp03-b04-p64-b5d605bf4f39b5ab18f01c98e04dc07e53764354/experiments/candidates/vsp_03/vsp03_b04/deadline.py --start-monotonic 375534.924519 --cap 120.0 --reserve 10.0 --record /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p64_20260908_terminal.payload.json -- bash -c '\''/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p64_20260908_admission.json && exec /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b04.py --seed 6 --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p64_20260908 --started-monotonic "$VSP03_B04_STARTED" --node wsl_4070'\''' >> "/home/wu/.agent-tasks/vsp03-b04-p64-20260908/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/vsp03-b04-p64-20260908/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/vsp03-b04-p64-20260908/status"
else
    echo "failed" > "/home/wu/.agent-tasks/vsp03-b04-p64-20260908/status"
fi
echo "=== Task 'vsp03-b04-p64-20260908' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/vsp03-b04-p64-20260908/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
