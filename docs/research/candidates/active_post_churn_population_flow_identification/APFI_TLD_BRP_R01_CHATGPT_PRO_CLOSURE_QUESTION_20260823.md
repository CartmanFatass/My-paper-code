# APFI TLD-BRP R01 mathematical and causal closure request

You are the dedicated ChatGPT External Pro mathematical and causal reviewer
for one new HMASD direction-scoped object.

```text
OBJECT=APFI-TLD-BRP-SCIENCE-20260823-01
HOST=TLD-BRP-TRANSMISSION-LINE-DOCK-BANK-READINESS-PROBE-v1
STAGE=PROSPECTIVE_DEFINITION_ONLY
SCIENTIFIC_ACTIVITY_BEGUN=false
```

Your authority is limited to the mathematical and causal disposition of this
exact prospective definition. Do not review code, files, tests, hashes,
runtime behavior, implementation correctness, portfolio priority, resource
allocation, real-flight approval or deployment readiness.

Your first nonempty response line must be exactly one of:

```text
CLOSED
```

or

```text
REVISION_REQUIRED
```

Do not return conditional closure or a third disposition. If any science-
bearing fact is underspecified or inconsistent, use `REVISION_REQUIRED` and
identify every exact defect. `CLOSED` means only that this object is internally
coherent and causally capable of supporting its narrow claim ceiling.

## Scientific objective and grounding

After an identical battery-driven fleet exit, can one shared variable-roster
policy issue a safe read-only readiness probe, infer whether persistent
replacement cadence is fast or deferred, and choose the correct downstream
inspection allocation?

Operational grounding, not evidence for the toy effect:

- NASA demonstrated UAV inspection of high-voltage transmission structures:
  https://ntrs.nasa.gov/citations/20180006297
- Persistent-surveillance work couples energy-constrained UAV trajectories and
  charging schedules and uses time between visits as an endpoint:
  https://arxiv.org/abs/1908.05727
- MIT demonstrated persistent multi-UAV operation with automated battery
  swaps: https://acl.mit.edu/projects/automated-battery-management-system
- DJI documents unattended dock operation, recharge timing, Cloud API access
  and read-only task/charge properties:
  https://enterprise.dji.com/dock-2/specs
  https://enterprise.dji.com/dock-2/faq
  https://developer.dji.com/doc/cloud-api-tutorial/en/api-reference/dock-to-cloud/mqtt/dock/dock2/properties.html

The multi-dock bank, hidden cadence pair, readiness endpoint, timing, rewards,
sham and controls below are proposed toy semantics. DJI Dock 2 itself holds one
aircraft and does not automatically swap batteries.

## Frozen twins and source laws

- Target operational roster size is three UAVs.
- At `t=-1`, the same UAV exits for battery service in both twins.
- At `t=0`, both twins have identical complete policy-visible history, active
  roster `{u1,u2}`, positions, batteries, inspection-age map, dock occupancy
  and charge stocks, link state, clock, legal-action mask, identifiers and
  every policy-visible byte.
- The sole difference is latent transition law `Z`, absent from policy input:
  - `FAST`: while a vacancy exists, one replacement may join at `t=3,5,7,...`;
  - `DEFERRED`: while a vacancy exists, one replacement may join at
    `t=7,11,15,...`.
- Battery-exit dynamics are identical. Both downstream actions leave enough
  energy that no additional sink occurs before `t=6`.
- Cadence continues after the first join and is intended as a persistent source
  law, not a one-off event.
- Downstream allocation is at `t=2`, before passive arrival discloses `Z`.

## Probe and sham

At `t=0`, `u1` flies the same inspection micro-loop in every arm.

`READINESS_CHECK` transmits a fixed-size, non-reserving
`can_fill_vacancy_by_t3?` transaction. At `t=1`, the scheduler returns `r=1`
under `FAST` and `r=0` under `DEFERRED`.

`SHAM_LINK_CHECK` uses identical trajectory, imagery, radio power, packet
length, response latency, compute shell and cost. It contacts a law-independent
loopback and returns a stratified balanced bit with the same marginal
distribution.

Both cost `c=0.25` value units and perform identical useful inspection work.
Neither may launch, reserve, charge, reroute or alter a vehicle, dock queue,
calendar or task state. The intended response is a physical scheduler data-
link reply, not a simulator field containing `Z` or a realized future arrival.

## Opposite-action witness

At `t=2`, the identical legal actions are:

- `EXPAND`: send `u2` to a time-critical remote spur;
- `HOLD`: retain `u1,u2` on the critical trunk.

The spur yields six units only when dispatched at `t=2`. Trunk service yields
eight units only with two UAVs by `t=3`; a later replacement cannot reach the
spur inside the horizon.

```text
FAST/EXPAND=14
FAST/HOLD=8
DEFERRED/EXPAND=6
DEFERRED/HOLD=8
```

