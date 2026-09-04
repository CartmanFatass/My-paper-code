# APFI TLD-BRP active post-churn identification definition — revision 01

```text
owner=direction:active_post_churn_population_flow_identification
object=APFI-FRESH-PRINCIPAL-FLOW-HOST-DISCRIMINATOR-R01
revision=APFI-TLD-BRP-SCIENCE-20260823-01
host=TLD-BRP-TRANSMISSION-LINE-DOCK-BANK-READINESS-PROBE-v1
stage=prospective_definition_only
scientific_activity_begun=false
construction_authorized=false
empirical_activity_authorized=false
pro_closed=false
```

## Decision first

This card freezes one active post-churn dynamic-`N` host witness selected from
the Portfolio's finite four-family registry. It asks whether a legal,
non-reserving dock-readiness transaction reveals a persistent replacement-flow
law that changes the task-value-maximizing downstream inspection action.

The object is paper-and-pencil only. It establishes no APFI efficacy,
representation necessity, containing-RNN inferiority, general dynamic-`N`, UAV
performance, safety or deployment. The exact first closure question is whether
the readiness response is a legitimate action-conditioned physical scheduler
observation or an oracle label for the hidden law.

## Source-grounded operational bridge

The following are operational grounding, not evidence for the proposed toy
effect:

- NASA demonstrated UAV inspection of high-voltage transmission structures
  with onboard sensing, GPS, ground-station logging and real-time tracking:
  `https://ntrs.nasa.gov/citations/20180006297`.
- Persistent-surveillance research couples energy-constrained UAV trajectories
  and charging schedules and uses time between visits as a service endpoint:
  `https://arxiv.org/abs/1908.05727`.
- MIT demonstrated persistent multi-UAV operation with automated battery swaps,
  including a three-hour mission and more than 90 swaps:
  `https://acl.mit.edu/projects/automated-battery-management-system`.
- DJI documents unattended dock operation, nominal recharge timing, Cloud API
  access and read-only task/charge properties:
  `https://enterprise.dji.com/dock-2/specs`,
  `https://enterprise.dji.com/dock-2/faq`, and
  `https://developer.dji.com/doc/cloud-api-tutorial/en/api-reference/dock-to-cloud/mqtt/dock/dock2/properties.html`.

The multi-dock bank, hidden cadence pair, non-reserving readiness endpoint,
timing, reward law, sham and causal controls below are proposed toy semantics.
DJI Dock 2 itself accommodates one aircraft and does not automatically swap
batteries.

## Scientific question

After an identical battery-driven fleet exit, can one shared variable-roster
policy profitably issue a safe read-only readiness probe, infer whether the
persistent replacement cadence is fast or deferred, and choose the correct
downstream inspection allocation?

## Twin histories and persistent population-flow laws

- Target operational roster size is three UAVs.
- At `t=-1`, the same UAV exits for battery service in both twins.
- At `t=0`, both twins have identical complete policy-visible history, active
  roster `{u1,u2}`, positions, batteries, inspection-age map, dock occupancy
  and charge stocks, link state, clock, legal-action mask, identifiers and
  policy-visible bytes.
- The sole difference is latent transition law `Z`, which is absent from every
  policy input:
  - `FAST`: while a vacancy exists, one replacement may join at `t=3,5,7,...`;
  - `DEFERRED`: while a vacancy exists, one replacement may join at
    `t=7,11,15,...`.
- Battery-exit dynamics are identical. Both downstream actions leave enough
  energy that no additional sink occurs before `t=6`.
- The cadence continues after the first join, so the contrast is a persistent
  source law rather than a scripted one-off arrival.
- The downstream decision is at `t=2`, before a passive arrival can disclose
  `Z`.

Thus current roster, physical state, legal actions and all pre-probe policy-
visible information are identical while the persistent future source laws
differ.

## Probe, sham and legality

At `t=0`, `u1` flies the same inspection micro-loop in all arms.

- `READINESS_CHECK`: transmit a fixed-size, non-reserving
  `can_fill_vacancy_by_t3?` transaction. At `t=1`, the scheduler returns `r=1`
  under `FAST` and `r=0` under `DEFERRED`.
- `SHAM_LINK_CHECK`: identical trajectory, imagery, radio power, packet length,
  response latency, compute shell and cost; it contacts a law-independent
  loopback and returns a stratified balanced bit with the same marginal
  distribution.

Both cost `c=0.25` value units and perform identical useful inspection work.
Neither launches, reserves, charges, reroutes or changes a vehicle, dock queue,
calendar or task state. The intended response is a physical data-link reply
from the scheduler interface, not a simulator law label or realized future
arrival. This is a toy-level legality/safety assertion only.

## Opposite legal actions and exact value witness

At `t=2`, the identical legal set is:

- `EXPAND`: send `u2` to a time-critical remote spur;
- `HOLD`: retain `u1,u2` on the critical trunk.

The remote spur yields six units only if dispatched at `t=2`. Critical-trunk
service yields eight units only with two UAVs by `t=3`; a later replacement
cannot reach the spur inside the horizon.

