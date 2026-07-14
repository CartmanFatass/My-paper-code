# HA-CTSE Experiment Dashboard

Updated: 2026-07-14

Purpose: compact factual state for current experiments and standing evidence.
The controller records a meaningful launch/result transition here before acting;
completed detail stays in frozen designs, raw run artifacts, or
`memory/LTM/EXPERIMENT_ARCHIVE.md`.

## Protocol

Required dashboard columns:

```text
ID | Status | Stage | Location | Next Read | Key Evidence | Decision
```

Status vocabulary: `planned`, `launch-ready`, `running`, `completed`,
`stopped`, `failed`, `invalid`, `superseded`, `blocked`,
`standing-reference`.

Standing references are fixed comparison data. Do not rerun the HMASD baseline
or R25 arm0/arm2 unless a new design proves them incomparable and the user
explicitly approves the exception.

## Current Dashboard

| ID | Status | Stage | Location | Next Read | Key Evidence | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| EXP-20260714-r33-irsc-gate | completed — valid `FAIL_M1_RETIRE_R33_IRSC` | hierarchy-L2 mechanism-matched intervention/composition gate | local CUDA; `logs/r33_irsc_gate_20260714_214411`; implementation commit `465ee3c` | none | M0 PASS; heldout expected alignment gain `0.001955` and top-2 mass gain `0.001250`; coverage `427/429`, nonredundant ratio `0.984925`; R30 safety PASS | Permanently retire direct intervention-scored roster-complementarity selection; obtain failure review before one structurally different edge. |
| EXP-20260714-r32-ifepg-paired-gate | completed — valid `FAIL_M1_RETIRE_R32_IFEPG` | hierarchy-L1 intervention-to-effect creation and natural-transport gate | local CUDA; `logs/r32_ifepg_paired_gate_20260714_193304`; commit `ddbdab9` | none | M0 PASS; causal ratio `1.01554`, gain `0.02875`; between ratio `1.02997`; coverage ratio `1.01282` | Retire direct IFEPG without tuning or expansion; seek one structurally different post-R32 causal edge. |
| EXP-20260714-r31-cfei-reward-off-gate | completed — valid `FAIL`; R31 retired | hierarchy-L1 reward-off natural/forced causal gate | local CUDA; `logs/r31_cfei_reward_off_gate_20260714_181038`; commit `a7b985b` | none | M1 natural `0.487866`, but direct forced-skill M2 ratio `0.889613`; no gate checkpoint written | Retire R31-CFEI and do not launch the 160K reward pair or retune this target. |
| EXP-20260714-r30-fixed-clock-paired-320k | stopped — superseded before completion | hierarchy-L2 reward-pure temporal-controller mechanism gate | local CUDA; `logs/r30_fixed_clock_paired_320k_20260714_115559`; commit `b670eb6` | none | legacy arm completed; treatment retry was stopped when the user selected the faster Alice--Bob mechanism screen | Preserve the incomplete logs; no M1-M4 scientific outcome exists. |
| EXP-20260714-r29-t10-paired-320k | completed — `PRELIMINARY_FAIL`; online family retired | preliminary hierarchy-L2 mechanism-matched reward comparator | local CUDA; `logs/r29_t10_paired_320k_20260714_010026` | none | implementation valid; R26 probe `PASS` versus reward `MIXED`; paired score CI crosses zero; task reward degraded `31.56%`; GPT-5.6 Pro verdict `RETIRE` | Keep R29 diagnostic-only. Do not promote, retune, or expand seeds; move to the reward-off stochastic realized-effect edge. |
| EXP-20260713-r29-g0-counterfactual-action-information | completed — `PASS_COUNTERFACTUAL_ACTION_INFORMATION_TARGET` | hierarchy-L1 reward-off target gate | local CUDA; `logs/r29_action_information_20260713_230631` | none | 3/3 checkpoints PASS; active means `0.017050`/`0.017990`/`0.019208`; inactive max `5.96e-8` | Accept the support-native target only. Next test is a direct mechanism-matched reward comparator, not a separate smoke. |
| EXP-20260713-r28-forced-execution-support-transport | completed — `FAIL_STOCHASTIC_SUPPORT_TRANSPORT` | reward-off matched-domain causal diagnostic | local CUDA; `logs/r28_support_transport_20260713_222807` | none | 1,024 paired rows/mode; deterministic OOD `0.068359`, stochastic OOD `0.823242`; 64 rows/cell | Random action execution alone breaks frozen support. Retire the forced-deterministic scorer family from online reward use. |
| EXP-20260713-r28-g1-causal-skill-forcing-reward | blocked — `BLOCKED_SUPPORT_OOD`; formal experiment not run | prelaunch engineering for promotion stage 3; planned formal comparator was baseline hierarchy L2 | local smokes `logs/r28_g1_engineering_smoke_20260713_212008` and `logs/r28_g1_engineering_smoke_20260713_213746`; no formal run root | none; cross-round failure review complete | same-config one-update OOD `0.950617`/`0.9375`; support kill in both; zero R28 reward applied; no mapping defect found | Retire the frozen G1 launch package. Do not refit/relax/repeat or infer reward efficacy; next action is a reward-off matched-domain transport diagnostic. |
| EXP-20260713-r28-g0-action-process-target-calibration | completed — accepted `PASS_TARGET_NULLS` 2026-07-13 | diagnostic-null calibration before any level-3 reward | cloud RTX 4090 CUDA; run `logs/r28_g0_action_process_target_20260713_175600`; commit `3eb22d5` | none; preserve scorer as frozen input to later review | final and update30 PASS; update25 FAIL only on train-test gap; validated scorer `r28_g0_scorer_final.pt`; zero env steps/policy updates | Accept the offline target/null gate only. This freezes the final scorer and permits focused G1 package implementation review; it does **not** authorize reward implementation launch or any team/cooperation claim. |
| EXP-20260712-r27-g2-forced-z-trajectory-effect | completed — accepted `PASS_BEHAVIOR_EFFECT` 2026-07-13 | level-2 reward-off forced-`z_i` trajectory/effect intervention | cloud RTX 4090 CUDA; run `r27_g2_overnight_20260713_095408`; commit `6c06cde` | none; preserve beside R26 natural negative | 192/192 `OK` shards; aggregate validation `valid=true`, `scientific_status=PASS`; A/B1/B2/B3/C PASS at update25/update30/final | Accept forced persistent conditional behavior and local effect through native H40 only. Record `FORCED_CAUSAL_CAPACITY_WITH_OBSERVATIONAL_NEGATIVE`; do not infer natural selection, reward usefulness, cooperation, task gain, or async-lifetime benefit. |
| EXP-20260711-r27-g1-low-actor-capacity-autopsy | completed — accepted 2026-07-12 | reward-off immediate-capacity autopsy | cloud CUDA; 64 reset groups; R25 arm0 update25/update30/final | none | `dist/r27_g1_capacity_autopsy_cloud64_20260712_151313_extracted/`; result read under `logs/r27_g1_result_read_20260712/` | `STATIC_USED_OBSERVATIONAL_MISS`: immediate `z_i`-conditioned action-distribution sensitivity exists; persistence/effect were not established by this gate. |
| EXP-20260711-r26-g1a-individual-skill-screening | completed — accepted natural observational negative 2026-07-12 | reward-off natural behavior-window screen | local CUDA; six frozen R25 checkpoints | none | `logs/r26_g1a_screening_20260711_105522/` | Primary arm0 family FAIL: final FAIL and update25/update30 MIXED. Arm2 is contextual only. Preserve this result unchanged beside R27 forced evidence. |
| EXP-20260710-r25-qa-verification-1m | standing-reference | 1M HA-CTSE verification | cloud CUDA, 64 env, arm0/arm2 | none | `dist/logs_cloud_r25_qa_verification_1m/`; `gate_read_r25_seed1.md` | arm0 outperformed q_A arm2 late; q_A reward remains default-off. Single-seed parity remains open; do not rerun these arms. |
| EXP-20260709-r24-frozen-qd-null-probes | completed — accepted FAIL 2026-07-09 | frozen `q_d` diagnostic-null probes | cloud archive plus local analysis | none | `dist/logs_cloud_r24_frozen_qd_overnight_20260709_005624/` | Under tested policies/setup, 3/4 collapsed. Old `q_d/q_D` reward line remains blocked; no target/coefficient sweep. |
| REF-20260617-hmasd-baseline-s7s1-seed1 | standing-reference | HMASD S7-S1 reference | local 32 env; stopped cleanly at 2.112M/3.2M steps | none | `logs/hmasd_baseline_read_20260709/metric_extract.md` | Coverage first reached 0.7 at 480k and 0.9 at 800k; late mean 0.9639. Reference-only because env/update exposure differs; do not rerun. |

