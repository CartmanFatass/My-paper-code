# Typed lifecycle selective-retention online churn discriminator

Authoring scope: `direction:dual_epoch_project_bridge`  
Recommended program placement: later treatment in `variable-N fleet churn`  
Treatment identity: `VNFC-B2-TYPED-CAPSULE-RETENTION-v1`

## Decision first

The deterministic typed lifecycle carrier should be a **later selective-retention
treatment inside the variable-N Fleet Churn program**, not a scientifically
separate portfolio direction.

The remaining answer-changing question is no longer whether a verifier can compress
a bounded receipt history. It is whether selective restoration changes external
cooperative return and recovery under real within-episode roster churn. That is a
variable-`N` fleet-churn treatment question. The current `VNFC-B1` host cannot
answer it: dropped identities never return, there is no private fact or role-state
payload to recover, and every learned arm is memoryless across its three allocation
events. Adding capsule flags to that host would therefore be an inert or
label-like graft.

`VNFC-B2-TYPED-CAPSULE-RETENTION-v1` must be constructed as a separate successor
surface without changing `VNFC-B1`. It uses the same program-level destination—one
shared policy under varying roster membership—but isolates a new treatment-level
uncertainty: whether entity memory and entity-bound role memory should have
different lifecycle masks.

The named `VARIABLE_N_FLEET_CHURN_SCIENCE_CARD.md` is used only as a Root-relayed
prospective host/mechanism inspiration packet. No result, threshold, acceptance,
claim, or scientific authority transfers from that direction into this card.

## Same-direction External Pro intake

The completed constructive review agrees with the narrow B1 interpretation:
`(live, content-or-bottom)` is a target-sufficient three-symbol code, and a
`GRU-DUAL` versus `GRU-RAW` gap is a finite-budget preprocessing and inductive-bias
result, not a Bayes-information gap or proof that dual lineage is universally
necessary. Its useful project recommendation is to move from supervised receipt
decoding to external task return under actual churn, keep identity and authority
checks deterministic, and compare typed retention with a relationally adequate
raw recurrent baseline.

This card adopts four review points:

1. authorization to consider stored state is a hard lifecycle fact; usefulness of
   valid state remains a task-policy question;
2. owner continuity and role/lease continuity must mask distinct payloads rather
   than one slot-indexed recurrent tensor;
3. the raw comparator receives primitive verified lifecycle relations so that its
   loss cannot be blamed on learning equality over opaque bit strings; and
4. a positive toy result remains variable-`N` evidence only. Exogenous lease
   duration does not identify adaptive skill period `k`.

The review also discussed transferable role-owned state across different entities.
That is intentionally outside this treatment. Here `RoleCapsule` is an
**entity-bound role/commitment capsule**: replacement or any owner break deletes
both capsules even when the public role label or tensor slot is reused. A future
authenticated cross-owner handoff would be a different scientific treatment.

## Science card

### Question

In a cooperative partially observed relay-coverage task with one shared policy
across roster sizes, does deterministic typed selective restoration:

- retain an `EntityCapsule` after temporary leave and rejoin by the same entity;
- retain a `RoleCapsule` only when that same entity's role/lease authority is
  continuous; and
- delete both on replacement or owner-generation break,

improve external task return or reduce post-event recovery regret relative to
resetting all memory and to a capacity-matched raw-history masked recurrence,
without increasing stale-state errors?

### Protected lifecycle semantics

Opaque entity, owner-generation, role, lease-generation, and membership-session
handles are registry keys only. Their raw numeric or textual encodings are never a
policy input. The registry maps active rows to state after each fresh row
permutation.

`EntityCapsule` is keyed by persistent entity and owner generation. A membership
epoch changes on every leave/rejoin session so stale in-flight messages cannot be
accepted, but that session change alone does not delete the entity payload.

`RoleCapsule` is keyed by the same entity and owner generation plus the current
role and lease generation. It is valid only while role/lease authority is
continuous. In this treatment it never transfers across owners.

The deterministic masks are:

| Event cell | Lifecycle fact | Entity mask | Role mask |
|---|---|---:|---:|
| `C0_NO_CHURN` | same live entity, same continuous lease | 1 | 1 |
| `C1_SAME_ENTITY_SAME_ROLE` | temporary absence; same entity and owner generation return; membership epoch changes; lease authority remains continuous | 1 | 1 |
| `C2_SAME_ENTITY_NEW_ROLE` | temporary absence; same entity and owner generation return; old lease closes and a new role/lease is issued | 1 | 0 |
| `C3_REPLACEMENT_SAME_SLOT` | old owner leaves; different entity/new owner generation enters the same transport slot and receives the same public role label under a new lease | 0 | 0 |

Invalid, ambiguous, forged, duplicate, out-of-order, or missing lifecycle edges
fail closed. A learned gate cannot override a zero mask. Slot equality and repeated
role labels are not continuity evidence.

### Host and task dynamics

The host is a small cooperative relay-coverage partially observed Markov game.
There are two persistent public service roles, `RELAY` and `COVERAGE`. An episode
has ticks `0..11`.

- At tick `0`, each initially active entity receives a one-tick private calibration
  cue `e_i in {0,1}`.
- At tick `1`, each entity receives a one-tick private synchronization cue
  `q_l in {0,1}` for its current continuous role lease `l`.
- Ticks `2..11` are rewarded service ticks. At every service tick, each role has a
  fresh public phase `z[r,t] in {0,1}` and each active entity has a fresh public
  energy cost `eta[i,t] in [0.01,0.03]`.

All bits are independent fair draws except where lifecycle continuity requires a
fact to persist. Entity calibration persists for one owner generation. Lease phase
persists for one continuous lease. A replacement draws a fresh calibration and
lease phase; a new role/lease for the same entity draws only a fresh lease phase.

Every active entity has one public current role lease. Each roster contains at
least one leaseholder for each role. For `C2`, the focal entity is sampled from a
role with at least two leaseholders, then receives the other role at return, so
both roles remain serviceable without changing another entity's lease. For `C3`,
the replacement receives the departed entity's public role label, making slot or
role-label reuse actively misleading.

At a rewarded tick, each active agent chooses one action from:

`IDLE`, `PROBE_ENTITY`, `PROBE_ROLE`, `SERVE_0`, or `SERVE_1`.

`PROBE_ENTITY` or `PROBE_ROLE` consumes the current service opportunity and exposes
the requested current fact as a one-tick cue in the next observation. A valid cue
may then populate the corresponding explicit capsule in the typed and reset arms
or be encoded by recurrence in the raw arm. Only one fact can be probed per tick.

For an agent with current lease `l` for role `r`, service mode `m` is correct iff

`m = e_i XOR q_l XOR z[r,t]`.

Thus neither capsule alone determines an action, and even both capsules are
insufficient without the current public phase. Agents with the same role must also
use current energy costs and the active-set context to avoid redundant service.

Let `correct[r,t]` be the number of current leaseholders of role `r` selecting the
correct service mode, `wrong[t]` the number of incorrect service actions,
`duplicate[t] = sum_r max(correct[r,t]-1,0)`, and `probe[t]` the number of probe
actions. Shared reward is

`reward[t] = 0.5 * sum_r 1[correct[r,t] >= 1]`
`            - 0.25 * wrong[t]`
`            - 0.05 * duplicate[t]`
`            - 0.05 * probe[t]`
`            - sum_i eta[i,t] * 1[action_i is SERVE]`.

The reward is task-external: there is no receipt label, reuse label, lifecycle
classification loss, oracle imitation, or action target in training.

### Roster sizes, schedules, and shortcut controls

One parameter-shared actor is trained at initial active sizes `N in {3,4}`. The
focal entity's absence produces temporary active sizes `2` or `3`. `N=5` is absent
from training and is the held-out roster size.

Training samples the four event cells uniformly and samples these schedules
uniformly:

- `S1`: leave or checkpoint at tick `4`, return after one inactive tick at tick `5`;
- `S2`: leave or checkpoint at tick `6`, return after two inactive ticks at tick
  `8`.

The held-out churn schedule is:

- `S*`: leave or checkpoint at tick `5`, return after three inactive ticks at tick
  `8`.

`C0_NO_CHURN` receives the checkpoint token at the named leave time but has no
absence or lifecycle change. It anchors ordinary memory access over the same
horizon.

