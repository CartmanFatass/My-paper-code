# HMASD Conjectures

These are scientific possibilities, not implementation authority. Active role
authority is defined by `AGENTS.md` and `.agents/roles/`; this ledger records
the Project Manager-accepted CDC state.

## C-OPEN-ROSTER-DIRECT — A shared direct policy is usable across dynamic N

- Status: accepted as a usable prefix-normalized dynamic-roster algorithm test
  version for the registered heterogeneous family through N=80.
- Claim: a parameter-shape-`N`-independent direct recurrent policy with
  lifecycle-owned hidden state and active-set aggregation can learn one task
  policy that remains usable under within-episode JOIN, temporary leave,
  rejoin, genuine join and terminal leave, including held-out active counts.
- Retained evidence: formal G5 reaches IID deterministic utility CI95
  `[0.9985352, 0.9994303, 1.0]` and held-out CI95
  `[0.9828880, 0.9939927, 1.0]`; the worst held-out replicate is `0.9828880`.
  One checkpoint transfers from training counts through seven to held-out
  counts through nine and from capacity 10 to 12. Formal G6 then freezes those
  checkpoints and reaches count-scale CI95 `[0.9294811, 0.9728004, 0.9990977]`
  and joint CI95 `[0.9358802, 0.9763486, 0.9999524]` through N=16 with unseen
  event times. R49 independently proves active-only permutation, padding,
  replay and membership mechanics through `N=16`.
- Formal counterexample: G7 keeps the successful checkpoints frozen but obtains
  moderate CI95 `[0.8590299, 0.9346962, 0.9864063]`, far CI95
  `[0.8089696, 0.8922767, 0.9669230]` and joint CI95
  `[0.8377266, 0.9154998, 0.9789795]`. Persistent duty remains perfect; short
  allocation degrades across seeds as scale grows.
- Prototype separation: the registered eight-variant screen selects raw active
  sum, original log-count and action-prefix fractions with minimum-domain mean
  `0.8317871`, a `0.0563965` lead over the runner-up. This is candidate
  selection, not formal evidence or unique causal attribution.
- Formal repair evidence: freshly trained G8 reaches deterministic CI95 LCBs
  `0.9432373` IID, `0.9469604` held-out, `0.9321289` moderate, `0.9302979` far
  and `0.9299927` joint, with joint stochastic mean `0.8994221` and positive
  learned-gain LCB. G7 remains the valid frozen raw-prefix failure.
- Formal churn evidence: frozen G8 finals retain deterministic CI95 LCBs
  `0.9309692`, `0.9294434` and `0.9299316` across repeated-rejoin,
  load-proximal and mixed eight-edit domains; the mixed stochastic mean is
  `0.9099933`.
- Formal composition evidence: G10 places N=12--40 and eight membership edits
  in the same episodes. Its deterministic lower bounds are `0.9296265`,
  `0.9245605` and `0.9272461`, with mixed stochastic mean `0.8963305`.
- Formal layout evidence: G11 produces exactly zero persistent, short or utility
  mismatches under reversed keys, odd sparse keys and affine-scattered capacity
  128. Every deterministic layout has CI95
  `[0.9252930, 0.9513707, 0.9991316]`; stochastic mean is `0.8969246`.
- Strongest remaining counterexample: the same slot-invariant representation
  may still lose allocation quality when active count exceeds 40.
- Separating evidence: G12 now freezes the G8 finals and crosses the observed
  N=40 boundary at maxima 48, 64 and 80 without retraining, threshold changes
  or task-semantic changes. Formal deterministic LCBs are `0.9251709`,
  `0.9230957` and `0.9270020`, and N=80 stochastic mean is `0.8973560`.
- Strongest remaining counterexample: each registered domain still uses one
  hand-authored membership schedule, so process-level schedule memorization is
  not excluded.
- Separating evidence: G13 now draws valid event time, type, magnitude, member
  keys and active-count trajectories independently per episode under frozen
  checkpoints. Formal random-process LCBs are `0.9249674`, `0.9270833` and
  `0.9283854`; the random-ultra stochastic mean is `0.8892955`.
