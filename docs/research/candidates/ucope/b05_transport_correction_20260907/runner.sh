#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/ucope-shared-return-b05-seed6701-20260907/pid"
START_TS=$(date +%s)
echo "=== Task 'ucope-shared-return-b05-seed6701-20260907' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/ucope-shared-return-b05-seed6701-20260907/task.log"

# Execute command capturing output
set +e
eval '/usr/bin/time -f '\''whole_wall_seconds=%e peak_rss_kib=%M'\'' /usr/bin/timeout --signal=KILL 600s /bin/bash --noprofile --norc -c '\''cd /home/wu/hmasd-worktrees/ucope-shared-return-b04-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/shared-data-return-b05-seed6701/resource_admission.json && /home/wu/.venvs/hmasd/bin/python -c "from scripts.run_ucope_shared_data_return_model_b02 import run; import sys; raise SystemExit(run(sys.argv[1], seed=int(sys.argv[2]), object_id=sys.argv[3], batches=int(sys.argv[4])))" temp/directions/ucope/exp/shared-data-return-b05-seed6701 6701 UCOPE-SHARED-DATA-RETURN-MODEL-B05 512' >> "/home/wu/.agent-tasks/ucope-shared-return-b05-seed6701-20260907/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/ucope-shared-return-b05-seed6701-20260907/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/ucope-shared-return-b05-seed6701-20260907/status"
else
    echo "failed" > "/home/wu/.agent-tasks/ucope-shared-return-b05-seed6701-20260907/status"
fi
echo "=== Task 'ucope-shared-return-b05-seed6701-20260907' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/ucope-shared-return-b05-seed6701-20260907/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
