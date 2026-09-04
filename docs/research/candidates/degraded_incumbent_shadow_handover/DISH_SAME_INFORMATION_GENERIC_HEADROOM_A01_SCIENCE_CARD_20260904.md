# DISH same-information generic transfer headroom A01 — science card

- Direction: `degraded_incumbent_shadow_handover`
- Object ID: `DISH-SAME-INFORMATION-GENERIC-HEADROOM-A01`
- Evidence class: **A/RECON**
- Result family: `GH-X/O/B/Z/P`
- Frozen: `2026-09-04T07:05:24-07:00`, before implementation, cost execution,
  resource admission, or scientific calculation
- Launch state: **FROZEN / NOT IMPLEMENTED / NOT LAUNCHED**
- Object-tier provenance:
  `DISH_A1_CURRENT_HOST_BASELINE_INVENTORY_20260904.md`
- Portfolio boundary: lifecycle remains `ACTIVE / MEDIUM`; no MEI, fusion, PARK, or B decision is
  encoded here

## 1. Question and claim ceiling

On a small, fixed population of `RIDGE-BEND-HOT-STANDBY-RELAY-2UAV-v3`, how much raw
harm-compatible 200-tick recovery-service headroom remains between:

1. one globally tuned, no-learner, same-information generic binary RETAIN/TRANSFER rule; and
2. a privileged per-row hindsight choice between the same two branches?

The object measures decision-only generic owner-remap headroom under one common no-learner
physical-action carrier. It does not ask whether shadow recurrent state has value.

The maximum positive claim is that, on the declared finite measurement rows, a per-row hindsight
choice inside the exact binary family attains more service than the calibration-selected global
same-information rule while satisfying the row's frozen harm and energy envelope. The maximum
zero-gap claim is only that the selected rule matches that binary-family reference on these rows.
Neither result upper-bounds all legal policies, proves learner headroom, establishes expected
return, or supports a B launch.

## 2. Non-goals and live explanations

Non-goals:

- do not run, repair, import, or modify B01 or its quarantined conformance bytes;
- do not test RETAIN/COPY/SHADOW recurrent-source value, train a controller, or create a
  checkpoint;
- do not revive the R02 prevalence object, its root map, formal certificates, or complete
  production stack;
- do not apply the proposed 5%/25% MEI numbers or any other materiality threshold;
- do not infer fusion with VNFC, PARK, priority, lifecycle, or Portfolio investment; and
- do not call the privileged upper reference a deployable policy or an optimum outside the
  declared binary decision family.

Live explanations for a raw gap are:

1. one global observable threshold is insufficient across package, schedule, speed, geometry,
   and owner identity;
2. the fixed common carrier creates row-specific transfer consequences that a richer generic
   policy could identify;
3. hindsight selection creates an intentionally optimistic reference that no online rule may
   realize; and
4. an absent or zero gap may reflect the carrier, opportunity definition, finite panel, or binary
   action restriction rather than lack of replacement value on the host.

## 3. Frozen host population

Use only the existing constructive R06 coordinate law, with no rejection, replacement, search, or
learned selection.

Common coordinates:

- host: `RIDGE-BEND-HOT-STANDBY-RELAY-2UAV-v3`;
- block: `0`;
- packages: `TARGET_VISUAL_MASK`, `TERRAIN_RELAY_MASK`;
- route speeds: `4`, `6`, and `8` m/s;
- within-speed slots: `ell=0,...,7`, covering each of the eight reflection/initial-owner/
  physical-assignment combinations once per package/schedule/speed cell;
- degradation mask: on;
- public deterministic master:
  `SHA256(UTF8("DISH-SAME-INFORMATION-GENERIC-HEADROOM-A01/public-master/v1"))`; and
- all configurations and both branches consume the same row's exogenous tape and counter
  frontier.

The **calibration population** uses schedules `K4` and `K12`:

```text
2 packages * 2 schedules * 3 speeds * 8 slots = 96 rows.
```

The disjoint **measurement population** uses schedules `K8` and `K4_TO_K12` with the same other
indices, also 96 rows. `K12_TO_K4`, blocks 1--23, slots 8--15, mask-off views, training resets,
and every other R06 row are outside this A/RECON claim.

Every coordinate remains present if terminal or opportunity-absent. Calibration outcomes can tune
one global rule ID; no measurement outcome may do so.

## 4. Common carrier, opportunity, and causal cut

