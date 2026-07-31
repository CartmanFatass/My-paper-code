## `TOY_SCIENCE_CONTRACT` 1 — VAP-FOLR-CORE

### 1. Object identity, lineage, and disposition

* **contract_id:** `TOY-SCI-VAP-FOLR-CORE-P1-R1`
* **workflow_id:** `EXPLORER-TOY-VALIDATION-2026-07-31-P1`
* **stage_commit:** `ff7cd4bab13b22beb0606cd5761d14e74ca4b257`
* **family_id:** `FAM-VAP-FOLR`
* **candidate_id:** `CAND-VAP-FOLR-CORE`
* **input_conjecture_version:** `VAP-MYLIB-2026-07-30-C1/campaign_v3@workflow_commit=5179398`
* **exact lineage:**
  `CAND-VAP-FOLR` → `AIP-INN-VAP-C2-01` → `CAND-VAP-FOLR-CORE` → `AIP-VAP-C3-01`
  Principles: `RLPA-VAP-C2-01`, `RLPA-VAP-C3-01`
  Critics: `CAP-VAP-C2-01`, `CAP-VAP-C3-01`
  Candidate-scoped correction source: `2026-07-31_variable_agent_population_folr_core_advisory_delta_v4.json`
* **provenance.cross_pollination_edges:** Parent-to-core split only. `CAND-VAP-FOLR-SCOPE-1S`, cross-epoch restoration, all VSP mechanisms, and the paused UAV/G0/G51 workflow are excluded.
* **conflicting prior assessments preserved:** the campaign labeled the child `validation_ready`; the later candidate audit returned `REVISION_REQUIRED` and materialized five revisions without reacceptance. This contract accepts only the narrower Phase-1 toy specified below, not the campaign’s broader downstream-performance claim.
* **disposition:** `ACCEPT_FOR_TOY`
* **acceptance scope:** deterministic lifecycle, state-ownership, survivor-continuity, stale-state-exclusion, and delayed-receipt conformance plus a proof-sized behavioral-necessity witness.
* **not accepted:** learned membership management, cross-epoch restoration, improved MARL return, sample efficiency, natural-policy transport, integration, or a scalability result.
* **formal_project_effect:** `none`
* **implementation_authorized:** `false`
* **compute_authorized:** `false`
* **cpm_dispatch_authorized:** `false`

### 2. MRM-01 / MRM-08 / MRM-14 — smallest claim and mathematical defect

**smallest_claim `FOLR-P1-C1`:** On the frozen finite trace population, an owner-and-epoch-addressed lifecycle transducer can preserve exactly the self-private state of uninterrupted survivors, initialize every new owner epoch freshly, reject stale or wrong-owner inputs, and terminate every admitted action receipt by exactly one valid resolution or cancellation, with no slot-history inheritance or current-occupant credit reassignment.

The claim is about the deterministic history-to-admission map. It is not a claim that preserving state or late credit improves learned return.

**mathematical defect addressed:**

1. A reusable slot is not a persistent entity. A state map keyed only by `slot_id` is non-Markov under replacement or slot reuse because the same slot observation can correspond to incompatible owner histories.
2. An active mask identifies current participation but not which recurrent variables remain valid after membership changes.
3. Resetting all active recurrent state after every roster event destroys a sufficient statistic of an uninterrupted survivor whenever that statistic is not reobserved.
4. A delayed outcome belongs to the action instance created at initiation. Routing it through the current slot map implements the wrong ownership function whenever the slot has been reassigned.
5. A single undifferentiated mask is valid only if representation, communication, action, and credit domains are provably identical.

### 3. MRM-01 / MRM-02 / MRM-05 — scientific object, law, process, and scope

**scientific_object:** A finite-horizon partially observed stochastic game with exogenous within-episode membership events and a frozen shared recurrent policy.

**toy population and state law:**

* Persistent owner set: (\mathcal O={A,B,C,D}).
* Reusable slots: (\mathcal S={0,1,2}).
* Active set size: one to three.
* Every accepted activation creates a fresh `owner_epoch`.
* Each owner epoch receives an independent private bit (b_{o,e}\sim\mathrm{Bernoulli}(1/2)). It is observed once at activation and is not reobserved after an unrelated roster event.
* At registered post-event query boundaries, each active owner must output its current epoch’s bit.
* An action may create an outcome whose delivery is delayed until after leave, replacement, or slot reuse.
* Membership events are exogenous to all policies and are drawn from the frozen trace matrix rather than learned.
* Skill lifetime and skill-period control are frozen and absent.

**objective:** External toy reward is one for each correct active-owner query and zero otherwise. Receipt ownership is also audited directly. Reward is diagnostic only; no policy or learner is trained in this Phase-1 unit.

**scope.population:** the sixteen exact trace cases listed under evidence volume, including owner and slot permutations fixed before execution.

**membership_nonstationarity.sources:**

* active-set change: present;
* composition/type shift: owners are behaviorally homogeneous, so type shift is absent;
* persistent identity and recurrent-state ownership: present;
* topology change: only active incidence changes; no learned graph;
* partner-policy drift: absent;
* endogenous joining or leaving: absent;
* censoring by leave, replacement, and delayed outcomes: present.

**membership_nonstationarity.consequences:** possible erasure of survivor-private state, stale roster-dependent state, illegal inactive actions, slot inheritance, and delayed-receipt reassignment.

**policy_process and solution concept:** one frozen shared recurrent policy is executed by all owners. Partner behavior is frozen and later swapped as a control. This is a controller-conformance and best-response-access toy, not an equilibrium or co-adaptation claim.

### 4. MRM-03 — identity and ownership map

| Object                 | Meaning                                   | Persistence and ownership rule                                                    |
| ---------------------- | ----------------------------------------- | --------------------------------------------------------------------------------- |
| `owner_id`             | Authenticated persistent entity pseudonym | May recur across episodes or absences; never identifies a current epoch by itself |
| `owner_epoch`          | One uninterrupted active tenure           | Strictly new on join or rejoin; closed epochs never reopen                        |
| `slot_id`              | Reusable physical position                | Carries no state, policy, role, or credit ownership                               |
| policy identity        | Shared frozen policy parameters           | Global and unchanged across owners                                                |
| role/type              | Homogeneous in this toy                   | Cannot be used as an owner shortcut                                               |
| `skill_instance_id`    | Fixed-lifetime execution instance         | Fresh for a new owner epoch; no adaptive period                                   |
| recurrent-state owner  | Exact `(owner_id, owner_epoch)`           | Only declared self-private state may survive an unrelated roster event            |
| action-credit owner    | Immutable `action_instance_id`            | Never rekeyed through the current slot map                                        |
| roster-dependent state | Current `roster_version`                  | Invalidated before the first affected post-event action                           |

**symmetry assumptions:** owner labels and slot labels are permutation-equivariant. A paired identity/slot permutation must permute outputs and receipts but leave aggregate outcomes unchanged. The only nonexchangeable information is each epoch’s realized private history.

### 5. MRM-04 — complete clock map

| Clock               | Frozen definition                                                                                    |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| primitive clock     | Logical environment boundary (t=0,\ldots,H-1), with (H\le 12)                                        |
| opportunity clock   | Each boundary at which a currently active, valid owner may act                                       |
| initiation clock    | Creation of one immutable `action_instance_id` after legal-action admission                          |
| termination clock   | First valid outcome, registered cancellation, or receipt expiry                                      |
| union-event clock   | Total ordered stream of lifecycle, outcome, observation, message, and learner-admission events       |
| membership clock    | Monotone accepted `event_seq`; one accepted nonduplicate event advances `roster_version`             |
| update clock        | Frozen learner-admission boundary after receipt resolution; no optimizer executes in Phase 1         |
| credit clock        | `RESOLVED_READY → CONSUMED` or one terminal cancellation                                             |
| physical-time clock | Equal to primitive time in this toy but logged as a distinct field                                   |
| discount clock      | (\gamma=1); discounted-return inference is not made                                                  |
| interruption clock  | Leave, replacement, episode end, or explicit cancellation                                            |
| censoring clock     | Finite `D_outcome_max`, `D_event_replay_max`, `B_open`, and `B_tombstone`, frozen before realization |

Exactly one environment binding is used per trace: `CANCEL_ON_LEAVE` or `AWAIT_OUTCOME`. The two same-boundary orderings—outcome before lifecycle and lifecycle before outcome—are separate frozen traces.

### 6. MRM-10 — exact identifying toy

**full toy state**

[
s_t=(t,A_t,M_t,V_t,{b_{o,e}},{h^{self}_{o,e}},
h^{roster}_t,\mathcal R_t,\mathcal Q_t,\xi_t),
]

where:

* (A_t) is the active owner-epoch set;
* (M_t) maps slots to current owner epochs;
* (V_t) is `roster_version`;
* (h^{self}_{o,e}) is owner-private recurrence;
* (h^{roster}_t) is any state with teammate, roster, message, or aggregate ancestry;
* (\mathcal R_t) is the immutable action-receipt set;
* (\mathcal Q_t) is quarantine/conflict state;
* (\xi_t) is the frozen exogenous event tape.

