# Project Manager scientific reconciliation: UAV charge-rotation G2

## Authority and disposition

```text
semantic_author=project_manager
scientific_input=external_pro_raw_only
pm_acceptance_authority=exclusive
controller_validation_authority=none
source_family=UAV_CHARGE_ROTATION_ROSTER_G2
disposition=ACCEPT_EXECUTABLE_CONTRACT
iteration_cost=0
```

The exact scientific input is
`docs/external-review/rounds/20260723_uav_charge_rotation_g2_evidence_contract/21_PRO_OPEN_RAW.md`
from the review boundary at
`68d16b62f980c3be264a4e4d77ef3517969da290`. The mechanical intake records the
stable external message and transport provenance. This reconciliation does not
use the in-flight G1 run or any partial runtime value as evidence.

The raw uniquely closes the missing G2 controls, safety admission, formal
exposure and first-match semantics. No further scientific question is needed.

## Adopted source boundary

G2 keeps unchanged S7-S3 physics, four continuous primitive action coordinates,
external QoS/safety reward, eight physical UAVs, 1,500 physical steps, 160 Wh
batteries, two one-slot 1,000 W charging stations and no temporary failures.
Training/IID, LOW_ENERGY and SYNCHRONIZED_PRESSURE use the exact previously
frozen initial-energy multisets with a fresh per-episode permutation.

Service activity is distinct from physical existence. Ordinary return transit
remains service-active. A lifecycle leaves at the first pre-action boundary
where its dock request is active inside capture, including queueing, or the
battery reaches the existing cutoff. While absent, deterministic physical
docking, holding, queueing and charging continue, but the lifecycle has no
service-policy action, actor row, likelihood or PPO loss. Temporary recurrence
freezes and restores; terminal depletion deletes it. Recharge to 0.80 causes
REJOIN at the next pre-action boundary.

Actors receive only current physical, energy, station, queue, dock-request and
service-mask information. The critic may receive the full current physical
state. Neither receives future energy, user, channel, queue, completion or
rotation schedules. Physical storage identity may route recurrence but is not
an actor feature.

## Source screen

The accepted controls are evaluation-only:

- `CONSTRUCTIVE_CHARGE_ROTATION` plans the latest safe departure under exact
  current physics, charges to 0.80 and recomputes service targets on LEAVE and
  REJOIN;
- `NO_PROACTIVE_ROTATION` freezes the pre-departure service targets and never
  voluntarily docks, while retaining unchanged emergency return, cutoff,
  depletion and charging physics.

Both begin from the same deterministic Scenario-7 service layout and use the
same per-episode physical/random source realization. The constructive control
may forward-simulate only its own scripted actions with current state, station
geometry, exact energy equations and known horizon. Future users, channels,
queues and policy randomness remain prohibited.

Because charge timing is endogenous, source identification uses the raw's
exact PBRS-free safety score `Phi`, not `J_event`. Each registered energy
profile must satisfy:

```text
mean(Phi_constructive) >= 0.90
LCB95(Phi_constructive - Phi_no_rotation) > 0.10
```

All raw-listed support predicates are adopted: zero constructive cutoff,
depletion and return-cost rows; charge-cycle floors; complete 60-step recovery
windows; station use; synchronized concurrent absence; no-charge pressure; and
exact physical consistency. Equality passes only where the raw says it passes.

Failure of any source predicate selects
`SOURCE_NON_IDENTIFIABLE_UAV_CHARGE_ROTATION_G2` before learned training.

## Learned evidence and safety

The learned comparison remains `FIXED_MASK_REC` versus
`PREFIX_NORMALIZED_OPEN_ROSTER`, with identical actor/critic information,
primitive support, parameters, initialization, environment interactions,
optimizer exposure, PPO, reward, checkpoint rule and paired randomness.

The primary per-cell access statistic remains:

```text
A[a,c] = min(J_event[a,c] / 0.80, Q_ordinary[a,c] / 0.90)
A[a] = min_c A[a,c]
```

Energy-safety admission is absolute and cellwise. In all three profiles and
both action modes, an admitted arm requires:

```text
UCB95(catastrophe_episode_fraction) <= 0.05
UCB95(mean_capped_return_cost_burden) <= 0.05
```

An arm confidently fails access if QoS access has `UCB < 1` or either safety
quantity has `LCB > 0.05`. All other unresolved arm-level patterns are
underpowered. Safety remains an access guardrail, not a reward change or an
open-versus-mask estimand.

The held-out mechanism comparisons retain the exact parent margins for
`G_svc`, `G_rejoin` and `G_ordinary`. A missing fully observed rejoin sample is
never imputed. It makes the corresponding fixed/dynamic comparison predicate
false; if some arm is otherwise access-positive, the first-match system reaches
`MIXED_ANOMALOUS_UAV_CHARGE_ROTATION_G2`. This is the conservative direct
realization of the raw's exhaustive branch 7, not an added gate or threshold.

## Frozen formal schedule

```text
paired_replicates=3
parallel_environments_per_arm_replicate=8
horizon=1500
updates_per_arm_replicate=128
ppo_passes_per_update=4
training_profile=IID
evaluation_profiles=IID|LOW_ENERGY|SYNCHRONIZED_PRESSURE
action_modes=deterministic|stochastic
evaluation_episodes_per_cell_arm_replicate=128
evaluation_batch_size=16
control_episodes_per_profile_replicate=128
checkpoint=final_update_128_only
bootstrap_resamples=10000
backend=cpu
torch_threads=1
```

Exact integer seeds and storage schemas remain implementation-only. Seeds must
be fresh/disjoint from G1, paired across arms where required, separated between
training/evaluation/controls/bootstrap, and exactly restorable on resume.

## First-match result system

The adopted immutable order is:

1. `INVALID_UAV_CHARGE_ROTATION_G2`
2. `SOURCE_NON_IDENTIFIABLE_UAV_CHARGE_ROTATION_G2`
3. `NO_ACCESS_UAV_CHARGE_ROTATION_G2`
4. `UNDERPOWERED_ACCESS_UAV_CHARGE_ROTATION_G2`
5. `USABLE_MASK_SUFFICIENT_UAV_CHARGE_ROTATION_G2`
6. `DYNAMIC_LIFECYCLE_SUPPORTED_UAV_CHARGE_ROTATION_G2`
7. `MIXED_ANOMALOUS_UAV_CHARGE_ROTATION_G2`

The exact branch predicates and smallest claim updates are adopted verbatim
from the raw. No result may be rescued by changing profiles, reward,
observation, model, threshold, seed, budget or source name.

Burst remains an independent legal successor after every valid G2 result.
Composition remains prohibited after non-identifiable, no-access or
underpowered G2, and otherwise still requires all three isolated sources to be
identifiable/access-positive plus at least one genuine membership source not
resolved confidently for mask sufficiency.

## Executable sufficiency and next boundary

The contract is executable without another protected scientific choice.
Implementation may choose the smallest active-line module layout, fresh seed
integers, telemetry schema, checkpoint serialization and worker topology that
preserve the exact contract.

G2 implementation remains conditionally queued until G1 returns a valid
non-`INVALID` terminal result. The current next boundary therefore remains G1
formal terminal intake; after that prerequisite, the next PM-owned boundary is
`UAV_CHARGE_ROTATION_ROSTER_G2_EXECUTABLE_REALIZATION`.

```text
formal_g2_compute_status=not_launchable_before_valid_g1_and_pm_nonformal_acceptance
conclusion_bearing_iterations_consumed=0
blockers=G1_VALID_TERMINAL_PREREQUISITE_ONLY
```
