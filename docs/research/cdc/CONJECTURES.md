# HMASD Conjectures

These are scientific possibilities, not implementation authority. Active role
authority is defined by `AGENTS.md` and `.agents/roles/`; this ledger records
the Project Manager-accepted CDC state.

## C-OPEN-ROSTER-DIRECT — A shared direct policy is usable across dynamic N

- Status: supported as a usable prefix-normalized dynamic-roster algorithm
  through N=40 with eight-edit churn by formal G10; slot-layout invariance
  remains open.
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
  checkpoints; every source instance is recomputed and its formal result is
  pending.
- Scope: skill selection, skill lifetime, EHC, intrinsic reward and comparative
  advantage are frozen out. Success establishes a usable dynamic-roster base,
  not the final two-axis HMASD algorithm.

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
