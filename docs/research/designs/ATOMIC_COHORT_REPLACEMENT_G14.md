# Atomic cohort-replacement G14

Status: executable definition and implementation accepted; bounded nonformal
exercise operationally valid; formal iteration 15 ready.

## Frozen algorithm

```text
algorithm=ATOMIC_COHORT_REPLACEMENT_G14
checkpoint_run=logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1
checkpoint_source_commit=fcce714c296c55f3dcb5a0c0ee11090b393c26ba
checkpoint_result=USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8
checkpoints=3_final_update_250
training_operation=none_frozen_g8_checkpoint_import
optimizer_steps=0
policy_representation=sum_log1p_count_active_fraction_prefix
```

G8--G13 remain closed. G14 changes only the evaluation membership transaction
distribution and capacity. It changes no policy, task, reward, observation,
action, wave, horizon, lifecycle ownership, PPO or action RNG.

## Atomic process

Every generated profile has six events at `9, 24, 32, 40, 49, 64`. Each event
contains both:

```text
terminally_left=random_active_cohort
joined=random_never_seen_cohort
len(terminally_left)=len(joined)>0
```

Thus active N is constant at every timestep, while fresh members start with
zero hidden state and terminal members never reactivate.

```text
atomic_moderate: capacity=64,  N=[12,20], replacement_batch=[2,6]
atomic_wide:     capacity=144, N=[32,48], replacement_batch=[6,14]
mixed_churn:     capacity=192, N=[64,80], replacement_batch=[10,18]
```

Each episode owns a deterministic seed-derived profile. Formal source controls
cover all 32 profiles per domain and require unique identities, exact atomic
event signatures, constant schedules, exact wave demand, constructive utility
one and terminal/cold-start lifecycle validity.

## Formal execution

```text
authorization_token=AUTHORIZE_ATOMIC_COHORT_REPLACEMENT_G14_FORMAL_CPU_V1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_replicates=3
optimizer_steps=0
evaluation_episodes_per_cell=32
evaluation_cells=18
utility_values=576
source_control_rows=96
bootstrap_repetitions=10000
atomic_moderate_ledger_seed=3881000
atomic_wide_ledger_seed=3881100
mixed_churn_ledger_seed=3881200
action_seed_base=3981000
bootstrap_seed=4081014
```

## Gates and first match

- atomic-moderate deterministic utility CI95 LCB `>=0.90`;
- atomic-wide deterministic utility CI95 LCB `>=0.90`;
- atomic-ultra deterministic utility CI95 LCB `>=0.90`;
- minimum atomic-ultra deterministic replicate mean `>=0.85`;
- atomic-ultra stochastic mean `>=0.80`.

After operational validity, first match is:

1. `NO_ATOMIC_MODERATE_ACCESS_G14`;
2. `NO_ATOMIC_WIDE_ACCESS_G14`;
3. `NO_ATOMIC_ULTRA_ACCESS_G14`;
4. `UNSTABLE_ATOMIC_REPLACEMENT_G14`;
5. `ROBUST_ATOMIC_COHORT_REPLACEMENT_G14`.

Invalid evidence returns `INVALID_ATOMIC_COHORT_REPLACEMENT_G14` and consumes
no iteration. Nonformal evidence returns
`NONFORMAL_ATOMIC_REPLACEMENT_G14_EXERCISE_COMPLETE`.
