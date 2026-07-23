# Slot-layout invariance G11 prelaunch acceptance

Date: 2026-07-23

```text
focused_tests=6_passed
combined_g11_g5_tests=11_passed
backend=cpu
torch=2.7.0+cpu
torch_threads=1
nonformal_run=logs/nonformal_slot_layout_g11_20260723_pm2
nonformal_branch=NONFORMAL_SLOT_LAYOUT_G11_EXERCISE_COMPLETE
nonformal_operational_valid=true
nonformal_optimizer_steps=0
nonformal_evaluation_cells=8
nonformal_model_state_unchanged_exact=true
reverse48_paired_outcome_mismatch_count=0
sparse96_paired_outcome_mismatch_count=0
affine_padded128_paired_outcome_mismatch_count=0
```

All four layout source controls close: injective mappings, identical logical
wave arrivals, exact mapped priorities, roster schedules, demand, lifecycle
state and constructive utility one.

The earlier `pm1` diagnostic remapped stochastic uniforms by lifecycle key.
Code inspection showed that the actor consumes them by autoregressive token
position, explaining deterministic equality but stochastic mismatch. The
accepted source keeps the first 48 position draws fixed and pads only unused
positions. This repairs the paired control and does not change the policy,
environment, gate or result meaning.

## Formal boundary

After this note is integrated, resolve `<SOURCE_COMMIT>` and one fresh
`<RUN_ROOT>`, then assign the fixed Luna-low operator:

```powershell
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_slot_layout_g11.py train --run-root <RUN_ROOT> --source-commit <SOURCE_COMMIT> --formal --authorization-token AUTHORIZE_SLOT_LAYOUT_INVARIANCE_G11_FORMAL_CPU_V1 --g8-run-root logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1 --replicates 3 --eval-episodes 64
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_slot_layout_g11.py evaluate --run-root <RUN_ROOT>
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_slot_layout_g11.py analyze --run-root <RUN_ROOT>
```

Restart/resume are forbidden. A valid result consumes iteration 12.
