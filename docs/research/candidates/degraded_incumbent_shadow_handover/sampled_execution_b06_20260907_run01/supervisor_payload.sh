dish_b06_command=$(cat <<'DISH_B06_COMMAND'
export DISH_B06_CWD=/home/wu/hmasd-worktrees/dish-b06-seed113-20260907-run01
export DISH_B06_ENVELOPE="$DISH_B06_CWD/temp/directions/degraded_incumbent_shadow_handover/exp/sampled_execution_b06_seed113_20260907_run01"
mkdir -p "$DISH_B06_ENVELOPE" &&
/usr/bin/time -v -o "$DISH_B06_ENVELOPE/whole_chain.time.txt" \
  /usr/bin/timeout --signal=ALRM --kill-after=9s 1780s bash -lc '
    dish_b06_chain_started=$SECONDS
    cd "$DISH_B06_CWD" &&
    export PATH="/home/wu/.local/bin:/usr/lib/wsl/lib:$PATH" \
      PYTHONPATH="$DISH_B06_CWD" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
      OPENBLAS_NUM_THREADS=1 MAX_JOBS=1 &&
    /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py \
      admit-memory --out "$DISH_B06_ENVELOPE/admission.memory.json" &&
    exec /home/wu/.venvs/hmasd/bin/python scripts/run_dish_sampled_execution_b06.py \
      --seed 113 --out "$DISH_B06_ENVELOPE/result" \
      --admission "$DISH_B06_ENVELOPE/admission.memory.json" \
      --prior-check-seconds "$((10 + SECONDS - dish_b06_chain_started + 1))"
  ' > "$DISH_B06_ENVELOPE/stdout.log" 2> "$DISH_B06_ENVELOPE/stderr.log"
DISH_B06_COMMAND
)
/usr/local/bin/agent-task run dish_b06_seed113_20260907_run01 "$dish_b06_command"