**observations**

* On activation: the owner observes its fresh private bit once.
* At ordinary queries: current local query marker, legal-action mask, and current active mask.
* All arms receive identical current observations, event timing, action opportunities, recurrence capacity, and policy parameters.
* `owner_id`, epoch, roster version, slot map, receipt status, and event sequence are sanitation/audit fields, not actor features.
* No future event, delayed outcome, prior slot content, or closed-epoch bit is observable.

**actions**

* `REPORT_0`, `REPORT_1`, or `NO_ACTION` when inactive/quarantined.
* Lifecycle events are not policy actions.
* Learner admission is an audited transducer output, not an agent action.

**events**

`JOIN`, `LEAVE`, `REPLACEMENT`, `REJOIN`, `SLOT_REUSE`, exact duplicate, stale event, sequence gap/conflict, observation, message, action admission, delayed outcome, duplicate outcome, learner admission, and expiry.

**transition requirements**

* Join/rejoin initializes fresh owner-private state and exploration stream.
* Leave closes the epoch permanently.
* Replacement closes the old epoch and activates a fresh new epoch atomically.
* Uninterrupted survivors preserve only strictly self-ancestry recurrence.
* Every roster-dependent state and derived mask is invalidated or rebuilt before the next affected action.
* Stale, wrong-epoch, inactive, or quarantined inputs cause no action, recurrence, normalization, or learner effect.
* An action receipt is created once, retains immutable origin, and reaches exactly one terminal state.
* A delayed outcome never writes a new occupant’s private state.

**hidden variables:** fresh private bits, future membership events, future delayed outcomes, and frozen exogenous random tape.

**public variables:** current active mask and ordinary task observations. Audit metadata is public to the harness but not to the policy.

**intervention hooks**

* `do(S=0/1)`: reset or preserve uninterrupted survivor-private state.
* `do(C=0/1)`: cancel or retain immutable origin credit after owner departure.
* owner-label and slot-label permutation;
* partner-policy swap;
* duplicate, stale, conflicting, or missing event injection;
* receipt-owner shuffle;
* lifecycle/outcome order reversal;
* inert event placebo;
* unbound action-affecting-state sentinel;
* audit-field actor-visibility sentinel.

### 7. Optimal-policy necessity and final-capability link

The post-event query makes survivor continuity behaviorally necessary. For an uninterrupted survivor whose bit is not reobserved, any controller that fresh-resets every recurrent state has maximum success probability (1/2), while a controller preserving the valid self-private bit can attain one. Owner identifiers or slots cannot solve this because the bit is resampled independently for every epoch.

Slot reuse makes stale-state exclusion necessary: a new occupant receives an independent bit, so inheriting the old slot state is wrong with probability (1/2).

The delayed-outcome trace makes action-instance ownership necessary: the outcome is delivered only after replacement, so current-slot routing necessarily assigns it to the wrong epoch.

**general-MARL capability link:** the toy tests a substrate required by anonymous dynamic-membership MARL: valid survivor continuity, fresh join/rejoin state, and delayed-action ownership. It does not show that this substrate improves coordination or return in a learned task.

### 8. MRM-06 — one estimand, hierarchy, uncertainty, and thresholds

**primary_estimand**

[
\psi_{\mathrm{FOLR}}
=\frac1{16}\sum_{m=1}^{16}
\mathbf 1{\text{trace }m\text{ contains any forbidden state/action/update influence,
receipt multiplicity, or required-witness failure}}.
]

**target population:** the exact sixteen registered complete traces.

**top-level independent unit:** one complete trace. Events, agents, actions, receipts, and query boundaries are nested observations.

**sampling hierarchy:** finite census; no trace is treated as a stochastic replication of another.

**identification assumptions**

* event source and owner authentication are correct;
* both latency bounds and the selected in-flight binding are finite;
* all action- or update-affecting variables bind to exactly one declared state class;
* the private bit is not reintroduced through an undeclared observation or global state;
* frozen actor outputs and event tapes are identical across comparator arms.

**uncertainty_plan:** no confidence interval substitutes for finite conformance. The result is a complete census of the declared toy population.

**thresholds**

* `ACCEPT_CONFORMANCE`: (\psi_{\mathrm{FOLR}}=0);
* receipt creation count per admitted action: exactly one;
* terminal receipt consumption or cancellation count: exactly one;
* wrong-owner, wrong-epoch, stale-input, and inactive-action effects: exactly zero;
* FullCore success on the survivor-bit necessity trace: one;
* fresh-reset upper bound on that trace: one-half in expectation;
* no-churn/no-delay equivalence: byte-identical action and update destinations.

**bounded evidence volume**

Sixteen traces, each at most twelve boundaries; at most (16H\le192) evidence transitions. Twelve traces are exposed construction cases and four are frozen held-out owner/order permutations. There is no optional stopping, retry, seed replacement, or expanded trace search.

### 9. MRM-07 / MRM-09 — strongest nulls, controls, and counterexamples

**default strongest null — `MASKRESET-RNN`:** the same shared policy, active mask, legal actions, actor-visible information, recurrence capacity, normalization state, event stream, receipt storage bytes, action opportunities, and budget, but every active owner is fresh-reset after any roster change and objectively late receipts are cancelled rather than reassigned.

**factorial comparators**

* `MASKRESET-RNN`: survivor continuity off, origin credit off;
* `RECEIPT-ONLY`: continuity off, origin credit on;
* `CONTINUATION-ONLY`: continuity on, origin credit off;
* `FULLCORE`: continuity on, origin credit on.

**additional controls**

* **equivalence control:** no roster change and no delayed outcome; all four arms must be exact.
* **negative controls:** no self-private hidden bit, no open receipt, stale event, inactive observation, wrong-epoch message.
* **placebo:** notification with no active-set or roster-version change.
* **identity permutation:** exchange owner labels while preserving histories.
* **slot permutation:** exchange slots independently of owners.
* **policy swap:** replace the frozen partner behavior with a held-out policy while keeping the focal history.
* **held-out conditions:** four frozen event/order/identity traces unavailable to any implementation-specific case table.
* **frozen-output control:** replay identical actor actions and learner payloads through each transducer arm.
* **ablations:** remove survivor preservation only; remove immutable-origin credit only; key state by slot; collapse masks without an equality witness; expose audit fields to the actor.

**strongest counterexamples sought**

* If the bit is reobserved after every event, fresh reset passes and the toy is nonidentifying.
* If no slot is reused, slot-keyed state can satisfy surface metrics.
* If no delayed outcome crosses replacement, current-slot and action-origin credit coincide.
* If a globally persistent scratchpad retains the private bit, the claimed owner-private mechanism is bypassed.
* If all policy-relevant recurrence has teammate ancestry, there may be no nontrivial survivor-private state to preserve.

Any such construction blocks or narrows the corresponding claim rather than being tuned away.

### 10. Safety/accounting versus learned paths

* Lifecycle ledger, owner epochs, state classification, mask construction, receipt transitions, cancellation, and quarantine are deterministic safety/accounting paths.
* They receive no reward, value, intrinsic signal, exploration bonus, policy gradient, or learned gate.
* The shared policy, critic, optimizer, task reward, and ordinary exploration are retained but frozen.
* No receipt outcome may write a closed epoch’s private state.
* No event audit field may alter the actor kernel unless exposed identically in every arm and included in the declared information set.
* There is no intrinsic reward or task-specific shaping.

### 11. MRM-08 — replacement ledger

**DELETE**

* slot-keyed continuity;
* cross-epoch state restoration;
* reset-all presented as the only legal lifecycle rule;
* current-slot delayed-credit ownership;
* assumed equality of representation, communication, action, and credit masks;
* learned lifecycle or release decisions.

**RETAIN**

* one shared policy and critic;
* ordinary active mask and legal-action mask;
* ordinary external task reward and exploration;
* base recurrent capacity;
* global learner parameters and valid normalization state.

**ADD**

* authoritative owner/epoch/slot ledger;
* dependency-closed state classification;
* fresh epoch on every activation;
* typed admission masks where domains differ;
* immutable action-instance receipt and bounded terminal FSM;
* exact duplicate handling and fail-closed quarantine.

### 12. Retirement, failure boundaries, and complexity

**retirement conditions**

* If `MASKRESET-RNN` attains the same complete action/update mapping on every necessity trace without an undeclared persistent channel, retire survivor preservation for this scope.
* If `RECEIPT-ONLY` is equivalent to FullCore, retain receipt ownership and retire the continuity increment.
* If `CONTINUATION-ONLY` is equivalent to FullCore, retain continuity and retire the delayed-credit increment.
* If no declared base state has strictly self-only ancestry, mark survivor continuity `not_applicable` and retain only sanitation and receipts.
* A structural proof that one active mask has exactly the same domain and transition law as all typed masks permits their collapse.

**failure boundaries**