## Current Gate Detail

### EXP-20260714-r33-irsc-gate

- Causal edge and upstream authorization: complete-roster intervention at a
  natural R30 check should identify stable non-additive role swaps; an exact
  update of the R30 joint skill distribution should select those pairs and
  transport them to broader, nonredundant natural visitation. R32 established
  that direct individual-effect maximization makes only a small forced shift
  and does not transport. GPT-5.6 Pro confirmed that valid failure and selected
  team composition as the one structurally different next level.
- Estimand correction: for every replica and agent, double-center the complete
  `4 x 4` roster-effect table over both skill axes. From the residual agent
  contrasts for `(a,b)` and `(b,a)`, form the antisymmetric role-swap component
  `h` and symmetric component `k`. The signed pair score is
  `0.25 * (<h1,h2> - <k1,k2>)`. It is zero for additive independent-skill
  effects and one-sided orientation effects, and positive only for a stable
  non-additive sign reversal. This modifies the external raw score while
  retaining its fixed budget and standardized thresholds.
- Source and split: both arms start from the same frozen adaptive-R30
  Alice--Bob checkpoint used by R32,
  `logs/r30_alice_bob_paired_64k_20260714_163908/runs/adaptive_keep_set/seed30031/standalone_process_core_final.pt`.
  Seed `33031` collects 24 stochastic 80-step episodes, exactly 192 natural
  pre-check contexts and 1,920 shared primitive steps. The first 16 episodes
  provide 128 train contexts; the last eight provide 64 heldout contexts.
- Shared intervention table: enumerate all 16 final rosters at every context.
  Each branch restores the environment and recurrent snapshot, forces the
  roster for `W=k0=10`, and runs the frozen low policy. Replica 0/1 use
  independent random streams; all 16 rosters within one context/replica use
  common random numbers. Train exposure is
  `128 x 16 x 2 x 10 = 40,960` shared steps; heldout exposure is
  `64 x 16 x 2 x 10 = 20,480` shared steps. Position-only per-agent effects are
  endpoint displacement plus late-half mean displacement, shape `[2,4]`.
