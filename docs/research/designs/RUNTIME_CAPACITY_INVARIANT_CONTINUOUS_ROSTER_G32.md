# Runtime-capacity-invariant continuous roster G32

```text
status=PM_ACCEPTED_IMPLEMENTATION_PENDING_INTEGRATED_NONFORMAL
algorithm=RUNTIME_CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32
environment=toy
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal=false
conclusion_bearing=false
iterations_remaining=14
```

## Scientific question

Can a fresh G31-style continuous policy keep one strict-loadable checkpoint
across different operational member capacities while retaining within-episode
temporary leave, rejoin, fresh join, terminal leave and continuous allocation?

Success is limited to the registered capacity-6/8/12 toy family. It does not
establish arbitrary fleet size, UAV transport, comparative advantage or a new
claim about delayed reward attribution.

## Single algorithmic delta

Preserve G31's actor, realized future-tail target, direction-balanced gradient
composition, PPO, recurrent lifecycle state, active-set sum, raw log-count and
active-fraction prefix. Remove maximum padding capacity from value parameters:

```text
base_critic_input=context_input+critic_state
slow_critic_input=critic_state+log1p(active_count)
padded_active_mask_as_critic_input=forbidden
capacity_in_parameter_shape=forbidden
```

`member_capacity` remains local runtime packing metadata. It may control tensor
validation and loop length but is absent from state-dict keys and shapes. No
checkpoint adapter, tensor slicing, key remapping or compatibility reader is
allowed.

## Capacity-independent toy source

The new source retains the 48-step, two-coordinate continuous-service task and
events at steps 12, 24 and 36. Each active member observes its two capability
coordinates, anonymous current priority, load, target mix,
`log1p(active_count)`, lifecycle age, two previous actions and normalized time.
The fixed-width critic state is load, target mix, two active capability sums,
`log1p(active_count)` and normalized time.

No field is divided by maximum capacity. Ledgers generate active lifecycle data
by stable episode/member identities so adding permanently inactive padding does
not shift any RNG draw or active value. Reward, action support and constructive
allocation remain the G17 continuous-service semantics.

Registered profiles are:

```text
train_capacity_8=(4->3->6->5,5->3->7->6,6->4->8->6)
padding_pair_capacity_8=(4->3->6->5)
padding_pair_capacity_12=(4->3->6->5 plus four never-active slots)
small_capacity_6=(4->2->6->3)
large_capacity_12=(6->3->10->7)
```

All profiles contain temporary leave, rejoin plus fresh join, and terminal
leave. Empty rosters and count/capacity overflow fail closed.

## Training and evaluation identity

All checkpoints are fresh. Training occurs only at capacity 8. Each final
state is strict-loaded into new capacity-6, capacity-8 and capacity-12 model
instances. Evaluation performs zero optimizer steps, and the exact state dict
before and after every cell must match.

The formal schedule, if the bounded package passes, is:

```text
authorization_token=AUTHORIZE_RUNTIME_CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32_FORMAL_CPU_V1
replicates=3
fast_updates=100
return_to_go_updates=100
environments_per_update=8
ppo_passes=2
evaluation_episodes_per_cell=128
bootstrap_resamples=10000
checkpoint_selection=final_only
```

The bounded nonformal exercise uses one replicate, one fast update, one
return-to-go update, two environments and four episodes per cell. It may only
return a nonformal branch.

## Required invariants

- state-dict keys and tensor shapes are exactly equal at capacity 6/8/12;
- strict loading succeeds with no missing or unexpected key;
- cap8/cap12 paired-padding common active observations, values, deterministic
  actions, rewards and lifecycle transitions are bitwise equal;
- inactive action, likelihood and hidden-state drift are exactly zero;
- temporarily absent hidden state freezes, rejoin restores, fresh join starts
  at zero and terminal state is deleted;
- replay error is at most `1e-6` at every capacity;
- constructive utility and roster/count/source controls close exactly;
- evaluation has zero optimizer steps and exact model-state identity;
- checkpoint identity, capacity cell inventory, seeds, runtime and result
  precedence fail closed under tamper.

## First-match result semantics

Operational invalidity returns `INVALID_RUNTIME_CAPACITY_G32` and consumes no
iteration. Otherwise the registered order is:

1. any state-shape, strict-load, padding, RNG or zero-step identity failure ->
   `NO_PADDING_CAPACITY_INVARIANCE_G32`;
2. capacity-8 deterministic utility CI95 lower bound `<0.90`, gain lower bound
   `<=0`, or inherited mapping/lifecycle gate failure ->
   `NO_TRAIN_CAPACITY_ACCESS_G32`;
3. capacity-6 or capacity-12 deterministic utility CI95 lower bound `<0.90`,
   or their combined final-minus-zero gain lower bound `<=0` ->
   `NO_COUNT_CHURN_ACCESS_G32`;
4. minimum held-out replicate `<0.85` or held-out stochastic mean `<0.80` ->
   `UNSTABLE_RUNTIME_CAPACITY_G32`;
5. otherwise -> `USABLE_RUNTIME_CAPACITY_G32`.

A bounded run returns only
`NONFORMAL_RUNTIME_CAPACITY_G32_EXERCISE_COMPLETE`. Formal-required validation
must reject it.

## Proof-sized realization

Modify only the two capacity-bound critics, add one active G32 source/runner and
two focused test files. Retain existing G17/G19/G30/G31 focused tests as the
regression proof. Do not add adapters, compatibility schemas, UAV integration,
extra review layers or unrelated refactors.

## Implementation acceptance

The active realization is:

```text
core=ha_ctse_process/runtime_capacity_continuous_roster_g32.py
runner=scripts/run_runtime_capacity_continuous_roster_g32.py
shared_changes=ha_ctse_process/continuous_roster_policy.py|ha_ctse_process/anchored_residual_g19.py
focused_tests=13_passed
focused_regression=56_passed
backend=cpu
torch_threads=1
```

State-dict shapes are identical and strict-load at capacities 6/8/12. The
cap8/cap12 padding oracle covers every step and every bounded evaluation
episode with exact observation, value, action, reward, hidden and lifecycle
equality; inactive padding is exact zero. Evaluation records zero optimizer
steps and before/after state identity. A PM-found analyzer defect was repaired
so a finite natural padding mismatch reaches the registered `NO_PADDING`
branch, while malformed diagnostics, nonfinite values, duplicate inventory,
state drift and checkpoint tampering remain operationally invalid.

The focused test exercise is not the retained bounded evidence artifact. One
fresh nonformal pipeline must run after the implementation has an integrated
source commit. Formal iteration 24 remains unlaunched.