- Formal atomic evidence: G14 terminates and joins matched random cohorts in
  the same transaction while holding active count fixed. Its deterministic
  LCBs are `0.9230957`, `0.9257813` and `0.9291992`; the ultra stochastic mean
  is `0.8951629`.
- Formal interaction evidence: G15 uses unequal positive terminal/fresh-join
  cohorts in every atomic event and alternates large low/high count bands. Its
  deterministic LCBs are `0.9188949`, `0.9166667` and `0.9225260`; ultra
  stochastic mean is `0.8936155`.
- Formal deployment evidence: G16 uses 108 fresh-seed profiles with exact
  12/12/12 mode balance per scale across serial random edits, equal atomic
  replacement and unequal atomic count shocks. Deterministic LCBs are
  `0.9253538`, `0.9231771` and `0.9251302`; ultra stochastic mean is
  `0.8928564`.
- Remaining limitations, not active counterexamples: arbitrary process laws,
  N above 80, asynchronous skill lifetime, intrinsic-reward benefit and
  comparative advantage are outside the completed grant.
- Current role: G8 remains the accepted dynamic-roster base and complete
  comparator for the C-ALPSW direction; it supplies no skill-lifetime claim.
- Scope: skill selection, skill lifetime, EHC, intrinsic reward and comparative
  advantage are frozen out. Success establishes a usable dynamic-roster base,
  not the final two-axis HMASD algorithm.

## C-ALPSW — Agent-local predictive sparse-write slow state

- Status: exact registered formulation rejected before implementation by
  `NO_ONLINE_IDENTIFIABLE_SLOW_STATE` in S1. Predictive-state and sparse-
  segmentation families remain broader than this result; no local correction
  is selected.
- Refuted claim at exact scope: the registered predictive NLL plus learned-write
  cost can uniquely identify a lifecycle-owned slow state while an unrestricted,
  unpenalized fast recurrent state reads the same online history and is also
  supplied to the predictive decoder.
- Exact evidence: a finite anonymous 21-transition construction has independent
  lifecycle scripts, complete active-step lifetimes 2 and 3, exact boundary
  precision/recall 1, `U_star_ALPSW=U_star_G8=1` and zero invariance mismatch.
  Nevertheless a one-bit never-write recurrence attains the entropy lower bound
  with zero learned-write cost.
- General disproof: on any finite discrete source the recurrent state can encode
  legal history or its predictive sufficient statistic and marginalize the
  writer's internal randomness. Its expected predictive NLL is no greater.
  Thus `beta>0` favors no-write, `beta=0` is non-unique and `beta<0` favors
  always-write; the required open beta interval is empty.
- Smallest retained proposition: finite lifecycle recurrence can absorb the
  registered slow state and match prediction. This does not imply equal
  optimization, sample efficiency, causal mediation or held-out transport.
- Disposition: closed at the exact S1 formulation with no local rescue.
  Broader predictive state and sparse segmentation remain unresolved; only a
  new external-Pro scientific contract may change the information partition or
  complexity accounting.

## C-ALPSC — Agent-local predictive slow channel

- Status: exact S2 contract rejected before implementation by
  `NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL`; no local interval, decoder or null
  restriction is selected.
- Refuted claim at exact scope: exclusive temporal ownership makes the cue
  writer uniquely optimal throughout `0 < beta < (1/2) ln 3`.
- Decisive evidence: the admissible never-write null preserves structural
  `z=B` and fits `P(Y=z|z)=4/7`, giving
  `L_NW=ln 7-(4/7)ln 4-(3/7)ln 3`. It ties the cue writer at
  `beta_star=(7/2)ln 7-(11/2)ln 4+(9/8)ln 3`, which lies strictly inside the
  frozen interval, and wins above it.
- Contract validity: the exclusive writer/decoder contains no fast-state,
  clock, action, direct-cue, active-set-history or auxiliary-memory channel.
  All deterministic schedules, candidate maps, periodic and membership
  policies, post-hoc null and stochastic mixtures have an exact finite
  enumeration; the decisive never-write null itself uses no side channel.
- Smallest retained proposition: excluding alternative temporal channels is
  necessary for ownership identification but not sufficient; an optimized
  decoder still creates a rate--distortion tradeoff between predictive
  precision and write rate.