- Comparator and optimization: `real_complementarity` uses the true six
  unordered-pair scores. `pair_sham` uses the fixed source-index permutation
  `[5,4,3,2,1,0]`, corresponding to
  `01<->23, 02<->13, 03<->12`. Every mapped pair shares no skill with its
  source. It preserves each context's 16-score multiset and changes only pair
  attribution; it does not claim equal parameter-gradient norm. Scores use
  population standard deviation plus `1e-8`; a zero-variance context therefore
  contributes an all-zero target. Both arms make
  eight Adam updates (`lr=3e-4`), 16 distinct contexts per update, one epoch,
  gradient clip `0.5`. All 128 train contexts are used exactly once.
  Teacher-forced probabilities over all 16 final rosters drive the exact loss
  `-mean_c sum_r pi(r|c) stopgrad(A_c(r))`. Only
  `FixedClockAREditPolicy.skill_head` may receive gradient.
- Total exposure and uncertainty: natural transport is 64 paired stochastic
  episodes per arm, 5,120 steps per arm. Total including the shared source and
  intervention table is exactly 73,600 environment steps. Confidence
  intervals use 10,000 bootstrap draws with seed `40033031`; M1 clusters by
  heldout source episode and M2 by paired natural reset. Expected local-CUDA
  wall clock is 1--3 hours.
- M0 implementation validity: exact counts `192/128/64`; every context has
  `16 x 2` branches of exactly 10 steps; replica independence and within-replica
  roster CRN hold; maximum enumerated probability-sum error `<=1e-6`; pre-update
  natural token teacher-forcing error `<=1e-5`; paired initial parameters are
  equal; maximum sorted true/sham score-multiset difference `<=1e-8`; each arm
  makes exactly eight finite optimizer calls with finite loss/gradient values;
  gradients are confined to `high.skill_head`; all non-head parameter drift
  `<=1e-8`; stored-prefix stochastic KEEP probabilities drift `<=1e-8`; and
  task reward has zero objective/gradient reads with no low, critic, posterior,
  or normal-high-PPO update. Head gradient/drift is recorded but has no
  unconditional lower bound: a zero mathematical causal gradient is valid M1
  failure evidence, not an implementation defect.
- M1 heldout causal alignment: with true standardized roster scores,
  `mean[V(real)-V(sham)] >=0.20` and its source-episode-cluster 95% CI lower
  bound `>0`. For the two highest-scoring unordered pairs in each context,
  with lexicographic order breaking exact ties, the two-orientation
  probability-mass gain must be `>=0.10` with CI lower bound `>0`.
- M2 natural transport: 625-cell joint-position union coverage requires
  `coverage_real/coverage_sham >=1.10` and the mean paired-reset
  per-episode-coverage difference CI lower bound `>0`. Per episode,
  `D=|A1 symmetric_difference A2|/25` requires
  `mean(D_real)/mean(D_sham) >=1.15` and paired-reset difference CI lower
  bound `>0`. Button, target, contact, coordination, and external reward are
  diagnostics only.
- M3 R30 safety on the real arm: normal-check full-sync SET rate `<=0.50`;
  conditional SET-skill entropy divided by `log(4)` `>=0.80`; minimum SET-skill
  share `>=0.05`; and
  `min(P(T>4*k0), P(T<=4*k0)) >=0.05`.
- Outcome branches: any M0 miss -> `INVALID_R33_IMPLEMENTATION` and repair only
  the concrete implementation defect. Valid M1 miss ->
  `FAIL_M1_RETIRE_R33_IRSC` and permanently retire direct
  intervention-scored roster-complementarity selection. M1 pass/M2 miss ->
  `FAIL_M2_COUNTERFACTUAL_ONLY` and retire counterfactual-only roster fitting.
  M1/M2 pass/M3 miss -> `FAIL_M3_R30_COLLAPSE` and retire the route as
  synchronous/skill-supply/lifetime collapse. All gates pass ->
  `PASS_R33_IRSC`, authorizing only preparation of a sparse-source,
  mechanism-matched `real_complementarity` versus `pair_sham` comparison.
  There is no UNDERPOWERED, automatic rerun, seed expansion, or threshold
  revision branch.
- Prohibited: low actor/critic/action log standard deviation, KEEP head, high
  shared trunk/value, OPT/bridge, posteriors, R29/R31/R32 objectives, transition
  classifier, sampled team latent, `q_d/q_D`, team reward/classifier, task
  reward, shaping, normal high PPO, temperature/update/budget/score clipping
  changes, and claims about task improvement, cooperation, HMASD parity, or S7
  transfer.
- Status source: the single decision artifact is
  `logs/r33_irsc_gate_20260714_214411/result/r33_irsc_gate.json`.
- Result: valid `FAIL_M1_RETIRE_R33_IRSC`. Every M0 check passed. Natural
  high-token replay error was zero, maximum 16-roster probability-sum error was
  `2.38e-7`, and true/sham score-multiset error was `6.66e-16`. Both arms made
  eight finite head-only updates; selected-head relative drift was
  `0.027634` real and `0.026423` sham, with zero non-head drift/gradient and
  zero forbidden update.
