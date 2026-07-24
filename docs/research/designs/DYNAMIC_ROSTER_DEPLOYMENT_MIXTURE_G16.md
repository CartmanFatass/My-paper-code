# Dynamic-roster deployment mixture G16

Status: frozen executable contract for formal iteration 17.

## Frozen algorithm and scope

```text
algorithm=DYNAMIC_ROSTER_DEPLOYMENT_MIXTURE_G16
checkpoint_run=logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1
checkpoint_source_commit=fcce714c296c55f3dcb5a0c0ee11090b393c26ba
checkpoint_result=USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8
checkpoints=3_final_update_250
training_operation=none_frozen_g8_checkpoint_import
optimizer_steps=0
policy_representation=sum_log1p_count_active_fraction_prefix
```

G5--G15 remain closed. G16 changes only the evaluation distribution by mixing
already accepted process classes under new seeds. It changes no policy, task,
reward, observation, action, horizon, lifecycle, PPO, checkpoint, gate or
action-RNG meaning.

## Balanced deployment mixture

Each domain contains exactly one third `serial_random`, one third
`atomic_equal` and one third `atomic_shock` episodes.

```text
deployment_moderate: capacity=128, active_count<=40, shock=[12..16]<->[24..32]
deployment_wide:     capacity=192, active_count<=64, shock=[28..32]<->[52..64]
deployment_ultra:    capacity=224, active_count<=80, shock=[40..48]<->[72..80]
serial_random_events=12
atomic_equal_events=6
atomic_shock_events=6
```

Every profile is rebuilt from its G16 seed. Serial random profiles contain all
four membership operation types. Equal atomic profiles use positive equal-size
terminal/fresh-join cohorts and constant N. Shock profiles use positive unequal
cohorts and exact alternating low/high count bands. Lifecycle-key reuse is
forbidden.

## Formal execution

```text
authorization_token=AUTHORIZE_DYNAMIC_ROSTER_DEPLOYMENT_MIXTURE_G16_FORMAL_CPU_V1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_replicates=3
optimizer_steps=0
evaluation_episodes_per_cell=36
process_profiles_per_mode_per_domain=12
evaluation_cells=18
utility_values=648
source_control_rows=108
bootstrap_repetitions=10000
deployment_moderate_ledger_seed=4481000
deployment_wide_ledger_seed=4481100
deployment_ultra_ledger_seed=4481200
action_seed_base=4581000
bootstrap_seed=4681016
```

Source controls require 108 unique names, exact 6/12 event counts, exact
process-mode balance, all four operation types across the mixture, constructive
utility one, exact roster schedules and wave demand, lifecycle validity and
exact reconstruction of every profile. Imported checkpoints and evaluated
models remain exactly unchanged.

## Gates and first match

- deployment-moderate deterministic utility CI95 LCB `>=0.90`;
- deployment-wide deterministic utility CI95 LCB `>=0.90`;
- deployment-ultra deterministic utility CI95 LCB `>=0.90`;
- minimum deployment-ultra deterministic replicate mean `>=0.85`;
- deployment-ultra stochastic mean `>=0.80`.

After operational validity, first match is:

1. `NO_DEPLOYMENT_MODERATE_ACCESS_G16`;
2. `NO_DEPLOYMENT_WIDE_ACCESS_G16`;
3. `NO_DEPLOYMENT_ULTRA_ACCESS_G16`;
4. `UNSTABLE_DYNAMIC_ROSTER_DEPLOYMENT_G16`;
5. `USABLE_DYNAMIC_ROSTER_DEPLOYMENT_G16`.

Invalid evidence returns `INVALID_DYNAMIC_ROSTER_DEPLOYMENT_MIXTURE_G16` and
consumes no iteration. Nonformal evidence returns
`NONFORMAL_DEPLOYMENT_MIXTURE_G16_EXERCISE_COMPLETE`.