Trusted authoritative membership and owner authentication are prerequisites, not learned capabilities. Unknown event ordering, unbounded outcome latency, or action-dependent undeclared in-flight semantics is `NO_ACCESS`, not a negative result.

**resource_bounds**

* `K_search=16` fixed trace cases; no tree search, beam search, replanning, or nested rollouts.
* evidence-search bound: (O(HK));
* state and receipt processing in the toy: (O(N+R_{\text{open}}));
* scalable deployment claim, if later made: (O(Nk_{\text{neighbor}})), (k_{\text{neighbor}}\le16), or (O(N\log N));
* no dense (O(N^2)) deployment claim;
* nonformal wall-clock ceiling: twenty minutes after a separate prelaunch bound;
* this audit consumes zero compute.

### 13. CPM-facing invariants, stop condition, and result propositions

**CPM-facing scientific invariants**

1. Every action- or update-affecting variable has exactly one state-class binding.
2. Slot identity never grants read access.
3. Every activation creates a strictly fresh epoch.
4. Only uninterrupted self-ancestry recurrence may survive.
5. All roster-dependent state is invalid before the next affected action.
6. Stale, wrong-epoch, inactive, or quarantined inputs have zero downstream effect.
7. Every action creates at most one immutable receipt.
8. Every valid outcome resolves only its originating action.
9. Every receipt terminates exactly once.
10. Audit metadata cannot silently become policy information.
11. The default null is matched on information, recurrence, events, storage, and budget.
12. No trace-specific exception table is part of the scientific object.

**exact stop condition:** A future toy execution stops at the first invariant failure or after exactly one pass through all sixteen frozen traces. It does not proceed automatically to training or downstream return comparison.

| Evidence class         | Smallest proposition                                                                                                                                |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| positive               | The deterministic transducer and the two necessity witnesses hold on the registered finite population; no downstream MARL claim follows             |
| negative               | FullCore and the matched fresh-reset null are equivalent on every necessity witness; retire the smallest unnecessary continuity or credit component |
| mixed                  | Retain whichever of survivor continuity or origin credit is identified; do not preserve the conjunctive claim                                       |
| underpowered           | Not applicable to the finite census; missing or unexecuted traces are incomplete evidence, not a null result                                        |
| access-failed          | Authoritative identity, total event order, or finite latency cannot be bound; no candidate update                                                   |
| implementation-invalid | Any invariant, manifest, information, or matching failure; no scientific update beyond the invalid realization                                      |

---

## `TOY_SCIENCE_CONTRACT` 2 — VSP-ASYNC-ESCROW

### 1. Object identity, lineage, and disposition

* **contract_id:** `TOY-SCI-VSP-ASYNC-ESCROW-P1-R1`
* **workflow_id:** `EXPLORER-TOY-VALIDATION-2026-07-31-P1`
* **stage_commit:** `ff7cd4bab13b22beb0606cd5761d14e74ca4b257`
* **family_id:** `FAM-VSP-ASYNC-ESCROW`
* **candidate_id:** `CAND-VSP-02`
* **input_conjecture_version:** `VSP-MYLIB-2026-07-30-C1/campaign_v3@workflow_commit=5179398`
* **exact lineage:**
  Source packets: `SRP-VSP-01`, `SRP-VSP-03`, `SRP-VSP-07`
  `AIP-VSP-02` → `RLPA-VSP-02` → `CAP-VSP-02` → `AIP-VSP-C2-02` → `RLPA-VSP-C2-02` → `CAP-VSP-C2-02`
  Candidate-scoped correction source: `2026-07-31_variable_skill_period_async_duration_escrow_advisory_delta_v4.json`
* **provenance.cross_pollination_edges:** no VAP mechanism and no semantic-completion mechanism enters this contract. Owner epochs are used only to invalidate focal records after leave or replacement.
* **conflicting prior assessments preserved:** the campaign labeled the candidate `validation_ready`; the later audit returned `REVISION_REQUIRED` and materialized six revisions. This audit additionally introduces the question-required per-step and termination-time nulls and narrows Phase 1 to a frozen-primitive timing toy.
* **disposition:** `ACCEPT_FOR_TOY`
* **acceptance scope:** staged ledger conformance, physical-time estimator calibration, and a bounded context-adaptive nominal-duration discriminator.
* **not accepted:** agent-specific causal responsibility, learned completion semantics, continuous-duration control, joint primitive-duration training, adapting-partner transport, or general MARL superiority.
* **formal_project_effect:** `none`
* **implementation_authorized:** `false`
* **compute_authorized:** `false`
* **cpm_dispatch_authorized:** `false`

### 2. MRM-01 / MRM-04 / MRM-08 — smallest claim and mathematical defect

**smallest_claim `ESCROW-P1-C1`:** Each eligible initiation-time nominal-duration decision can be represented by one immutable record that receives one exclusive terminal cause and at most one physical-time SMDP score release, invariant to primitive frame refinement, duplicate delivery, and noncausal teammate union events.

**separate value hypothesis `ESCROW-P1-C2`:** Conditional on `C1`, effective short and long duration actions, and an identifying crossed toy, a context-conditioned timing policy may outperform tuned fixed, context-shuffled, and ordinary recurrent timing controls. `C1` does not imply `C2`.

**mathematical defect addressed**

* Primitive-step credit can multiply one duration decision by frame count.
* Union-event credit can multiply it by teammate boundary frequency.
* Termination-time relabeling may condition the action on post-treatment information.
* Atomic-step discounting changes under physically equivalent frame refinements.
* Nominal duration and realized duration diverge under interruption.
* A late or duplicate reward can emit more than one update without immutable decision ownership.
* A stale behavior-policy version can turn the released score into an undeclared off-policy estimator.
* Correct bookkeeping alone does not prove that duration is a useful action.

### 3. MRM-01 / MRM-05 — scientific object, policy process, and objective

**scientific_object:** A two-agent asynchronous Dec-SMDP reduced to a focal timing-control problem against a frozen partner policy.

**solution concept:** best response of the focal duration policy under frozen primitive, high-level, partner, and membership processes. No Nash-equilibrium, co-adaptation, or decentralized-team-optimality claim is made.

**objective:** expected shared external team return per common unit of physical time,

[
J=\mathbb E\left[\int_0^{4}e^{-0.1u}r_{\mathrm{team}}(u),du\right],
]

normalized by (\int_0^4e^{-0.1u}du). No duration, renewal, escrow, ledger, optimizer, or intrinsic reward is added.

**scope.partner_policy_population:** one familiar frozen partner-event family during timing learning and two held-out frozen families with altered event timing but matched physical competence.

**membership law:** roster is fixed in ordinary episodes. Focal leave and replacement appear only as registered competing-cause controls; a replacement receives a fresh owner epoch and no inherited duration record.

### 4. MRM-03 — identity and ownership

* Persistent entity: `agent_uuid`.
* Active tenure: `owner_epoch`.
* Duration action owner: immutable `decision_id=(agent_uuid,owner_epoch,own_boundary_index,behavior_version)`.
* Skill identity: frozen high-level skill bit; it is distinct from duration.
* Nominal duration: initiation action (D_q\in{1,4}) physical seconds.
* Realized duration: (\Delta_q=T_q-\tau_q), separately recorded.
* Primitive recurrent state: frozen and duration-blind.
* Duration recurrent state: owned by the focal owner epoch and reset on replacement.
* Reward receipt ownership: physical event time plus interval ownership; the same team reward may belong once to each concurrently active agent record but never twice to one record.
* Symmetry: swapping focal and partner labels together with their event tapes must preserve the corresponding result. Partner identity itself is not an input.

### 5. MRM-04 — complete clock and SMDP contract

| Clock               | Frozen definition                                                                                                      |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| primitive clock     | Base physical discretization of (0.25) seconds; a (4\times) refined clone uses (0.0625) seconds                        |
| opportunity clock   | Focal owner’s own eligible renewal boundaries only                                                                     |
| initiation clock    | Time (\tau_q) at which one duration is drawn and `decision_id` is committed                                            |
| termination clock   | Earliest of nominal expiry, skill completion, focal leave, focal replacement, forced interruption, or episode terminal |
| union-event clock   | Ordered union of focal, partner, membership, reward, and administrative notifications                                  |
| membership clock    | Normally frozen; controlled leave/replacement causes advance owner epoch and roster version                            |
| update clock        | One frozen physical-time cohort boundary after every admitted record has drained                                       |
| credit clock        | Sole compare-and-set transition from reward-complete pending record to consumed/rejected                               |
| physical-time clock | Continuous elapsed seconds; all reward and discount calculations use it                                                |
| discount clock      | (\Gamma(u)=e^{-0.1u}), independent of frame index                                                                      |
| interruption clock  | Forced interruption at (3.25) seconds with probability (0.15), paired across arms, plus controlled leave/replacement   |
| censoring clock     | Reward-completeness watermark (T_q+0.25) seconds and strict behavior-version cohort                                    |

**cause precedence at equal physical time:** episode terminal → replacement → leave → forced interruption → skill completion → nominal expiry; final tie-break by immutable event UUID.