- M1: real-minus-sham heldout exact expected-score gain was positive but only
  `0.001955` (source-episode cluster CI
  `[0.000744,0.003105]`), versus `0.20`. Correct-top-two-pair probability-mass
  gain was `0.001250` (CI `[0.000520,0.001908]`), versus `0.10`. The high head
  could follow the residualized complementarity table only at a negligible
  effect size.
- M2: natural joint-position union coverage was `427` real versus `429` sham,
  ratio `0.995338`, with paired-reset CI `[-0.000300,0]`. Role-free
  nonredundant coverage was `0.367500` versus `0.373125`, ratio `0.984925`,
  CI `[-0.021875,0.005000]`. There was no natural transport.
- M3 passed independently: real full-sync SET `0.185268`, SET-skill entropy
  `0.997333`, minimum skill share `0.216000`, and lifetime breadth
  `0.081841`. Failure is not controller, skill-supply, or lifetime collapse.
- Decision: enter the registered M1 branch. Permanently retire direct
  intervention-scored roster-complementarity selection and do not rescue it
  with temperature, more updates, score clipping, another pair permutation,
  new team latent, `q_D`, or team reward. No normal-trainer integration, seed
  expansion, or repeat is authorized.

### EXP-20260714-r32-ifepg-paired-gate

- Causal edge and upstream authorization: randomized focal-skill intervention
  at a natural R30 decision context should create noise-corrected persistent
  position effects through a skill-FiLM-only policy gradient and transport them
  to broader natural joint-state visitation. R31's direct M2 failure and the
  archived GPT-5.6 Pro `VALID FAIL / R32-IFEPG` review authorize this one paired
  Alice--Bob mechanism gate only.
- Source and context banks: both arms start from
  `logs/r30_alice_bob_paired_64k_20260714_163908/runs/adaptive_keep_set/seed30031/standalone_process_core_final.pt`
  and the same immutable natural-R30 snapshots under the current collection-only
  sparse environment. Paired seed `32031` collects 256 source contexts and 128
  disjoint heldout contexts, balanced across the two focal agents. The fixed
  collection schedule is 24 stochastic 80-step episodes, or 1,920 shared
  primitive environment steps and exactly 384 focal-agent contexts; no update
  occurs while building either bank.
- Comparator and nulls: `probe_only` and `real_update` use the same context
  order and branch-seed schedule. Both calculate the same signed eight-dimensional
  position-effect U-statistic; probe performs no optimizer step, while real
  updates only `low.actor_film`. Two independent within-arm replicas estimate
  same-skill execution noise; the paired probe arm is the update null, and
  paired natural reset coverage is the transport null. R31 posteriors and
  environment/task reward do not enter the objective.
- Training contract: 20 updates x 32 contexts x 4 skills x 2 independent
  replicas x `W=10` gives exactly 5,120 branch windows and 51,200 shadow steps
  per arm. Contexts are reused only by the fixed seed-`32031` schedule, with no
  repeats inside an update. Each context score is the mean of the six cross-skill
  replica dot products divided by effect dimension 8; it remains signed. A
  leave-one-context standardized advantage drives one PPO-clipped epoch
  (`clip=0.10`, gradient clip `0.5`) per update. The real arm therefore has
  exactly 20 FiLM optimizer steps and probe has zero. The external review did
  not specify auxiliary learning rate, so the gate minimally reuses the low
  actor rate `3e-4` and freezes it in this contract.
- Evaluation exposure: heldout intervention evaluation is 128 contexts x 4
  skills x 2 cross-skill-common-random-number replicas x 10 steps = 1,024
  windows and 10,240 steps per arm. Natural transport uses 64 paired stochastic
  resets x 80 steps = 5,120 steps per arm. Thus each arm has exactly 66,560
  post-bank shadow/natural steps; the pair has 133,120, plus the one-time shared
  1,920-step bank collection. All confidence intervals use 10,000 paired
  context/reset cluster-bootstrap draws from a seed derived from `32031`.
  Expected local-CUDA wall clock is 1--3 hours.
- M0 implementation validity: replay-versus-stored focal per-step log-probability
  maximum error `<=1e-5`; all context/window/skill/replica counts above are
  exact; probe FiLM drift `<=1e-8`; real FiLM relative L2 drift is finite and
  `>1e-6`; every real non-FiLM parameter drift `<=1e-8`; and no optimizer
  update reaches the low critic, high policy, OPT/bridge, or any posterior.
  Neither task nor environment reward enters an update. Any miss is `INVALID`
  and permits repair of that path only.
- M1 direct causal SNR: on 128 heldout contexts, real median between/within
  ratio is `>=1.50` with 95% context-cluster-bootstrap lower bound `>1.0`;
  median paired-context `(real - probe)` is `>=0.40` with lower bound `>0`;
  and every skill's pooled ratio is `>1.0`.
- M2 stochastic-noise null: mean between-skill effect satisfies
  `mean(B_real)/mean(B_probe) >=1.50`, with paired-context difference 95% lower
  bound `>0`, while same-skill variability satisfies
  `mean(W_real)/mean(W_probe) <=1.25`.
