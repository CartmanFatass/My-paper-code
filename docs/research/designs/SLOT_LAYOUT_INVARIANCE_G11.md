# Slot-layout invariance G11

Status: executable definition and implementation accepted; bounded nonformal
exercise operationally valid; formal iteration 12 ready.

## Frozen logical source

```text
algorithm=SLOT_LAYOUT_INVARIANCE_G11
checkpoint_run=logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1
checkpoint_source_commit=fcce714c296c55f3dcb5a0c0ee11090b393c26ba
checkpoint_result=USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8
logical_profile=oscillating_scale_churn_8_edits
logical_active_count_range=[12,40]
logical_capacity=48
training_operation=none_frozen_g8_checkpoint_import
optimizer_steps=0
```

G8--G10 remain closed. G11 changes no policy, task, reward, observation, wave,
lifecycle transition, count or event schedule.

## Physical layouts

For logical keys `k=0..47`:

```text
dense48:             physical(k)=k, capacity=48
reverse48:           physical(k)=47-k, capacity=48
sparse96:            physical(k)=2*k+1, capacity=96
affine_padded128:    physical(k)=(37*k+11) mod 128, capacity=128
```

Each map is injective. Membership events and owner, presentation and frontier
priority columns are mapped by the same function. The actor consumes stochastic
uniforms by autoregressive token position rather than lifecycle key, so the
first 48 position draws remain in place and only unused later positions are
padded. Source controls require equal wave arrivals, mapped priority equality,
exact roster schedules/demand, lifecycle freeze/restore and constructive
utility one.

## Formal execution

```text
authorization_token=AUTHORIZE_SLOT_LAYOUT_INVARIANCE_G11_FORMAL_CPU_V1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_replicates=3
optimizer_steps=0
evaluation_episodes_per_cell=64
evaluation_cells=24
utility_values=1536
bootstrap_repetitions=10000
ledger_seed=2681000
action_seed_base=2781000
bootstrap_seed=2881011
```

For every replicate and deterministic/stochastic mode, compare each transformed
layout to `dense48` episode by episode. An episode mismatches if any of its
persistent, short or utility values differs exactly.

## Gates and first match

- dense deterministic CI95 LCB `>=0.90`;
- paired outcome mismatch count is exactly zero for each transformed layout;
- minimum deterministic replicate/layout mean `>=0.85`;
- mean across all stochastic replicate/layout cells `>=0.80`.

After operational validity, first match is:

1. `NO_DENSE_LAYOUT_ACCESS_G11`;
2. `REVERSE_SLOT_DEPENDENCE_G11`;
3. `SPARSE_SLOT_DEPENDENCE_G11`;
4. `PADDING_SLOT_DEPENDENCE_G11`;
5. `UNSTABLE_SLOT_LAYOUT_G11`;
6. `SLOT_LAYOUT_INVARIANT_G11`.

Invalid evidence returns `INVALID_SLOT_LAYOUT_INVARIANCE_G11` and consumes no
iteration. Nonformal evidence returns
`NONFORMAL_SLOT_LAYOUT_G11_EXERCISE_COMPLETE`.
