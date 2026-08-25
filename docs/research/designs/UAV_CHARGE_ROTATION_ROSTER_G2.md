# UAV charge-rotation roster G2 executable design

Status: frozen source contract; executable realization active after valid G1 terminal

## Scientific question

Can explicit service-lifecycle ownership improve safe charging rotation and
post-charge service recovery beyond the strongest correctly masked fixed-slot
recurrent controller, when inactive UAV physical energy, position and queue
state continue evolving?

The claim is limited to the registered eight-UAV S7-S3 source and its three
initial-energy profiles. It does not cover demand bursts, temporary failure,
arbitrary fleet size or composition.

## Frozen environment

```text
preset=S7-S3
physical_uavs=8
episode_steps=1500
battery_capacity_wh=160
charging_stations=2
station_capacity=1_each
charging_power_w=1000
temporary_failures=false
training_energy=(0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90)
heldout_low=(0.45,0.50,0.55,0.60,0.65,0.70,0.75,0.80)
heldout_sync=(0.55,0.55,0.60,0.60,0.65,0.65,0.70,0.70)
rejoin_battery_ratio=0.80
```

Each episode applies a fresh permutation of the selected multiset without
consuming user-motion, channel, station or action RNG. Station geometry,
energy/return physics, action support, QoS/safety reward and graph PBRS remain
unchanged.

## Service-lifecycle state machine

At each pre-action boundary, each physical slot is exactly one of:

- `ACTIVE`: service policy acts and contributes likelihood/PPO exposure;
- `CHARGE_ABSENT`: deterministic physical docking/queue/charge continues,
  service recurrence freezes and service links/actions are absent;
- `TERMINAL`: service recurrence is deleted and no later rejoin is possible.

An active UAV stays active through normal return transit. It enters
`CHARGE_ABSENT` when a dock request is active inside capture, including a full
station queue, or when battery reaches the existing cutoff. An inactive UAV is
driven only by the common deterministic docking mechanism. Reaching 0.80 while
nonterminal schedules REJOIN for the next pre-action boundary and restores the
same recurrent state. Depletion outside capture is terminal; depletion while
captured/charging remains a temporary absence because recharge is possible.

The wrapper records exact LEAVE, queue, charge, REJOIN and terminal boundaries.
The policy mask, communication availability, likelihood mask and recurrent
ownership must agree at every boundary.

## Information and matched arms

Active actors receive the existing current S7-S3 local/communication fields
plus current battery ratio, return margin, relative station positions, current
occupancy/queue length, dock request and current service status. Physical peer
records are anonymously ordered; inactive physical state remains observable
only through these permitted current fields. No future schedule, completion
time, queue order, energy use, user trajectory or desired rotation is exposed.

The centralized critic receives the full current physical fleet, charge/queue
state and service mask, never future state.

`FIXED_MASK_REC` and `PREFIX_NORMALIZED_OPEN_ROSTER` use the same matched
continuous recurrent actor-critic, active-set sum, `log1p(active_count)`,
active-fraction autoregressive prefix, action support and parameter count. The
fixed arm routes recurrence through stable physical storage; the open arm
routes it through the compact active lifecycle set. Temporary state freezes
and restores in both; terminal state deletes in both.

## Source controls

`CONSTRUCTIVE_CHARGE_ROTATION` and `NO_PROACTIVE_ROTATION` share the same
initial deterministic service layout. The constructive control forward-plans
only its scripted energy evolution, schedules the latest safe station arrival,
charges to 0.80 and recomputes survivor targets at LEAVE/REJOIN. The
no-proactive control freezes those service targets and relies only on unchanged
emergency-return and energy physics. Neither control trains or contributes a
learned comparison.

The implementation must reproduce every support/count predicate in the PM
reconciliation before learned training can exist.

## Metrics and result semantics

Control source identification uses the PBRS-free per-step safety score
`qos_satisfaction_ratio - 2*return_cost - 5*new_cutoff - 10*new_depletion`,
averaged across 1,500 steps. Learned access uses the frozen `J_event`,
`J_rejoin`, `Q_ordinary`, worst-cell access and absolute catastrophe/return-cost
safety admission.

All confidence intervals use the paired hierarchical 10,000-resample bootstrap.
The analyzer recomputes the seven registered first-match predicates and emits
exactly one result. Lower-precedence gain diagnostics never relabel source
failure or no access.

## Runtime realization

The active implementation should replace the closed G1 executable line rather
than add compatibility layers. Reuse only genuinely common policy, PPO,
checkpoint and chunk-journal logic; delete G1-only runtime adapters/tests once
G1 evidence is durably recorded. Git history and the iteration report preserve
the closed source.

Formal execution is CPU-only with the registered interpreter, torch 2.7.0+cpu
and one torch thread. Source controls run first and can terminate branch 2 with
zero model initialization, training or learned checkpoints. Update and
evaluation chunks are direct-write, identity-bound and resumable only under
the same command/source/run root/token.

## Proof-sized acceptance

The minimum implementation proof covers:

- exact energy-profile permutations and RNG separation;
- ACTIVE/CHARGE_ABSENT/TERMINAL transitions, cutoff, capture, queue contention,
  0.80 rejoin and deterministic inactive evolution;
- no inactive policy action, likelihood, PPO loss or hidden-state drift;
- anonymous actor information and no future leakage;
- exact arm parameter/action/exposure matching and replay;
- constructive/no-proactive behavior and all source-support predicates;
- metric boundaries, safety pass/fail equality, seven-branch precedence and
  formal validator rejection of nonformal artifacts;
- one bounded nonformal CPU exercise after the focused checks.

No compatibility reader, broad regression suite or additional review is
required absent a concrete shared-surface failure.

## Admission boundary

```text
implementation_prerequisite=satisfied_by_SOURCE_NON_IDENTIFIABLE_UAV_TEMP_LOSS_G1
formal_prerequisite=accepted_G2_implementation_and_nonformal_evidence
iteration_cost_before_valid_formal_result=0
```

## Accepted executable realization

The Project Manager accepts the active implementation in
`ha_ctse_process/uav_charge_rotation_g2.py` and
`scripts/run_uav_charge_rotation_g2.py` against this contract. The realization
adds no compatibility reader or G1 rescue path. Its source evidence records the
initial RESET projection separately from all later REJOIN projections, retains
already-absent station commitments during replanning, and fails closed unless
every projection, lifecycle plan, physical transition and source predicate is
consistent. Terminal owners lose recurrent state before the next learned
evaluation step.

Interruption recovery is limited to parse-truncated uncommitted bindings and
markers. A valid but conflicting identity, digest, payload or committed pair is
never rewritten. The same-root path therefore remains resumable without
weakening artifact authority.

Acceptance evidence is 42 focused CPU one-thread tests plus the fresh bounded
nonformal pipeline
`logs/nonformal_uav_charge_rotation_g2_cpu_20260724_pm2`. Its registered result
is `NONFORMAL_UAV_CHARGE_ROTATION_G2_EXERCISE_COMPLETE` with
`operational_valid=true`, `formal=false` and `conclusion_bearing=false`.
Formal iteration 23 uses the already frozen schedule and consumes no iteration
until a valid conclusion-bearing analysis exists.