- M3 natural transport and R30 safety: fixed 625-cell joint-position coverage
  satisfies `coverage_real/coverage_probe >=1.10`, with paired-reset coverage
  difference 95% lower bound `>0`; natural `full_sync_SET_rate <=0.50`,
  `H(Z|SET)/log(4) >=0.80`, and
  `min(P(T>4*k0), P(T<=4*k0)) >=0.05`. Collection, button/target contact, and
  sparse task reward are diagnostic only.
- Outcome branches: M0 miss -> `INVALID`, repair only and rerun this contract.
  Valid M1 miss -> retire direct interventional FiLM-effect policy gradient;
  valid M2 miss -> retire it as stochastic/noise exploitation; valid M3 miss ->
  retire it as forced-only capacity, failed natural transport, or lifetime
  collapse. M0 plus all M1--M3 thresholds -> `PASS`, authorizing only a later
  sparse-source R30 integration with one FiLM-only IFEPG auxiliary step. There
  is no `UNDERPOWERED` branch and no automatic seed or budget expansion.
- Prohibited: actor base/RNN/action head/log-std, critic, high controller,
  OPT/bridge, posterior, task-PPO, GAE, entropy, reward, or environment updates;
  shaping; normal-trainer R32 integration before PASS; coefficient, effect,
  window, replica, threshold, arm, or seed changes; and conclusions about task
  gain, cooperation, semantic roles, lifetime superiority, HMASD parity, or S7
  transfer.
- Operational transition: the first root ending `192508` completed the probe
  shadow collection, then failed at the first real backward because cuDNN does
  not permit RNN backward while the GRU module is in eval mode. No real
  optimizer step occurred. The scoped repair places only the focal actor RNN
  in training mode for auxiliary backward while its parameters remain frozen,
  then restores eval before heldout/natural evaluation. The replacement keeps
  every scientific parameter, seed, branch schedule, and threshold unchanged.
- Status source: the single decision artifact is
  `logs/r32_ifepg_paired_gate_20260714_193304/result/r32_ifepg_pair.json`.
- Result: valid `FAIL_M1_RETIRE_R32_IFEPG`. M0 passed every check: both arms
  collected exactly 5,120 train branches and 1,024 heldout branches, maximum
  replay error was `4.77e-6`, probe parameters were static, real FiLM changed,
  and non-FiLM drift/gradient escape and all forbidden updates were zero.
- M1: real heldout median between/within ratio was `1.015540` (95% CI
  `[0.877865, 1.207808]`) versus the `1.50`/lower-`>1` gate. Paired median gain
  was positive but only `0.028746` (CI `[0.024775, 0.033320]`) versus `0.40`.
  Skills 0/1 remained below the required pooled ratio (`0.658951`/`0.998809`),
  while skills 2/3 were `1.374737`/`2.150302`.
- M2: between-skill mean increased only `1.029965x` versus the required
  `1.50x`; its paired gain CI was positive, while within-skill noise stayed
  flat at `0.998550x`. The update produced a small genuine separation shift,
  not the required effect-creation magnitude and not noise inflation.
- M3: natural union coverage was 553 versus 546 cells (`1.012821x`, required
  `1.10x`) and the paired-reset gain CI `[-0.000125, 0.000725]` crossed zero.
  R30 safety itself remained healthy: real full-sync SET `0.158482`, switch
  entropy `0.995952`, and lifetime breadth `0.110169`.
- Decision: the precommitted M1 branch retires direct interventional
  FiLM-effect policy gradient. Do not change learning rate, update count,
  window, replicas, effect, threshold, or seed, and do not integrate R32 into
  normal training. The next review must choose one structurally different
  causal edge rather than rescue this line.

### EXP-20260714-r31-cfei-reward-off-gate

- Causal edge and authorization: in natural stochastic adaptive-R30 checks,
  changing focal persistent skill should create a task-agnostic joint-position
  effect beyond context recovery and same-skill stochastic variability. GPT-5.6
  Pro accepted R31 and authorized this reward-off gate only.
- Source/nulls: frozen Alice--Bob adaptive-R30 final checkpoint, seed `31031`,
  sparse collection reward, `W=k0=10`; context-only posterior and matched
  context shuffle are observational nulls, while two common-random-number
  stochastic replicas per forced skill estimate execution noise. Forced rows
  never train the posterior and no policy optimizer runs.
- Exposure: 64 reset groups x 80 steps yield up to 1,024 natural agent-windows;
  48 groups train the posterior and 16 are held out. The audit uses 128 heldout
  decision contexts x 4 focal skills x 2 replicas x 10 steps = 10,240 forced
  primitive steps. Cluster bootstrap uses 10,000 draws. Expected wall clock is
  under 30 minutes on local CUDA.
- Metrics/thresholds: M1 requires heldout mean `>=0.02` nats, CI lower `>0`,
  every skill mean `>=0.005`, and at least 64 heldout rows per skill. M2 requires
  median between/within effect ratio `>=1.5`, CI lower `>1`, every skill pooled
  ratio `>=1`. The original contract also imposed a near-zero matched-shuffle
  threshold; GPT-5.6 Pro later established that null was mathematically invalid.
- Outcome branches: all valid thresholds PASS -> only the matched 160K
  `probe_only`/`real_reward` pair; nonpositive M1 or causal ratio `<=1` -> FAIL
  and retire R31; threshold-directed point estimates with insufficient rows/CI
  -> UNDERPOWERED and append one identical 64-reset batch. The obsolete shuffle
  branch is not reused.