Thus `FAST` uniquely favors `EXPAND` and `DEFERRED` uniquely favors `HOLD`.
With a balanced law prior, the best passive action is `EXPAND`, worth `10`.
Truth-conditioned allocation is worth `(14+8)/2-0.25=10.75`. An optimal sham
policy cannot improve on passive information before paying matched cost.

## Information boundary

Policy input includes complete roster/event history, per-UAV position and
energy, inspection ages, link health, clock, legal mask, prior actions, and the
response only after the chosen transaction. It excludes `Z`, dock-calendar
bytes, future arrivals, scenario/seed names, truth-coded identifiers, law-
dependent response latency, reward lookahead and collector-only fields. Real
and sham bits are marginally balanced. Any pre-response law prediction above
balanced prior invalidates the object.

The response is intended as the sole prospectively declared observation caused
by the legal probe. Direct exposure of `Z` or a future realized event is
invalid.

## Treatment and exact-containing comparator

APFI uses a shared permutation-invariant roster encoder and recurrent state

```text
b_t=(posterior source-cadence belief,predicted join hazard,predicted sink hazard).
```

Probe and downstream-action heads consume it.

`RNN-CONTAIN` receives the same roster encoding, complete observation/action/
response history, legal actions and probe opportunity. It has an unconstrained
recurrent state using the same primitive update functions and at least APFI's
state dimension. Freeing the anchored block's weights gives the generic model;
one exact setting of a recurrent block and heads must recover every APFI policy.
APFI is therefore a parameter subset, not a larger-information/action arm.
Real, sham and no-probe arms exist for both.

## Frozen causal controls

1. `REAL/SHAM` separates information value from physical work.
2. `HISTORY_SWAP` crosses each admissible public history with both laws while
   preserving state; pre-response belief/action must remain law-blind.
3. `RESPONSE_SWAP` exchanges truthful replies without changing laws or
   trajectories. Under truth-following response, expected downstream value
   changes from `11` to `(8+6)/2=7` before common cost. Retained benefit rejects
   the response pathway.
4. `DOWNSTREAM_ACTION_CLAMP` forces each action separately. Within fixed law
   and action, real/sham trajectories and returns must match except message.
5. `NO_RESPONSE_CLAMP` executes the real transaction but masks the reply;
   behavior must reduce to passive information with transaction cost explicit.

Two fatal alternatives are registered:

- a generic RNN or simple response-conditioned policy can infer sufficient
  belief without an anchored representation; this kills representation
  advantage but not automatically the narrower host/probe claim;
- the probe helps by physical work or state displacement. Reservation, launch,
  charging, queue/calendar change, scored-work difference, action-clamped
  return difference or response-swap-resistant value invalidates the mechanism.

## Claim ceiling

The maximum claim is only constructibility of this named host, insufficiency of
passive pre-probe information, and existence of a legal information-bearing
probe. It excludes APFI learning efficacy, anchored-belief necessity, RNN
inferiority, general dynamic-`N`, UAV performance, safety and deployment.

## Required review

Audit all of the following:

1. Is deterministic `can_fill_vacancy_by_t3?` a legitimate action-conditioned
   physical scheduler observation, or `Z` exposed behind an action? State the
   causal criterion.
2. Can twins have identical complete history, roster, dock occupancy/charge,
   physical state, legal actions and visible bytes while differing only in a
   scheduler transition law? Must scheduler configuration/calendar memory be
   current state?
3. Does “may join” define the deterministic arrivals required by the value
   table and reply, including continuing cadence?
4. Does joining at `t=3` mean task-ready on the trunk by `t=3`, or is travel/
   readiness missing?
5. Verify strict inequalities, passive optimum, `10.75`, and cost treatment in
   sham/no-response arms.
6. Can loopback genuinely match server path, cost, timing, useful work,
   actuation shell, format and relevant physical interaction?
7. Is marginal balance sufficient, or must sham be conditionally independent
   of `Z` for every history/state? Audit all swaps/clamps.
8. Does “same primitives and at least APFI dimension” guarantee exact RNN
   containment, including normalization, posterior/hazard update, roster
   encoder, heads and auxiliary objectives?
9. Do controls distinguish information from work, and is RNN fatal only to
   representation advantage?
10. Is the claim ceiling maximal and every failure branch stopped?

After the first disposition line, provide the scheduler-observation/oracle
ruling, clause-by-clause analysis, strongest surviving alternative, maximum
claim and highest-information next scientific discriminator without authorizing
implementation.

If `REVISION_REQUIRED`, enumerate every science-bearing defect, why existing
controls/ceiling do not cure it, the minimum complete replacement semantics,
and the unrepaired claim ceiling. Insufficient information requires
`REVISION_REQUIRED`; do not silently assume missing facts.
