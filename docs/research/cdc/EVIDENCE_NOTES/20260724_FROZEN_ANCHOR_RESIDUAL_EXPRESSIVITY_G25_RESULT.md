# Frozen-anchor local residual expressivity G25 result

Date: 2026-07-24

## Evidence identity

```text
source_commit=b8b18dc1980a617f21b156e565be2a9506dacac1
run=logs/nonformal_frozen_anchor_residual_expressivity_g25_20260724_b8b18dc_pm1
formal=false
iteration_consumed=false
status=COMPLETE
branch=NO_POINTWISE_LOCAL_RESIDUAL_FIT_G25
runtime=cpu, torch 2.7.0+cpu, one thread
```

The registered operator completed train, evaluate and branch recomputation with
zero exits. The G18 information gate, all 36 constructive rows, three slot
orders, all twelve time steps, lifecycle schedule, inactive targets/actions,
finite updates and residual-only optimizer ownership close exactly. Replay
error and frozen-anchor difference are both `0.0`.

## Registered evidence

```text
initial_active_action_mse=1.4311925173
final_active_action_mse=0.3735838234
final_to_initial_ratio=0.2610297489
absolute_gate=0.001
relative_gate=0.10
fast_anchor_utility=0.6667880132
final_utility=0.6435695264
gain_over_anchor=-0.0232184868
final_spike_utility=0.8240061485
final_rotating_effort_share=0.8099307853
```

The pointwise branch precedes closed-loop diagnostics, so the nonformal result
is exactly `NO_POINTWISE_LOCAL_RESIDUAL_FIT_G25`. The probe establishes neither
a formal failure nor a learned-algorithm result and consumes no conclusion-
bearing iteration.

## Scientific effect

G23's near-threshold PPO behavior did not prove that its local
`[candidate, prefix, observation]` residual could fit the constructive delayed
mapping. Under the accepted representation measurement it cannot. Longer fit,
new optimizer, relaxed MSE, changed labels or extra seeds would rescue the
closed probe and are not selected.

G23 and G24 nevertheless isolate two complementary inputs. G23 retained the
autoregressive prefix and approached the spike gate while receiving peer-set
information only through the frozen candidate. G24 read direct actor-set
context but removed the prefix and collapsed to zero spike service. The
smallest new representation is therefore direct anonymous set context plus the
current prefix in one routed residual. It must pass the same expressivity gate
before any PPO screen.