- Prohibited: environment shaping, online reward, policy updates, forced-row
  posterior fitting, fixed teammate action tapes, coefficient/target/null
  changes, extra arms/seeds, or claims about cooperation/task efficacy.
- Status source: `logs/r31_cfei_reward_off_gate_20260714_181038/result/r31_causal_effect_gate.json`.
- Result: `FAIL`. Natural heldout effect information was `0.487866` nats
  (cluster CI `[0.319984, 0.638954]`), but the forced-skill between/within
  median ratio was `0.889613` (CI `[0.763227, 1.078315]`), pooled ratios for
  skills 0/1 were `0.551521`/`0.841928`, and matched shuffle was `-2.068` nats.
  The posterior learned natural association but the causal intervention did not
  exceed stochastic execution noise. The shuffle value is retained only as a
  disruption diagnostic and is not an independent failure reason.
- Failure review: execution and comparator counts were valid; posterior
  capacity was adequate; the skill-3 heldout count of 44 is non-decisive because
  direct M2 already fired. Reusable negative and the single next causal edge are in
  `memory/LTM/R29_R31_EFFECT_REWARD_FAILURE_REVIEW_20260714.md`.
- Decision: no online R31 reward, gate checkpoint, 160K pair, identical-batch
  append, threshold change, or R31 retuning. Seek one intervention-anchored
  effect-creation route before any further reward implementation.

### EXP-20260714-r30-fixed-clock-paired-320k

- Causal edge: removing the active duration action and replacing expired-only
  edits with a fixed `k0=10` all-agent autoregressive `KEEP/SET(skill)` check
  should permit lifetimes beyond the old four-block cap without short-segment
  high-sample bias, while retaining asynchronous edits and switch-skill supply.
- Upstream authorization: GPT-5.6 Pro returned `MODIFY R30`; its four algorithm
  corrections are accepted. The user authorized a local CUDA short run of up
  to 320K transitions per experiment with 16 environments. This is one
  mechanism seed, not parity, long-run efficacy, or a semantic-skill claim.
- Comparator/null: `legacy_duration` and `r30_fixed_clock_ar_edit` both start
  from the registered R25 arm0 1M/update32 checkpoint, seed `30031`, matched
  environment streams, deterministic expected bridge context, the unchanged
  low policy, and raw environment reward only. The legacy arm retains frozen
  duration choices `(1,2,3,4)`; the treatment changes only the temporal high
  controller, critic/buffer grain, and required checkpoint migration.
- Exposure: arms run concurrently on local CUDA with 16 spawned subproc envs,
  S7-S1, six agents, rollout `501`, and +320,000 transitions per arm to
  1,320,000 total steps/update72. The non-check-aligned rollout makes the
  critic-only continuation observable. Each arm receives 40 rollout/high-PPO
  updates, 15,570 recurrent low-actor and 15,570 low-critic minibatch updates
  (`15` epochs), followed by 20 deterministic evaluation episodes. Expected
  wall clock is 5-10 hours.
- Operational transition: the first launch root ending `115241` failed before
  any environment step or optimizer update because the reward-pure legacy arm
  strictly rejected four retired sampled-team residual weights. Commit
  `b670eb6` adds an explicit allowlisted drop of only those weights and resets
  the high optimizer in both arms. The replacement root ending `115559` was
  stopped incomplete on 2026-07-14 when the user selected the faster role-free
  Alice--Bob mechanism screen; it has no M1-M4 outcome.
- M1 implementation gate: every real decision row has exactly six valid edit
  tokens, maximum teacher-forced replay log-probability error is `<=1e-5`, at
  least one continuation row is observed, and all continuation rows have zero
  actor tokens. Any failure is implementation-invalid and permits only repair
  of the failed path under this same contract.
- M2 lifetime breadth: over the final 10 updates, eligible spell events must
  satisfy `min(P(T>4*k0), P(T<=4*k0)) >= 0.05`. Episode-terminal right-censored
  spells are excluded; a short spell is counted when `SET` ends it at or before
  four blocks, and a long spell once when `KEEP` carries it beyond four blocks.
- M3 asynchronous supply: over the final 10 updates, full-synchronous `SET`
  rows are `<=0.50`, empirical `H(Z|SET)/log(4) >=0.80`, and every skill has at
  least `0.05` of switch selections.
- M4 task safety: relative deterministic reward degradation versus legacy is
  `<=0.10`, and absolute worsening of zero-throughput step fraction is
  `<=0.10`.
- Outcome branches: M1 fail -> repair only and resume the same gate; M1 pass
  but M2 or M3 fail -> retire the current R30 formulation without keep entropy,
  semantic reward, or coefficient sweep; M4 fail -> block promotion for task
  safety; all pass -> accept R30 only as the next core temporal controller and
  move to the separate reward-off realized-effect diagnostic.
- Prohibited while open: extra seeds or arms, duration/keep/switch sweeps,
  sampled team intent, intrinsic/team/process/topology reward, edit/switch or
  lifetime payment, metric redesign, and claims of MAT/HAPPO theorem, reduced
  joint action space, HMASD parity, semantic differentiation, task improvement,
  long-run stability, or cross-environment generalization.
- Status sources: `<run-root>/runner_status.txt`, both arms' single
  `metrics/train_updates.csv` and `metrics/eval_episodes.csv`, and
  `<run-root>/result/r30_fixed_clock_pair.json`.

