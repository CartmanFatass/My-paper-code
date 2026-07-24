# Prefix-normalization G8 prototype screen

Date: 2026-07-23

```text
artifact=logs/nonformal_scale_normalized_g8_screen_20260723_pm1/screen_result.json
formal=false
branch=NONFORMAL_SCALE_NORMALIZATION_SCREEN_COMPLETE
backend=cpu
torch=2.7.0+cpu
torch_threads=1
variants=8
updates_per_variant=60
environments_per_update=4
evaluation_episodes_per_domain=32
conclusion_bearing_iteration_cost=0
```

## Closed prototype decision

All eight pre-registered combinations were finite, lifecycle-valid and had
maximum replay error zero. The frozen ranking rule selected:

```text
active_aggregation=sum
count_coordinate=log1p
autoregressive_prefix=active_fraction
active_fraction(action)=prefix_action_count/active_count
minimum_domain_mean=0.831787109375
runner_up_minimum_domain_mean=0.775390625
winner_margin=0.056396484375
```

The winner's deterministic domain means were IID `0.8464355`, held-out
`0.8317871`, moderate `0.8349609`, far `0.8559570` and joint `0.8391113`.
The exact G5 representation with raw prefix counts had minimum domain mean
`0.6823556`. The winner exceeds the runner-up by more than the registered
`0.01` simpler-preference margin, so no tie rule is invoked.

Mean aggregation harmed the short-budget learning slope, and a bounded count
coordinate did not improve the best minimum-domain score. They are removed
from the active implementation. This nonformal screen selects an engineering
candidate only; it is not evidence that raw prefix growth uniquely caused G7,
nor that the selected algorithm meets a formal usability gate.

```text
selected_algorithm=PREFIX_NORMALIZED_OPEN_ROSTER_G8
next_boundary=PREFIX_NORMALIZED_OPEN_ROSTER_G8_EXECUTABLE_DEFINITION
iterations_remaining=9
```
