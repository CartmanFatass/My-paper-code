# G18 one-step TD compatibility implementation plan

> Use `$hmasd-agile-research-development`. Generic Superpowers execution,
> compatibility work, workflow hashes and review stacks are disabled.

```text
active_implementation=ONE_STEP_TD_BOOTSTRAP_G18_COMPATIBILITY_SCREEN
derivation=docs/research/cdc/EVIDENCE_NOTES/20260724_DELAYED_EFFECT_CONTINUOUS_ROSTER_G18_DERIVATION.md
status=IMPLEMENTED_9_FOCUSED_TESTS_PASS_SCREEN_READY
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal_iteration=none
iterations_remaining=9
formal_compute=not_running
```

## Minimal code delta

1. `gae_lambda` is exposed in the existing continuous-roster PPO update; its
   default remains unchanged and G17's integrated formal source is preserved by
   Git identity.
2. A standalone tensor proof verifies that `lambda=0, gamma>0` uses exactly the
   next-state value and no later TD carry.
3. The small G18 screen analyzer imports only the accepted G17 policy/source
   and generic training functions, uses fresh G18 seeds, trains one fresh model,
   and writes one nonformal result plus checkpoint.
4. Nine focused tests pass, including custom credit/checkpoint round-trip and
   candidate selection. The next action is exactly one bounded CPU screen
   through the fixed experiment operator.

No UAV environment, radio, motion, charging-station, reward, checkpoint or
formal artifact is imported. A passing screen advances to a fresh delayed
battery/charging toy definition. A failing screen retires TD(0) without tuning.