**credit rule:** one initiation log-probability, one physical-time return target, one pre-draw baseline, and zero or one score

[
g_q=\nabla_\theta\log\mu_v(D_q\mid H_q),
\mathrm{stopgrad}(\widehat Q_q-\widehat V_v(H_q)).
]

### 6. Exact toy state, information, actions, and transitions

**state**

[
s(u)=(C,z,x,p,A,V,\mathcal E,\mathcal W,\xi),
]

where:

* (C\in{C_{\mathrm{FAST}},C_{\mathrm{STABLE}}}) is balanced and visible before the duration draw;
* (z\in{0,1}) is the frozen high-level skill bit;
* (x) is the public target bit;
* (p) is uninterrupted option progress;
* (A,V) are active roster and owner epoch;
* (\mathcal E) is the focal escrow record;
* (\mathcal W) is the reward watermark state;
* (\xi) is the frozen exogenous interruption and partner-event tape.

**initiation information (H_q)**

Current decentralized observation, context, current skill, active mask, owner epoch, and prior own-boundary recurrent summary. It excludes future target changes, future events, realized duration, accumulated interval reward, remaining time, and evaluation labels.

**actions**

* Focal duration: `SHORT=1s` or `LONG=4s`.
* At an eligible renewal, the same frozen high-level selector may retain or change (z).
* Primitive action is generated by the frozen duration-blind controller.
* Partner actions and event times are frozen.

**positive-control transition law**

* In `C_FAST`, the target begins at zero and flips once at (u=1.5). A short regime permits a renewal at (u=2) and correction; a long regime cannot renew before the reward window ends.
* In `C_STABLE`, reward begins only after (2.5) uninterrupted seconds of progress. Every registered renewal resets progress, even when the same skill is reselected. Short renewals cannot reach the threshold; long commitment can.
* Forced interruption at (u=3.25) truncates the current record but does not alter prior reward.
* External reward exists only through (u=4); (u\in(4,4.25]) is a watermark-closing tail.

**record FSM**

`ABSENT → PENDING → WAITING_REWARD_WATERMARK → CONSUMED` or one of `DIAGNOSTIC_NO_SCORE`, `REJECTED_VERSION`, `REJECTED_LATENCY`, `CANCELLED_PREEXECUTION`, `INVALID_CONFLICT`.

Byte-identical duplicates are no-ops. Conflicting reuse of an event or decision identifier invalidates the record. Other-agent administrative events may not terminalize, resample, release, or advance the focal RNG.

**hidden variables:** future interruption, future target transition before it occurs, future partner action, future reward arrival, and future terminal cause.

**public variables:** current context, target observation, ordinary partner effects, current skill, and active mask. Escrow internals are audit-only and absent from primitive-policy inputs.

### 7. Optimal-policy necessity and general-MARL link

In `C_FAST`, short is strictly better because it exposes a post-flip renewal opportunity unavailable to long commitment. In `C_STABLE`, long is strictly better because every short renewal destroys the progress required for reward. With balanced contexts, a context-adaptive policy strictly dominates both globally fixed endpoints.

Repeated short choices cannot emulate long in `C_STABLE` without deleting the registered progress-reset transition. Long cannot emulate short in `C_FAST` without an undeclared mid-commitment renewal. Thus the optimal-policy set requires context-dependent temporal behavior.

A matched recurrent renew/continue controller may implement the same behavior without a nominal-duration catalogue. If it does, the toy supports adaptive timing but refutes the necessity of the catalogue.

**general-MARL capability link:** the candidate supplies individual own-boundary SMDP accounting for asynchronous skill periods. Frozen partners mean the toy does not yet establish strategic multi-agent credit or coordination.

### 8. MRM-06 — one estimand, hierarchy, assumptions, and volume

**deterministic prerequisite:** every valid initiation record has release count one; every diagnostic, cancelled, rejected, or invalid record has release count zero. This is a conformance gate, not the primary estimand.

**primary_estimand**

[
\Delta_{\mathrm{timing}}
========================

\min\left{
\mathbb E[Y_A-Y_{\mathrm{TF}}],
\mathbb E[Y_A-Y_{\mathrm{CS}}],
\mathbb E[Y_A-Y_{\mathrm{RT}}]
\right},
]

where:

* (A): context-adaptive initiation-time policy using the accepted escrow;
* `TF`: training-selected tuned fixed duration;
* `CS`: context-shuffled timing policy with the same marginal contexts;
* `RT`: capacity-matched recurrent renew/continue timing;
* (Y): normalized external physical-time return over the common horizon.

This scalar asks whether adaptive initiation-time timing beats all three value explanations, not merely one convenient baseline.

**top-level independent unit:** one independently initialized timing-policy run block. Episodes, duration records, partner events, and primitive frames are nested.

**sampling hierarchy:** sixteen independent run blocks; within each block all arms share the same initial primitive checkpoint and paired physical tapes but use independent preassigned timing RNG namespaces.

**identification assumptions**

* context is pretreatment and execution-visible;
* short and long remain effective actions under interruption;
* the primitive action kernel cannot infer duration, countdown, or escrow state;
* reward ownership and completeness watermark are correct;
* rejected-record rates are not differential enough to alter the target population;
* tuned-fixed selection uses training-side data only;
* partner policies remain frozen.

**uncertainty_plan:** run-block-level paired randomization inversion with simultaneous two-sided 95% intervals for the three components of the minimum. Equivalence uses simultaneous 90% intervals wholly inside ([-0.02,0.02]). Frames and records are never resampled as independent runs.

**thresholds**

* zero conformance violations;
* analytic positive-control normalized values reproduced within `0.01`;
* short-minus-long in `C_FAST` and long-minus-short in `C_STABLE`: simultaneous lower bound above `0.05`;
* nominal-expiry probability at least `0.20` for both durations in each context;
* absolute difference in mean realized durations at least `0.50` seconds;
* (\Delta_{\mathrm{timing}}) simultaneous lower bound above `0.02`;
* held-out adaptive advantage positive and noninferior to familiar advantage within `0.02`;
* original/refined target absolute difference at most (10^{-8});
* score relative-norm and cosine discrepancies at most (10^{-6});
* sham-union effect on release count exactly zero.

**bounded evidence volume**

* fixed arm count: eight;
* independent blocks: sixteen;
* per block and learned arm: at most 512 timing decisions per context for fitting;
* evaluation: 64 paired episodes per context, arm, and partner factor;
* common physical horizon: 4.25 seconds;
* no sequential stopping, run replacement, hyperparameter search, or outcome-driven support expansion.

### 9. MRM-07 / MRM-09 / MRM-10 — nulls and controls

**question-required credit nulls**

1. **`PER_STEP-CREDIT`:** same observations, duration catalogue, timing recurrence, parameter budget, physical reward measure, and optimizer opportunities. The initiation log-probability is carried through primitive steps and the interval return is algebraically partitioned across them. In a clean ordered trace, its summed score must equal escrow’s score; frame or event multiplication is a falsification.
2. **`TERMINATION-TIME-CREDIT`:** same initiation information receipt and duration head, but one score is constructed at termination without an immutable decision FSM or reward watermark. In a clean in-order trace it must be equivalent; duplicate, stale, or delayed-reward failures test whether the missing ownership contract matters.

These controls test whether escrow is a necessary accounting representation. Equivalence means escrow is a robust implementation primitive, not a new learning rule.

**value nulls**

* tuned fixed short-or-long duration;
* context-shuffled adaptive timing;
* capacity-matched recurrent renew/continue controller;
* oracle context mapping, diagnostic only.

**negative and placebo controls**

* four-way physical frame refinement;
* noncausal teammate union-event expansion;
* duplicate and reordered terminal delivery;
* late reward beyond the watermark;
* behavior-version mismatch;
* focal leave and replacement;
* duration/age/countdown sentinel injection into audit-only fields;
* context permutation with physical process held fixed.

**identity permutations and policy swaps**

* exchange focal and partner owner labels with corresponding tapes;
* swap familiar and held-out frozen partner-policy families;
* replace a genuine partner event by a sham notification while preserving all focal physical consequences.

**held-out conditions**

* altered partner boundary frequency;
* altered notification latency;
* one held-out context ordering;
* one held-out interruption tape family.

**frozen-output controls**

* Freeze duration actions and primitive actions, then compare escrow, per-step, and termination-time estimators.
* Freeze the learned timing policy, then compare original and refined frames.
* Replay one record’s exact receipts through duplicate and reorder interventions.

**ablations**

* no decision-ID uniqueness;
* no deduplication;
* no reward watermark;
* no behavior-version check;
* allow duration or countdown into the primitive actor;
* condition primary analysis on nominal expiry only.

### 10. Safety/accounting versus learned paths

