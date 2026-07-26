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

- Status: supported and retained at the G36 boundary as a usable
  actual-history-sensor-substituted, configured-capacity,
  bounded-random-process continuous dynamic-roster test version for the
  registered 48-step capacity-6/8/12 toy family. G37 does not extend this
  accepted boundary.
- Claim: a capacity-shape-independent no-carry actor trained only at capacity 8
  remains usable at configured capacities 6, 8 and 12 across the fixed G32
  process and bounded G34-P0 random process. For the exact formal G35 CS final
  checkpoints, the actor's actual true-time, lifecycle-age and previous-action
  sensor bundle may be replaced by the frozen G36 active-count-conditioned,
  internally coherent source-valid donor generator.
- Retained actual actor information: capability, anonymous priority, current
  load and target mix, raw log1p(active_count), active mask and active-fraction
  autoregressive prefix.
- Retained surrogate interface: the four actor coordinates for age, two
  previous actions and time remain present. The accepted deployment boundary
  populates them through the exact coherent G36 donor law; this is sensor
  substitution rather than ten-to-six-dimensional architectural deletion.
- Formal immediate/delayed evidence: G31 passes the paired G17/G18 utility,
  spike-allocation, rotation, learned-gain and fresh-seed stability gates.
- Formal configured-capacity evidence: G32 supports strict-loadable
  capacity-6/8/12 deployment and exact common-active padding invariance.
- Formal bounded-process evidence: G34 supports zero-training transport from the
  fixed 12/24/36 process to its registered one-each-of-L/R/J/T random process.
- Formal current-state evidence: G35 freshly trains matched REC and CS arms.
  Both access; pooled REC-minus-CS CI95 is
  [-0.0173505, -0.0081213, 0.0007130], and every capacity-specific UCB is at
  most 0.0054082 against the 0.05 margin.
- Formal actual-history substitution evidence: G36 replaces actor time, age and
  previous-action fields with an independent coherent donor bundle. All
  fixed/random capacity-6/8/12 access gates pass. Primary
  registered-minus-substitution CI95 is
  [-0.0024790, 0.0001048, 0.0035749], and the largest component UCB is
  0.0075287.
- Formal coherence evidence: G37 independently samples and permutes each donor
  column while preserving every column's complete active-count-conditioned
  empirical marginal. Its primary joint-minus-factorized CI95 is
  [0.0063906, 0.0215989, 0.0515355]. This supports a directional factorization
  cost and rejects exact zero average effect on the frozen primary estimand, but
  neither noninferiority nor >0.05 material loss closes. Capacity-8/12 fixed
  and random deterministic access LCBs miss 0.90, while no confident-access-
  failure predicate fires. The terminal branch is
  MIXED_UNDERPOWERED_HISTORY_PROXY_COHERENCE_G37.
- Accepted deployment boundary: retain the coherent G36 donor generator.
  The G37 factorized generator is neither accepted nor confidently rejected.
- Retired alternatives: within the registered family, usable deployment does
  not require capacity-shaped learned parameters, capacity-specific retraining,
  checkpoint adapters, the exact fixed 12/24/36 schedule, atomic R+J, learned
  per-lifecycle actor carry, or acquisition of the target episode's actual
  time/age/previous-action bundle. G37 additionally retires only the exact
  zero-average-effect point null for its primary joint-minus-factorized
  estimand.
- Lifecycle boundary: active masks, likelihood ownership, environment lifecycle
  state, fresh initialization, temporary leave/rejoin, terminal deletion and
  survivor continuity remain part of the runtime contract.
- Scope: H=48; configured capacity is fixed within a trajectory and belongs to
  6/8/12; G34-P0 contains one each of L/R/J/T and three legal event orders; G36
  and G37 use their exact frozen donor distributions.
- Strongest remaining explanations: G37 may expose generic multivariate
  distribution-shift sensitivity or specialization of checkpoints trained on
  coherent inputs. Whether a freshly trained six-coordinate actor can delete
  the entire surrogate interface remains open.
- Critic and credit boundary: the critic retains true time, and the checkpoints
  retain G31 training provenance. G37 performs zero training and supplies no
  credit-comparator evidence.
- UAV boundary: temporary-service-loss G1 and charge-rotation G2 remain source
  non-identifiable. G33 and all derivatives remain abandoned by user
  instruction.
- Exclusions: arbitrary capacity/process/horizon, arbitrary filler robustness,
  architectural coordinate deletion, globally memoryless control, UAV
  usability, asynchronous skill lifetime, intrinsic-reward advantage,
  complete-algorithm superiority and G31-credit redundancy remain unsupported.

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
  sources, while learned actor carry is rejected as load-bearing in G35-P0 and
  target-coherent actor history sensors are replaceable for the exact G35 CS
  checkpoints under the frozen G36 donor law.
- Memory-source claim: a matched recurrent MARL controller can represent useful
  persistence without explicit event-held commitment when task-relevant
  information is absent from the current observation.
- Continuous-roster carry result: G35 compares parameter-identical REC and CS
  arms under identical current information, G31 credit, source, interactions
  and optimizer exposure. Both access; every REC-minus-CS UCB is at most
  0.0054082 against the 0.05 margin.
- Continuous-roster sensor result: G36 replaces the exact CS checkpoints'
  actual time, age and previous-action bundle with a target-history-independent,
  source-valid donor bundle. All access gates pass and the primary
  registered-minus-substitution UCB is 0.0035749.
- Smallest retired units: learned cross-step actor carry is not required or
  materially advantageous in G35-P0; the target episode's actual coherent
  history bundle is not required or materially advantageous for those exact
  CS checkpoints under G36-P0.
- Retained distinction: G36 preserves four history-shaped model coordinates, a
  source-valid donor generator, active masks, lifecycle ownership and the
  centralized critic. It does not establish that the task or all policy classes
  are memoryless.
- Reactivation condition: an identified source with task-relevant sequential
  information absent from current observations, followed by a matched material
  recurrent advantage. More seeds, budget or threshold changes on G35/G36-P0
  are not reactivation evidence.
- G37 update: the mixed factorization result does not reopen G35's rejection of
  learned actor carry or G36's rejection of actual target-history acquisition.
  Its positive primary contrast concerns the distribution of four execution-time
  nuisance coordinates for exact frozen CS checkpoints; it is not recurrence
  evidence. Cross-column donor coherence remains unresolved, and fresh
  six-coordinate retraining is the relevant architectural discriminator.

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

- Status: supported for the registered G17/G18 paired toy family; still open
  for UAV transport and unrelated source families.
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
