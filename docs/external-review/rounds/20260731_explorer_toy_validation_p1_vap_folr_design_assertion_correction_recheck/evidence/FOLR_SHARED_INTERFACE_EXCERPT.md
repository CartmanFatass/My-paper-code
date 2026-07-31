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
