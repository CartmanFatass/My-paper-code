# Beyond-declared-count G7 prelaunch

Date: 2026-07-23

## Accepted realization

The active G6 module, runner and test are removed; Git history at the G6 source
commit is their archive. The G7 replacements preserve the repaired G5
checkpoint intake and replace only the stress profiles, registered seeds,
result semantics and active-count validation.

The inherited count feature is not clipped or renormalized. At N=40 it equals
`1.3107280023564027`, so the new path truly evaluates outside the declared
N=16 normalization range. Generic-SHORT reward, observations, wave windows,
primitive actions, lifecycle ownership and model weights remain unchanged.

## Focused acceptance

```text
interpreter=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
backend=cpu
torch_threads=1
g7_focused_tests=7_passed
g7_plus_g5_focused_tests=12_passed
py_compile=passed
old_g6_active_files=absent
new_g7_active_files=present
nonformal_run=logs/nonformal_open_roster_beyond_count_g7_20260723_g7impl_r1
nonformal_formal=false
nonformal_branch=NONFORMAL_BEYOND_DECLARED_COUNT_G7_EXERCISE_COMPLETE
nonformal_operational_valid=true
nonformal_optimizer_steps=0
nonformal_imported_replicates=1
nonformal_evaluation_cells=6
model_state_unchanged_exact=true
source_controls_all_pass=true
iteration_cost=0
iterations_remaining=10
```

The four-episode nonformal means are `0.9868750` moderate,
`0.97086797` far and `0.98314089` joint deterministic; joint stochastic is
`0.94170358`. They demonstrate path closure only and cannot bear a conclusion.

No conclusion-bearing anomaly appeared after the previously reviewed G6 intake
was carried forward. Under the proof-sized review policy, no additional
advisory review is added.

## Formal launch boundary

After Git integration, assign one exact CPU foreground pipeline to the fixed
Luna-low experiment operator:

```text
authorization_token=AUTHORIZE_BEYOND_DECLARED_COUNT_G7_FORMAL_CPU_V1
source_commit=<integrated G7 commit>
g5_run=logs/formal_open_roster_direct_g5_cpu_20260723_4b38eae_r1
fresh_run=logs/formal_beyond_declared_count_g7_cpu_20260723_<short-commit>_r1
eval_episodes=128
replicates=3
cells=18
optimizer_steps=0
restart_policy=forbidden
```

A valid result consumes iteration 8 and leaves nine rounds. Formal compute is
not launched by this prelaunch acceptance.
