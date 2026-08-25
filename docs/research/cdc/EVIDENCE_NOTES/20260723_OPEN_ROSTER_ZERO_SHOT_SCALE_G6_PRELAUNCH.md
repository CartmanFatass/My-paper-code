# Open-roster zero-shot scale G6 prelaunch

Date: 2026-07-23

## Accepted realization

G6 adds an independent evaluation-only ledger/environment and runner. It does
not modify G5. The runner's ordered `train` phase validates and materializes the
three closed G5 final checkpoints, records zero optimizer steps and distinguishes
the G5 training source from the current G6 evaluation source. It then evaluates
count-scale, event-time and joint stress domains with model parameters exactly
unchanged.

The source retains Generic-SHORT reward, wave windows, actions, observations,
lifecycle ownership and the exact G5 count feature. Active count stops at 16;
capacity 20 is padding only. Expected short work is derived from actual wave
arrivals under each profile's membership times.

## Focused acceptance

```text
interpreter=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
backend=cpu
torch_threads=1
g6_focused_tests=7_passed
g6_plus_g5_focused_tests=12_passed
py_compile=passed
nonformal_run=logs/nonformal_open_roster_zero_shot_g6_20260723_pm2
nonformal_formal=false
nonformal_branch=NONFORMAL_OPEN_ROSTER_G6_EXERCISE_COMPLETE
nonformal_operational_valid=true
nonformal_optimizer_steps=0
nonformal_imported_replicates=1
nonformal_evaluation_cells=6
model_state_unchanged_exact=true
source_controls_all_pass=true
iteration_cost=0
iterations_remaining=11
```

The nonformal deterministic count-scale, event-time and joint CIs are each
`[1.0, 1.0, 1.0]`; joint stochastic mean is `0.9793894622`. These reduced
counts prove only path closure and are not conclusion-bearing.

One bounded advisory review found that the initial intake omitted the exact G5
formal authorization token. The repair now requires the token during intake,
records it in G6 provenance, rechecks it in analysis and rejects both missing
and wrong values. The same reviewer accepted that exact repair. No hash workflow
or compatibility path remains.

## Formal launch boundary

After Git integration, assign exactly one foreground
`train(import) -> evaluate -> analyze` sequence to the registered Luna-low
experiment operator:

```text
authorization_token=AUTHORIZE_OPEN_ROSTER_ZERO_SHOT_SCALE_G6_FORMAL_CPU_V1
source_commit=<integrated G6 commit>
g5_run=logs/formal_open_roster_direct_g5_cpu_20260723_4b38eae_r1
fresh_run=logs/formal_open_roster_zero_shot_g6_cpu_20260723_<short-commit>_r1
eval_episodes=128
replicates=3
cells=18
optimizer_steps=0
restart_policy=forbidden
```

A valid analysis consumes iteration 7 and requires the Chinese report before
the next automatic action. Formal compute is not executed by this prelaunch
acceptance.