The arm-independent prefix and consequence carrier is the already defined
`SCRIPTED-RETAIN` receding-horizon controller. It uses no learned state or action and permanently
masks transfer false. Its use of current evaluator state is a shared nuisance carrier, not an
input to the generic decision rule below; the claim is explicitly conditional on this carrier.

Starting at degradation, scan ordinary renewals through the first application tick no later than
`tau_d+20 s`. At each renewal, construct the canonical A01 one-transfer intent from current causal
protocol headers. A **census opportunity** is the first intent whose next-tick application passes
the unchanged native owner, epoch, sequence, common SOURCE-lineage, nonterminal, positive-battery,
separation, and stored-action slew predicates. The opportunity selector never reads a learned
proposal, branch endpoint, or future tape.

At the opportunity origin, save the two current production actor vectors for the physical
authoritative copies: owner-I and standby-S. At the next tick, after common arrivals and buffer
assimilation and before owner remap, freeze one parent and branch:

- **RETAIN:** consume the same A01 transaction shell, bytes, and energy, but retain owner and
  actuator assignment; and
- **TRANSFER:** consume the identical shell and atomically remap owner and actuator to the standby.

There is no recurrent source, snapshot bridge, COPY/SHADOW distinction, or application policy
forward. The carrier is memoryless with respect to learned state and replans from the branch's
current physical/native state. Both branches execute exactly 200 primitive ticks with the same
future exogenous tape. No second transfer is allowed.

If no census opportunity occurs, record the row as opportunity-absent; do not replace it. Branch
and gap fields are explicitly undefined for that row, while unconditional opportunity counts keep
the population total.

This A01 cut is a new decision-only diagnostic. Its implementation may not import or repair the
uncommitted B01 conformance path.

## 5. Same-information generic baseline family

At the opportunity origin, the generic score receives exactly the ordered raw causal values in
the current owner-I and standby-S 54-vectors. This is an optimistic centralized use of the same
information set already present in the deployed actor copies. It receives no centralized critic,
true package label, absolute tick, remaining horizon, opaque SOURCE body, evaluator ground truth,
future target, future `k`, future disturbance, RNG address, branch endpoint, or measurement-row
identity.

From those visible values, form one deterministic 20-tick mean rollout for RETAIN and one for
TRANSFER:

- enumerate the existing five raw acceleration commands per UAV,
  `{(0,0),(3,0),(-3,0),(0,3),(0,-3)}`;
- use the current visible self navigation, delivered partner STATE, camera-filter target position
  and velocity, battery, margins, buffers, public `k`, and protocol bits;
- linearly extrapolate the visible target filter for 20 ticks;
- set unknown or absent fields to their actor-vector sentinels and all future noise innovations to
  zero;
- hold each candidate command pair for the whole prediction;
- apply the registered projection, energy, service, and one-owner transaction recurrence; and
- select within each owner choice by maximum predicted valid-service ticks, then minimum predicted
  propulsion energy, then UAV-0 and UAV-1 command indices.

Let

```text
d_hat = predicted_service_ticks(TRANSFER) - predicted_service_ticks(RETAIN).
```

The finite family is exactly:

```text
ALWAYS, Q0, Q1, Q2, Q4, Q8, NEVER,
```

where `Qq` selects TRANSFER iff `d_hat>=q`, ALWAYS selects TRANSFER, and NEVER selects RETAIN.
Every configuration makes one decision and has zero learned or recurrent state.

On the 96 calibration rows, run both native branches once and score every configuration offline
from its decision. A configuration is calibration-compatible iff its aggregate count for every
hard-event type is no greater than NEVER and its aggregate branch energy is at most `1.05` times
NEVER. NEVER is therefore always available. Select one global baseline ID by:

1. maximum mean 200-tick recovery service;
2. maximum mean worst-contiguous-20-tick service;
3. minimum mean recovery delay to ten consecutive service-positive ticks;
4. minimum aggregate energy; and
5. conservative fixed ID order `NEVER,Q8,Q4,Q2,Q1,Q0,ALWAYS`.

Freeze that selected ID before any measurement-row branch endpoint is inspected. The selected
configuration, not a measurement-retuned configuration, is the tuned generic baseline.

## 6. Upper reference

For each opportunity-present measurement row, first apply the frozen baseline ID and identify its
realized RETAIN or TRANSFER branch. The row's admissible upper-reference set contains the baseline
branch and the other branch only when the other branch:

- has no greater count for any registered hard-event type; and
- has total consequence energy at most `1.05` times the baseline branch energy.