* Escrow identity, deduplication, terminal-cause arbitration, watermark closure, version checking, and exposure accounting are deterministic.
* They supply no reward or intrinsic objective.
* Primitive actor, primitive critic, primitive recurrence, skill implementation, and their normalizers are frozen.
* Duration policy and duration critic have disjoint parameters, normalizers, losses, optimizers, and gradient graphs.
* Primitive loss cannot update a duration object; duration loss cannot update a primitive object.
* Team reward is permitted as the joint-policy objective but is not interpreted as retrospective focal-agent responsibility.
* The timing policy receives one score per consumed initiation decision, normalized by common physical exposure rather than record count.
* No future event, terminal cause, or reward may enter initiation information.

### 11. MRM-08 — replacement ledger

**DELETE**

* primitive-frame multiplication of one duration decision;
* teammate-union-event multiplication;
* nominal-expiry-only primary analysis;
* duration labels or countdowns in the primitive actor;
* silent off-policy consumption;
* shared primitive-duration trainable parameters;
* reward or intrinsic bonuses for longer or shorter periods.

**RETAIN**

* frozen primitive controller and skill implementation;
* shared external team reward;
* ordinary observations and active mask;
* fixed partner and membership processes;
* the two-value duration catalogue for this toy.

**ADD**

* immutable initiation record;
* exclusive terminal-cause transducer;
* reward-completeness watermark;
* physical-time discount and cause-dependent bootstrap;
* strict behavior-version cohort;
* exposure ledger;
* separate timing policy and timing critic.

### 12. Retirement, failure, and complexity

**retirement conditions**

* Ledger passes but adaptive timing is equivalent to tuned fixed: retain accounting only and use fixed duration.
* Adaptive timing is equivalent to context shuffle: stochastic timing or regularization is sufficient; retire context-sensitive timing.
* Adaptive timing is equivalent to recurrent timing: retain adaptive timing behavior but retire the explicit duration catalogue.
* Correct per-step or termination-time credit is equivalent under all asynchronous interventions: reduce escrow to the simpler equivalent representation.
* Oracle succeeds but learned timing fails: timing value is accessible; the learning rule is unsupported.
* Short and long realized-duration laws collapse under interruption: report `NO_EFFECTIVE_DURATION_SUPPORT`, not a negative ledger result.
* Differential reward-latency rejection blocks the value claim.

**resource and complexity bounds**

* `K_search=8` fixed evidence arms; no candidate generation or online trajectory search.
* Any common-fork evidence procedure is (O(HK)) with (K=8).
* Runtime accounting is (O(1)) per event and (O(N)) open records with one active timing record per owner.
* Deployment memory is linear in active owners; no dense pairwise mechanism.
* Nonformal exercise must be projected below twenty minutes before realization.
* Failure to meet that bound is `NON_EXECUTABLE_EVIDENCE_DESIGN`, not evidence against the candidate.

### 13. CPM-facing invariants, stop condition, and result propositions

**CPM-facing scientific invariants**

1. One immutable decision ID per eligible initiation.
2. Nominal and realized durations are distinct fields.
3. One exclusive terminal cause under the frozen total order.
4. At most one learning release.
5. Reward interval is half-open ([\tau_q,T_q)), plus only an explicitly owned terminal impulse.
6. The reward watermark proves target completeness.
7. Another agent’s administrative event cannot terminalize or release the focal record.
8. Physical frame refinement preserves physical reward, cause, target, advantage, and score.
9. No primitive-duration parameter or gradient sharing.
10. Every arm has matched physical time, observations, duration support where applicable, recurrence capacity, optimizer opportunities, and evaluation count.
11. All eligible decisions remain in the intention-to-treat population.
12. Per-step and termination-time controls are implemented strongly enough to be algebraically equivalent in their declared clean regime.

**exact stop condition:** stop at the first Stage-A conformance failure; otherwise stop after the fixed Stage-B estimator/positive-control evidence and, only if those gates pass under a separately authorized realization, the fixed Stage-C volume. No failed value result triggers tuning, a larger duration catalogue, extra runs, or joint primitive learning.

| Evidence class         | Smallest proposition                                                                                                                                  |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| positive               | Bounded evidence for context-adaptive nominal-duration value under the registered frozen-partner SMDP; ledger and estimator claims remain separate    |
| negative               | Ledger valid but timing equivalent to the relevant fixed, shuffled, or recurrent null; retire only the corresponding adaptive claim                   |
| mixed                  | Ledger/estimator pass while adaptive learning, held-out transport, or one comparator gate fails; retain the passed lower-stage proposition only       |
| underpowered           | Simultaneous interval crosses the registered margin or effective support is too small; preserve unresolved alternatives                               |
| access-failed          | No trustworthy physical timestamps, reward watermark, finite terminal causes, or strict behavior-version cohort; no candidate update                  |
| implementation-invalid | Any duplicate release, cause conflict, frame sensitivity, reward incompleteness, gradient leakage, or exposure mismatch; no scientific interpretation |

---

## `TOY_SCIENCE_CONTRACT` 3 — VSP-SEMANTIC-HANDOFF

### 1. Object identity, lineage, and disposition

* **contract_id:** `TOY-SCI-VSP-SEMANTIC-HANDOFF-P1-R1`
* **workflow_id:** `EXPLORER-TOY-VALIDATION-2026-07-31-P1`
* **stage_commit:** `ff7cd4bab13b22beb0606cd5761d14e74ca4b257`
* **family_id:** `FAM-VSP-SEMANTIC-HANDOFF`
* **candidate_id:** `CAND-VSP-05`
* **input_conjecture_version:** `VSP-MYLIB-2026-07-30-C1/campaign_v3@workflow_commit=5179398`
* **exact lineage:**
  Source packets: `SRP-VSP-02`, `SRP-VSP-03`, `SRP-VSP-04`
  `AIP-VSP-05` → `RLPA-VSP-05` → `CAP-VSP-05` → `AIP-VSP-C2-05` → `RLPA-VSP-C2-05` → `CAP-VSP-C2-05`
  Candidate-scoped correction source: `2026-07-31_variable_skill_period_semantic_completion_safe_handoff_advisory_delta_v4.json`
* **provenance.cross_pollination_edges:** no FOLR state continuity, no duration escrow, and no learned period mechanism. Owner epoch is used only for provenance and stale-event rejection.
* **conflicting prior assessments preserved:** the campaign labeled the candidate `validation_ready`; the later audit returned `REVISION_REQUIRED` and supplied six revisions. This audit replaces the advisory delta’s composite weighted utility with one primary false-latch estimand and adds the question-required fixed-duration, age-aware recurrent, and unsplit controls.
* **disposition:** `ACCEPT_FOR_TOY`
* **acceptance scope:** locally observable ontology-supported completion, age/future leakage exclusion, a monotone reject-only residual, explicit semantic waiting, and independent safe handoff.
* **not accepted:** discovering completion outside the hard-gate support, counterfactual causal responsibility, reward-derived completion, general option discovery, improved task return, or algorithmic novelty of the classifier architecture.
* **formal_project_effect:** `none`
* **implementation_authorized:** `false`
* **compute_authorized:** `false`
* **cpm_dispatch_authorized:** `false`

### 2. MRM-01 / MRM-08 / MRM-14 — smallest claim and defect

**smallest_claim `SEM-P1-C1`:** Among unique, provenance-valid, hard-positive current events, an age-free one-sided classifier can veto aliases and reduce premature semantic declarations relative to the exact deterministic hard conjunction, while never accepting a hard-negative event and while keeping semantic declaration separate from physical handoff.

The classifier may delay or miss a true declaration. Those costs are mandatory guardrails, not hidden in a composite utility.

**mathematical defect addressed**

* Elapsed age, frame count, timeout proximity, and future task success are post-initiation shortcuts rather than semantic evidence.
* An observable event class does not identify counterfactual causal responsibility.
* Semantic completion and safe successor execution are different stopping times with different information sets.
* A single stop/handoff decision cannot represent “semantically complete but physically unsafe to hand off” unless it internally reconstructs an equivalent latent state.
* Duplicate or stale events can multiply terminal transitions without immutable event identity.
* A learned classifier that may override failed hard predicates can create unsupported completion rather than refine an identified candidate set.
* A weighted utility can conceal an unacceptable miss or unsafe handoff behind return gains.

### 3. MRM-01 / MRM-05 — scientific object and strategic scope

**scientific_object:** A finite event-driven Dec-POSMDP with one focal agent, two frozen partners, fixed ordinary roster, asynchronous semantic events, and an independently changing handoff-safety certificate.

**objective of the scientific test:** reduce false semantic declarations on prospectively assigned ontology-supported skill instances. External return, waiting time, misses, and handoff safety are guardrails and reported components, not training labels or a weighted primary objective.

**policy process**

* Primitive focal and partner policies are frozen.
* Event production and handoff safety are exogenous under the frozen toy law.
* The residual is fitted by current-time supervised alias labels.
* No policy co-adaptation occurs.
* The relevant solution concept is an event classifier embedded in a frozen controller, not a MARL equilibrium.

**scope.partner_policy_population:** three familiar source-behavior families and three held-out families differing in acknowledgment latency and alias prevalence but not exposing identity to the residual.

