# VSP-02 guidance A1 current-host headroom census — science card

- Direction: `vsp_02`
- Object id: `VSP02-GUIDANCE-A1-HEADROOM-CENSUS-R01`
- Evidence class: **A/RECON**, adaptive retained-evidence census
- Frozen: **2026-09-04T07:06:00-07:00**, before the formal rule application recorded in the
  result evidence
- Authority: guidance action A1, Object tier under the standing unattended delegation
- Evidence-byte binding: `b9c63e6d8fbc6f8b74470c8e2312c2c1b42c6a8c`
- Consumption: none; A objects have no consumption state

The VSP-02 evidence surface is byte-identical between the bound commit and the freeze-time
checkout. This is a static calculation over accepted retained evidence. It does not reopen or
reinterpret B1V2 through B5R1, and it creates no learner, model, optimizer, RNG master,
checkpoint, environment process, or result-bearing experimental invocation.

## 1. Question, claim ceiling, and non-goals

On the current host family `VSP02-A2-PHYSICAL-LIFECYCLE-HOST-v1`, what native-return headroom
remains between:

1. the strongest legal policy that uses only the public cue available to the policy; and
2. the strongest accepted competent generic same-information learner, projected through the same
   deterministic greedy evaluator on the same finite held-out population?

The estimand is

```text
H_greedy = J_upper_greedy - J_generic_greedy.
```

The maximum positive claim is a finite-host measurement fact: the accepted generic learner leaves
a stated amount of native-return headroom on the declared B1V2 held-out clone population. A zero
gap means only that this generic learner's greedy action map saturates that finite host's legal
cue-to-action optimum. It does not show that Adam state is irrelevant to learning trajectories,
that the recurrent learner is competent, that carry and reset are equivalent, or that the host
binds roster-age MARL structure.

The object cannot establish a mechanism effect, sample-efficiency ordering, stable multi-seed
superiority, variable-population value, general optimizer behavior, multi-agent coordination,
transfer, UAV value, safety, deployment, direction lifecycle, priority, fusion, separation,
registration, capacity, or investment. It applies no minimum effect of interest: the guidance
MEI and its PARK/fusion proposals remain unratified Portfolio-tier choices.

## 2. Current host and event-to-consequence trace

The current physical host is the accepted B1V2 host reused by B2 through B5R1. Each episode has a
fresh lifecycle id and owner-epoch token but the following fixed structure:

- slot `3`;
- authoritative owner `owner-A` at one episode-specific epoch;
- visible roster exactly `("owner-A", "partner-B")`;
- one frozen primitive and one frozen no-op partner policy;
- one public cue observation followed by a masked decision observation;
- one owner action, `RELEASE` or `HOLD`; and
- target closure after authorized release or one frozen primitive followed by natural termination.

For cue `X_b=1`, `RELEASE` returns `1` and `HOLD` returns `-1`. For cue `X_b=0`, `RELEASE`
returns `1` and `HOLD` returns `2`. The two cues have equal held-out weight. Discounting inside an
episode is already included in these exact physical returns.

| trace link | current-host meaning |
| --- | --- |
| environment event | A fresh owner epoch claims one fixed slot, observes one public cue, commits one release/hold boundary action, and closes the target. |
| entity and role ownership | `owner-A` alone owns the action and return. `partner-B` is a fixed visible no-op label and does not act, learn, join, leave, or adapt. |
| available information | The policy sees the cue once, then a masked decision observation containing fixed lifecycle clocks, the owner token, fixed roster, primitive policy, and partner policy. Future reward, hidden outcome, and oracle action are unavailable as policy inputs. |
| action or credit path | The owner's `RELEASE/HOLD` action fixes the physical return. Historical neural objects train actor/critic credit from that return; B5R1 additionally uses a post-forward privileged correctness sign only in the training coefficient. |
| learner exposure | This census has none. Historical X-memory exposure is declared in section 4; historical B5R1 carry/reset exposure is contrary evidence only. |
| native consequence | Exact held-out return and cue-conditioned legal action on the finite host. |

### Binding-MARL-structure assessment

No guidance-P3 MARL structure is bound by the current host:

- agent count and visible roster never vary;
- each owner epoch is a fresh episode label rather than an entity that joins, leaves, rejoins, or
  survives a replacement;
- slot identity is fixed and never competes with entity identity;
- there is no survivor state, censoring, replacement, partner co-adaptation, or population-scaled
  action space;
- the partner does not induce non-stationarity or hidden state; and
- one owner receives all native credit.

B5R1 resets Adam after one common **training update**, not at an environment membership event or a
predeclared roster age. Its remaining 127 updates are optimizer age, not entity lifetime. Thus the
recorded VSP-02 question is currently an optimizer/representation question on a single-controller
lifecycle toy. This direction-local inference is not a Portfolio decision and cannot select PARK
or fusion with VNFC.

## 3. Treatment and strongest competent comparator

### Treatment: retained greedy upper-reference census

The treatment reads the accepted B1V2 host law, held-out support, and result summary. It computes
the legal public-cue oracle:

```text
cue 0 -> HOLD -> return 2
cue 1 -> RELEASE -> return 1
J_upper_greedy = (2 + 1) / 2 = 3/2 = 1.50.
```

The oracle may use only the same presented public cue stored by the baseline. It may not use the
hidden treatment identity, future terminal tape, future reward, owner-epoch split membership,
true cue through a separate channel, or B5R1's training-only correctness sign.

### Comparator: saturation-qualified X-memory table

The strongest accepted generic same-information comparator is
`X_MEMORY_TABULAR_MONTE_CARLO` from B1V2. It is a generic two-key sample-mean action-value table:
the public presented cue is its key, it updates only the executed action cell from real physical
return, and it contains no VSP-02 Adam carry/reset mechanism, recurrent representation, partner
model, or oracle label.

The accepted B1V2 index records strict correct held-out greedy mapping and exact
`J_eval=1.35` in `5/5` seeds. Its retained evaluator records that the `1.35` value includes the
fixed `0.8*greedy + 0.2*Uniform` action mixture, hence probability `0.9` on the greedy action and
`0.1` on the other action. Strict mapping in every held-out clone therefore fixes the greedy
projection without a new learner or new environment call:

```text
J_generic_greedy(seed) = 3/2 for every accepted seed.
```

No tuning sweep or model selection was performed. For this exact finite A estimand, five-seed
strict saturation of the unique optimal action in every held-out clone is stronger than an
empirical tuning claim: no hyperparameter choice can exceed `3/2` under the same legal greedy
policy class. This does **not** turn X-memory into a tuned learning-curve baseline on another
population, budget, roster age, or evaluator.

### The historical unmatched number

The retained fixed `EVALUATOR_ONLY_ORACLE` uses deterministic actions and has `J=1.50`, while
B1V2's stored X-memory `J_eval=1.35` retains the exploration floor. Their arithmetic difference
is

```text
3/2 - 27/20 = 3/20 = 0.15.
```

That is an evaluation-policy-law gap, not A1 headroom. It must be reported but cannot replace the
matched greedy estimand. Equivalently, constraining the oracle to the same `0.9/0.1` mixture gives
`J=27/20`, equal to the accepted X-memory value.

## 4. Population, information, and work exposure

The declared population is the B1V2 held-out clone population:

- sixteen held-out owner epochs `EV-00` through `EV-15`, disjoint from training epochs;
- two equally weighted cues per epoch;
- both forced legal actions per clone for exact policy-value reconstruction;
- `64` retained forced-action rows and `32` owner-epoch/cue clones per seed; and
- five accepted X-memory seeds, hence `320` forced rows and `160` clones for the generic baseline.

The upper and comparator use the same public cue, host transition/reward law, clone weights,
greedy action semantics, and native-return definition. The owner-epoch string, static roster, and
lifecycle clocks are available to the host but X-memory deliberately needs only the cue; omitting
nuisance fields cannot weaken a comparator that already attains the exact upper.

Historical generic-baseline work per seed is `1,024` real training episodes, `1,024` policy,
learner, trainer, and tabular sample-mean updates, followed by `64` forced evaluation rows with no
evaluation update. Across five seeds this is `5,120` training episodes, `5,120` tabular updates,
and `320` evaluation rows. Parameter/optimizer displacement is inapplicable to the sample-mean
table; model-selection exposure is zero. The upper reference has no training work.

B5R1 used the same host law with a different fresh five-root population, one common Adam update,
then `127` updates per carry/reset arm/root, `1,024` training episodes per arm/root, and one
128-row held-out panel per arm/root. Those counts are not pooled into the A1 population or gap.

## 5. Observable, estimand, and ordered result rule

The census records:

1. exact `J_upper_greedy`;
2. exact per-seed and mean `J_generic_greedy` derived only from the accepted strict mapping and
   forced return cells;
3. `H_greedy`;
4. the raw unmatched deterministic-oracle minus mixture-baseline number;
5. upper, baseline, population, information, work, and selection counts;
6. the current-host binding-MARL assessment; and
7. the strongest contrary observation from B5R1 without adding it to the estimand.

Apply the first matching branch:

1. **HC-X / EVIDENCE_OR_SEMANTICS_INCOHERENT.** The accepted host/result bytes are unreadable,
   B1V2 validity is contradictory, the strict mapping cannot be recovered, any seed lacks the
   required held-out support, or upper and comparator cannot be placed under the same greedy
   action and native-return law. Mapping: publish no matched gap, name the defect, launch nothing.
2. **HC-A / MATCHED_GREEDY_HEADROOM_ZERO.** All five X-memory seeds have the strict correct greedy
   map on every held-out clone and exact greedy return `3/2`, equal to the upper. Mapping: report
   `H_greedy=0`; this closes only the A1 measurement on this host and admits no B.
3. **HC-B / MATCHED_GREEDY_HEADROOM_POSITIVE.** The comparator is valid and competent but its
   exact greedy return is below `3/2` in at least one accepted seed. Mapping: report every seed,
   the mean, and the raw positive gap; apply no MEI and admit no B automatically.
