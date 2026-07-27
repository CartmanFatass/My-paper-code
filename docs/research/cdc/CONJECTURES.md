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
- Scope: skill selection, skill lifetime, EHC, intrinsic reward and comparative
  advantage are frozen out. Success establishes a usable dynamic-roster base,
  not the final two-axis HMASD algorithm.

## C-CONTINUOUS-ROSTER — Continuous control under dynamic membership

- Status: supported and retained at G39 as a usable freshly trained,
  native-six-coordinate, no-carry, configured-capacity,
  bounded-random-process continuous dynamic-roster test version for the
  registered H=48, capacity-6/8/12 toy family.
- Claim: a capacity-shape-independent actor trained only at capacity 8 remains
  usable at configured capacities 6, 8 and 12 across the fixed G32 process and
  bounded G34-P0 random process. The retained actor is six-coordinate from
  initialization and contains no actor history fields, constant columns, donor
  interface or post-training fold.
- Actor information: two capability coordinates, anonymous presentation
  priority, current load, current target mix and log1p(active_count). Active
  mask, active-set aggregation and the active-fraction autoregressive prefix
  remain part of the policy contract.
- Native training boundary: the only raw-input affine maps are
  Linear(6,32) and Linear(6,2). The actor carries no learned cross-step hidden
  state and never reads lifecycle age, previous actions or normalized physical
  time.
- Formal immediate/delayed evidence: G31 passes the paired G17/G18 utility,
  spike-allocation, rotation, learned-gain and fresh-seed stability gates.
- Formal configured-capacity evidence: G32 supports strict-loadable
  capacity-6/8/12 deployment and exact common-active padding invariance.
- Formal bounded-process evidence: G34 supports zero-training transport from
  the fixed 12/24/36 process to its registered one-each-of-L/R/J/T random
  process.
- Formal current-state evidence: G35 freshly compares matched REC and CS arms.
  Both access; every REC-minus-CS UCB is at most 0.0054082 against the 0.05
  margin.
- Formal history-interface evidence: G36 shows that exact G35 CS checkpoints do
  not require the target episode's actual time, age or previous-action bundle
  when supplied with a coherent donor. G37's complete donor factorization
  closes mixed and remains historical checkpoint-sensitivity evidence.
- Formal folded-architecture evidence: G38 freshly trains a constant-input
  FOLD6 arm and folds it into a true six-coordinate deployment actor. Both
  FULL10 and FOLD6 access, and FULL10-minus-FOLD6 CI95 is
  [-0.01008621, -0.00312729, 0.00841468].
- Formal native-training evidence: G39 compares function-matched CONST10_FOLD6
  and NATIVE6_CS routes with identical actor information, critic, G31 credit,
  source, interactions and optimizer-step exposure. Both access. The
  CONST-minus-NATIVE pooled CI95 is
  [-0.00286042, 0.00393514, 0.00975470]; capacity-6/8/12 UCBs are
  0.00834785, 0.00857325 and 0.01206800. Native-six is noninferior by the
  frozen 0.05 margin.
- Accepted training and deployment boundary: NATIVE6_CS. Delete the four
  constant columns, their 136 trainable weights and Adam moments, and the
  post-training fold from the retained route.
- Retired alternatives: within G39-P0, usable deployment and training do not
  require capacity-shaped learned parameters, capacity-specific retraining,
  checkpoint adapters, the exact fixed schedule, atomic R+J, learned actor
  carry, actual actor time/age/previous-action sensors, donor/filler inputs,
  ten-coordinate deployment, constant-column overparameterization or a fold.
  A >0.05 finite-budget advantage for either the four varying history fields
  or the redundant constant parameterization is closed.
- Lifecycle boundary: active masks, likelihood ownership, environment
  lifecycle state, fresh initialization, temporary leave/rejoin, terminal
  deletion and survivor continuity remain protected runtime semantics.
- Scope: H=48; configured capacity is fixed within a trajectory and belongs to
  6/8/12; G34-P0 contains one each of L/R/J/T and three registered legal event
  orders.
- Strongest remaining training explanations: the centralized critic's true
  current state and the G31 realized-future-tail/direction-balanced credit
  package remain retained. G39 does not identify whether either can be
  simplified.
- Initialization boundary: G39 proves native-six sufficiency under a
  function-matched projected initialization, not under every independently
  sampled native initializer.
- UAV boundary: temporary-service-loss G1 and charge-rotation G2 remain source
  non-identifiable. G33 and all derivatives remain abandoned by user
  instruction.
- Exclusions: arbitrary capacity/process/horizon, critic-time reduction,
  ordinary-credit equivalence, UAV usability, asynchronous skill lifetime,
  intrinsic-reward advantage and complete-algorithm superiority remain
  unsupported.

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

- Status: selected as a sufficient capability in the exact G1/G2 memory
  sources, while learned actor carry and actor history inputs are rejected as
  load-bearing in the fully observed G35/G38 continuous-roster source family.
- Memory-source claim: a matched recurrent MARL controller can represent useful
  persistence when task-relevant information is absent from the current
  observation.
- Continuous-roster carry result: G35 compares parameter-identical REC and CS
  arms under identical information, G31 credit, source, interactions and
  optimizer exposure. Both access; every REC-minus-CS UCB is at most 0.0054082
  against the 0.05 margin.
- Continuous-roster sensor result: G36 shows that exact G35 CS checkpoints do
  not require the target episode's actual time, age or previous-action bundle
  when supplied with a coherent donor.
- Continuous-roster architecture result: G38 freshly trains a FOLD6 arm that
  never reads those four actual fields and converts it exactly into a true
  six-coordinate actor. Both FULL10 and FOLD6 access; pooled
  FULL10-minus-FOLD6 CI95 is
  [-0.01008621, -0.00312729, 0.00841468].