### EXP-20260714-r29-t10-paired-320k

- Causal edge: a detached recurrent terminal-block density ratio added to the
  low reward should make persistent natural skill-conditioned behavior more
  distinguishable than computing the same ratio without reward injection.
- Upstream authorization: R29-G0 established a support-native action signal;
  GPT-5.6 Pro recommended R29-T10; the user authorized one local 320K run per
  arm. This does not authorize a three-seed conclusion.
- Comparator/null: `probe_only` and `real_reward` start from the same R25 arm0
  1M checkpoint and seed `29031`. Both replay every fixed candidate skill over
  the same complete natural lifetime and compute the same final-10-step score;
  only `real_reward` adds the detached clipped scalar to the terminal low reward.
- Exposure: two arms run concurrently on local CUDA, each with 16 subproc envs,
  rollout 500, skill interval 10, lifetimes `(1,2,3,4)`, and +320K environment
  steps. This is 40 policy-update cycles and 15,000 recurrent low-PPO minibatch
  optimizer steps per arm (`15` epochs, `800` sequence chunks, batch `32`).
  Final task evaluation uses 20 deterministic episodes; final natural-process
  evidence uses 64 reset groups and the unchanged R26 analyzer. Expected total
  wall clock is 5-10 hours.
- Preliminary decision metrics: actual-skill replay likelihood error must stay
  `<=2e-5`; complete segments and all four skills must be represented. Over the
  final 10 policy updates, `real_reward - probe_only` R29-T10 mean must be
  `>=0.05` with a positive paired-update bootstrap lower bound and no negative
  per-skill mean difference. R26 transfer requires real PASS while probe is not
  PASS and a `>=0.05` real-minus-probe full-minus-prior accuracy gain.
- Operational note: two launches failed before any optimizer update because
  CUDA GRU replay accumulated `2.6e-3`, then `1.3e-3`, numerical drift when its
  batch shape differed from collection. The scorer now anchors the natural
  column to PPO's stored old likelihood after removing the common tanh Jacobian
  and reports unanchored recurrent drift separately.
- Safety: real normalized skill entropy `>=0.8`, full-rollout intrinsic/env
  mean-absolute ratio `<=0.05`, deterministic task reward degradation `<=10%`
  relative to probe, and zero-throughput step-fraction worsening `<=0.10`.
- Branches: preliminary PASS -> external GPT-5.6 Pro review before deciding on
  the remaining paired seeds; MIXED -> external review of the frozen evidence
  with no retuning; FAIL -> run the research failure review and retire or select
  one externally justified revision; INVALID/crash -> repair only the failed
  operational path and resume the same contract.
- Prohibited while open: coefficient/clip/terminal-window changes, learned
  priors, high-level reward, task-reward changes, extra arms, extra seeds, and
  conclusions about cooperation, task improvement, or exact mutual information.
- Status sources: `<run-root>/runner_status.txt`, each arm's
  `metrics/train_updates.csv` and `metrics/eval_episodes.csv`, final R26 JSON,
  and `<run-root>/result/r29_t10_pair.json`.
- Result: completed `PRELIMINARY_FAIL` on the authorized single seed `29031`;
  `implementation_valid=true`, `r26_transfer_pass=false`,
  `score_pass=false`, and `safety_pass=false`.
- Mechanism evidence: probe-only retained an R26 `PASS` with post-minus-pre
  `0.061090`, full-minus-prior `0.073063`, and label entropy `0.998223`.
  The reward arm was `MIXED`, with post-minus-pre `-0.002817`,
  full-minus-prior `0.014952`, and label entropy `0.997911`. The reward therefore
  did not transfer the accepted natural differentiation signal.
- Paired score evidence: the final-window real-minus-probe mean was `0.031265`
  with bootstrap 95% interval `[-0.005331, 0.064452]`, below the registered
  mean threshold and without a positive lower bound.
- Safety evidence: deterministic task reward was `130.452` for probe versus
  `89.278` for reward, a relative degradation of `0.315623`; backhaul connected
  fraction also fell from `0.7776` to `0.6823`. Healthy label entropy does not
  override the failed task-safety gate.
- Decision: preserve this as a single-seed preliminary negative, not a
  three-seed scientific conclusion. GPT-5.6 Pro returned `RETIRE`; the raw
  response and disposition are under
  `docs/external-review/gpt5_6_pro/20260714_r29_t10_result/`. Retire the online
  same-action density-ratio family, keep R29 diagnostic-only, and move to the
  reward-off stochastic realized-effect edge recorded in
  `memory/LTM/R29_ACTOR_DENSITY_RATIO_FAILURE_REVIEW_20260714.md`.

### EXP-20260713-r29-g0-counterfactual-action-information

- Hypothesis/edge: on natural on-policy observation and rollout-hidden states,
  the skill-conditioned low actor carries a support-native action signal:
  `z_i -> sampled action likelihood relative to the uniform counterfactual-skill
  mixture`. The density ratio uses the same raw action under all candidates, so
  the tanh Jacobian cancels.
- Comparator/baseline: hierarchy-L1 reward-off diagnostic. Active source-skill
  likelihood is paired with a cyclic-label sham and inactive-FiLM identity
  control under identical states and Gaussian noise.