4. **HC-C / COMPETENT_GENERIC_BASELINE_NOT_ESTABLISHED.** The upper is valid but X-memory lacks
   accepted competence/support or its retained evidence cannot fix a greedy projection. Mapping:
   report the missing baseline and no numeric A1 gap; do not train or tune inside this object.

No threshold, direction disposition, successor, or mechanism polarity is encoded in this rule.

## 6. Predictions on record

- **DM:** `HC-A / MATCHED_GREEDY_HEADROOM_ZERO`. The accepted index already reports strict correct
  mapping and exact mixture value in `5/5` X-memory seeds, so the retained greedy projection should
  equal the legal `3/2` upper in every seed. This prediction follows preliminary evidence triage
  and is not independently blinded.
- **Owner:** `not taken (unattended)`.

Predictions cannot alter the rule.

## 7. Budget, stop rule, portability, exposure, and cost

- Seeds: no new seed; read the five already accepted B1V2 seeds.
- Evidence budget: one pass over the exact seven bound paths named in the result evidence.
- New environment transitions, episodes, learner/trainer/evaluator calls, model fits, optimizer
  steps, gradients, checkpoints, RNG draws, and result-bearing experiment invocations: zero.
- Machine-time cap: 15 minutes of local control-plane inspection and exact arithmetic.
- Stop success: one branch from section 5, all counts, both matched values, the unmatched raw
  number, the binding-structure trace, and the contrary observation.
- Stop refusal: any evidence/semantic conflict selects HC-X; do not repair or launch inside this
  object.
- Portability: repository-byte inspection and rational arithmetic are portable across configured
  nodes; host/device semantics are not part of the estimand. Because there is no result-bearing
  invocation, the static census stays on the local control plane. A future scientific invocation
  would be remote-first at an exact committed SHA with a fresh same-node 4 GiB preflight.
- Exposure line: `NO_NEW_LEARNER; parameter displacement=0; initialization scale=N/A; exposure
  ratio=N/A; new transitions=0; new gradient-bearing updates=0; new model-selection exposure=0`.
- Sweep and per-arm projection: none. There are no new arms or runner cost law.
- Resource admission: not applicable because no scientific process/root/RNG/model/optimizer is
  created. A local memory reading cannot admit any future remote run.

## 8. Contrary observation and live explanations

The accepted B5R1 result is valid and reports equal exact-success sets
`C=R={VSP02-B5R1-U03}`. Its descriptive final `J_eval` means are approximately
`0.9742296613` for CARRY and `0.9704376397` for RESET, a paired mean difference of
`+0.0037920216`; four paired differences are positive and one is negative. Those scalar metrics
were prospectively descriptive only. They show that equal exact endpoints do not erase continuous
path variation, but they do not identify optimizer value or alter this census.

OEER separately observed a negative direct Adam-history contrast near `-0.025` on its frozen
one-binary-policy host. Its authority explicitly says it has no roster variation, supplies no
variable-N result, and does not transfer polarity into VSP-02.

Surviving explanations are therefore:

- the current finite host has zero terminal greedy mapping headroom for a simple table, while
  recurrent actor-critic credit or optimization can still fail to reach that map;
- Adam carry/reset can change transient trajectories without changing the finite exact-success
  set;
- the stored `0.15` difference is entirely the evaluator's exploration floor; and
- a genuine roster-age question remains uninstantiated because the current host has no membership
  event, age-indexed entity state, or partner adaptation.

## 9. Object-tier design decision

Options:

- **(a)** treat the historical deterministic-oracle minus exploratory-baseline value `0.15` as
  A1 headroom;
- **(b)** freeze and execute this minimal no-learner retained-evidence greedy census, preserve the
  unmatched `0.15` separately, and return only the matched raw gap to Root; or
- **(c)** construct/tune a new learner, open a roster-age mechanism object, or launch B now.

Recommendation: **(b)**. It aligns information, evaluation action law, population, and native
return without weakening the generic comparator, inventing a new learner result, or taking an
unauthorized direction/Portfolio action.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (b).** Provenance:
`OWNER_DELEGATED`. The decision is reversible and creates no external or scientific runtime
effect.

## 10. Protected semantics, side effects, and engineering scope

The object must not change B1V2/B5R1 host physics, rewards, discount, observation fields, cue
weights, owner/slot identity, action mixture, training artifacts, numerical precision, RNG,
checkpoint, result branch, result bytes, or OEER meaning. It may write only this card, result
evidence, intake, a bounded DIRECTION summary after acceptance, and audit rows.

Technical completion can establish only that the named bytes and exact arithmetic were inspected.
It cannot establish mechanism value, select a B object, or decide PARK/fusion.

**This object needs none of the default-prohibited machinery in
`docs/project/ENGINEERING_SCOPE_SPEC.md` section 4.** It adds no code, runner, tests,
distributed/resumable execution, queue, scheduler, retry, lease, heartbeat, checkpoint recovery,
tamper evidence, provenance guard, incident tree, schema validator, registry, telemetry,
compatibility shim, or repeated smoke. Section 5 code budgets are zero and cannot be breached.
