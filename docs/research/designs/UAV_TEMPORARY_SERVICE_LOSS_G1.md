# UAV temporary service loss G1

Status: frozen executable definition, implementation complete; prelaunch acceptance pending

Scientific authority:
`docs/external-review/rounds/20260723_uav_dynamic_service_roster_source_contract/21_PRO_OPEN_RAW.md`

PM reconciliation:
`docs/external-review/rounds/20260723_uav_dynamic_service_roster_source_contract/30_PM_SCIENTIFIC_RECONCILIATION.md`

## Question and claim unit

Does explicit compact service-lifecycle ownership improve service during an
exogenous recoverable temporary UAV loss and continuity after rejoin, relative
to the strongest correctly masked fixed-slot recurrent controller?

The claim unit is limited to an eight-asset S7-S1-like fleet with the registered
single-loss and overlapping-two-loss distributions. It excludes charging,
terminal loss, demand bursts, composition, arbitrary fleet size, skill
lifetime, sample efficiency and general UAV advantage.

## Source

The unchanged S7-S1 environment supplies eight physical UAVs, thirty users,
one ground base station, 500 physical steps, 1 Mbps ordinary per-user demand,
the 0.90 QoS target, continuous four-dimensional actions and the existing
external reward. Batteries and charging remain disabled.

### Registered ledgers

| Cell | Loss ledger |
|---|---|
| train / `IID_SINGLE` | one uniform owner; onset uniform integer 120..240; duration uniform integer 30..60 |
| `LATE_LONG_SINGLE` | one uniform owner; onset 280..330; duration 70..100 |
| `OVERLAPPING_DOUBLE` | two distinct uniform owners; onset1 140..200; onset2 = onset1 + uniform integer 10..20; two iid durations 50..80 |
| `NO_DISTURBANCE` | no loss |

Owner, onset, duration, user motion, channel randomness, policy randomness and
initial physical state use independent namespaces. Paired arms share the exact
episode ledger and exogenous randomness.

Before an affected physical step's action collection, loss sets the service
mask false. The affected UAV holds position with zero velocity, contributes no
communication link, actor row, action, log probability or PPO loss, and its
service recurrent state freezes. Rejoin restores the same lifecycle state,
refreshes the current physical observation and samples the next action only
after restoration. Survivor state is bitwise unchanged by another lifecycle's
leave/rejoin routing. No future ledger field is actor- or critic-visible.

## Matched learned arms

`FIXED_MASK_REC` and `PREFIX_NORMALIZED_OPEN_ROSTER` share one continuous
recurrent policy/critic architecture and differ only in row and lifecycle-state
routing.

Common contract:

```text
member_encoder=shared
active_set_aggregation=sum
count_coordinate=log1p_active_count
autoregressive_prefix=active_action_fraction
action_distribution=tanh_gaussian_four_dimensions
actor_information=current_only
critic_information=identical_full_current_state_and_service_mask
trainable_parameter_count=exact_equal
inactive_actor_likelihood=none
inactive_actor_loss=none
ppo_and_checkpoint_rule=identical
```

The fixed arm routes recurrence through eight stable physical storage slots and
uses the current service mask. The open arm compacts only active lifecycle rows
and routes recurrence by lifecycle ownership. Physical-slot identity is never
an actor input. The implementation retains the existing S7-S1 local physical,
user, SINR, connection, service and base-station information, filters inactive
peers, and anonymously repacks the original owner-indexed UAV records; it does
not add a global observation or future clock. Autoregressive presentation order
is a function of anonymous current physical content rather than storage slot.
A mathematically equivalent or mask-sufficient result is valid.

The executed action is the exact `tanh` transform of its stored pre-transform
Gaussian latent. Replay scores that latent with the stable transform Jacobian;
there is no post-transform clipping or collapsed tail probability.

## Controls

The constructive controller and no-reallocation control are evaluation-only.
They use the same 128 paired episode ledgers per cell and replicate as learned
evaluation and receive no optimizer exposure. The constructive controller may
read the complete loss ledger and current physical state only to certify source
feasibility. The no-reallocation control preserves the pre-loss action/layout
target.

The constructive implementation uses two deterministic relay slots, survivor
targets contracted only as much as required by the pre-onset physical travel
budget, and ordinary service targets for affected owners so that physical hold
during loss also preserves their rejoin location. A bounded one-versus-two
relay diagnostic selected two relays. The representative diagnostic is
prelaunch evidence only: it obtained `J_event=0.943997` for constructive and
`J_event=0.967834` for ledger-blind no-reallocation, so the formal
load-bearing predicate is at substantial risk of failing. This risk is not an
implementation defect and must not be tuned away.

Source identification requires:

```text
mean_constructive_J_event >= 0.90
LCB95(constructive_J_event - no_reallocation_J_event) > 0.10
```

## Metrics

Let `rho_t` be the existing `qos_satisfaction_ratio` using the current user
target rates. Let `W` be the union of service-loss intervals and `R` the union
of the first 60 physical steps after every recoverable rejoin. Overlap counts
once. Registered schedules leave every recovery window fully observed.

```text
d_t = max(0, 0.90 - rho_t) / 0.90
J_event = 1 - mean(d_t for t in W union R)
J_event(NO_DISTURBANCE) = 1.0
Q_ordinary = mean(rho_t for t outside W union R)
J_rejoin = 1 - mean(d_t for t in R)
```

For arm `a`, cell `c`:

```text
A_a_c = min(J_event_a_c / 0.80, Q_ordinary_a_c / 0.90)
A_a = min_over_registered_cells(A_a_c)
G_svc = mean(J_event_open - J_event_mask)
G_rejoin = mean(J_rejoin_open - J_rejoin_mask)
G_ordinary = mean(Q_ordinary_open - Q_ordinary_mask)
```

Here `c` is exactly one of the four named evaluation cells. Deterministic and
stochastic action evaluations remain paired and separately reported, but their
episode metrics are averaged within each cell before the minimum over the four
cells. They are not eight independent access cells.

The no-disturbance cell has no `J_rejoin`; it contributes only its access
guardrail and is excluded from `G_rejoin`.

## Confidence and first-match result

Use 95% hierarchical paired bootstrap intervals with 10,000 resamples:
resample the three paired replicates, then resample whole paired episode IDs
while preserving arms, controls, cells and action modes.

Source validity precedes access. Access is established when
`LCB95(max_a A_a) >= 1`, no access when `UCB95(max_a A_a) < 1`, and otherwise
is underpowered.

First-match order:

1. `INVALID_UAV_TEMP_LOSS_G1`: any operational, provenance, reward,
   probability, lifecycle, RNG, replay, checkpoint or comparator-match
   invariant fails.
2. `SOURCE_NON_IDENTIFIABLE_UAV_TEMP_LOSS_G1`: any source-law, support,
   leakage, feasibility or load-bearing predicate fails.
3. `NO_ACCESS_UAV_TEMP_LOSS_G1`: source valid and access UCB is below 1.
4. `UNDERPOWERED_ACCESS_UAV_TEMP_LOSS_G1`: source valid and access interval
   crosses 1.
5. `USABLE_MASK_SUFFICIENT_UAV_TEMP_LOSS_G1`: fixed mask accesses and
   `UCB95(G_svc) <= 0.03` and `UCB95(G_rejoin) <= 0.02`.
6. `DYNAMIC_LIFECYCLE_SUPPORTED_UAV_TEMP_LOSS_G1`: open roster accesses,
   `LCB95(G_svc) > 0.03`, `LCB95(G_rejoin) > 0.02`, and
   `LCB95(G_ordinary) >= -0.02`.
7. `MIXED_ANOMALOUS_UAV_TEMP_LOSS_G1`: every other valid access-positive
   pattern.

No later branch is read after the first match. No threshold, budget, seed,
reward, observation, distribution or name rescue is permitted.

## Formal exposure

```text
backend=cpu
torch_threads=1
paired_replicates=3
learned_arms=2
parallel_environments_per_arm_replicate=16
episode_and_rollout_steps=500
updates=200
environment_transitions_per_arm_replicate=1600000
ppo_passes_per_update=4
checkpoint_selection=final_only
evaluation_cells=NO_DISTURBANCE|IID_SINGLE|LATE_LONG_SINGLE|OVERLAPPING_DOUBLE
evaluation_action_modes=deterministic|stochastic
evaluation_episodes_per_cell_mode_arm_replicate=128
bootstrap_resamples=10000
```

Fresh PM-owned seed bases are:

```text
model_initialization_seed_base=181200
training_ledger_seed_base=181400
training_environment_seed_base=181600
training_action_seed_base=181800
evaluation_ledger_seed_base=182000
evaluation_environment_seed_base=182200
evaluation_action_seed_base=182400
control_seed_base=182600
bootstrap_seed=182800
```

Replicate IDs add `0`, `1000`, and `2000`; namespaces never share generator
state. Learned training trajectories are never reused as evaluation data, and
there is no cross-backend resume. The formal control rows produced by the
first-match source screen are already evaluation evidence and are therefore
reused byte-for-byte rather than recomputed.

### First-match compute pruning and interruption safety

Formal execution evaluates the exact constructive and no-reallocation support
before creating or optimizing a learned model. It applies the registered
source-identifiability predicates with the same 10,000-sample paired bootstrap.
If either predicate fails, training is skipped, zero learned checkpoints are
accepted, and analysis returns the already registered second branch
`SOURCE_NON_IDENTIFIABLE_UAV_TEMP_LOSS_G1`. If both pass, the unchanged learned
budget proceeds and later evaluation reuses the already committed control
rows. A source-screen pass alone is not a scientific conclusion.

Training commits a validated continuation state after each completed update;
evaluation commits each completed registered batch. Repeating the same command
may resume only when source, runtime, configuration, seeds, episode coordinate,
model, optimizer, RNG and cumulative audit identity match exactly. Incomplete
fragments are ignored and a mismatched fragment fails closed. Only the final
registered learned checkpoint is conclusion-bearing. Content digests are used
only inside this runtime journal and for final-checkpoint integrity; they are
not workflow, Git, review or handoff hashes.

## Acceptance before formal launch

Focused tests must cover the exact ledger supports, pre-action LEAVE, no
inactive likelihood/loss, hidden freeze/restore, survivor continuity, current-
only information, parameter/exposure equality, metric boundaries, first-match
precedence, checkpoint/RNG continuation and tamper rejection. One reduced
nonformal CPU exercise must close train/evaluate/analyze and be rejected by the
formal analyzer. It is operational evidence only.

Formal authorization token after accepted implementation:

`AUTHORIZE_UAV_TEMPORARY_SERVICE_LOSS_G1_FORMAL_CPU_V1`
