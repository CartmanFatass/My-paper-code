#!/usr/bin/env bash
echo $$ > "/home/wu/.agent-tasks/frrie-a04-system312-p11-d6844bb25f6f/pid"
START_TS=$(date +%s)
echo "=== Task 'frrie-a04-system312-p11-d6844bb25f6f' started at $(date -Iseconds) ===" >> "/home/wu/.agent-tasks/frrie-a04-system312-p11-d6844bb25f6f/task.log"

# Execute command capturing output
set +e
eval 'cd /home/wu/hmasd-worktrees/frrie-a04-d6844bb25f6f && timeout --signal=TERM --kill-after=5s 300s bash -c "export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1; /home/wu/.local/bin/uv venv --no-config --no-python-downloads --python /usr/bin/python3.12 /home/wu/.venvs/hmasd-frrie-system312-a04-20260907 && /home/wu/.local/bin/uv pip install --no-config --python /home/wu/.venvs/hmasd-frrie-system312-a04-20260907/bin/python --default-index https://pypi.org/simple --only-binary :all: --no-deps numpy==1.26.3 && /usr/bin/python3.12 scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/frrie-a04-d6844bb25f6f/temp/directions/finite_resource_relational_inductive_efficiency/technical/a04_system312_admission.json && /home/wu/.venvs/hmasd-frrie-system312-a04-20260907/bin/python -X faulthandler -m scripts.run_frrie_r09_tape_isolation_a03 --arm T0 --repeat 3 --updates 2 --eval-episodes 256 --out /home/wu/hmasd-worktrees/frrie-a04-d6844bb25f6f/temp/directions/finite_resource_relational_inductive_efficiency/exp/a04_system312 --launch-sha d6844bb25f6f1030aa7123467935861dcc719450 --admission-receipt /home/wu/hmasd-worktrees/frrie-a04-d6844bb25f6f/temp/directions/finite_resource_relational_inductive_efficiency/technical/a04_system312_admission.json"' >> "/home/wu/.agent-tasks/frrie-a04-system312-p11-d6844bb25f6f/task.log" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
echo $EXIT_CODE > "/home/wu/.agent-tasks/frrie-a04-system312-p11-d6844bb25f6f/exit_code"
if [ $EXIT_CODE -eq 0 ]; then
    echo "finished" > "/home/wu/.agent-tasks/frrie-a04-system312-p11-d6844bb25f6f/status"
else
    echo "failed" > "/home/wu/.agent-tasks/frrie-a04-system312-p11-d6844bb25f6f/status"
fi
echo "=== Task 'frrie-a04-system312-p11-d6844bb25f6f' exited with code $EXIT_CODE at $(date -Iseconds) (Duration: $((END_TS - START_TS))s) ===" >> "/home/wu/.agent-tasks/frrie-a04-system312-p11-d6844bb25f6f/task.log"

# Keep session alive briefly for inspection, then exit
sleep 1
