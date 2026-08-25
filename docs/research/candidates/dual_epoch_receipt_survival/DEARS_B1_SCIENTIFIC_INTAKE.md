# Dual-Epoch Authenticated Receipt Survival B1 scientific intake

Owner: `direction:dual-epoch-authenticated-receipt-survival` Explorer Manager  
Treatment: `DEARS-B1-DUAL-VERIFIER-v1`  
Science card: [`DUAL_EPOCH_AUTHENTICATED_RECEIPT_SURVIVAL_SCIENCE_CARD.md`](DUAL_EPOCH_AUTHENTICATED_RECEIPT_SURVIVAL_SCIENCE_CARD.md)  
Project bridge: [`DEARS_PROJECT_ALIGNMENT_ADDENDUM.md`](DEARS_PROJECT_ALIGNMENT_ADDENDUM.md)  
Result: [`DEARS_B1_RESULT.json`](DEARS_B1_RESULT.json)

## Observed result

The registered run produced question-relevant data for all ten seeds, all six
learned arms, and every refined held-out cell, with no reported material anomaly.
The scientific-activity criterion was reached. `RULE-DUAL` had worst-cell
correct-action probability `W=1.0`.

The learned worst-cell results were:

| Arm or paired contrast | Mean | Two-sided 95% interval |
|---|---:|---:|
| `GRU-DUAL` | `0.987973` | `[0.986874, 0.989072]` |
| `GRU-ORACLE` | `0.975982` | `[0.972018, 0.979946]` |
| `GRU-RAW` | `0.237095` | `[0.195102, 0.279087]` |
| `GRU-DUAL - GRU-ORACLE` | `0.011991` | `[0.008152, 0.015829]` |
| `GRU-DUAL - GRU-RAW` | `0.750878` | `[0.709156, 0.792601]` |

`GRU-DUAL` therefore clears the frozen learned-sufficiency criterion, the
oracle arm establishes that the common learner and budget can learn explicit
semantic factors, and the paired dual-minus-raw lower bound greatly exceeds the
registered `0.10` finite-budget abstraction-advantage threshold. The snapshot,
unbound-content, and validity-only arms did not violate their information
ceilings. This is the card's high-summary, exact-rule, low-raw branch.

The small positive `GRU-DUAL - GRU-ORACLE` difference is not evidence that the
summary contains more semantic information than the oracle factors. Both have
information ceiling one; it is a finite-training difference under the frozen
architecture and budget.

## Smallest scientific conclusion

In this constructed one-decision host, the fail-closed summary
`(live, content-or-bottom)` is sufficient and generalizes across held-out opaque
owner handles, owner epochs, lease handles, lease epochs, and handoff offsets.
For the frozen GRU and finite data budget, learning the three-way decision from
that summary is substantially easier than learning the required authentication
and two equality/coverage chains from raw relational history.

This supports an **explicit lifecycle-state carrier as a variable-`N` algorithm
hypothesis**. It does not support asking a policy GRU to infer lifecycle
ownership from raw churn logs when the environment or system can maintain those
facts directly.

It does not support a learned verifier module. `RULE-DUAL` is exact, and
`(0,bottom)`, `(1,0)`, and `(1,1)` are already a lossless three-symbol action
code. The difficult work was performed by the deterministic verifier. The
learned result shows finite-budget accessibility of the summary, not autonomous
lineage reasoning or adaptive superiority over a state machine.

## Concrete variable-`N` algorithm bridge

The result recommends testing a deterministic **typed lifecycle router** in
front of one parameter-shared, permutation-compatible MARL policy. The router,
not the policy network, owns identity equality, lineage updates, lease coverage,
and stale-state deletion.

The candidate carrier should distinguish two payload classes rather than bind
all recurrent state to one physical slot:

1. `EntityCapsule = (entity_handle, membership_epoch, entity_state)` stores
   state that may survive a temporary service leave and rejoin by the same
   persistent entity.
2. `RoleCapsule = (entity_handle, membership_epoch, role_handle, lease_epoch,
   valid_interval, role_state_or_commitment)` stores state that is valid only
   while both entity ownership and the named role lease remain continuous.

At every join, leave, rejoin, replacement, or role-rebinding event, the
deterministic router should expose to the shared policy only typed validity
flags and the corresponding masked payloads:

- same entity epoch after temporary leave: restore `EntityCapsule`;
- same entity and continuous role lease: also restore `RoleCapsule`;
- role/lease break with the same entity: invalidate role-specific state and
  require role replanning, while treating entity-state retention as a new
  hypothesis rather than deleting it by assumption;