Evaluation has four disjoint panels so size and schedule generalization are not
conflated:

1. seen size/seen schedule: `N in {3,4}`, `S1` and `S2`;
2. held-out size only: `N=5`, `S1` and `S2`;
3. held-out schedule only: `N in {3,4}`, `S*`;
4. joint holdout: `N=5`, `S*`.

Fresh opaque handles and fact bits are sampled per episode. Input rows are freshly
permuted at every tick; no stable slot index is observed. Evaluation repeats each
base world under stable-role order, reverse order, and two counter-keyed random
row-order tapes, maps actions back through the external registry, and averages
replicas before seed-level analysis. A material order-dependent physical action or
reward is an implementation/equivariance defect, not treatment evidence.

### Treatment and comparators

All learned arms use separate weights but the same parameter count, actor/critic
widths, optimizer work, episode worlds, fact/event exposure, action space, and
training budget.

The common actor embeds each public agent row with a `64 -> 64` SiLU MLP, combines
the local row with masked DeepSets mean and sum summaries, passes the result through
a 64-unit GRU, and emits the five-action categorical policy. The centralized
training critic uses the same active-set summaries and a 64-unit recurrent core.
All arms reserve identical input slots for `(entity_valid, entity_payload,
role_valid, role_payload)` and receive the chronological primitive lifecycle
event stream.

1. `TYPED-SELECTIVE-CARRIER`: the registry stores the acquired entity and role
   facts in separate capsules. Before the actor step, the hard table above exposes
   only valid payloads and bottom-masks invalid payloads. The transient actor GRU
   is reset on leave/rejoin or rebind, so the named persistent information path is
   the typed carrier rather than an unlogged slot state.
2. `RESET-ALL-MASKED-RECURRENT`: identical explicit capsules and policy, but any
   leave/rejoin, role rebind, replacement, or owner break clears both capsules and
   resets the actor GRU. `C0` does not reset. The arm can reacquire facts only by
   probing.
3. `RAW-HISTORY-MASKED-RECURRENT`: the four reserved capsule slots are zero. It
   receives the original fact cues, probe cues, and every chronological lifecycle
   event. Primitive verified relation fields include event type, same-owner edge,
   owner-generation continuity, same public role, lease-edge continuity, absence
   age, and active mask, but never opaque handle values or final capsule-validity
   decisions. Its 64-unit recurrent state is stored by persistent entity outside
   the numerical policy and is hard-reset on owner break, so it cannot inherit a
   replacement's slot. On same-owner role rebinding it must learn from raw event
   history how to preserve entity information while discarding obsolete role
   information.

This raw comparator deliberately removes the frozen B1's bitwise-identity and
interval-parsing burden. A typed advantage is therefore about explicit state-scope
factorization and lifecycle accumulation at this finite budget, not about one arm
being handed authenticity while another must infer it from opaque strings.

A nonexecuted `FRESH-FACT ORACLE` observes current true entity and lease facts and
enumerates the lowest-cost correct joint service choice for both roles. It supplies
an access ceiling and the recovery-regret counterfactual; it is not a learner,
feature source, or training label.

### Training and scientific counts

Use centralized-training recurrent PPO for every learned arm:

- Adam learning rate `3e-4`, PPO clip `0.20`, `gamma=0.99`, GAE `lambda=0.95`,
  value coefficient `0.5`, entropy coefficient `0.01`, gradient clip `0.5`;
- 32 updates, 128 twelve-tick episodes per update, four PPO epochs per update,
  minibatch size 256 agent-event rows; and
- final update-32 checkpoint only. Validation is reporting-only and cannot choose
  a checkpoint, seed, width, threshold, or hyperparameter.

The eight paired base seeds are

`[1301,1321,1361,1381,1423,1451,1481,1511]`.

Per arm and seed, training is exactly 4,096 episodes. Evaluation uses 32 disjoint
base worlds for every event-cell, size, and schedule combination in panels 1--3
and 64 disjoint base worlds per event cell in the joint-holdout panel, each under
the four row-order replicas. All world, fact, schedule, initialization, sampling,
minibatch, and evaluation namespaces are counter-keyed by base seed and arm where
appropriate. Arm execution order cannot change a world.

