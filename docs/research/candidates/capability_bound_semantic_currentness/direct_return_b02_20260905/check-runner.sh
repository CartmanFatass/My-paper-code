#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/cbsc-direct-b02-2c9254f70-check/pid"
START_TS=$(date +%s)
echo "=== Task 'cbsc-direct-b02-2c9254f70-check' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/cbsc-direct-b02-2c9254f70-check/task.log"

# Execute command capturing output
set +e
eval 'bash -lc '\''/usr/bin/time -f '\''"'\''"'\''process_wall_seconds=%e peak_rss_kib=%M'\''"'\''"'\'' -o /home/wu/hmasd-worktrees/cbsc-direct-return-b02-2c9254f70-20260905/temp/directions/capability_bound_semantic_currentness/test/cbsc_direct_return_b02_2c9254f70/check-time.txt timeout -k 2s 173s bash -lc '\''"'\''"'\''cd /home/wu/hmasd-worktrees/cbsc-direct-return-b02-2c9254f70-20260905 && export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/cbsc-direct-return-b02-2c9254f70-20260905/temp/directions/capability_bound_semantic_currentness/test/cbsc_direct_return_b02_2c9254f70/check-admission.json && /home/wu/.venvs/hmasd/bin/python -m pytest -q -s -p no:cacheprovider --maxfail=1 --basetemp /home/wu/hmasd-worktrees/cbsc-direct-return-b02-2c9254f70-20260905/temp/directions/capability_bound_semantic_currentness/test/cbsc_direct_return_b02_2c9254f70/focused tests/experiments/candidates/capability_bound_semantic_currentness_omrc_b01/test_direct_return_b02.py::test_two_arm_real_update_native_return_and_paired_readback'\''"'\''"'\'''\''' >> "/home/wu/.agent-tasks/cbsc-direct-b02-2c9254f70-check/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/cbsc-direct-b02-2c9254f70-check/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/cbsc-direct-b02-2c9254f70-check/status"
else
    echo "failed" > "/home/wu/.agent-tasks/cbsc-direct-b02-2c9254f70-check/status"
fi
echo "=== Task 'cbsc-direct-b02-2c9254f70-check' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/cbsc-direct-b02-2c9254f70-check/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