| Hidden law | `EXPAND` | `HOLD` | Unique optimum |
| --- | ---: | ---: | --- |
| `FAST` | `8 trunk + 6 spur = 14` | `8` | `EXPAND` |
| `DEFERRED` | `0 trunk + 6 spur = 6` | `8` | `HOLD` |

With a balanced law prior, the best passive action is `EXPAND`, worth `10`.
Truth-conditioned action is worth `(14+8)/2-c = 10.75`. An optimal sham policy
cannot exceed passive value before paying the matched cost.

## Information and leakage boundary

Policy input contains the complete roster/event history, per-UAV position and
energy, inspection ages, link health, clock, legal mask, prior actions, and the
response only after the chosen transaction. It excludes `Z`, dock-calendar
bytes, future arrivals, scenario/seed names, truth-coded identifiers,
law-dependent latency, reward lookahead and collector-only fields. Law and sham
response bits are marginally balanced. Any pre-response law prediction above
the balanced prior invalidates the object.

The response is the one prospectively declared observation caused by the legal
probe and arrives before the downstream action. Direct exposure of `Z` or a
realized future arrival is invalid.

## Treatment and exact-containing comparator

`APFI` uses one shared permutation-invariant roster encoder and recurrent
population-flow state

```text
b_t=(posterior source-cadence belief,predicted join hazard,predicted sink hazard).
```

Probe and downstream-action heads consume this state.

`RNN-CONTAIN` uses the same roster encoder, complete observation/action/response
history, legal actions and probe opportunity, followed by an unconstrained
recurrent state with the same primitive update functions and at least the APFI
state dimension. Freeing the anchored block's weights gives the generic model;
setting one recurrent block and its heads to the APFI update exactly recovers
every APFI policy. APFI is a parameter subset, not a larger-information arm.
Real, sham and no-probe arms exist for both models.

## Causal controls

- `REAL/SHAM` separates information value from matched physical work.
- `HISTORY_SWAP` crosses admissible public histories with both laws while
  preserving current state; pre-response belief/action must remain law-blind.
- `RESPONSE_SWAP` exchanges truthful bits without changing future laws or
  trajectories. Truth-following then yields `(8+6)/2=7`, versus `11` before
  common probe cost. Retained benefit rejects the intended pathway.
- `DOWNSTREAM_ACTION_CLAMP` separately forces `EXPAND` and `HOLD`; within each
  law/action, real and sham trajectories/returns must match except message
  contents.
- `NO_RESPONSE_CLAMP` masks the real reply; value must fall to the best passive-
  information policy.

## Fatal alternatives and validity stops

1. A generic full-history RNN or simple response-conditioned policy may learn
   the sufficient belief without an anchored flow representation. If its
   population value matches or exceeds APFI under the same real probe, further
   APFI-specific investment is unsupported.
2. If readiness reserves, launches, charges, changes a queue/calendar, changes
   scored work, or retains value under response swap/action clamp, the probe
   works physically rather than informationally and the object fails.

Stop before production if any twin byte, current physical state, legal mask or
pre-response observable differs by law; if the reply cannot be a non-reserving
action-conditioned observation; if the sham is not matched in cost, timing,
useful work and actuation shell; or if either strict optimal-action inequality
fails. Stop the response mechanism if truthful response does not beat response-
swap. If direction Pro judges the reply an oracle rather than a legitimate
physical scheduler response, this host fails and R01 becomes a complete no-host
result unless Portfolio later authorizes a newly sourced registry.

Question-relevant activity begins only if a learner later receives its first
trajectory under this frozen law/interface. No law, reward, response, mask,
sham or control may change thereafter.

## UAV bridge and claim ceiling

The bridge maps unordered active roster, UAV energy/position, inspection age,
join/exit events, link health and post-probe dock reply to inspection-loop,
readiness/loopback and trunk/spur allocation actions. The variable-`N` event is
`3->2`, then `2->3` under `FAST` or persistent `N=2` under `DEFERRED`.
The failure mode is a battery-created coverage vacancy; the endpoint is
weighted inspection freshness/critical-span service.

A valid construction supports only named-host constructibility, insufficiency
of passive pre-probe information and existence of a legal information-bearing
probe. It does not establish learning efficacy, anchored-belief necessity,
RNN superiority, general dynamic-`N`, UAV performance, safety or deployment.

## Required provider purposes and activity fence

The dedicated APFI ChatGPT Pro question must request `CLOSED` or
`REVISION_REQUIRED` on twin equality, persistent-law validity, opposite-action
arithmetic, the scheduler-reply oracle boundary, sham/clamp sufficiency, exact
RNN containment, fatal alternatives and claim ceiling. The separate Gemini
question seeks operational counterexamples, a less label-like readiness
response inside the same host, dock/charging regimes, stronger shams and
toy-to-UAV failure modes. Answers and conversations remain mutually blind.

This card authorizes no provider send, CM request, source, build, test,
simulation, identity, coordinate, model, training, evaluation, result, lease,
compute, production, deployment, flight or Git action.