### Observables

Average row-order replicas within a base world, worlds within a seed, and use the
eight paired seeds as analysis units. Report seed values, paired mean, standard
deviation, and two-sided 95% Student-`t` interval for every named contrast.

1. **External return `J`**: mean shared reward over ticks `2..11`, reported by arm,
   event cell, size/schedule panel, and seed.
2. **Three-step recovery regret `RR3`**: from the focal return tick—or the matched
   checkpoint for `C0`—sum `reward_fresh_oracle[t] - reward_arm[t]` over the next
   three rewarded ticks on the same exogenous world. Lower is better.
3. **Hard stale-state errors**: counts of a non-bottom entity payload under
   `entity_mask=0`, a non-bottom role payload under `role_mask=0`, and any capsule
   mapped across an owner-generation break. These must be exactly zero for the
   typed arm; any nonzero count is non-identifying implementation output, not a
   scientific loss.
4. **Behavioral stale-command rate `SCR`**: in `C2` and `C3`, among focal
   post-return service decisions where the command implied by invalid old facts
   differs from the current correct command, the fraction selecting that old
   command. This is a safety outcome, not proof that a hidden state caused an
   individual action. For arm `a`, seed `s`, cell `c`, and evaluation panel `p`,
   sum over all focal decisions from return through tick `11` after mapping the
   four row-order replicas back to the physical entity:

   `E[a,s,c,p] = sum 1[action is SERVE_0 or SERVE_1 and old_command != current_command]`

   `K[a,s,c,p] = sum 1[eligible and action == old_command]`

   and define `SCR[a,s,c,p] = K/E`. For this conditional rate only, numerator and
   denominator are pooled across the registered replicas and base worlds within a
   seed; do not average per-world ratios. Report `K` and `E` with every rate.

   If `E=0`, `SCR` for that arm/seed/cell/panel is undefined. Do not impute zero,
   drop the seed, pool across seeds, or substitute an idle/probe action as a safe
   service decision. A paired `SCR_TYPED-SCR_RESET` interval for a cell exists only
   when both arms have `E>0` in all eight paired seeds. In the joint-held-out panel,
   support condition 4 requires a defined eight-seed interval separately in both
   `C2` and `C3`; a zero denominator for either required arm in any seed makes the
   affected SCR safety condition unavailable, so the full treatment-level pattern
   cannot be supported from this run. It is non-separation of the conditional
   safety claim, not evidence of harm. `J`, `RR3`, `D_E`, `D_ER`, hard stale-state
   counts, and every other well-defined contrast remain independently
   interpretable under their own registered conditions.
5. Report probe counts, time to first correct post-return service, wrong and
   duplicate actions, per-role coverage, permutation deviations, actual parameter
   and optimizer counts, CPU time, peak RSS, and inference p50/p95 by `N` as
   diagnostics.

The most informative selective-retention estimands use regret because replacement
provides a matched cell where both capsules should reset:

`D_E = (RR3_RESET - RR3_TYPED)[C2] - (RR3_RESET - RR3_TYPED)[C3]`

`D_ER = (RR3_RESET - RR3_TYPED)[C1] - (RR3_RESET - RR3_TYPED)[C3]`.

`D_E` isolates the value of retaining entity state while invalidating role state;
`D_ER` isolates retaining both under continuous owner and lease authority. Also
report `RR3_RAW - RR3_TYPED` and `J_TYPED - J_RAW` in every cell rather than only an
aggregate.

### Interpretation and support conditions

The treatment-level pattern is supported in the joint held-out panel only if:

1. `D_E` and `D_ER` each have paired mean at least `0.10` regret units and a 95%
   lower bound above zero;
2. typed retention clears one common metric against `RESET` across both retention
   cells. This condition holds iff either (a) `J_TYPED-J_RESET` has paired mean at
   least `0.05` and a 95% lower bound above zero separately in both `C1` and `C2`,
   or (b) `RR3_RESET-RR3_TYPED` has paired mean at least `0.10` and a 95% lower
   bound above zero separately in both `C1` and `C2`. The metric may not switch by
   cell: `J` qualifying only in one cell and `RR3` only in the other does not
   satisfy this condition, though both cell-specific observations remain
   reportable;
