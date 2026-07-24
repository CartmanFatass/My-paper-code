# Continuous service roster G17 formal result

Date: 2026-07-24

The exact source `91f6cbb58dfacd7e30462828aeb301d9c96df9dd`
completed at
`logs/formal_continuous_service_roster_g17_cpu_20260724_91f6cbb_r1`.

```text
formal=true
backend=cpu
torch=2.7.0+cpu
torch_threads=1
replicates=3
updates_per_replicate=100
environments_per_update=8
ppo_passes=2
evaluation_cells=15
evaluation_utility_rows=1920
checkpoint_references=6/6_present
source_control_rows=10
maximum_replay_error=0.0
operational_valid=true
operational_errors=[]
branch=USABLE_ONE_STEP_CONTINUOUS_ROSTER_G17
```

The Project Manager independently closed all checkpoint references, evaluation
inventory, runtime/source identity, registered schedules and constructive
controls, then reproduced the frozen first-match branch.

```text
iid_deterministic_utility_ci95=[0.9486910209654903,0.951396353517726,0.9539132476867568]
heldout_deterministic_utility_ci95=[0.9372597817958475,0.9431132844133234,0.9474354622960345]
heldout_final_minus_zero_ci95=[0.30171233812718806,0.5464016693083042,0.7473720613733101]
minimum_heldout_replicate_mean=0.9366204591420624
heldout_stochastic_mean=0.8380883011546648
minimum_effort_correlation=0.9637707195047537
minimum_mix_correlation=0.9904293793182415
maximum_effort_mae=0.026173708121253487
maximum_mix_mae=0.018548222081638716
```

## Smallest scientific update

The capacity-generic active-set/lifecycle policy, an optional direct
current-observation residual, and objective-aligned one-step actor credit form a
usable continuous dynamic-roster controller on the registered immediate-service
source. The result separates the successful credit alignment from failed
exposure, exploration-scale, representation-only and curriculum variants.

This does not establish long-horizon credit, energy/battery planning, UAV radio
or motion control, S7-S1 performance, comparative advantage, asynchronous skill
lifetime or arbitrary roster processes. `gamma=0` is not promoted unchanged to
UAV merely because it passes this immediate source.

The nearest counterexample is a dynamic-roster continuous toy where present
effort changes later service availability, such as a small battery/charging
state. The next zero-compute derivation will isolate whether one-step TD credit
can carry that policy-dependent transition without reintroducing the unrelated
future-demand noise that defeated long GAE.

```text
conclusion_bearing_iteration=18
toy_first_chain_iterations_consumed=1
iterations_remaining_after_run=9
next_boundary=DELAYED_EFFECT_CONTINUOUS_ROSTER_G18_CREDIT_DERIVATION
```
