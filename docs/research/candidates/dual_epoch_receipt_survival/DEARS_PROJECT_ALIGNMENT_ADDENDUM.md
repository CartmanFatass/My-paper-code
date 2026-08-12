# Dual-Epoch Receipt Survival project-alignment addendum

Owner: `direction:dual-epoch-authenticated-receipt-survival` Explorer Manager  
Applies to: `DEARS-B1-DUAL-VERIFIER-v1`  
Relation to the science card: project alignment and outcome-to-design routing
only. It does not change the frozen host, treatment, comparators, observables,
budget, activity boundary, or interpretation rules.

## Classification

Dual-Epoch Receipt Survival is **not a variable-`N` or variable-`k` MARL
algorithm candidate**. Its frozen host has one decision, a one-member visible
roster, supervised labels, no online reinforcement learning, no coordination,
and no change in agent count or selected skill period.

It is an **answer-changing enabling experiment for variable-`N` fleet churn and
role rebinding**. The result can decide whether a later dynamic-roster algorithm
should expose a fail-closed lifecycle summary to the policy, or whether a
capacity-matched generic recurrent policy can learn the same decision directly
from raw event history on held-out identities and time offsets.

The bridge is strongest for state ownership across leave, rejoin, replacement,
and role reassignment:

- owner lineage represents whether recurrent state or a prior commitment still
  belongs to the same persistent entity after active-set changes;
- skill/lease lineage represents whether the role or duty under which that state
  was written remains valid through renewal and handoff;
- receipt content represents an action-relevant prior commitment, such as a
  coverage sector, relay parent, charging reservation, or handoff target;
- `live` is a proposed reuse guard: restore or consume prior state only when its
  entity owner and role/lease authority both remain continuous; otherwise reset
  and replan rather than transferring stale state through a reused slot.

This is only weak enabling evidence for variable `k`. Lease offsets and renewal
events test validity across temporal handoffs, but B1 neither selects nor adapts a
skill period, compares policies across held-out `k`, nor measures a benefit from
variable duration. It therefore cannot choose a variable-`k` algorithm.

## Outcome-to-algorithm decision map

| B1 observation | Consequence for a later variable-`N` algorithm |
|---|---|
| `GRU-DUAL` satisfies learned sufficiency, `GRU-ORACLE` establishes common-learner access, and `GRU-DUAL` has the registered advantage over `GRU-RAW` | Retain an explicit lifecycle-state carrier in the next dynamic-roster toy. Key persistent state by entity/lifecycle identity, update role ownership through authenticated owner and lease transitions, and expose a fail-closed reuse/reset summary rather than requiring the policy GRU to rediscover equality chains from raw opaque events. Keep `GRU-RAW` as the strongest learned recurrent baseline. This supports testing the architecture; it does not yet establish MARL or UAV value. |
| `GRU-DUAL` and `GRU-RAW` are both high and within the card's equivalence band | Do not claim an abstraction advantage and do not add a learned dual-lineage module. Use the simpler generic recurrent history path with correct lifecycle masks as the learned baseline. A deterministic reuse guard may still be a safety/protocol primitive, but B1 gives no reason to count it as an adaptive algorithmic contribution. |
| `RULE-DUAL` is exact but learned `GRU-DUAL` is low | The summary is deterministically sufficient but the learned decoder is unreliable under the frozen learner and budget. For the next variable-`N` design, prefer a deterministic state-retention/reset rule at the lifecycle boundary; do not promote a learned receipt decoder. This outcome does not refute owner/lease semantics. |
| `GRU-ORACLE` does not establish common-learner access, or the raw-history gap is not separable from a general learner/budget failure | Do not change the variable-`N` architecture on the basis of the raw-history shortfall. The experiment has not isolated representation from optimization or capacity. A new run is warranted only if Root still needs that distinction and a materially better comparator can answer it. |
| Failure is confined to forgery, owner-break, or lease-break cells | No dual-lineage promotion. Forgery failure removes any fail-closed safety claim. Owner-break failure means safe state ownership/rebinding under roster change remains unsupported. Lease-break failure prevents using the result for role/skill continuity. A surviving single axis is descriptive enabling evidence only and must earn its own dynamic-roster discriminator. |
| A ceiling violation, wrong rule action, split overlap, missing cell, or pre-activity terminal occurs | No scientific algorithm update. Unchanged-science repair remains CM work; it is not evidence against the direction. |

