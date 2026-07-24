# Actor/critic-isolated G18 formal prelaunch

Date: 2026-07-24

The bounded formal-path exercise completed at source commit
`712cbd089dc6fd4c16a6eaa558d68f5b8fc97d98`:

```text
run=logs/nonformal_critic_isolated_g18_formal_path_20260724_712cbd0_pm1
formal=false
backend=cpu
torch=2.7.0+cpu
torch_threads=1
status=COMPLETE
operational_valid=true
maximum_replay_error=0.0
branch=NONFORMAL_CRITIC_ISOLATED_FORMAL_PATH_EXERCISE_COMPLETE
```

Training, evaluation and analysis exited successfully. Both source lifecycles,
inactive action zero, parameter movement, checkpoints, runtime identity and
artifact binding closed. Re-running the analyzer with `--require-formal`
returned the expected direct `ValueError: formal analysis requires formal
artifacts`; the exercise cannot be accepted as conclusion-bearing evidence.

The formal algorithm, sources, seeds, budgets, thresholds, branch precedence
and authorization token remain exactly those frozen in
`ACTOR_CRITIC_ISOLATED_CHANNEL_CREDIT_G18.md`. Formal iteration 19 is ready for
one registered CPU/one-thread operator run. No scientific iteration has yet
been consumed by the G18 preparation or screens.
