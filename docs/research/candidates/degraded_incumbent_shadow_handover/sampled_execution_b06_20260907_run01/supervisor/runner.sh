#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/dish_b06_seed113_20260907_run01/pid"
START_TS=$(date +%s)
echo "=== Task 'dish_b06_seed113_20260907_run01' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/dish_b06_seed113_20260907_run01/task.log"

# Execute command capturing output
set +e
eval $'export DISH_B06_CWD=/home/wu/hmasd-worktrees/dish-b06-seed113-20260907-run01\nexport DISH_B06_ENVELOPE="$DISH_B06_CWD/temp/directions/degraded_incumbent_shadow_handover/exp/sampled_execution_b06_seed113_20260907_run01"\nmkdir -p "$DISH_B06_ENVELOPE" &&\n/usr/bin/time -v -o "$DISH_B06_ENVELOPE/whole_chain.time.txt" \\\n  /usr/bin/timeout --signal=ALRM --kill-after=9s 1780s bash -lc \'\n    dish_b06_chain_started=$SECONDS\n    cd "$DISH_B06_CWD" &&\n    export PATH="/home/wu/.local/bin:/usr/lib/wsl/lib:$PATH" \\\n      PYTHONPATH="$DISH_B06_CWD" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \\\n      OPENBLAS_NUM_THREADS=1 MAX_JOBS=1 &&\n    /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py \\\n      admit-memory --out "$DISH_B06_ENVELOPE/admission.memory.json" &&\n    exec /home/wu/.venvs/hmasd/bin/python scripts/run_dish_sampled_execution_b06.py \\\n      --seed 113 --out "$DISH_B06_ENVELOPE/result" \\\n      --admission "$DISH_B06_ENVELOPE/admission.memory.json" \\\n      --prior-check-seconds "$((10 + SECONDS - dish_b06_chain_started + 1))"\n  \' > "$DISH_B06_ENVELOPE/stdout.log" 2> "$DISH_B06_ENVELOPE/stderr.log"' >> "/home/wu/.agent-tasks/dish_b06_seed113_20260907_run01/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/dish_b06_seed113_20260907_run01/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/dish_b06_seed113_20260907_run01/status"
else
    echo "failed" > "/home/wu/.agent-tasks/dish_b06_seed113_20260907_run01/status"
fi
echo "=== Task 'dish_b06_seed113_20260907_run01' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/dish_b06_seed113_20260907_run01/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
