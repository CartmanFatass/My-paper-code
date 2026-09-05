#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/cbsc-approved-repro-8003b96bd-03/pid"
START_TS=$(date +%s)
echo "=== Task 'cbsc-approved-repro-8003b96bd-03' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/cbsc-approved-repro-8003b96bd-03/task.log"

# Execute command capturing output
set +e
eval 'bash -lc '\''cd /home/wu/hmasd-worktrees/cbsc-approved-repair-8003b96bd-20260905 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/cbsc-approved-repair-8003b96bd-20260905/temp/directions/capability_bound_semantic_currentness/test/approved-repair/repro03-admission.json && CBSC_R05_FIXTURE=/home/wu/hmasd-inputs/cbsc-r07-resource-repair-20260904/snap_r05 CBSC_B0_FIXTURE=/home/wu/hmasd-worktrees/cbsc-approved-repair-8003b96bd-20260905/temp/directions/capability_bound_semantic_currentness/test/approved-repair/input-b0 /usr/bin/time -f '\''"'\''"'\''process_wall_seconds=%e peak_rss_kib=%M'\''"'\''"'\'' -o /home/wu/hmasd-worktrees/cbsc-approved-repair-8003b96bd-20260905/temp/directions/capability_bound_semantic_currentness/test/approved-repair/repro03-time.txt timeout -k 1s 181s /home/wu/.venvs/hmasd/bin/python -m pytest -q -s -p no:cacheprovider --maxfail=1 --basetemp /home/wu/hmasd-worktrees/cbsc-approved-repair-8003b96bd-20260905/temp/directions/capability_bound_semantic_currentness/test/approved-repair/repro03 tests/experiments/candidates/capability_bound_semantic_currentness_omrc_b01/test_b1_formal_path_repairs.py::test_r05_complete_formal_publication_preserves_original_receipts'\''' >> "/home/wu/.agent-tasks/cbsc-approved-repro-8003b96bd-03/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/cbsc-approved-repro-8003b96bd-03/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/cbsc-approved-repro-8003b96bd-03/status"
else
    echo "failed" > "/home/wu/.agent-tasks/cbsc-approved-repro-8003b96bd-03/status"
fi
echo "=== Task 'cbsc-approved-repro-8003b96bd-03' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/cbsc-approved-repro-8003b96bd-03/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
