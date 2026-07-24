# Project Manager scientific reconciliation

Date: 2026-07-23

```text
reconciliation_owner=project_manager
pm_acceptance_authority=exclusive
external_scientific_authority=question_scoped
stage_commit=770fa45100134e887c50ab34b36c57f68ded5516
raw=docs/external-review/rounds/20260723_uav_dynamic_service_roster_source_contract/21_PRO_OPEN_RAW.md
raw_message_id=24c5675d-3aac-4abc-aee2-d443ab3d5483
disposition=ADOPT_UAV_SOURCE_LADDER_AND_TEMPORARY_LOSS_G1
conclusion_bearing_iteration_cost=0
uav_chain_iterations_remaining=10
```

## Accepted scientific correction

The review closes the central abstraction error. Scenario 7 has two distinct
objects:

- the fixed physical fleet of eight UAV assets; and
- the service-active lifecycle set that may temporarily exclude an asset.

A service LEAVE is genuine only when the absent UAV contributes no
communication or motion-policy action, has no actor row or likelihood/PPO loss,
and has explicit lifecycle-state ownership. Temporary absence freezes and later
restores service recurrence; terminal loss deletes it. Merely multiplying a
fixed row by an availability bit is not enough, although a correctly masked
fixed-slot recurrent controller remains the strongest ordinary reduction.

## Adopted source ladder

1. `UAV_TEMPORARY_SERVICE_LOSS_G1`: S7-S1 plus exogenous recoverable
   service LEAVE/REJOIN. This is the first executable source.
2. `UAV_CHARGE_ROTATION_ROSTER_G2`: S7-S3 charging and queueing with physical
   state evolution during service absence.
3. `UAV_LOCALIZED_DEMAND_BURST_G3`: constant service roster with localized
   time-varying demand; it tests rapid coverage reallocation, not dynamic
   membership.
4. `UAV_COMPOSED_SERVICE_ROSTER_G4`: admitted only after all isolated sources
   are identifiable and accessible and at least one membership source has not
   resolved confidently in favor of mask sufficiency.

No composed source may rescue an invalid, non-identifiable, inaccessible or
underpowered isolated source.

## First source frozen contract

The first conclusion-bearing source is exactly the review's
`UAV_TEMPORARY_SERVICE_LOSS_G1`:

```text
base_preset=S7-S1
physical_uavs=8
users=30
episode_steps=500
battery_and_charging=disabled
training_and_iid_loss_count=1
training_and_iid_owner=uniform_0_to_7
training_and_iid_onset=discrete_uniform_120_to_240
training_and_iid_duration=discrete_uniform_30_to_60
heldout_late_long_onset=discrete_uniform_280_to_330
heldout_late_long_duration=discrete_uniform_70_to_100
heldout_double_owner=two_distinct_uniform_without_replacement
heldout_double_onset1=discrete_uniform_140_to_200
heldout_double_delta=discrete_uniform_10_to_20
heldout_double_duration=two_iid_discrete_uniform_50_to_80
temporary_physics=zero_velocity_position_hold_and_no_communication
lifecycle=freeze_same_owner_then_restore_on_rejoin
future_ledger_actor_or_critic_visibility=forbidden
```

The two learned arms are:

- `FIXED_MASK_REC`: fixed physical slots with the correct current mask, no
  inactive likelihood/loss, and exact temporary hidden freeze/restore; and
- `PREFIX_NORMALIZED_OPEN_ROSTER`: compact service-active rows, active-set
  sum, `log1p(active_count)`, active-fraction autoregressive prefix and
  lifecycle-owned recurrence.

They receive identical current information, primitive continuous actions,
critic state, episode ledgers, trainable parameter count, environment
interactions, PPO exposure, checkpoint rule and paired randomness. Stable
physical slots may route baseline state but may not be actor features. Only row
representation and lifecycle routing differ.

The fixed-mask arm may be functionally equivalent. That is not an anomaly or a
weak result: `USABLE_MASK_SUFFICIENT_UAV_TEMP_LOSS_G1` is the registered
ordinary-reduction conclusion when its exact confidence conditions pass.

## Executable metric closure

The raw freezes `J_event`, `J_rejoin`, `Q_ordinary`, the worst-cell access
statistic, comparison margins and seven first-match branches. Two mechanical
closures are uniquely implied and introduce no alternate scientific task:

1. In `NO_DISTURBANCE`, the empty event/recovery union has
   `J_event=1.0`; the cell is therefore governed by `Q_ordinary`. This is the
   vacuous no-deficit identity, not a selected reward or threshold.
2. Constructive and no-reallocation controls use the same 128 paired episode
   ledgers per registered cell and replicate as learned-arm evaluation. They
   receive no training and enter only the source-identifiability predicates.

All confidence intervals use the frozen 95% hierarchical paired bootstrap with
10,000 resamples, first over the three paired replicates and then whole paired
episode IDs.

## Frozen exposure and result order

Per learned arm and paired replicate:

```text
parallel_environments=16
rollout_and_episode_length=500
updates=200
environment_transitions=1600000
ppo_passes_per_update=4
checkpoint=final_only
```

Evaluation uses `NO_DISTURBANCE`, `IID_SINGLE`, `LATE_LONG_SINGLE` and
`OVERLAPPING_DOUBLE`, deterministic and stochastic, with 128 episodes per cell
per arm and replicate.

First-match order is immutable:

1. `INVALID_UAV_TEMP_LOSS_G1`
2. `SOURCE_NON_IDENTIFIABLE_UAV_TEMP_LOSS_G1`
3. `NO_ACCESS_UAV_TEMP_LOSS_G1`
4. `UNDERPOWERED_ACCESS_UAV_TEMP_LOSS_G1`
5. `USABLE_MASK_SUFFICIENT_UAV_TEMP_LOSS_G1`
6. `DYNAMIC_LIFECYCLE_SUPPORTED_UAV_TEMP_LOSS_G1`
7. `MIXED_ANOMALOUS_UAV_TEMP_LOSS_G1`

The exact access and comparison inequalities are adopted directly from the raw
and may not be rescued by changing threshold, seed, budget, reward,
observation, distribution or name.

## Executable sufficiency and next boundary

The raw uniquely closes the first source. No further external question is
required before implementation. File layout, compact-index storage, padding,
telemetry schema, checkpoint serialization and fresh integer seed values are PM
implementation choices within the exact scientific bounds.

```text
next_boundary=UAV_TEMPORARY_SERVICE_LOSS_G1_EXECUTABLE_DEFINITION_AND_IMPLEMENTATION
formal_compute_status=authorized_by_user_but_not_launchable_until_pm_evidence_contract_and_nonformal_acceptance
external_review_status=complete
blockers=none
```
