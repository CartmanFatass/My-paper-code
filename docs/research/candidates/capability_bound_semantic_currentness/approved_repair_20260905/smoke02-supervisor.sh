#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/cbsc-approved-smoke-8003b96bd-02/pid"
START_TS=$(date +%s)
echo "=== Task 'cbsc-approved-smoke-8003b96bd-02' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/cbsc-approved-smoke-8003b96bd-02/task.log"

# Execute command capturing output
set +e
eval 'bash -lc '\''cd /home/wu/hmasd-worktrees/cbsc-approved-repair-8003b96bd-20260905 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/cbsc-approved-repair-8003b96bd-20260905/temp/directions/capability_bound_semantic_currentness/test/approved-repair/smoke-admission.json && /usr/bin/time -f '\''"'\''"'\''process_wall_seconds=%e peak_rss_kib=%M'\''"'\''"'\'' -o /home/wu/hmasd-worktrees/cbsc-approved-repair-8003b96bd-20260905/temp/directions/capability_bound_semantic_currentness/test/approved-repair/smoke-time.txt timeout -k 1s 58s /home/wu/.venvs/hmasd/bin/python -m pytest -q -s -p no:cacheprovider --maxfail=1 --basetemp /home/wu/hmasd-worktrees/cbsc-approved-repair-8003b96bd-20260905/temp/directions/capability_bound_semantic_currentness/test/approved-repair/smoke tests/experiments/candidates/capability_bound_semantic_currentness_omrc_b01/test_b1_metrics_production.py::test_unified_test_profile_runs_canonical_a_b_c_and_publishes_15_tables'\''' >> "/home/wu/.agent-tasks/cbsc-approved-smoke-8003b96bd-02/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/cbsc-approved-smoke-8003b96bd-02/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/cbsc-approved-smoke-8003b96bd-02/status"
else
    echo "failed" > "/home/wu/.agent-tasks/cbsc-approved-smoke-8003b96bd-02/status"
fi
echo "=== Task 'cbsc-approved-smoke-8003b96bd-02' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/cbsc-approved-smoke-8003b96bd-02/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
