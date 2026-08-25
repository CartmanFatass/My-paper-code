# Open-roster direct MVP G5 prelaunch

## Accepted implementation

The direct policy, recurrent replay and evaluation path now derive operational
roster width from the supplied batch. Model parameters remain independent of
capacity. The new task family trains on `3->2->4->3`, `4->2->6->4` and
`5->3->7->5`, then evaluates `6->2->8->4` and `7->4->9->6` under a larger
padding capacity.

Asynchronous skills, skill lifetime, EHC and intrinsic reward are absent. The
result can support only absolute dynamic-roster usability.

## Focused evidence

```text
tests=6_passed
interpreter=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
backend=cpu
torch_threads=1
exercise=logs/nonformal_open_roster_direct_g5_20260723_pm1
exercise_formal=false
exercise_branch=NONFORMAL_OPEN_ROSTER_G5_EXERCISE_COMPLETE
probe=logs/nonformal_open_roster_direct_g5_probe20_20260723_pm1
probe_updates=20
probe_iid_deterministic_utility=0.682373046875
probe_heldout_deterministic_utility=0.6054909446022727
probe_heldout_zero_utility=0.3560014204545454
maximum_replay_error=0.0
source_controls_constructive_utility_one=true
iteration_cost=0
iterations_remaining=8
```

The exercise proves command and artifact closure. The probe only establishes a
positive learning slope and motivates retaining the proven 250-update optimizer
exposure; neither artifact is conclusion-bearing.

## Formal launch boundary

The contract in `docs/research/designs/OPEN_ROSTER_DIRECT_MVP_G5.md` is frozen.
After Git integration, the registered `hmasd-experiment-operator` receives one
CPU one-thread foreground pipeline with the exact authorization token and fresh
run root. A valid analysis consumes iteration 6 and requires the Chinese report
before the next automatic iteration.