Choose from that set by maximum realized 200-tick service, then maximum worst-20-tick service,
minimum recovery delay, minimum energy, and RETAIN before TRANSFER.

This `PER-ROW-BINARY-HINDSIGHT` choice is privileged and nondeployable. It is an exact upper
reference only for the declared harm-compatible binary action family on that row. Because the
baseline branch is always admissible,

```text
upper_reference_service_ticks >= baseline_service_ticks
```

holds by construction. It is not an upper bound over other transfer times, action carriers,
learners, recurrent sources, or all legal host policies.

## 7. Information and work exposure

### Learner exposure line

- trainable parameters: `0`;
- initialization norm/scale: `N/A`;
- parameter displacement L2/RMS: `0 / 0`;
- optimizer, gradient, update, episode-training, checkpoint, and replay counts: `0`;
- displacement-to-initialization ratio: `N/A`.

### Selection and outcome exposure

- calibration information exposure: seven rule decisions over 96 rows, using the two common
  branch outcomes per row only to select one global ID;
- measurement baseline exposure: the frozen ID sees only its legal opportunity-origin vectors;
- measurement upper-reference exposure: both realized branch outcomes on 96 rows, inspected only
  after the baseline ID is frozen and used only for the privileged per-row reference;
- no calibration row enters a primary gap and no measurement row changes the baseline ID; and
- no seed, model family, budget, row, threshold, or action is added after any outcome.

### Native work exposure

Each of 192 total coordinates executes one common prefix. Every opportunity-present coordinate
executes two 200-tick branches; absent rows execute no branch. The conservative maximum is:

```text
prefix ticks per coordinate <= 860
branch ticks per coordinate <= 2*200
total native primitive ticks <= 192*(860+400) = 241,920.
```

The seven threshold configurations are offline decisions over the same two outcomes; they do not
create seven native arms.

## 8. Required raw observables and gaps

For every coordinate, publish package, schedule, speed, slot, master identity, terminal status,
opportunity-present flag, origin/application ticks, owner, native legality facts, the complete two
54-vector inputs or an exact lossless numeric serialization, `d_hat`, and all seven decisions.

For each opportunity-present branch publish:

- `recovery_service_ticks_200` and fraction;
- `worst_contiguous_20_service_ticks`;
- `recovery_delay_10`, capped at 200;
- consequence energy;
- counts of invalid commit, token gap, dual owner, dual payload, buffer clear, command-slew breach,
  separation breach, battery exhaustion, and terminal ticks; and
- transaction bytes/messages, owner before/after, and branch label.

For every opportunity-present measurement row, the primary raw fields are exactly:

```text
baseline_configuration_id
baseline_action
upper_reference_action
baseline_service_ticks
upper_reference_service_ticks
gap_service_ticks = upper_reference_service_ticks - baseline_service_ticks
baseline_service_fraction
upper_reference_service_fraction
gap_service_fraction
baseline_worst20_ticks
upper_reference_worst20_ticks
gap_worst20_ticks
baseline_recovery_delay_10
upper_reference_recovery_delay_10
gap_recovery_delay_10 = baseline_delay - upper_delay
baseline_energy
upper_reference_energy
upper_minus_baseline_energy
baseline_hard_event_vector
upper_reference_hard_event_vector
```

Report every raw row and, without confidence intervals or MEI comparison, exact counts and
arithmetic means overall and by package, measurement schedule, and speed. Also report defined-gap
count, opportunity-absent count, positive-gap count, zero-gap count, minimum/maximum gap, and the
complete calibration ranking table. No row weighting, bootstrap, p-value, clipping, thresholding,
or hidden favorable subset is permitted.

## 9. Ordered descriptive result rule and predictions

Apply once to one complete measurement population:

1. **`GH-X / INVALID_OR_INCOMPLETE`.** Any illegal information, population/count mismatch,
   changed host/branch/carrier law, measurement-retuned baseline, missing raw field, nonfinite
   native quantity, branch-common-tape mismatch, failed resource admission, or cap breach.
   Quarantine the attempt and assign no A result.
2. **`GH-O / NO_CENSUS_OPPORTUNITY`.** Zero measurement rows have a census opportunity. Report all
   row facts; the binary gap is unidentified on this panel.
3. **`GH-B / TUNED_BASELINE_NOT_COMPETENT`.** On opportunity-present measurement rows, the frozen
   baseline has lower mean service than NEVER, exceeds NEVER on any aggregate hard-event count, or
   exceeds `1.05` times NEVER energy. Report the raw upper gap, but do not call it residual above a
   competent generic baseline.