- Scope ceiling: this result does not reject exclusive predictive channels,
  sparse segmentation or variable lifetime generally. Any beta-interval,
  decoder-family, objective or source correction requires external Pro.

## C-ALCPS — Agent-local controlled predictive state lifetime

- Status: exact S3 derivation PASS; implementation and compute remain
  unauthorized pending a new external Pro decision.
- Supported claim: on the frozen finite source, the coarsest minimum-transition
  state sufficient for the full vector of primitive-action-interventional
  observation laws has a canonical active-step lifetime `{2,3}`.
- Exact result: the candidate reaches `(E_ctrl,q,K)=(0,2/7,2)`. Every
  controlled-sufficient online model has `q>=2/7`; equality writes exactly on
  the two post-join cue rows, and decoder-equivalent nuisance subdivisions
  merge to two kernels.
- Strongest simpler explanation: G8 recurrence stores the same controlled
  statistic and attains the same external utility. The result establishes no
  optimization, causal-use, sample-efficiency, robustness or transport benefit.
- Intervention consequence: the full external query-kernel vector distinguishes
  regimes while the uniformly marginalized action law does not.
- Natural and held-out consequences: not established. Any implementation or
  behavioral action requires another Pro selection and must retain G8 plus a
  mechanism-matched comparator.
- Main unresolved counterexample: one-step controlled equivalence may merge
  histories whose delayed controlled futures differ.

## C-ALSCPS — Agent-local sequential controlled predictive state

- Status: accepted exact S4 derivation PASS at the registered horizon-2 scope;
  implementation and compute remain unauthorized.
- Supported claim: on the frozen source, the coarsest minimum-transition
  quotient sufficient for all four horizon-2 controlled sequence kernels is
  update-congruent and has active-step lifetimes `{2,3}`.
- Exact result: `one_step_TV=0,K_1=1`; every complete plan has
  `horizon2_TV=1/2`; the candidate uniquely attains
  `(E_2,q,K_2)=(0,2/7,2)` up to null events and relabeling.
- Strongest simpler explanation: G8 recurrence stores the same delayed
  statistic and attains the same external utility. No optimization, mediation,
  natural-value or transport benefit is established.
- Refuted proposition: equality of immediate controlled observations is
  sufficient for equality of delayed controlled futures.
- Scope ceiling: `FUTURE_CLOSED` means only the frozen horizon-2 query family;
  arbitrary-horizon, natural-future, learned and held-out consequences remain
  unestablished.
- Main unresolved counterexample: a generic predictive-phase update may occur
  inside a constant current-behavior segment.

## C-ALBPF — Agent-local behavioral / predictive-phase factorization

- Status: live correction candidate selected only for the exact S5 predictive-
  phase/skill-lifetime confound derivation; no implementation or compute is
  authorized.
- Claim: current action-relevant behavior and generic transition phase may
  require separate lifecycle projections so an information-only phase update
  does not reset behavioral skill lifetime.
- Exact selected witness: age 1 and the legal script-32 age-2 no-cue history
  have identical current controlled behavior (`TV_behavior=0`) but next-active
  cue laws separated by `TV_phase=1/2`.
- Strongest simpler explanation: G8 recurrence stores both objects without an
  explicit factorization.
- Intervention consequence: changing predictive phase alone changes the
  transition law but not the current controlled action kernel; changing
  behavioral state changes current behavior.
- Natural consequence: a legal no-cue may update phase while behavior persists.
- Held-out, learned, architectural and policy consequences: not established.


## C-JRDM — Jointly rate-coded dual memory

- Status: parked pending a representation-invariant joint codelength or mutual-
  information contract for `h` and `z`.
- Strongest counterexample: activation, dimension or parameter penalties depend
  on arbitrary coding units and invertible mixing, so they need not identify
  temporal ownership.

## C-ALH — Explicit categorical agent-local hazard

- Status: parked. Reactivate only if an identified predictive boundary later
  requires task-directed termination without reviving R43--R45.
- Strongest counterexample: per-agent categorical KEEP/RENEW evaluated every
  active step is the existing opportunity mechanism with `k=1`, not a
  structurally new lifetime mechanism.