- Sources/exposure: fixed R25 arm0 update25/update30/final checkpoints and their
  64-reset R27 natural snapshots; 8 Monte Carlo samples per row/skill, seed
  `29001`; reset bootstrap 2,000 reps, seed `29002`; local CUDA with three
  checkpoint workers, expected 2-5 minutes; zero environment steps, optimizer
  updates, and reward-applied steps.
- Checkpoint gate: at least 5,000 rows and 48 resets; natural-label normalized
  entropy `>=0.8`; active mean `>=0.01` nats; every skill mean `>=0.005` nats;
  active-minus-sham reset-bootstrap lower bound `>0`; inactive maximum absolute
  reward `<=1e-6`. Family PASS requires final PASS and at least 2/3 checkpoints.
- Result: all three checkpoints PASS. Active means are `0.017050`, `0.017990`,
  and `0.019208` nats; minimum skill means are `0.008170`, `0.013948`, and
  `0.015080`; real-minus-sham lower bounds are `0.043887`, `0.043184`, and
  `0.048487`; inactive maximum absolute reward is `5.96e-8`.
- Branches: PASS -> run one bounded mechanism-matched reward comparator; FAIL -> retire the
  individual action-information target; INVALID -> repair evidence code only;
  UNDERPOWERED -> add snapshot support under the unchanged contract only.
- Fixed while open: source checkpoints/snapshots, rollout hidden state, uniform
  four-skill mixture, cyclic sham, inactive control, common noise, seeds,
  thresholds, zero reward, and zero updates.
- Runner: `scripts/run_r29_action_information_local.ps1`; status source is
  `logs/r29_action_information_20260713_230631/r29_action_information.json`.

### EXP-20260713-r28-forced-execution-support-transport

- Edge/comparator: under the final R25 forced hold, compare deterministic and
  six-agent stochastic environment execution from the same reset/prefix using
  common policy noise; both modes score only their same-forward deterministic
  action means with the frozen G0 support envelope. This is hierarchy-L1,
  reward-off evidence.
- Exposure: final checkpoint only; resets `0..63`, focal agent `reset_id % 6`,
  four labels and four native duration windows per mode; 111,100 environment
  steps, zero optimizer updates and zero reward; local CUDA with four reset
  workers, expected 15-30 minutes.
- Gate: at least 48 paired rows per label-duration cell. Deterministic source
  replication and stochastic transport each require overall and every cell OOD
  `<=0.20`.
- Branches: stochastic PASS -> test forced versus natural renewal under matched
  stochastic execution; stochastic FAIL after deterministic PASS -> retire the
  forced-deterministic scorer family from online reward; deterministic failure
  -> `INVALID` source/evidence repair only; insufficient paired cells -> add
  support only under the unchanged contract; crash -> operational repair.
- Fixed while open: checkpoint, prefix/reset seeds, forced roster, feature
  function, scorer/support, thresholds, common noise, zero reward, and zero
  optimizer updates.
- Result: deterministic overall OOD `0.068359` and cell maximum `0.109375`
  validate source replication. Stochastic overall OOD is `0.823242`; 15/16
  cells exceed `0.20`, and the four action-std residuals average
  `10.60-14.08` sigma. Classification is
  `FAIL_STOCHASTIC_SUPPORT_TRANSPORT`.
- Decision: retire this scorer family from online reward use and return to a
  support-native observational target. No scorer refit, threshold relaxation,
  reward test, or natural-renewal follow-up is authorized by this result.
- Runner: `scripts/run_r28_support_transport_local.ps1`; status source is
  `logs/r28_support_transport_20260713_222807/r28_support_transport.json`.

### EXP-20260713-r28-g1-causal-skill-forcing-reward

- Scientific status: the planned hierarchy-L2 matched three-arm comparator at
  promotion stage 3 was never opened, so R28-G1 has no reward-efficacy result.
- Engineering evidence: seed 28030, CUDA, one environment, +500 steps, and one
  low PPO epoch/update in each exact local smoke. The runs produced 81/80
  structurally eligible rows, OOD `0.950617`/`0.9375`, one support kill each,
  and zero R28 reward-applied steps.
- Diagnosis: G0/G1 feature order, deterministic-action evidence, duration
  indexing, source identity, and support-distance formula match. The second
  run's distance/threshold mean was `94.9766`; all four temporal action-standard-
  deviation residuals were `12.64-20.39` sigma while means/slopes were much
  smaller. This is a genuine forced-to-natural trajectory support mismatch,
  not an `INVALID_MAPPING` repair branch.
- Decision: block and retire this frozen G1 launch package. Preserve the scorer
  and thresholds; do not refit, relax, rerun the same smoke, or launch formal
  training. This does not imply that a support-compatible reward would fail.
- Next causal action: the reward-off matched-domain transport diagnostic in
  `memory/LTM/R26_R27_R28_FAILURE_REVIEW_20260713.md`.
- Frozen unexecuted contract: retained in
  `docs/research/R28_G1_CAUSAL_SKILL_FORCING_REWARD_DESIGN_20260713.md`.
- Status sources: this dashboard and the two local smoke roots above.

## Completed Evidence and Archive Pointers

The completed G0 protocol is frozen in the R28 design and its row points to the
raw run artifacts. R27-G2 and prior completed detail are in
`memory/LTM/EXPERIMENT_ARCHIVE.md`; earlier imported records remain in
`memory/LTM/EXPERIMENT_RECORD_20260707_full_import.md`.