- Smallest retired units: learned cross-step actor carry, acquisition of the
  target's actual actor-history bundle, donor-generated history values and a
  ten-coordinate deployment actor are not required in G38-P0. The varying
  four-field bundle supplies no >0.05 finite-budget advantage.
- Retained distinction: G38 preserves current load/mix, capabilities,
  active-set information, lifecycle runtime state, the action prefix, a
  true-current-state critic and G31 training credit. It does not establish that
  partially observed tasks or all policy classes are memoryless.
- Reactivation condition: an identified source containing task-relevant
  information absent from current observations, followed by a matched material
  recurrent advantage. More seeds, budget or threshold changes on G35/G38-P0
  are not reactivation evidence.
- G39 update: native-six training from a function-matched initialization reaches
  the complete continuous-roster access contract without actor history fields
  or learned actor carry. This strengthens the local fully observed
  current-state reduction but does not change recurrence's retained role on
  sources containing task-relevant information absent from current
  observations.

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

- Status: supported retained for the registered G17/G18 paired toy family and
  the shared-anchor G40-P0 branch; universal necessity remains unsupported for
  UAV transport and unrelated source families.
- Claim: representation is adequate but primitive-step credit cannot assign
  delayed consequences to asynchronous events.
- Separating evidence: representation held fixed while only a well-defined
  temporal-credit estimator changes.
- Current paired evidence: formal G18 shows that independently normalized
  immediate/successor credit can learn the delayed G18 source but is not stable
  on G17 across fresh seeds. G19--G26 show that exact frozen-anchor additive
  residual families are too weak. G27 restores full actor capacity and keeps
  G17 strong under strict successor/immediate non-conflict, but G18 returns to
  zero spike service. G28 protects only the equal combined raw gradient and
  raises G18 spike utility to `0.88983` while retaining G17, narrowly missing
  the frozen `0.90` access floor. G29's realized Adam constraint triggers much
  more often and removes G18 access entirely. G30's equal global gradient
  directions preserve G17 and learn high broad delayed utility across fresh
  seeds, but the spike-utility LCB remains below access. G31's bounded screen
  replaces the one-step learned successor bootstrap with an environment-neutral
  realized future tail and passes both paired sources strongly. Formal G31
  confirms this across fresh seeds: every G17 and G18 gate passes, including
  spike utility LCB `0.95969`. The remaining discriminator is UAV transport,
  not another paired-toy seed or threshold change.
- G34 update: a checkpoint trained with G31 credit transports to the bounded
  G34-P0 process family, but G34 performs zero optimization and contains no
  matched credit comparator. It therefore adds checkpoint-usability evidence,
  not causal evidence that realized-future-tail credit is necessary. C-CREDIT
  remains supported only inside the registered G17/G18 paired toy family.
- G35 update: both REC and CS use identical G31 realized-future-tail targets,
  direction-balanced actor updates, critics and optimizer exposure. Current-state
  sufficiency therefore isolates actor carry only; it supplies no evidence that
  G31 credit is necessary or replaceable in this source. The G31 credit claim
  remains supported only by its registered paired G17/G18 evidence.
- G36 update: G36 freezes the G35 CS final checkpoints and performs zero
  optimization. Actual-history sensor substitution therefore adds no evidence
  about whether G31 realized-future-tail credit was necessary for learning the
  checkpoints or can be replaced. C-CREDIT remains supported only by its
  registered paired G17/G18 evidence.
- G38 update: FULL10 and FOLD6 use identical G31 realized-future-tail targets,
  direction-balanced updates, critics and optimizer exposure. The successful
  six-coordinate reduction therefore isolates actor information and deployment
  architecture only. It neither establishes G31-credit necessity nor shows that
  ordinary credit can replace it.
- G39 update: the actor information, recurrence and training-parameterization
  reductions are now settled inside the continuous-roster P0 family. Both G39
  arms still use identical G31 realized-future-tail targets and
  direction-balanced updates, so G39 supplies no credit-comparator evidence.
  A representation-, information-, source- and exposure-matched ordinary-credit
  reduction is now eligible as the next local separating question. Any pass or
  failure must remain local to its frozen source and cannot rewrite G31's
  accepted G17/G18 evidence.
- G40 update: after one shared accepted native-six fast anchor, G31's retained
  immediate/realized-successor decomposition, shared two-output baselines and
  direction-balanced actor-gradient package reaches the complete access
  contract, while the matched TEAM_GAE1 branch confidently fails and the
  G31-minus-TEAM_GAE1 pooled and capacity-specific lower confidence bounds all
  exceed 0.05. The supported unit is the complete package, not future-return
  information alone; standalone slow-critic and component necessity remain
  open, and no universal temporal-credit or UAV claim follows.

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
- UAV correction: temporary-service-loss G1 fails both constructive feasibility
  and load-bearing separation with zero learned training. It is a benchmark
  failure, not an algorithm failure, and cannot be rescued by lower-precedence
  learner diagnostics.

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

## G41 update (mechanically recorded from External Pro)

- The standalone centralized slow critic is not part of the load-bearing
  post-anchor G31 actor-credit package. Its parameters, return loss, optimizer
  and value output factorize from the actor and shared immediate/successor
  baseline updates and are exactly removable.
- The retained package still uses a shared two-output baseline module with
  true-current-state inputs. G41 is not a centralized-information reduction.
- The remaining component-attribution question is limited to realized-successor
  targeting, immediate/successor decomposition, shared-baseline conditioning,
  per-channel normalization and direction balancing. No status change is made
  to C-REC, C-BASE, C-COORD or C-BENCH.
