#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/vsp03-b05-p76-20260909/pid"
START_TS=$(date +%s)
echo "=== Task 'vsp03-b05-p76-20260909' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/vsp03-b05-p76-20260909/task.log"

# Execute command capturing output
set +e
eval '/home/wu/.venvs/hmasd/bin/python /home/wu/hmasd-worktrees/vsp03-b05-p76-32ce8a7355b86bee64956e3d24b76d01c31a8d77/experiments/candidates/vsp_03/vsp03_b04/deadline.py --start-monotonic 407907.852649 --cap 120.0 --reserve 10.0 --record /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b05_seed7_p76_20260909_terminal.payload.json -- bash -c '\''/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b05_seed7_p76_20260909_admission.json && exec /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b05.py --seed 7 --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b05_seed7_p76_20260909 --started-monotonic "$VSP03_B04_STARTED" --node wsl_4070'\''' >> "/home/wu/.agent-tasks/vsp03-b05-p76-20260909/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/vsp03-b05-p76-20260909/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/vsp03-b05-p76-20260909/status"
else
    echo "failed" > "/home/wu/.agent-tasks/vsp03-b05-p76-20260909/status"
fi
echo "=== Task 'vsp03-b05-p76-20260909' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/vsp03-b05-p76-20260909/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