## C-ATS — Continuous adaptive-timescale recurrence

- Status: parked pending a threshold-free survival or causal-persistence
  estimand and explicit accounting for alternative recurrent memory channels.
- Strongest counterexample: a continuous leak supplies no objective segment
  boundary, can be absorbed into ordinary recurrence, and leaves any claimed
  lifetime dependent on a post-hoc threshold.

## C-SEPM — Set-equivariant persistent population memory

- Status: parked pending an identified complementary-allocation source.
- Strongest counterexample: TEAM_REC or an ordinary set encoder may carry the
  same information, while adding population coordination and individual
  lifetime together prevents clean attribution.

## C-EHC — Event-held temporal state

- Status: unsupported after the five-iteration chain. G2 proves an event-held
  link can be causal, but ordinary recurrence is sufficient in G1/G2 and neither
  G3 attention nor G4 count preservation establishes robust roster access or
  advantage.
- Claim: under genuinely asynchronous partial edits, an unordered roster of
  lifecycle-owned commitments may improve learning and held-out transport when
  value depends on complementarity among retained and newly selected records.
- Necessary measurement consequences: policy-dependent persistence;
  sequence-level exact-snapshot intervention; natural mediation through later
  behavior and value; multiple simultaneous records; asynchronous edit/KEEP
  composition; resistance to TEAM_REC, independent-editor and shuffled-roster
  explanations; and held-out active-count/lifetime robustness.
- A single global record, instantaneous mark/logit sensitivity, natural use,
  realized lifetime diversity and external value are insufficient support.
- Strongest simpler explanation: a persistent recurrent team state or an
  ordinary roster/set encoder supplies the same useful context without a
  policy-selected event-held mechanism.
- Natural mark evidence must be invariant to mark-label permutation within each
  replicate. Raw `P(m=b)` is not an admissible future gate.
- Gate correction: uniqueness utility is structural only.
  `CE-DIVERSITY-AS-UTILITY` requires the learned source to score realized useful
  effects under demand states where duplicate commitments can be optimal.
- G3/G4 correction: neither softmax-normalized attention nor direct absolute
  multiset counts is accepted as a stable editor. `CE-COUNT-PRESERVATION-AS-
  SOLUTION` forbids treating a count-sufficient interface as learned competence.

## C-REC — Ordinary recurrence is sufficient

- Status: selected for both exact formal memory sources. In G1, OR and DUM
  reached the same `0.9344202` mean utility and both EHC gain UCBs were
  `0.0026465`. In G2, TEAM_REC and EHC both reached 1.0 and `G_team=0`.
- Claim: a matched recurrent MARL controller can represent the required
  persistence without an explicit commitment object when access and training
  are adequate.
- Separating evidence: matched capacity and information with held-out dynamic
  membership/lifetime evaluation.
- Scope correction: per-member recurrence loses creator-only information at a
  terminal handoff, but team recurrence carries one global bit exactly. Future
  evidence must target structured variable-cardinality factorization and
  held-out transport, not claim finite-network representational impossibility.
- Current comparison role: recurrence is the mandatory strongest simpler
  explanation, exact S1 absorption witness and complete external-policy
  comparator for C-ALPSC, but never a universal admission gate. Future claims
  must concern optimization, mediation, sample efficiency, robustness,
  complexity or held-out transport rather than representational impossibility.

## C-BASE — The shared base policy class is insufficient

- Status: live and strengthened as an optimization/access explanation for the
  identified G3/G4 useful-effect source, while still rejected for formal G1
  where every arm accessed above the `0.80` floor.
- Claim: the shared recurrent actor, critic, primitive distribution or state
  representation may be unable to express or stabilize the required policy;
  the EHC adapter cannot repair every common base limitation.
- Separating evidence: an information-matched stronger policy accesses the
  same benchmark under the same credit estimator and information contract.

## C-CREDIT — Temporal credit is the bottleneck

- Status: live generally but not selected for the one-step G4 decision, where
  delayed temporal credit is absent. It remains unsupported as a rescue of G1.
- Claim: representation is adequate but primitive-step credit cannot assign
  delayed consequences to asynchronous events.