- replacement or owner-epoch break: delete both old capsules and initialize a
  fresh owner state;
- invalid, ambiguous, forged, duplicate, or stale transition: fail closed and
  expose no old payload.

The policy input may include `entity_live`, `role_live`, masked entity state,
masked role commitment, current observations, and the active-set mask. Raw
opaque handles should remain routing keys outside the numerical policy input so
that a fixed identity codebook is not the cooperation mechanism. The same
policy parameters operate at every roster size and for every current entity.

No new optimizer or auxiliary receipt-classification loss follows from B1.
Training should use the actual cooperative task return. In particular, the next
toy must not expose another lossless `USE_0/USE_1/RESET` code: the restored
payload should be useful but insufficient without current observations and
other agents' state.

The two-capsule decomposition is a project design recommendation to test, not a
B1 result. B1 used one conjunction and did not contain owner-only or lease-only
summary arms, so it cannot establish whether all state should be reset when only
the role lease changes.

## Strongest remaining alternative

The strongest explanation is still deterministic preprocessing plus direct
label decoding. A simple lifecycle state machine computes the sufficient
statistic; the learner merely maps three symbols to three actions. The large
raw-history gap may reflect the frozen GRU's difficulty learning exact equality
and interval algorithms on unseen bitwise identifiers at this sample budget,
not an inherent limit of recurrent or relational models.

A second unresolved alternative is that a simpler carrier suffices. B1 does not
separate owner-only continuity, lease-only continuity, selective two-tier state,
and the monolithic dual conjunction. It therefore supports explicit state
ownership routing, but not the necessity of dual gating for every recurrent
state component.

## Smallest next discriminator before UAV work

Run one variable-`N` shared-policy fleet-churn toy whose optimal behavior
requires **selective state retention** rather than receipt classification.

The toy should have anonymous interchangeable slots and at least these matched
within-episode event cells:

1. same entity leaves and rejoins under the same role lease;
2. same entity rejoins under a new role lease;
3. a replacement entity occupies the same slot;
4. no-churn control.

Before the event, each entity acquires a private persistent fact and a distinct
role-specific commitment. After the event, good team return requires retaining
the private fact for the same entity, retaining the role commitment only when
the lease survives, and never transferring either payload to a replacement.
Neither payload alone determines the action; agents must combine it with current
observations to coordinate coverage or relay assignments.

Use one shared parameterization over multiple roster sizes, with either a held-
out size or a held-out churn schedule. The minimum informative arms are:

- `TYPED-LIFECYCLE-CARRIER`: deterministic selective entity/role restoration;
- `RESET-ALL-MASKED-RECURRENT`: the same shared policy and active masks, but all
  state is reset on leave/rebind;
- `RAW-HISTORY-MASKED-RECURRENT`: capacity- and exposure-matched recurrence over
  lifecycle events without derived carrier validity.

Measure external task return plus post-event recovery regret and stale-state
error by event cell. The lifecycle carrier is project-promising only if it
improves robustness or task performance without increasing replacement/rebind
errors. This one toy simultaneously tests whether the B1 representation
advantage survives online learning, variable roster size, multi-agent
coordination, and a non-label-like payload.

Only a positive identified result from that toy warrants UAV-simulator work.
The UAV mapping would then be physical UAV versus service-active membership,
temporary charging/detachment versus terminal replacement, and relay/coverage/
charging-role lease rebinding. Promotion value must be external: QoS or
connectivity return, recovery time/regret, and stale-state safety relative to
the strongest correctly masked recurrent baseline.

## Claim ceiling and direction action

The maximum B1 claim remains limited to the constructed one-receipt,
two-edge-per-lineage, one-decision, binary-content, supervised finite panel with
trusted updates and host-oracle authentication. It establishes neither
variable-`N` handling nor variable-`k` adaptation, online MARL, coordination,
task-return improvement, selective entity-versus-role state retention, necessity
of dual lineage, superiority over `RULE-DUAL`, UAV transfer, cryptographic
security, or deployment value.

The B1 mechanism question is answered at its stated ceiling. Do not repeat B1,
add seeds, enlarge the GRU, or tune the raw arm. Return its project-changing
primitive to Root: explicit fail-closed lifecycle routing is now justified as a
component to test in one variable-`N` MARL toy; the learned decoder and any
direct UAV claim are not.
