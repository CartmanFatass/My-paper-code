#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/vsp03-b03-p54-20260908/pid"
START_TS=$(date +%s)
echo "=== Task 'vsp03-b03-p54-20260908' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/vsp03-b03-p54-20260908/task.log"

# Execute command capturing output
set +e
eval $'cd /home/wu/hmasd-worktrees/vsp03-b03-p54-4eb8a36b9184633f5e28eff999a99f2dbc948040 || exit\nexport OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1\nexport VSP03_B03_COMMAND=\'VSP03_B03_STARTED=$(/home/wu/.venvs/hmasd/bin/python -c "import time; print(time.perf_counter())")\n/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b03_seed5_p54_20260908_admission.json && exec /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b03.py --seed 5 --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b03_seed5_p54_20260908 --started-monotonic "$VSP03_B03_STARTED" --node wsl_4070\'\nexec /usr/bin/time -f \'whole_wall_seconds=%e peak_rss_kib=%M\' /usr/bin/timeout --signal=KILL 120s bash -c "$VSP03_B03_COMMAND"' >> "/home/wu/.agent-tasks/vsp03-b03-p54-20260908/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/vsp03-b03-p54-20260908/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/vsp03-b03-p54-20260908/status"
else
    echo "failed" > "/home/wu/.agent-tasks/vsp03-b03-p54-20260908/status"
fi
echo "=== Task 'vsp03-b03-p54-20260908' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/vsp03-b03-p54-20260908/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