4. **`GH-Z / ZERO_DECLARED_BINARY_GAP`.** The baseline is competent and every defined
   `gap_service_ticks` is zero.
5. **`GH-P / POSITIVE_DECLARED_BINARY_GAP`.** The baseline is competent and at least one defined
   `gap_service_ticks` is positive.

Every branch returns the raw table to Root's A1 aggregation. None launches B, changes DISH
lifecycle, applies an MEI, or decides fusion/PARK.

Predictions on record:

- **DM:** `GH-P`, with a small and heterogeneous raw gap concentrated by package/schedule/speed;
  per-row hindsight should exploit variation that one global threshold cannot, but the fixed
  carrier and binary action family should limit the gap.
- **Owner:** `not taken (unattended)`.

## 10. Prospective cost, cap, resource, and stop rule

This is a two-arm paired native calculation, RETAIN and TRANSFER. Conservatively charge every
prefix to each arm. The maximum per-arm work is:

```text
192*(860 prefix ticks + 200 consequence ticks) = 203,520 primitive ticks.
```

Using the nearest current-byte conservative measurement already recorded by B01,
`10.672341100056656 s` per 4,096 native-connected transitions, plus a fixed 60-second
compile/publication allowance and a 1.5 multiplier, the frozen projection is:

```text
projected_arm_seconds
  = 1.5 * ((203520/4096)*10.672341100056656 + 60)
  = 885.4229226135976 seconds.
```

The runner's future non-result `project-cost` mode must emit one row for RETAIN and one for
TRANSFER with that complete law. The cap is **900 seconds per arm** and **1,800 seconds for the
single invocation**. A row above its cap refuses the calculation. There is no sweep over learner
budgets or seeds.

Before any future result invocation, run a fresh
`python scripts/hmasd_resource_preflight.py admit-memory --out <receipt>` and require physical and
effective available memory both at least 4 GiB. The result invocation must be detached from the
agent, use one CPU process and one computational thread, and bind a pushed launch SHA. Missing
ordinary RSS telemetry leaves a non-resource result valid as `resources_unmeasured`; missing
learner telemetry is inapplicable because there is no learner.

Stop after the complete 192-row population and one rule application, or at the first deterministic
row boundary after 1,800 wall seconds. A technical failure, incomplete row, or cap breach is GH-X;
no partial result is interpreted or resumed. There is no efficacy stop, result-informed row
replacement, retry, seed extension, or threshold change.

Freezing this card does not authorize implementation, `project-cost`, admission, or the result
invocation.

## 11. Protected semantics, expected surfaces, and engineering scope

Protect the R06 host recurrence, constructive coordinate law, public-master addressing, causal
actor vectors, ordinary renewal timing, native legality predicates, transaction cost/bytes,
one-owner state, service/energy/hard-event recurrences, branch-common future tape, float
precision, and all raw gap definitions. Direct observation must remain separate from the inference
that a richer policy could close a positive gap.

Any later implementation is isolated to:

- `experiments/candidates/degraded_incumbent_shadow_handover/generic_transfer_headroom_a01/`;
- `scripts/run_dish_generic_transfer_headroom_a01.py`, below 600 lines; and
- `tests/experiments/candidates/degraded_incumbent_shadow_handover/generic_transfer_headroom_a01/`.

The quarantined `first_trigger_source_scout_b01` worktree/paths, B01 card, production learner,
replay, evaluator, private B01 native API, R02 files, core MARL code, and existing historical
results are read-only and outside ownership.

**Engineering-scope section 4 declaration: this object needs none of the default-prohibited
machinery.** It adds no process pool, distributed execution, queue, scheduler, resume/checkpoint,
retry loop, lease, heartbeat, liveness probe, tamper evidence, hash chain, byte manifest,
provenance/currentness guard, incident tree, schema validator, registry, compatibility shim,
repeated smoke loop, or telemetry beyond wall time and peak RSS. Research code remains below
2,000 new non-test lines, the runner below 600, and orchestration below 30 percent.

Technical success could establish only that the no-learner paired calculation conforms. It cannot
establish GH polarity, a material gap, learner competence, recurrent-source value, or Portfolio
action.

## 12. Object-tier freeze decision

Options and recommendation are recorded in
`DISH_A1_CURRENT_HOST_BASELINE_INVENTORY_20260904.md`. The selected option is:

**Owner-delegated decision (unattended, 2026-09-03 instruction): freeze this A/RECON card only.**
Provenance: `OWNER_DELEGATED`.