3. in `C3`, typed and reset are practically equivalent: the 90% paired intervals
   for both `J_TYPED-J_RESET` and `RR3_RESET-RR3_TYPED` lie wholly within
   `[-0.03,+0.03]`;
4. typed hard stale-state errors are zero, and, separately in both `C2` and `C3`,
   the defined eight-seed 95% interval for `SCR_TYPED-SCR_RESET` has upper endpoint
   at most `+0.02`; and
5. the fresh-fact oracle is materially above at least one learned arm on a frozen
   joint-holdout recovery contrast. For each learned arm `a`, first form one value
   per paired base seed after the registered row-order and world averaging, then
   average `C1` and `C2` with equal weight:

   `OracleGap_J[a] = mean_(c in {C1,C2})(J_ORACLE[c] - J_a[c])`

   `OracleGap_RR3[a] = mean_(c in {C1,C2})(RR3_a[c] - RR3_ORACLE[c])`

   where higher `J` and lower `RR3` are better and `RR3_ORACLE=0` by definition.
   Oracle headroom exists iff, for at least one prespecified learned arm in
   `{TYPED, RESET, RAW}`, either the paired mean `OracleGap_J` is at least `0.05`
   return units with its two-sided 95% Student-`t` interval lower bound above zero,
   or the paired mean `OracleGap_RR3` is at least `0.10` regret units with its
   two-sided 95% Student-`t` interval lower bound above zero. The eight paired base
   seeds are the analysis units; neither event cells nor metrics may be selected
   post hoc.

If no learned arm satisfies either oracle-headroom rule, support condition 5 fails:
the joint-held-out surface is saturated at the resolution registered here, so it
cannot support the selective-retention treatment-level pattern even if another
typed-versus-comparator contrast is numerically favorable. Report those contrasts
descriptively, do not add seeds merely to create headroom, and do not interpret the
failure as evidence against the hard lifecycle masks, replacement safety, or the
carrier on a harder task surface.

An **explicit typed-carrier advantage over learned raw history** additionally
requires typed to improve joint-holdout `C2` return by at least `0.05` or reduce
`C2` `RR3` by at least `0.10` relative to raw recurrence, with a paired 95% lower
bound above zero. The raw arm must also be practically equivalent to typed in
`C0` ordinary-memory access: the 90% intervals for its return and regret contrasts
must lie within `[-0.03,+0.03]`. If raw is already deficient in `C0`, churn results
cannot isolate lifecycle factorization from general recurrent access failure.

Other patterns mean:

- typed beats reset but matches raw: memory retention matters, but deterministic
  typed factorization is not needed at this budget;
- typed and raw beat reset in `C1` but not `C2`: generic persistence is useful, but
  selective entity-versus-role retention is unsupported;
- typed gains in `C1/C2` but is worse than reset or has more stale commands in
  `C3`: no robustness or safety claim; the owner-break path or task policy remains
  confounded;
- reset matches typed and both are close to the oracle: reacquisition is cheap or
  the stored facts are not task-important here; do not invest in the carrier from
  this surface;
- all learned arms are far below the oracle, or raw is weak in `C0`: the named
  mechanism comparison is unresolved; more seeds alone are not the next action;
- row-order dependence, split/world contamination, wrong lifecycle masks, missing
  event cells, changed schedules, or incomplete paired output makes the affected
  contrast non-identifying. Before complete output it is CM engineering work.

Question-relevant activity begins when all three learned arms for one paired seed
have final checkpoints and emit every event cell in all four evaluation panels,
the fresh-oracle counterfactuals, stale-state instrumentation, and all four
row-order replicas. A launcher attempt, training curve, partial arm, or single cell
is not question-relevant output.

## Strongest alternative explanation

The strongest surviving explanation for a positive result is that this constructed
host makes two target-sufficient private bits costly to reacquire and gives the
typed arm a deterministic cache, while a finite 64-unit recurrent learner must
preserve and selectively overwrite the same historical facts. A gain would show a
useful finite-budget inductive bias under the tested churn, not that recurrence
cannot represent the solution or that every UAV state has these two scopes.