**membership_nonstationarity:** ordinary roster change is frozen. One owner-replacement trace is a negative control for epoch closure and stale replay only.

### 4. MRM-03 — identity, provenance, and symmetry

| Object                | Contract                                                                                     |
| --------------------- | -------------------------------------------------------------------------------------------- |
| persistent owner      | `agent_uuid`                                                                                 |
| active tenure         | `owner_epoch`; replacement closes the prior namespace                                        |
| skill identity        | immutable `skill_instance_id` plus `skill_semantic_id`                                       |
| event identity        | owner, epoch, skill instance, source, source epoch, class, subject, sequence, and event UUID |
| event source          | registered own sensor/controller, joint aggregator, or active partner epoch                  |
| event class           | self-triggered, joint-triggered, or partner-triggered observable receipt class               |
| semantic truth        | training-only current-time adjudication; never an execution feature                          |
| semantic latch owner  | current skill instance                                                                       |
| handoff receipt owner | current semantic-latched skill instance and successor transaction                            |
| partner identity      | excluded from the residual and replaced by source-type/provenance fields                     |
| symmetry              | owner and partner labels are permutation-equivariant once event histories are permuted       |

Self, joint, and partner-triggered denote receipt provenance, not causal attribution.

### 5. MRM-04 — clocks and competing causes

| Clock               | Frozen definition                                                                                                        |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| primitive clock     | Physical execution frames, not read by the target residual                                                               |
| opportunity clock   | Each unique processable hard-positive event while the skill is `RUNNING`                                                 |
| initiation clock    | Skill-instance creation                                                                                                  |
| termination clock   | Semantic latch, safe handoff, timeout, safety interrupt, leave, replacement, episode end, or protocol invalidation       |
| union-event clock   | Ordered stream of semantic receipts, handoff certificates, safety causes, membership controls, duplicates, and reorders  |
| membership clock    | Frozen except the replacement control                                                                                    |
| update clock        | Supervised residual optimizer steps on the frozen training partition                                                     |
| credit clock        | One supervised label per unique adjudicated hard-positive event; no task-return credit                                   |
| physical-time clock | Used for waiting, timeout, and reported delay; absent from residual features                                             |
| discount clock      | Not applicable to the primary false-latch estimand; external return is reported without becoming a label                 |
| interruption clock  | Safety interrupt, timeout, leave, replacement, or episode end                                                            |
| censoring clock     | Unresolved current-time adjudication, missing predecessor, unsupported ontology class, or higher-priority external cause |

**exclusive same-boundary priority:** episode end → replacement → leave → safety interrupt → timeout → protocol invalidation → semantic acceptance → safe handoff.

### 6. Exact ontology, state, observations, actions, and transitions

**registered event classes**

1. `SELF_TRIGGERED_EFFECT_ACK`
2. `JOINT_TRIGGERED_EFFECT_QUORUM`
3. `PARTNER_TRIGGERED_EFFECT_ACK`

Each class freezes allowed sources, owner/roster requirements, subject, effect token, target token, final progress code, local contemporaneous corroboration, and canonical alias families. Any unregistered class or source is a hard negative.

**state**

[
s_t=(q_t,A_t,V_t,k_t,\ell_t,\mathcal B_t,\sigma_t,\chi_t,\xi_t),
]

where:

* (q_t\in{\mathrm{RUNNING},\mathrm{SEMANTIC_WAITING},
  \mathrm{HANDED_OFF},\mathrm{TERMINAL}_{c}});
* (A_t,V_t) are owner epoch and roster version;
* (k_t) is the skill instance;
* (\ell_t) is the immutable event ledger;
* (\mathcal B_t) is a reorder buffer of capacity four;
* (\sigma_t) is the current safety/successor certificate;
* (\chi_t) is the current age-free event and local-state feature snapshot;
* (\xi_t) is the frozen future event, speed, partner, and handoff tape.

**observations**

All principal arms receive the same primitive observation stream and event payloads. The target residual reads only the unique current event and current local effect snapshot. It has no recurrence or history. Age-aware controls may derive timing from the same raw history; they receive no privileged future or semantic-truth label.

**hidden variables**

* true semantic versus hard-positive alias status;
* future safe-handoff availability;
* future reward, task success, timeout, partner event, and terminal cause;
* training-only current-time adjudication label until the supervision partition is opened.

**actions**

* while `RUNNING`: continue incumbent primitive execution;
* on a hard-positive event: residual `REJECT` or `ABSTAIN_FROM_VETO`;
* while `SEMANTIC_WAITING`: deterministic `SAFE_HOLD`;
* when independently certified: commit one handoff;
* unsupported or hard-negative events do not call the residual.

**hard semantic rule**

[
\mathrm{SEMANTIC_ACCEPT}(E,H)
=G_{\mathrm{SEM}}(E,H)\land
[V_\theta(E,H)=\mathrm{ABSTAIN_FROM_VETO}].
]

The accepted event set is always a subset of the exact deterministic hard-conjunction set. Learning cannot rescue a failed predicate or declare earlier than the deterministic conjunction on the same unique-event stream.

**state transitions**

* `RUNNING + accepted semantic event → SEMANTIC_WAITING`;
* `RUNNING + accepted semantic event + safe certificate → HANDED_OFF`, committing latch first and handoff second;
* `RUNNING + safe certificate without semantic acceptance → RUNNING`;
* `SEMANTIC_WAITING + unsafe/unavailable → SEMANTIC_WAITING` under deterministic safe hold;
* `SEMANTIC_WAITING + safe certificate → HANDED_OFF`;
* higher-priority external cause closes the instance;
* duplicates are no-ops;
* conflicting duplicates or unresolved excessive reordering invalidate the protocol;
* all terminal states are absorbing.

**count invariants**

[
N_{\mathrm{handoff}}\le N_{\mathrm{semantic}}\le1
]

per skill instance, and every closed instance has exactly one closing cause.

### 7. Information and gradient firewall

**allowed residual inputs**

* registered current event class and source type;
* current skill semantic and target declarations;
* current signed effect and progress fields;
* current local target-effect snapshot;
* current roster compatibility fields required by the ontology;
* training-frozen source-class reliability constant that is not owner-specific.

**forbidden direct or proxy inputs**

* elapsed age, frame count, event count, remaining timeout, source sequence value, buffer occupancy, time since prior event;
* recurrent hidden state, position embedding, temporal convolution, frame stack, event-history pooling, or within-skill running normalizer;
* reward, accumulated return, future success, future handoff, future terminal cause, or review outcome;
* partner identity or policy-family identity;
* later adjudication or retrospective causal labels.

**supervision**

* one unit is one unique hard-positive event key;
* `TRUE_SEMANTIC_COMPLETION → y_alias=0`;
* `HARD_POSITIVE_ALIAS_OR_NONCOMPLETION → y_alias=1`;
* unresolved or externally censored adjudication is excluded and reported, never labeled zero;
* labels are bound to the same current physical snapshot;
* task reward, duration, timeout proximity, later handoff, and future suffix are forbidden;
* gradients terminate at a frozen current-event encoder and cannot enter the ledger, hard gate, primitive policy, safe hold, handoff gate, or task value.

### 8. Optimal-policy necessity and final-capability link

The toy crosses semantic truth and handoff safety:

| Semantic truth | Handoff safe | Behavior required of any optimal controller                      |
| -------------- | ------------ | ---------------------------------------------------------------- |
| true           | false        | declare semantic completion, enter safe waiting, do not hand off |
| false          | true         | remain running; successor readiness cannot create completion     |
| true           | true         | declare once and hand off once                                   |
| false          | false        | remain running unless an external cause wins                     |

Therefore, successful behavior requires semantic completion and physical handoff to be separate decisions, whether represented by the explicit FSM or reconstructed internally by a matched recurrent null. A fixed-duration stop cannot satisfy both speed regimes. An unsplit controller that succeeds has implemented an equivalent hidden semantic state and reduces, rather than confirms, the need for the explicit interface.

The alias-positive stratum is constructed so the coarse hard predicates are identical for true and alias events, while current age-free local evidence is informative. If no such stratum exists, the deterministic conjunction is sufficient and the learned residual is retired.

**general-MARL capability link:** the toy tests whether individual skill completion can be locally identified without a duration shortcut and safely separated from successor execution under asynchronous partner events. It does not establish task-level skill usefulness or causal credit.

### 9. MRM-06 — one estimand, hierarchy, thresholds, and volume

**primary_estimand**

[
\Delta_{\mathrm{false}}
=======================

\mathbb E[
\mathbf 1{\text{false semantic declaration under deterministic conjunction}}
----------------------------------------------------------------------------

\mathbf 1{\text{false semantic declaration under target}}
],
]

over all prospectively assigned ontology-supported skill instances, with the three event classes weighted equally.

This is the only primary estimand. Return, misses, delay, waiting, and handoff outcomes are mandatory guardrails and component reports.

**top-level independent unit:** one independent training run with its own data partition, residual fit, thresholds, and frozen deployment.

**nested hierarchy:** events and duplicate families within skill instances; skill instances within trajectories; trajectories and partner realizations within runs.