- Separating evidence: representation held fixed while only a well-defined
  temporal-credit estimator changes.

## C-BENCH — The benchmark is not identifying

- Status: the useful-effect G3/G4 source is identified while learned access is
  underpowered/no-access. Formal G1 and G2 separately show that cue memory and a
  global handoff bit do not identify EHC over ordinary recurrence.
- Claim: current benchmark/control pairs do not separate representation,
  access, credit and coordination explanations.
- Separating evidence: a constructive policy or alternative task family that
  changes identification without changing the algorithm claim.
- Current correction: G3 now uses demand-served realized effects and passes its
  source controls. The remaining ambiguity is algorithmic access stability, not
  source identifiability or label-diversity reward.

## C-COORD — Complementary coordination is the load-bearing capability

- Status: causal roster response without registered competence. G3 and G4 both
  change policy under roster intervention, yet G3 access is underpowered and G4
  count-preserving access fails; neither establishes a >0.10 advantage.
- Claim: the important variable-N difficulty is joint complementary allocation,
  not an individual lifetime mechanism in isolation.
- Separating evidence: a roster-only intervention changes an asynchronous
  editor's demand-served effect and value, followed by natural and held-out
  transport beyond matched TEAM_REC and NO_ROSTER explanations. Duplicate-
  optimal demand prevents label diversity from satisfying the claim.
- Next correction under any new user authority: hold the count-sufficient
  representation fixed and separate policy optimization/access from
  representation before returning to a mechanism-gain claim.

## C-LINK-NULL — Commitment is not load-bearing for the source family

- Status: selected for the exact formal G1 source/comparator pair; it remains
  unselected by G0. G2 rejects link-null locally because EHC-DUM gain is 0.5 and
  mark intervention consequences are 1.0, while still selecting TEAM_REC
  sufficiency at higher precedence.
- Claim: ordinary recurrence may represent the useful behavior, or the task's
  temporal structure may be mismatched to KEEP/RENEW event-held commitment.
- Separating evidence: an access-positive mechanism-matched source with
  `UCB(G)<=0.10`, or repeated confident failure of executable and natural
  consequence gates after access.

## C-MEASURE — Current behavior metrics do not identify commitment

- Status: retained and corrected by formal G2. G1 exposed a decorative link;
  G2 exposed arbitrary latent-label symmetry despite perfect behavioral use.
- Claim: usage, realized lifetime diversity or logit perturbation can be passed
  without demand-responsive persistent semantics.
- Counterexamples: `CE-RANDOM-USE`, `CE-EXOGENOUS-LIFETIME`, and
  `CE-LOGIT-WITHOUT-BEHAVIOR` jointly invalidate the old surface implication.
- Separating evidence: policy-dependent persistence, sequence-level
  intervention, natural mediation, simpler-explanation resistance, and
  held-out robustness, with event forcing separated from mark intervention,
  representation influence and natural selection/support statistics.
- Prototype evidence: the combined tuple rejects the three constructed nulls;
  recurrence remains a distinct sufficient capability explanation rather than
  being mislabeled as an event-held mechanism.
- Formal evidence: `CE-RECURRENT-CUE-MEMORY`, `CE-LOCAL-UTILITY-DOMINANCE`, and
  `CE-DECORATIVE-COMMITMENT-CHANNEL` require the next source to place useful
  state across an anonymous creator-to-successor handoff.
- G2 correction: `CE-GLOBAL-BIT-TEAM-REC`, `CE-SINGLE-RECORD-NO-COMPOSITION`,
  `CE-PASSIVE-HANDOFF`, and `CE-LABEL-SYMMETRY` require multiple standing
  records, complementarity and label-invariant natural mediation.
- G3 gate correction: `CE-DIVERSITY-AS-UTILITY` separates a causal roster edit
  from task-useful complementary effects; formal evidence must measure demand
  served rather than label uniqueness.
- G3/G4 correction: `CE-CAUSAL-RESPONSE-WITHOUT-COMPETENCE` shows that positive
  roster intervention TV can coexist with underpowered/no-access natural
  behavior and cannot substitute for competence or mediation.