The host's exogenous two-role leases, XOR service rule, explicit lifecycle
relations, and probe cost also favor the declared decomposition. The raw arm's
`C0` access check, relation-level inputs, owner-safe registry, equal capacity and
budget, fresh oracle, and cellwise replacement control bound this alternative but
do not eliminate host specificity. The deterministic router—not a learned state
ownership rule—remains the candidate contribution.

## Claim ceiling

Any positive result supports at most this claim:

> In this constructed two-role relay-coverage game, one shared policy with a
> deterministic entity/role typed carrier improved external return or three-step
> churn recovery on the tested held-out roster and churn schedule, while respecting
> the declared replacement and role-break masks, relative to the named matched
> baselines at the frozen finite budget.

It does not establish universal state-ownership semantics, real-UAV performance or
safety, cryptographic authentication, arbitrary churn, cross-owner role transfer,
scalability, decentralized communications, learned lifecycle verification, or
adaptive skill period `k`. A negative or equivalent task result does not make the
fail-closed replacement rule unsafe; it says only that selective cached payloads
did not add external value on this surface and budget.

## Toy-to-UAV bridge

| Toy object | UAV meaning |
|---|---|
| persistent entity and owner generation | one physical UAV and the generation authorized to own its stored state |
| membership leave/rejoin | charging, temporary detachment, transient loss of service membership, then verified return |
| `EntityCapsule` calibration fact | vehicle calibration, battery/health estimate, actuator bias, or entity-local map feature |
| continuous role lease | uninterrupted relay, sector-coverage, or charging-duty authority |
| `RoleCapsule` synchronization fact | same-UAV relay channel/queue commitment, sector plan, or charging rendezvous commitment |
| same entity/new role | returning UAV receives a new relay or coverage assignment; keep entity state and discard the old commitment |
| replacement in the same slot | a new UAV inherits a tensor row, callsign, or public role label; transfer neither capsule |
| public phase and energy cost | current geometry/link phase, demand, battery cost, and other agents' active state |

Promotion requires task-native value: connectivity or delivered QoS, coverage or
tracking utility, energy, churn-conditioned recovery regret, and stale-transfer or
safety violations against the strongest entity-safe recurrent comparator. Opaque
aircraft identifiers remain runtime keys rather than a learned coordination
codebook.

## One next discriminator after this one

Only if typed retention beats both matched baselines with the required cell pattern
and stale-state bounds, move the same carrier into one 2-D kinematic fleet-service
surface with absence-induced geometry and neighbor drift. Compare deterministic
`always restore authorized state` with a learned `reuse versus refresh` gate that
may reject valid-but-aged state but can never override an invalid hard mask. Measure
external QoS/coverage return and churn-conditioned recovery regret. This single
follow-up separates lifecycle authorization from learned task usefulness and is
the minimum bridge before a project UAV simulator.

## Root-to-CM construction packet

Construction is scientifically warranted because the same-direction B1 emitted
complete identifying data on its registered positive representation branch, and
the successor asks the missing online task-value question. Route this card to CM
with the following exact request:

> Construct `VNFC-B2-TYPED-CAPSULE-RETENTION-v1` as a new isolated successor host
> and runner from this card. Do not modify or graft state into `VNFC-B1`. Implement
> the four event cells, protected two-capsule lifecycle table, three matched learned
> arms, fresh-fact oracle, shared-policy train sizes, held-out roster and schedule
> panels, row-permutation mapping, external reward, `J`, `RR3`, hard stale-state
> counts, behavioral stale-command rate, and frozen paired analysis exactly as
> specified. Opaque identity values remain outside every numerical policy input;
> replacement or owner break deletes both capsules. Return whether
> question-relevant output was produced; per-seed/per-cell/per-panel observations
> and named contrasts; activity and anomaly facts; actual sample, parameter,
> optimizer, time, memory, and latency counts; and what remains unknown. Missing
> host, code, runner, lifecycle registry, or adapter is construction work. Before
> question-relevant data, launcher or runtime failures return for unchanged-science
> repair rather than scientific reinterpretation.

Root retains the portfolio and scheduling decision. This packet authorizes neither
a change to `VNFC-B1` nor a separate portfolio direction.