**identification assumptions**

* the ontology and current-time adjudicator are frozen before data collection;
* both true and alias hard-positive support exist in every retained class;
* the adjudicator does not inspect future state;
* target and controls receive identical execution-visible event evidence;
* safe hold exists whenever semantic waiting is reachable;
* duplicate families never cross arms or partitions;
* partner identities are not residual inputs.

**uncertainty_plan:** paired run-cluster randomization intervals over sixteen independent runs, with simultaneous 95% control over the primary class-aggregate contrast and three class-specific diagnostic contrasts. No event-level pseudoreplication.

**primary threshold**

* simultaneous lower bound for (\Delta_{\mathrm{false}}) greater than `0.05`.

**mandatory guardrails**

* true-completion acceptance noninferior to deterministic conjunction within `0.02`;
* median additional unique-event-rank delay at most one;
* 95th percentile additional rank delay at most two;
* unsafe handoff count exactly zero;
* target must beat rate-matched random and label-shuffled sham controls on false declarations;
* held-out false-declaration improvement positive and noninferior to familiar improvement within `0.02`;
* age/speed/future-suffix invariance mismatches exactly zero;
* every retained event class has both true and alias support.

**bounded evidence volume**

* eight fixed principal/diagnostic arms;
* sixteen independent runs;
* per run and event class: at most 64 labeled true and 64 labeled alias training events;
* evaluation: 32 prospectively assigned instances for every reachable semantic-truth × handoff-safety × speed cell;
* two roster sizes, three event classes, two speed regimes;
* fixed sixteen-second horizon;
* no ontology expansion, threshold tuning, run replacement, or optional stopping.

### 10. MRM-07 / MRM-09 / MRM-10 — strongest nulls and interventions

**principal target:** split semantic/handoff FSM with the age-free reject-only classifier.

**strongest nulls**

1. **Exact deterministic conjunction:** identical ledger, hard gate, waiting, and handoff; accepts every hard-positive event.
2. **Fixed-duration control:** tuned fixed stopping time with identical safe-handoff gate and physical horizon.
3. **Age-aware recurrent control:** same raw observations and matched parameter/state budget, but it may exploit ordinary observation history and inferred elapsed time.
4. **Unsplit completion-handoff control:** same raw information and recurrent capacity, but no explicit semantic-latched state; it chooses whether to continue, wait, or hand off through one ordinary recurrent controller.
5. **Static age-free classifier:** same current features and capacity, but an unconstrained direct completion classifier rather than a reject-only residual.
6. **Label-shuffled sham learner:** matched model, examples, steps, parameter count, and class-specific rejection exposure.
7. **Rate-matched random rejection:** same cause-class rejection rates with no event-content dependence.

**equivalence controls**

* no-alias population: target and deterministic conjunction must be equivalent;
* handoff always safe: split and a correctly behaving unsplit controller may be equivalent;
* matched unique event under fast/slow schedules: target residual bytes and decision must be identical;
* fixed prefix with two future suffixes: current residual decision must be identical.

**negative controls and placebos**

* unsupported event class;
* stale prior-epoch event;
* byte-identical duplicate;
* conflicting duplicate;
* within-buffer reorder;
* missing predecessor;
* safe successor without semantic truth;
* semantic truth with unsafe successor;
* duplicated no-change frames;
* source sequence or buffer occupancy sentinel hidden from residual;
* random partner identity permutation.

**policy swaps and held-out conditions**

* eager, cautious, and noisy-but-valid familiar partners;
* held-out latency shift, missing-acknowledgment, and alias-prevalence shift;
* at least one held-out event-path template per retained class;
* owner and partner label permutation.

**frozen-output controls**

* Replay one fixed residual accept/reject sequence through split and unsplit state machines.
* Replay identical current event snapshots under fast and slow primitive schedules.
* Freeze semantic decisions and vary only handoff safety.
* Freeze handoff certificates and vary only semantic truth.

**ablations**

* permit age/history;
* remove immutable event key;
* merge semantic and handoff states;
* allow the classifier to rescue hard negatives;
* use future success as a label;
* remove safe hold;
* reveal partner identity.

### 11. Safety/accounting versus learned paths

* Ontology, signature checks, event deduplication, ordering, hard predicates, cause priority, semantic latch, safe hold, and handoff are deterministic safety/accounting.
* The residual learns only current-event alias rejection.
* It has no task reward, intrinsic reward, value function, exploration objective, policy-gradient path, or handoff gradient.
* Safe-wait cost and successor quality cannot train or tune the residual.
* The primitive and partner policies are frozen.
* External task return is reported only to expose downstream harm; it cannot rescue a failed semantic or safety gate.
* An unsupported or out-of-support event fails closed.

### 12. MRM-08 — replacement ledger

**DELETE**

* duration- or age-based completion from the target path;
* reward, later success, timeout proximity, or future handoff as completion labels;
* recurrent residual state;
* learned rescue of hard negatives;
* a single completion/handoff latch;
* event-class language interpreted as causal responsibility;
* weighted composite utility as the primary estimand.

**RETAIN**

* existing primitive and partner policies;
* externally registered timeout and safety interruption;
* ordinary event sources and local current observations;
* task reward as an external report;
* exact deterministic conjunction as fallback.

**ADD**

* versioned local completion ontology;
* immutable event key and bounded reorder behavior;
* one-sided age-free alias classifier;
* explicit `SEMANTIC_WAITING`;
* deterministic safe hold;
* separate exactly-once handoff certificate;
* current-time adjudication and support accounting.

### 13. Retirement, failure, and complexity

**retirement conditions**

* Target equivalent to deterministic conjunction on supported alias strata: delete the learned residual; retain the ontology and split FSM.
* Static age-free classifier equivalent to the target: the residual is ordinary supervised classification; retain only the one-sided safety contract if it has an independent benefit.
* Age-aware recurrence matches or exceeds target in held-out speed regimes without leakage: age-free semantic discrimination is unsupported in this scope.
* Unsplit recurrent control matches every crossed semantic/safety condition: explicit semantic state is unnecessary, although the successful null has implemented equivalent behavior internally.
* No locally observable true-versus-alias support: park the learned residual and use deterministic conjunction or timeout.
* No deterministic safe hold for a reachable waiting state: `NO_ACCESS`; do not improvise a learned waiting action.
* Any event class lacking both true and alias support is parked separately rather than averaged into retained classes.

**complexity and resource bounds**

* `K_search=8` fixed arms; no expanding search or rollout planning.
* Event processing is (O(1)) with a reorder buffer capped at four.
* Partner corroboration must use bounded neighborhood (O(Nk_{\text{neighbor}})), (k_{\text{neighbor}}\le16), or (O(N\log N)); no dense deployment claim.
* Classifier and matched learned controls use one fixed bounded parameter budget; no architecture search.
* The complete nonformal exercise must be projected below twenty minutes.
* Failure to meet the bound is non-executable design, not a scientific negative.

### 14. CPM-facing invariants, stop condition, and result propositions

**CPM-facing scientific invariants**

1. Ontology and event schema freeze before opening any training partition.
2. One immutable event key produces at most one residual call and one semantic transition.
3. Hard-negative events never reach the residual.
4. Target acceptance is a subset of deterministic hard-positive acceptance.
5. Residual features contain no age, temporal proxy, future information, reward, or partner identity.
6. Training labels are contemporaneous and event-key bound.
7. Ambiguous and censored events are excluded and reported.
8. Semantic and handoff counts are separately idempotent.
9. Handoff cannot precede semantic latch.
10. Safe successor availability cannot create semantic completion.
11. Every principal arm receives identical event evidence, physical process, policy capacity where applicable, horizon, and evaluation volume.
12. False declarations are measured over all prospectively assigned supported instances, not a post-selected accepted subset.

**exact stop condition:** stop at the first ledger, ontology, age/future firewall, state-transition, or safe-hold failure. Otherwise stop after the fixed familiar and held-out evidence volumes. No failed result permits ontology revision, threshold retuning, additional event classes, more runs, or reward-derived labels.

| Evidence class         | Smallest proposition                                                                                                                                                          |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| positive               | The bounded age-free reject-only rule reduces false declarations beyond deterministic and passive controls while preserving acceptance, delay, safety, and held-out transport |
| negative               | A named deterministic, fixed-duration, recurrent, static-classifier, or unsplit null is sufficient; retire only the increment it renders unnecessary                          |
| mixed                  | Split semantic/handoff interface passes but learned residual does not, or only some event classes transport; retain the interface or supported classes separately             |
| underpowered           | Class lacks true/alias support or the run-level interval crosses its margin; park that class without averaging it away                                                        |
| access-failed          | No current-time ontology, adjudicator, provenance, or safe-hold action exists; no mechanism conclusion                                                                        |
| implementation-invalid | Any duplicate transition, age/future leakage, label contamination, information mismatch, or unsafe handoff; no scientific update                                              |

---

## `SHARED_TOY_INTERFACE_CONTRACT`