The strongest alternative is deliberately preserved in every branch: the
verifier already computes a lossless three-symbol action code, and
`RULE-DUAL` decodes it exactly. Even a positive learned result favors a
structured deterministic lifecycle transition plus a normal policy more
directly than it favors a new learned neural module.

## Toy-to-UAV bridge

A positive B1 result may justify one later variable-`N` MARL toy, not immediate
UAV promotion. That toy must add the capability B1 lacks:

1. one parameter-shared policy runs across several roster sizes and experiences
   within-episode join, leave, rejoin, terminal replacement, and slot reuse;
2. an action-relevant commitment is written before churn and is beneficial only
   when restored to the same surviving entity under a still-valid role, while
   stale transfer after replacement or lease expiry causes measurable task loss;
3. the lifecycle-summary arm is compared with an otherwise matched generic
   recurrent raw-history arm and a correctly masked fixed-slot recurrent arm;
   the deterministic lifecycle rule is retained as a required simple comparator;
4. evaluation includes a held-out roster size or held-out membership process and
   reports external-return or robustness benefit, not receipt classification;
5. the toy excludes fixed-slot identity shortcuts and distinguishes persistent
   entity, physical slot, service-active membership epoch, role, skill lease, and
   recurrent-state owner.

The corresponding UAV semantics are concrete but prospective:

- persistent entity: a physical UAV or explicitly declared replacement asset;
- active membership: whether that UAV currently participates in communication
  service while charging, detached, failed, or rejoining;
- owner epoch: which lifecycle currently owns recurrent state and commitments;
- role/lease epoch: the validity interval of a relay, coverage, sensing,
  charging, or handoff duty;
- receipt content: the prior relay parent, sector assignment, reservation, or
  other commitment whose reuse can help recovery;
- external value: QoS/connectivity return, safety, recovery time or recovery
  regret after churn, compared under matched training and evaluation exposure.

This mapping is compatible with the existing UAV distinction between physical
fleet and service-active roster. It does not assert that current UAV code emits
authenticated receipts or that dual lineage is necessary there. A promoted UAV
test must construct the lifecycle interface explicitly and compare it with the
strongest correctly masked recurrent reduction.

## Continue/stop judgment

Continue the currently assigned CM construction and its one frozen real run.
The run is worth completing because its main outcomes choose between two
different variable-`N` design paths: an explicit fail-closed state-ownership
carrier, or a generic recurrent/masked history path. No treatment change or
extra pre-result review is needed.

The continuation is bounded. A supported `GRU-DUAL` versus `GRU-RAW` advantage
licenses only the variable-`N` MARL toy above. Equivalence licenses no learned
module and ends the abstraction-advantage branch. Exact `RULE-DUAL` with weak
learners routes toward deterministic lifecycle handling rather than more decoder
tuning. Axis-specific, non-identifying, or no-data outcomes do not justify UAV
promotion; unchanged-science technical repair stays with CM, while any new
scientific treatment returns to this direction EM.

## Claim ceiling

At most, B1 can show that a fail-closed summary of authenticated receipt,
owner-lineage continuity, and skill/lease-lineage continuity is deterministically
sufficient and, under the frozen finite learner and held-out panel, easier to
learn than raw relational history. It can make an explicit lifecycle carrier a
reasonable component to test in a variable-`N` MARL toy.

It cannot establish variable agent-count handling, variable skill-period
adaptation, survivor-state correctness in an online multi-agent process,
coordination, robustness or task-performance improvement, superiority over a
deterministic state machine, cryptographic security, UAV transfer, or real-world
deployment value. Each of those requires later evidence on the corresponding
toy or UAV process.