### 1. Identity and purpose

* **contract_id:** `SHARED-TOY-INTERFACE-P1-R1`
* **workflow_id:** `EXPLORER-TOY-VALIDATION-2026-07-31-P1`
* **stage_commit:** `ff7cd4bab13b22beb0606cd5761d14e74ca4b257`
* **purpose:** provide one isolated audit-record vocabulary while preserving separate VAP and VSP transition laws, information sets, rewards, RNG, state, and conclusions.
* **not a merged algorithm:** no VAP mechanism may solve a VSP task, and no VSP duration or semantic mechanism may alter a VAP trace.
* **UAV/G0/G51 effect:** none.
* **implementation_authorized:** `false`
* **compute_authorized:** `false`

The isolation requirement follows the project rule that membership and lifetime may be staged independently, that clocks and ownership must remain explicit, and that evidence search and deployment complexity remain bounded.

### 2. Mode contracts

**`MODE_VAP`**

* Skill identity and period are frozen.
* No duration action, completion learner, renewal policy, or semantic handoff path exists.
* Exposes join, leave, rejoin, replacement, slot reuse, active-set change, delayed outcome, duplicate, stale, and conflict events.
* Owns survivor-private and roster-dependent state distinctions.
* Reward and query law are the FOLR toy law only.

**`MODE_VSP_ESCROW`**

* Roster is fixed except controlled focal leave/replacement causes.
* Retains initiation, nominal expiry, realized termination, interruption, renewal, reward watermark, and physical-time credit clocks.
* No survivor-state restoration or dynamic-roster objective.
* Reward and context law are the crossed duration toy only.

**`MODE_VSP_SEMANTIC`**

* Roster is fixed except stale-replay/replacement controls.
* Retains skill initiation, semantic events, semantic latch, safe waiting, handoff, timeout, interruption, and event-order clocks.
* No duration action or duration credit.
* Reward is not a completion label.

### 3. Shared record vocabulary

| Shared field            | Permitted use                                           | Forbidden use                                            |
| ----------------------- | ------------------------------------------------------- | -------------------------------------------------------- |
| `owner_id`              | authenticate and address a current entity               | learned role, partner identity feature, or slot shortcut |
| `owner_epoch`           | distinguish active tenure and reject stale state/events | cross-epoch restoration                                  |
| `roster_version`        | validate membership-scoped records                      | VSP context or duration signal                           |
| `slot_map`              | audit current physical placement in VAP                 | continuity, role, skill, or credit ownership             |
| `event_uuid/source_seq` | deduplicate and order events                            | actor feature or temporal shortcut                       |
| `event_cause`           | deterministic terminal/censoring arbitration            | intrinsic reward or causal-responsibility label          |
| physical time           | SMDP discount, waiting, timeout, and audit              | semantic-residual input                                  |
| `skill_instance_id`     | scope a current skill and semantic event                | persistent owner identity                                |
| skill boundary          | initiation, renewal, completion, interruption, handoff  | implicit shared-duration synchronization                 |
| action/decision receipt | immutable initiation ownership and exactly-once closure | current-slot reassignment                                |
| audit receipt           | prove conformance and reproduce estimands               | policy observation, reward, or learned latent            |

### 4. Non-coupling and information invariants

1. Mode-specific state, recurrence, normalizers, replay, rewards, RNG namespaces, and optimizers are disjoint.
2. A shared field is actor-visible only when the applicable toy contract explicitly declares it and every comparator receives it identically.
3. Audit-only fields must pass a counterfactual no-effect test: zeroing or permuting an unused field leaves the action kernel, reward law, learning target, and primary estimand unchanged.
4. VAP’s roster version cannot influence VSP duration context or semantic classification.
5. VSP initiation, duration, completion, or handoff causes cannot alter VAP survivor-state admission.
6. No shared learned encoder, state bank, classifier, critic, scheduler, or reward term exists.
7. `owner_id`, `slot_id`, role, skill, and recurrent-state owner remain distinct types.
8. Event delivery time and physical event time remain separate.
9. Shared serialization or audit formatting is not evidence of a common scientific mechanism.
10. A field that creates result-changing information in only one mode must move into that mode’s private contract rather than remain shared.

### 5. Shared transition and resource boundaries

* Each mode has its own complete transition law; the interface cannot invent a default transition.
* One mode cannot call another mode’s event handler or state transition.
* Maximum fixed evidence-arm or trace count remains sixteen.
* No nested rollout, horizon-growing library, tree search, or beam search.
* Shared bookkeeping is (O(N+R_{\mathrm{open}})), with any neighborhood operation bounded by (k_{\text{neighbor}}\le16).
* A fixed small exact simulator may use dense physics only as a reference and cannot support a scalable-algorithm claim.
* Current review cost and compute remain zero.

### 6. Interface stop condition

If any shared field changes an action distribution, target, reward, state survival, or outcome in a mode without being declared in that mode’s information contract and matched across its comparators, the shared-interface assertion fails. The field must be separated; no toy may run under the coupled interface.

---

## `SCHEDULED_FIRST_TOY_ACTION`

* **action_id:** `FIRST-TOY-VAP-FOLR-CONFORMANCE-01`
* **scientific unit:** `TOY-SCI-VAP-FOLR-CORE-P1-R1`
* **action:** execute one frozen pass of the sixteen-trace FOLR lifecycle/state/receipt conformance and behavioral-necessity matrix.
* **schedule status:** `SCIENTIFICALLY_SCHEDULED_PENDING_SEPARATE_GATE`
* **implementation_authorized:** `false`
* **compute_authorized:** `false`
* **cpm_dispatch_authorized:** `false`
* **global-winner implication:** none. This is an attribution and cost ordering only.

### Selection rationale

* **dependency:** lifecycle ownership and immutable delayed receipts are prerequisites for interpreting any later VAP return comparison; the action has no dependency on a learned policy, optimizer, ontology, reward watermark, or partner training.
* **information gain:** one bounded matrix can expose contradictions in owner/epoch semantics, state ancestry, mask domains, event ordering, stale exclusion, slot reuse, and receipt ownership before any learned toy creates alternative explanations.
* **reversibility:** the harness is isolated, deterministic, checkpoint-free, and leaves no learned state or formal-project effect.
* **cost:** sixteen traces, at most twelve boundaries each, no optimizer and no model fitting; this is strictly cheaper than either VSP behavioral discriminator.
* **portfolio preservation:** VSP-ASYNC-ESCROW and VSP-SEMANTIC-HANDOFF remain live and accepted for toy design.

### Required pre-code `DESIGN_ASSERTION_AUDIT` gate

* **gate_id:** `DAA-PRECODE-FIRST-TOY-FOLR-01`
* **gate status:** `DEFINED_NOT_EXECUTED`

The future gate must establish all of the following before any implementation may be considered:

1. The complete state manifest binds every action- or update-affecting variable to exactly one ownership class.
2. `D_outcome_max`, `D_event_replay_max`, receipt retention, the in-flight binding, and both boundary-order traces are finite and unambiguous.
3. The exact sixteen trace rows, initial states, events, expected state reads/writes, masks, actions, receipts, and terminal results are frozen.
4. Actor-visible and audit-only fields are explicitly separated.
5. `MASKRESET-RNN` is matched on policy, information, recurrence capacity, initialization, events, storage, normalization, action opportunities, and budget.
6. The survivor-bit proof establishes the (1) versus (1/2) access separation without a global scratchpad, bit reobservation, owner-specific parameters, or slot shortcut.
7. The delayed-outcome proof forces current-slot and action-instance ownership to diverge.
8. No trace-specific exception table or undeclared state channel can satisfy the expected outputs.
9. `K_search=16`, total transitions are at most (16H), no nested rollout exists, deployment bookkeeping is linear or bounded-neighborhood, and projected wall clock is below twenty minutes.
10. Positive, negative, mixed, access-failed, and implementation-invalid first-match outputs are encoded exactly as this contract specifies.
11. The shared-interface counterfactual no-effect checks pass.
12. Passing this gate would establish design sufficiency only; it would not authorize code, compute, Stage B return evaluation, CPM activation, or formal adoption.

### Live unscheduled units and reactivation conditions

* **`CAND-VSP-02` remains live:** eligible for later scheduling after this first action is archived or ends in an access/implementation blocker, and after its own pre-code gate proves physical-time reward closure, exact per-step and termination-time controls, duration/primitive firewalls, effective duration support, and the analytic crossed optimal-policy ordering.
* **`CAND-VSP-05` remains live:** eligible for later scheduling after this first action is archived or ends in an access/implementation blocker, and after its own pre-code gate proves a nonvacuous true-versus-alias hard-positive population, current-time adjudication access, deterministic safe hold, the semantic-truth × handoff-safety optimal-policy cross, and complete age/future leakage exclusion.

**scheduled-action stop condition:** one execution of the frozen sixteen-trace matrix, or the first invariant failure, whichever occurs first. Archive that result and stop; do not automatically launch a VSP toy, a performance stage, implementation revision, or another scientific iteration.
