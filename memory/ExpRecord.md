# HA-CTSE Experiment Dashboard

Updated: 2026-07-16

Purpose: compact factual state for current experiments and standing evidence.
The controller records a meaningful launch/result transition here before acting;
completed detail stays in frozen designs, raw run artifacts, or
`docs/archive/legacy-memory/EXPERIMENT_ARCHIVE.md`.

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
| EXP-20260716-r49-orse-g0 | implementation ready -- launch authorized | architecture-only open-roster interface gate | isolated scripts; contract below; Pro source in R48 external-review entry | full local CPU gate | 16-case dry-run passed M0/M1; permutation/incremental errors `2.98e-8`, replay/padding `0`, prefix support `1.0`, zero complexity violations | Run the unchanged full gate; no inherited skill/lifetime/task/cooperation claim |
| EXP-20260716-r48-sbrs-g0 | completed -- Pro-confirmed valid `VALID_FAIL_R48_SBRS` | hierarchy-L1 reward-off recurrent-boundary abandonment gate | `logs/r48_sbrs_20260716_181833`; implementation `eb6b9e6`; result commit `985ab94`; R48 external-review entry | complete | M0 pass; H10 reset rho LCB `0.98468`, rho-ratio LCB `1.11816`, within UCB `1.01877`; H40 rho-ratio LCB `1.00223`, within UCB `1.00874` | Permanently retire recurrent-boundary line and stop fixed-N skill/lifetime exploration without rescue; only independent R49 architecture gate remains |
| EXP-20260716-r47-nsopm-g0 | completed -- Pro-confirmed valid `VALID_FAIL_R47_NSOPM` | hierarchy-L1 reward-off natural process-mode identifiability | `logs/r47_nsopm_20260716_172711`; implementation `078845b`; result commit `b758d8c` | complete | M0 pass; only eigen-rank 0 beats temporal null; lag-5 fails; H10 support `0.71875`; H10 D crosses zero; H40 skill 0 negative; causal SNR `0.0343/0.1992` | Permanently retire exact view/map/lag/basis/score/reward pair without rescue; proceed only to R48-SBRS-G0 |
| EXP-20260716-r46-hmrv-g0 | completed -- valid `VALID_FAIL_R46_HMRV_SUBSTRATE` | hierarchy-L1 reward-off heterogeneous-maintenance identifiability | `logs/r46_hmrv_64k_20260716_154508`; commits `67cfe72`, `45eb49d`, `cfc0ba4` | completed GPT-5.6 Pro result review | M0/M1/M2 pass; true/sham WMSE `10.6079/10.9186`; learned pooled and both role-stratum sign discordance exactly `0`; direct enumeration oracle discordance near `0.5675` | Retire the exact dynamics/estimand/context/critic/read combination without rescue; interpret as learned sign-transport failure and proceed only to R47-NSOPM-G0 |
| EXP-20260716-r45-sdra-g0 | completed -- valid `VALID_FAIL_R45_SDRA_IDENTIFIABILITY` | hierarchy-L1 reward-off natural-support renewal-credit identifiability | `logs/r45_sdra_160k_20260716_144312` | post-R45 causal-edge review | M0/M2 pass; true/sham WMSE `0.03830/0.37667`; M1 overlap fails; M3 sign discordance `0.000314` | Retire Alice--Bob K50 natural-support renewal credit and this temporal substrate without rescue |
| EXP-20260716-r44-fsnrc-k50 | completed -- valid `VALID_FAIL_R44_FSNRC` | hierarchy-L2 frozen-source renewal timing gate | `logs/r44_fsnrc_320k_20260716_132349` | post-R44 causal-edge review | M0/M1/M2 pass; both win/key0/key1 `0.93/1.00/0.93`; treatment actor drift `0.353245`, but both discordance `0`, full-sync RENEW `1`, min marginal `0` | Permanently retire frozen-source K50 renewal timing route without rescue; select one structurally different edge |
| EXP-20260716-r43-nrc-k50 | completed -- invalid `INVALID_R43_FIXED_ANCHOR_LOST` | hierarchy-L2 reset-censored true-renewal mechanism gate | `logs/r43_nrc_reset_censored_320k_20260716_121756_retry2` | completed GPT-5.6 Pro review | M0 pass; fixed final win/key0/key1 `0.52/0.54/0.81`; source checkpoint cross-eval `0.89/0.93`; two-update source-vs-wrapper parameter diff `0` | Fixed wrapper accepted source-equivalent; keep treatment diagnostic-only and proceed only to R44-FS-NRC |
| EXP-20260716-r42-irr-native-roster-residual | completed -- valid `VALID_FAIL_R42_IRR_SERVICE` | hierarchy-L2 same-checkpoint temporal mechanism gate | `logs/r42_irr_native_roster_residual_320k_20260716_100824` | completed GPT-5.6 Pro validity review | M0/M1 pass; fixed/treatment win `0.98/0.88`; delta CI `[-0.17,-0.03]`; treatment discordance `0.10` | Permanently retire R42; Pro selected modified R43 true renewal, pending clock correction |
| EXP-20260716-r41b-hmasd-alice-bob-full-source | completed -- valid `PASS_R41B_SOURCE_ACCESS` | baseline-L0 exact original-source access reproduction | `logs/r41b_hmasd_full_source_20260716_035300_retry2`; commit `e36f7df` | complete three-round Pro disposition | M0 PASS, replay `0`; final win/key0/key1 `0.89/0.97/0.92`; paired win CI `[0.82975,0.95]` | Positive source anchor established; pure categorical R42 retired as decorative after source audit; proceed to R42-IRR |
| EXP-20260716-r41a-hmasd-alice-bob-local-pilot | completed -- valid `NO_ACCESS_R41A_HMASD_ALICE_BOB_LOCAL_PILOT` | baseline-L0 original-source access pilot | local CUDA; `logs/r41a_hmasd_local_pilot_20260716_030013`; commit `a1ea76b` | completed GPT-5.6 Pro round 1 | M0 PASS with replay `0`; all five paths 14,055 updates; zero/final win `0/0`; paired CI `[0,0]` | Accepted as reduced-exposure no-access; run one exact 32-env full-source seed |
| EXP-20260715-r40-simple-spread-access | completed -- valid `VALID_FAIL_R40_ACCESS` | baseline-L1 public cooperative-access gate | `logs/r40_simple_spread_access_200k_20260715_235500_retry4`; result copied to external-review entry | GPT-5.6 Pro R40/R41 disposition | M0 PASS; MAPPO/random `-52.392238/-52.587268`; paired CI crosses zero; `0/4` blocks pass | Retire this exact substrate without rescue; proceed only to official-source R41 |
| EXP-20260715-r39-native-hmasd-toy-credit | completed -- valid `VALID_FAIL_R39_NATIVE_TOY_CREDIT_ANCHOR` | stage-0 native-HMASD fixed-N credit anchor | `logs/hmasd_original/two_timescale_role_free_actions-r39_native_hmasd_toy/mode-train_cfg-config_r39_native_hmasd_toy_seed-39041_envs-16_rollout-40_k-5_steps-12800_backend-sharded_metrics-light_workers-4x4_mmode-light/20260715_221219`; result owner `result/r39_native_hmasd_toy_credit.json` | post-R39 positive-substrate review | M0 valid; 12,800 steps, 20 outer updates, 60 high optimizer updates, replay max `4.768e-7`, zero low/discriminator updates; match/slow/fast `0.455078/0.464844/0.445313` | Retire this native fixed-N toy credit route under the registered valid-fail branch; no rescue or expansion |
| EXP-20260715-r39-toy-joint-credit-alignment | completed -- valid `PASS_R39_JOINT_CREDIT_ALIGNMENT` | stage-0 sampled-credit alignment diagnostic | `logs/r39_toy_joint_credit_alignment_1920_20260715_194904_retry3`; commit `c6d02e3` | native-HMASD toy design | 32 correct versus 352 incorrect rows; pooled raw block return `4.9010` versus `1.8170`; actor weight `+2.1207` versus `-0.1928`; replay zero | Reward timing and storage are correct. Stop patching standalone shared credit; preserve the small model and move the toy to native HMASD team/agent credit. |
| EXP-20260715-r39-toy-joint-factorization | completed -- valid `PASS_R39_JOINT_FACTORIZATION_CAPACITY` | stage-0 exact joint-policy capacity diagnostic | `logs/r39_toy_joint_factorization_20260715_193034`; commit `fd29e3e` | sampled joint-credit alignment | minimum correct unordered-pair mass `0.999487`, mean `0.999670`, probability-sum error `3.58e-7`, high policy 2,512 parameters | The small policy is expressive and exactly optimizable on the eight registered contexts. Do not enlarge it; localize sampled credit. |
| EXP-20260715-r39-toy-block-credit | completed -- valid `FAIL_R39_TOY_BLOCK_CREDIT` | stage-0 high actor-credit positive control | `logs/r39_toy_block_credit_12k8_20260715_192020`; commit `22a3162` | exact joint-roster factorization diagnostic | M0 PASS; SMDP-GAE and block-return both scored match/slow/fast `0.46875`, gain `0`, with exact replay, high3, and zero intrinsic | Retire actor-advantage source as the immediate cause. Test whether the tiny autoregressive joint policy can learn the four contextual roster mappings under exact supervision. |
| EXP-20260715-r39-toy-high-exposure | completed -- valid `FAIL_R39_TOY_HIGH_EXPOSURE_3` | stage-0 high optimizer-exposure gate | `logs/r39_toy_high_exposure_12k8_20260715_191019`; commit `b805abc` | high actor-objective positive control | M0 PASS; 3 epochs improved match `0.421875 -> 0.46875` (`+0.046875`), below access/effect gates; clip fraction `0`, mean last-epoch KL `6.12e-6` | Retire optimizer underexposure as the immediate cause. Compare SMDP-GAE with diagnostic block-return actor credit on the unchanged tiny model. |
| EXP-20260715-r39-toy-high-credit-diagnostic | completed -- credit directions aligned | stage-0 high-credit localization | `logs/r39_toy_high_credit_diag_1920_20260715_185721`; commit `ef9a34d` | high optimizer-exposure gate | M0 PASS; both arms had nonzero comparable GAE/block gradients and all six skill-head cosines were positive (`0.392-0.594`) | GAE does not extinguish or reverse immediate block credit. Test explicit three-epoch high PPO exposure on the same tiny model. |
| EXP-20260715-r39-toy-direct-state | completed -- valid `FAIL_R39_TOY_HIGH_CREDIT` | stage-0 high-context localization; hierarchy-L2 temporal control | `logs/r39_toy_direct_state_12k8_retry2_20260715_184646`; commit `1200bdf` | actor-only GAE/block-return gradient diagnostic | M0 PASS; direct state and zero team context replay exactly, low has zero parameters/updates, and actor/skill-head policy gradients are nonzero; both arms match `0.421875` | Context compression and a disconnected actor gradient do not explain the failure. Diagnose credit direction versus optimizer exposure on a smaller toy collection; do not enter S7 or enlarge the model. |
| EXP-20260715-r39-toy-fixed-primitives | completed -- valid `FAIL_R39_TOY_HIGH_ACCESS` | stage-0 high-controller positive control; hierarchy-L2 matched control | `logs/r39_toy_fixed_primitives_12k8_retry2_20260715_181752`; commit `19e7f5c` | high context/credit diagnosis | M0 PASS with zero low parameters/updates and zero intrinsic; adaptive/control match both `0.4375`, slow `0.40625`, fast `0.46875` | Failure is upstream of temporal efficacy: diagnose the high context/credit path on the toy; do not enter S7 or enlarge the model. |
| EXP-20260715-r39-toy-native-categorical | completed -- valid `NO_ACCESS_R39_TOY_32` | stage-0 joint-learning access gate; hierarchy-L2 matched control | `logs/r39_toy_native_categorical_12k8_20260715_180156`; commit `cafec51` | fixed-primitive positive control | M0 PASS; low replay `<=1.91e-6`, 16-env GAE, 3 PPO epochs, zero intrinsic; both arms match about `0.446` | Do not interpret temporal efficacy or enlarge the learner. Isolate the high controller with supplied primitives. |
| EXP-20260715-r39a-current-fixed-hmasd-anchor | planned -- package prepared and deferred | baseline-L1 current-interface source-anchor gate | cloud CUDA package; no launch during toy gate | toy result | GPT-5.6 Pro accepted a serial R39A anchor then R39B route; user selected a cheap toy mechanism gate before S7 compute | Preserve the exact package. Launch only after toy PASS; native-HMASD R39B still requires R39A PASS. |
| EXP-20260715-r37-actor-visible-identity-access | completed -- valid `FAIL_R37_ACCESS` | baseline-L0 observation-substrate validity gate | local CUDA; `logs/r37_actor_visible_identity_access_320k_20260715_090205`; commit `67cadc8` | GPT-5.6 Pro replacement-benchmark review | M0 PASS; visible identity caused 10/64 collections and a positive paired effect, but cycle mean `0.01953125` missed the `0.05` floor; M2/M3 PASS | Retire this sparse Alice--Bob algorithm gate; select and validate one replacement benchmark before more algorithm work. |
| EXP-20260715-r38-cts-access | completed -- valid `FAIL_R38_CTS_ACCESS` | baseline-L1 environment-access gate | local CUDA; `logs/r38_cts_access_320k_20260715_140641_retry2`; commit `db3502e` | post-R38 cross-round failure review | M0 PASS; 100 low updates and zero high/process/intrinsic updates; MAPPO short `0/256`, long `2/256`, full `0/256`; all four 64-reset blocks had zero full success | Retire CTS without shaping, intrinsic reward, learner, budget, seed, or threshold rescue; the lifetime-controller gate is not authorized. |
| EXP-20260715-r36-aem-access | completed -- valid `FAIL_M1_RETIRE_R36_AEM` | baseline-L0 non-skill sparse-access gate | local CUDA; `logs/r36_aem_access_320k_20260715_034611`; implementation `b0a5300` | none | M0 PASS; AEM coverage `0.0639` vs control `0.016575` (`3.8552x`), yet both had 0/64 collection episodes and zero cycle success | Retire exact episodic joint-count novelty; GPT-5.6 Pro accepted the failure and selected the R37 observation-substrate gate. |
| EXP-20260715-r35-sparse-mappo-reset | completed -- valid `NO_ACCESS_R35_UNRESOLVED` | baseline-L0 sparse optimization reset | local CUDA; `logs/r35_sparse_mappo_reset_320k_20260715_013000_retry4`; runner commit `030d0cd`, implementation `b372000` | none | M0 PASS; both arms completed 320K/250 low updates, but 0/64 paired indices had a collection and both cycle means were 0 | Do not interpret noninferiority or replace a baseline; do not rerun/expand R35; seek one non-skill access-first edge. |
| EXP-20260714-r34-bhmd-gate | completed -- valid `FAIL_M1_RETIRE_R34_BHMD` | hierarchy-L2 codebook-construction and transport gate | local CUDA; `logs/r34_bhmd_gate_20260715_001706`; implementation commit `d0d80ac` | none | M0 PASS; real forced fidelity `0.5752`, source-relative gain `0.0654`; real persistent SNR `1.5235`, source-relative gain `-0.2962`; no natural coverage transport | Permanently retire fixed balanced hindsight mode distillation and its registered clustering/epoch/scope variants; request one structurally different post-R34 edge. |
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

## EXP-20260716-r49-orse-g0 — Open-Roster Set-Equivariant Interface

- Status: implementation ready; user authorized the local CPU gate and its Git
  pushes. Automatic GPT-5.6 Pro review is not authorized; the prior quota is
  exhausted.
- Causal edge: variable active set -> set-equivariant roster state -> exact
  active-only variable-length autoregressive probability/membership semantics.
- Scope: architecture-only. The four categorical codes are opaque protocol
  states, not semantic skills. There is no environment, reward, intrinsic,
  PPO, skill training, checkpoint migration, S7, task-performance, or
  cooperation claim.
- Model: shared Deep Sets member encoder `19 -> 64 -> 64` with GELU. Inputs are
  12 generic member features, one-hot opaque code of size four,
  `log(1+age)/log(501)`, joined, and processed. There is no persistent ID,
  padded slot, membership epoch, task, or reward input.
- Set state: static summary is mean active-member embedding plus `log(1+N)`.
  The working-roster summary is a mean and after each token updates as
  `r_new=r_old+(u_new-u_old)/N`. The shared decoder consumes the current member,
  static summary, and working-roster summary and emits KEEP plus conditional
  SET-code logits. The scalar high value reads only the pooled active set and
  `log(1+N)`. Parameter shapes are independent of `N`.
- Data: local deterministic one-thread CPU; model/data/sampling seeds
  `49041/59041/69041`; active sizes `{1,2,3,4,6,8,12,16}`; 128 cases per size,
  1,024 base cases; eight permutations per case, 8,192 equivariance reads;
  1,024 random nonzero junk-padding variants; 1,024 sampling/replay sequences;
  256 join/leave event pairs. Environment steps and optimizer updates are zero.
- Ledger: active keys, membership epochs, masks, opaque codes, ages, external
  AR order, sampled tokens, actual applied prefixes, and old token
  log-probabilities are stored for every case.
- Comparator/nulls: original versus active-set permutation, junk padding,
  incremental versus full working-roster recomputation, and stored sampling
  versus replay. Join/leave pairs audit membership rather than efficacy.
- M0: exact counts; no ID/slot embedding; `N`-independent state-dict shapes and
  parameter count; no masked-slot token; complete order/active-set/epoch/prefix
  ledger; identical sampling/replay support; finite logits, values,
  log-probabilities, and gradients; zero environment/reward/optimizer/checkpoint
  activity; complete joiner/leaver/survivor records; both incremental and full
  recomputation logged.
- M1 invariance/parity: maximum token-logit and scalar-value permutation error,
  padding error, incremental/full-recompute error, and sampling/replay
  log-probability error are each `<=1e-6`.
- M1 membership: a joiner has no KEEP support; a leaver emits zero tokens;
  every survivor retains opaque code, age, low-hidden placeholder, and
  membership epoch; active token count equals active-member count.
- M1 actionability/complexity: for `N>=2`, prefix-probability gradient
  Frobenius norm is `>1e-8` in at least `0.99` of cases and its median is
  `>1e-4`; state-dict shapes are equal for all `N`; each check performs one
  active-set encode, exactly `N` incremental updates and decoder calls, and
  creates no pairwise `N x N` tensor.
- `INVALID_R49_ORSE_WIRING`: repair only the named wiring defect and rerun the
  unchanged gate.
- `PASS_R49_ORSE_ARCHITECTURE`: conclude only that the interface is correct;
  authorize next only a default-off, exogenous cross-episode variable-`N`
  compatibility step. Do not infer semantics, lifetime, intrinsic efficacy,
  within-episode join/leave, S7, task performance, or cooperation.
- `VALID_FAIL_R49_ORSE_ARCHITECTURE`: retire this exact Deep-Sets mean plus
  log-count, incremental-roster, shared active-only AR, pooled-scalar-value
  interface without graph, Transformer, model, budget, seed, or threshold
  rescue; stop the open-roster and current project line. There is no
  underpowered branch.
- Prohibited changes: graph/attention/ISAB, pairwise tensors, persistent ID or
  padded-slot embedding, semantic code interpretation, environment/reward,
  optimizer, skill training, checkpoint migration, or fixed-`N` rescue.
- Focused evidence: a 16-case dry-run covering every active size passed M0/M1;
  permutation-logit and incremental/full-logit errors were `2.98e-8`, padding
  and replay errors were `0`, prefix support was `1.0` with median `0.19955`,
  and complexity violations were zero. The transient output was removed.
- Formal expected wall clock: under 15 minutes on local one-thread CPU, based
  on the focused run. Authoritative status: `<run-root>/runner_status.txt`;
  result: `<run-root>/result/r49_orse.json`.

## EXP-20260716-r48-sbrs-g0 — Skill-Boundary Recurrent State

- Status: completed as Pro-confirmed valid `VALID_FAIL_R48_SBRS`.
- Causal edge: skill SET -> focal recurrent-state boundary -> lower same-skill
  stochastic variability -> codebook-wide persistent process separation.
- Authorization: user approved the Pro-selected R48 route, its local gate, Git
  push, and the remaining automatic Pro result exchange.
- Source: exact frozen adaptive-R30 checkpoint
  `logs/r30_alice_bob_paired_64k_20260714_163908/runs/adaptive_keep_set/seed30031/standalone_process_core_final.pt`;
  total steps `64,000`, update `50`, `N=2`, `K=4`, `k0=10`, episode `80`,
  recurrent hidden `64`, stochastic high and tanh-Gaussian low policy. Load no
  optimizers; freeze every parameter and normalizer.
- Natural contexts: source seed `47041`; 64 independent 80-step reset groups,
  focal `group mod 2`, context check `1 + floor(group/2) mod 4`, primitive time
  `{10,20,30,40}`. Capture after natural high commit and before that block's
  first low action. Natural source exposure is exactly 5,120 steps.
- Targets and arms: incumbent is the natural post-check focal skill; enumerate
  its three nonincumbent targets. For each target and two replicas,
  `carry_hidden` preserves the focal actor hidden while `reset_on_set` zeros
  only that hidden. Teammate actor hidden, all critic hidden, environment
  snapshot, observation, roster, team code, and network state match at the
  boundary. High checks remain suppressed and the forced roster is held 40
  steps.
- CRN and budget: pre-generated Gaussian innovation tape seed `68041`, shared
  across both arms and all three targets within a context/replica; replicas are
  independent. There are 384 branches per arm, 768 total, 30,720 branch steps,
  zero policy/high/critic/intrinsic optimizer steps, and no external-return or
  intrinsic read. Expected wall clock is under 20 minutes on local CUDA.
- Process read: `pbar=p/8`, `r_i=pbar_-i-pbar_i`, and
  `y_t=[pbar_i,t-pbar_i,0, r_i,t-r_i,0]` in four position-only dimensions.
  H10 is `t=1..10`; H40-late is `t=31..40`. Distance is the mean timewise
  squared Euclidean trajectory difference. No R47 view/basis/mode, action,
  reward, task object, contact, phase, success, or skill label enters the read.
- Statistics: per arm/context, `B` averages the same-replica distances over the
  three target pairs and two replicas; `W` averages replica distance over the
  three targets; `rho=E[B]/(E[W]+1e-8)`. Target-conditional rho compares each
  target with the other two. Bootstrap 10,000 times with seed `62048` using the
  complete source context as cluster and jointly resampling both arms, all
  targets, replicas, and trajectory coordinates.
- M0: exact source/config, schedule, 64 contexts, three nonincumbent targets,
  384 branches/arm, 30,720 branch steps, no early reset, exact snapshot restore,
  exact matched arm starts and innovation tape, only focal actor-hidden reset,
  exact parameter/normalizer freeze, zero optimizers, no task/reward evidence
  field, every target skill in at least 32 contexts, and finite trajectories,
  distances, B, W, and rho.
- M1: at both H10 and H40-late require reset-rho lower 95% bound `>1`,
  reset/carry rho-ratio lower bound `>1.25`, reset/carry within-ratio upper bound
  `<0.80`, and reset/carry between-ratio lower bound `>0.90`. H40-late also
  requires reset target-conditional rho `>1` for all four skills.
- `INVALID_R48_SBRS_WIRING`: repair only the named snapshot, hidden, CRN,
  count, or metric defect and rerun unchanged.
- `PASS_R48_SBRS_G0`: authorize only a mechanism-matched reward-pure R30
  `carry_on_SET` versus `reset_on_SET` pair with identical networks and external
  reward, no intrinsic, and external-only high return.
- `VALID_FAIL_R48_SBRS`: permanently retire SET-time focal zero-reset, the
  shared-parameter skill-boundary-reset line, this raw-trajectory gate, and the
  recurrent-contamination explanation; permanently stop fixed-N skill/lifetime
  algorithm exploration. No underpowered, added-seed/context, threshold, budget,
  model, reward, or environment rescue branch exists.
- Focused check: two contexts, 24 total branches, 960 forced steps; exact
  snapshot/hidden/CRN/count/freeze checks and finite H10/H40 statistics passed.
- Authoritative status: `<run-root>/runner_status.txt`; result:
  `<run-root>/result/r48_sbrs.json`.
- Terminal evidence: formal run `logs/r48_sbrs_20260716_181833` passed every M0
  check with 64 contexts, 768 complete branches, 30,720 forced steps, exact
  snapshot/hidden/CRN/freeze contracts, and no task/reward evidence field. H10
  reset rho lower bound was `0.98468`, reset/carry rho-ratio lower bound
  `1.11816`, and within-ratio upper bound `1.01877`. H40-late reset rho and all
  four target-skill rhos exceeded one, but reset/carry rho-ratio lower bound was
  `1.00223` and within-ratio upper bound `1.00874`. The valid-fail retirement
  and fixed-`N` stop branch are binding. GPT-5.6 Pro found no result-changing
  M0 defect, confirmed both retirements, and selected only the independent
  architecture-only `R49-ORSE-G0` interface gate.
- External review: GPT-5.6 Pro, 2026-07-16; raw response and accepted
  disposition are under
  `docs/external-review/gpt5_6_pro/20260716_r48_sbrs_result/`.

## EXP-20260716-r47-nsopm-g0 — Natural-Support Orthogonal Process Modes

- Status: completed and GPT-5.6 Pro-confirmed valid
  `VALID_FAIL_R47_NSOPM`; exact line retired without rescue.
- Causal edge: natural task-blind process support -> stable orthogonal
  persistent modes -> skill-conditioned causal mode occupancy.
- Scope: fixed-`N=2`, reward-off G0 only. No policy/high/critic/intrinsic
  update, task-performance claim, S7, open-roster, or variable-`N` claim.
- Source: frozen adaptive-R30 checkpoint
  `logs/r30_alice_bob_paired_64k_20260714_163908/runs/adaptive_keep_set/seed30031/standalone_process_core_final.pt`;
  total steps `64,000`, update `50`, `K=4`, `k0=10`, episode `80`, recurrent
  low hidden `64`, stochastic high and stochastic tanh-Gaussian low execution.
  Load optimizers false; all modules eval/frozen; low actor sees only `(o_i,z_i)`.
- Natural schedule: seed `47041`; 64 independent 80-step reset groups. Even
  groups use check indices `{0,2,4,6}`, odd groups `{1,3,5,7}`; both focal
  agents yield eight `[10,7]` windows/group and 512 total. Fit groups `0..31`,
  half A `0..15`, half B `16..31`, heldout `32..63`, nuisance train/test
  `32..47`/`48..63`. Environment reward is discarded; literal `0.0` advances
  the R30 clock.
- View: `pbar=p/8`; relative vectors `r_ij=pbar_j-pbar_i`; population mean and
  covariance over teammates. Transition order is
  `[delta pbar_x,delta pbar_y,delta mean_rel_x,delta mean_rel_y,
  delta covariance_xx,delta covariance_xy,delta covariance_yy]`. For `N=2`
  the covariance fields are exactly zero. No action, skill, age, ID, reward,
  task, contact, clock, success, or critic field enters mode fitting.
- Features: population mean/std from the owning fit split, with scale `1` when
  std `<1e-6`; initial-center every window; concatenate seven centered fields
  with the fixed row-major upper-triangular quadratic terms for 35 dimensions.
- Spectral estimator: within-window lags `{1,5}`; pooled source/target means and
  population `C00/C11`, lag-specific `C01`; covariance rank floor
  `max(1e-8,1e-6*lambda_max)`, whitening ridge `1e-4`; unsymmetrized
  `T_l=W0*C01(l)*W1`; `G=(T1*T1^T+T5*T5^T)/2`; mode floor
  `max(1e-10,1e-6*nu0)`. Four descending spectral-rank modes are frozen; no
  skill or forced-outcome alignment.
- M1 temporal/null/stability: 256 independent within-window nonidentity
  permutations, seed `57041`, refit the full estimator and require each real
  eigenvalue above its rank-matched null q95. Independently fit half A/B,
  exhaustively align each to primary on heldout activations, and require minimum
  A/B correlation `>=0.70`. For lag 1 and 5, heldout reset-group bootstrap of
  real minus mean frozen-basis temporal-null coherence must have lower 95%
  bound `>0`.
- M1 nuisance audit: target `g_q=C_q*X_q`; ten fields are focal/teammate start
  positions, focal indicator, clipped focal age, and focal/teammate action
  variances. Analytic multi-output ridge `1e-3`, nuisance-train standardization,
  unregularized intercept; maximum pooled/per-mode test R2 must be `<0.10`.
- Forced audit: one context per reset group with focal `g mod 2` and check
  `floor(g/2) mod 4` at time `{0,10,20,30}`. Snapshot after the natural high
  commit and before the first low action. Override only focal actor-visible
  skill, hold both skills for 40 steps, suppress high checks, continue both
  recurrent low states, and keep the teammate stochastic and policy-responsive.
  Four skills, two replicas, CRN seed `67041+2*c+r`, 20,480 total steps; any
  early reset invalidates the context and M0 requires none.
- M2 support: primary-fit Mahalanobis-whitened distance threshold is the
  heldout-natural pointwise q95. H10 and H40-late windows require at least 9/10
  supported points; a context is usable only when all eight branches pass, and
  each horizon requires support ratio `>=0.80`.
- M2 scores: `E_q=mean(m_q^2)`, `X_q=E_q/(sum E+1e-8)`,
  `C_q=(corr_lag1+corr_lag5)/2`, `g_q=C_q*X_q`. Candidate
  `S(w,z)=g_z-mean_q g_q` is detached and logged only. Assigned-mode contrast
  requires lower 95% bounds of pooled H10 and H40-late means `>0`, every
  H40-late per-skill point mean `>0`, between/within causal-SNR lower bounds
  `>1`, and intersection persistence `D40/(D10+1e-8)>=0.50`.
- Bootstrap: 10,000 repetitions, seed `62047`; natural cluster is reset group,
  causal cluster is matched context with all skills, replicas, and modes kept
  together.
- M0: exact source/config/counts/schema and fit splits; finite estimator/scores;
  512 complete natural windows; 64 contexts and 20,480 forced steps; frozen
  basis; no forced fit leakage, reward field/read, optimizer step, parameter
  drift, snapshot mismatch, or early branch reset.
- `INVALID_R47_NSOPM_WIRING`: repair only the identified wiring defect and rerun
  unchanged.
- `PASS_R47_NSOPM_IDENTIFIABILITY`: M0/M1/M2 pass; authorize only matched
  `probe_only` versus `real_reward` with the same formula, natural basis,
  collector, and low PPO; detached endpoint `S` enters low GAE only in the real
  arm while high return remains external-only.
- `VALID_FAIL_R47_NSOPM`: M0 valid and M1 or M2 fails; permanently retire this
  exact 7-D view, 35-D map, lags, four-mode basis, score and reward pair without
  window/lag/mode/encoder/kernel/seed/data/threshold or post-hoc alignment rescue.
- Focused dry run: two natural groups, 16 windows, one context, eight branches,
  320 branch steps, two temporal nulls, zero optimizers; no scientific status
  and transient output removed after success.
- Authoritative status: `<run-root>/runner_status.txt`; result:
  `<run-root>/result/r47_nsopm.json`.
- Terminal evidence: focused dry run passed and was removed. Formal run
  `logs/r47_nsopm_20260716_172711` completed `VALID_FAIL_R47_NSOPM` with M0
  pass and M1/M2 fail. Primary/half models each had 14 nontrivial modes and
  stability `0.8759--0.9610`; nuisance maximum R2 was `-0.0713`. Only rank 0
  beat the temporal-null q95 and lag-5 coherence lower bound was `-0.04475`.
  H10/H40 support was `0.71875/0.828125`; H10 assigned contrast lower bound was
  `-0.000652`; H40 skill 0 contrast was `-0.01542`; causal-SNR means were
  `0.0343/0.1992`. GPT-5.6 Pro found no result-changing M0 defect, confirmed
  the valid-fail retirement, and selected only the structurally distinct R48
  recurrent-state-boundary gate.

## EXP-20260716-r46-hmrv-g0 — Heterogeneous Maintenance Renewal Value

- Status: completed as valid `VALID_FAIL_R46_HMRV_SUBSTRATE`; pending external
  result review.
- Causal edge: native heterogeneous process degradation -> balanced natural
  KEEP/RENEW support -> action-specific delayed renewal value -> same-check
  agent/context-specific sign heterogeneity.
- Scope: reward-off fixed-`N=2` temporal-substrate positive control. It is not
  skill learning, intrinsic-reward training, benchmark performance, S7,
  open-roster, or variable-`N` evidence.
- Authorization: the user authorized the local gate and Git pushes within the
  bounded automatic Pro workflow.
- Execution: local CUDA only; cloud prohibited. Environment and behavior-action
  seeds `46041`; `N=2`; `k0=5`; horizon `40`; eight checks per episode; 16
  environments; 100 episodes per environment; 64,000 primitive steps. The
  behavior policy samples independent Bernoulli-0.5 `KEEP=0`/`RENEW=1` actions
  for both agents at every check. Even episode indices use degradation `(1,2)`
  and odd indices use `(2,1)`. Expected wall clock is under 30 minutes.
- Transition and reward: health starts at `(4,4)`. KEEP emits `u_i=h_i/4` and
  sets `h'_i=max(0,h_i-d_i)`; RENEW emits `u_i=0` and sets `h'_i=4`. Each
  primitive step in the block receives shared external reward
  `min(1,u_0+u_1)`. The reward consumes service output, not the token. There is
  no shaping, intrinsic, lifetime, or asynchrony reward.
- Outcome: `gamma=0.99` and
  `G_tau^(3)=sum_{r=0}^{14} 0.99^r r_env[tau*k0+r]`, covering the action's
  current block and the following two blocks without a discount restart. Only
  the first six checks enter the estimand: 9,600 usable checks and 19,200 focal
  rows.
- Context: exactly
  `[h_i/4,h_other/4,d_i/2,d_other/2,prefix_valid,b_<i]`. Agent 0 uses sentinel
  `[prefix_valid,b_<i>]=[0,0]`; agent 1 uses `[1,actual_b0]`. No identity,
  reward history, future, oracle, task, goal, contact, or success field enters.
- Critics: fixed folds A train env ranks `0..7` and hold out `8..15`; B reverses
  them. Each fold trains one true-Q and one action-blind propensity-mixture
  sham with identical initialization, normalization, minibatch schedule,
  capacity, and exposure. Architecture `6->32 GELU->2`; Adam `lr=5e-4`,
  `eps=1e-5`, betas `(0.9,0.999)`, zero weight decay, no AMSGrad; 15 epochs;
  minibatch 256; no drop-last. Fold A model/shuffle seeds `46041/1046044`;
  fold B `56041/1056044`. Each model takes 570 steps, 2,280 total. Policy,
  low, skill, and intrinsic optimizer steps are all zero.
- Evaluation: 100 episodes with action seed `56041`. Pre-generate the balanced
  role assignments and Bernoulli action tensor, then replay them exactly before
  and after critic fitting. Pairing is only an M0 trace-equality audit; no
  trained-policy arm exists.
- Bootstrap: 10,000 repetitions, seed `62046`. The scientific cluster is the
  independent source episode `(env_rank,episode_index)`, containing all six
  usable checks and both focal rows. M1 maximum-weight share remains grouped by
  persistent environment rank.
- M0: exact registered transitions/reward, propensity `0.5`, action replay,
  counts, zero noncritic optimizer steps, four critics with 570 steps each,
  nonoverlapping folds, finite gradients/predictions/weights/DR scores, exact
  six-field context and pre/post traces, plus at least one zero-reward and one
  full-service block.
- M1: every agent/action ESS `>=64` and persistent-environment maximum
  normalized weight share `<=0.10`.
- M2: lower 95% bound of `WMSE_sham/WMSE_true-1` is positive and the lower 95%
  bound of top-minus-bottom doubly robust score is positive.
- M3: for each agent, top-quartile DR lower bound is positive and bottom-
  quartile DR upper bound is negative. Pooled same-check predicted-sign
  discordance is at least `0.20` with lower bound above `0.10`; ordered role
  strata `(1,2)` and `(2,1)` each separately require a lower bound above
  `0.10`.
- `INVALID_R46_HMRV_WIRING`: M0 failure; repair only the explicit defect and
  rerun the unchanged contract.
- `PASS_R46_HMRV_IDENTIFIABILITY`: M0--M3 pass; authorize only a same-substrate
  per-agent renewal actor versus shared-sync control.
- `VALID_FAIL_R46_HMRV_SUBSTRATE`: M0 valid and any M1--M3 failure; permanently
  retire the exact dynamics, three-block estimand, and positive-control
  substrate without seed, data, capacity, threshold, clipping, reward, or
  environment rescue.
- Authoritative status: `<run-root>/runner_status.txt`; result:
  `<run-root>/result/r46_hmrv_identifiability.json`.
- Terminal evidence: run `logs/r46_hmrv_64k_20260716_154508` passed M0, M1,
  and M2. True/sham weighted MSE was `10.6079/10.9186`; ratio-gain interval
  `[0.02669,0.03189]`; top-minus-bottom DR interval
  `[2.5504,3.0374]`. M3 failed: pooled and both ordered-role-stratum sign
  discordance were exactly zero. The registered valid-fail retirement is
  binding unless review identifies a concrete result-changing M0 defect.

## EXP-20260715-r38-cts-access — Cooperative Two-Timescale Sparse Access

- Question: can functionally ordinary constant-code recurrent MAPPO access a
  swap-equivariant task that structurally requires one simultaneous long-lived
  anchor duty and one short shuttle duty?
- Causal edge: simultaneous anchor/shuttle duties -> recurrent MAPPO accesses
  both duties and joint sparse success -> one later lifetime-controller gate is
  eligible.
- Baselines: Level 1 trained constant-code recurrent MAPPO versus paired
  uniform-random actions on identical reset seeds. This is an environment
  access gate, not an algorithm comparison.
- Reward: shared +1 only on full success; otherwise zero. Intrinsic reward is
  identically zero and no environment-specific auxiliary signal is allowed.
- Budget: train seed 39031; CUDA; 16 parallel environments; rollout 200;
  320,000 environment steps; 100 outer low PPO updates; final stochastic eval
  seeds 139031..139286. Random action RNG seed 49031. Paired bootstrap 10,000
  repetitions with seed 59031.
- M0 implementation: exact scenario/config/seed/budget; 256 unique paired
  reset rows per policy; finite actions and metrics; MAPPO success rows end by
  termination and failures at step 200 by truncation; task reward equals the
  full-success indicator; all non-full rewards and all intrinsic rewards are
  zero.
- M1 access: MAPPO short-duty rate >= 0.10, long-duty rate >= 0.05, full-success
  rate > 0.10 (at least 26/256), and the paired MAPPO-minus-random bootstrap
  lower bound is > 0 for all three indicators.
- M2 repeatability: at least three of the four contiguous 64-reset MAPPO blocks
  contain at least one full success.
- PASS_R38_CTS_ACCESS: M0, M1, and M2 pass; authorize only registration of one
  shared-fixed-k versus per-agent-lifetime mechanism gate.
- INVALID_R38_IMPLEMENTATION: M0 fails; fix only the concrete wiring defect and
  rerun the unchanged contract.
- FAIL_R38_CTS_ACCESS: M0 passes and M1 or M2 fails; retire the benchmark with
  no shaping, intrinsic reward, budget, seed, threshold, or learner rescue.
- Prohibited: old Alice-Bob logic, identity cues, role labels, low-learner
  changes, high-policy updates, process/skill rewards, threshold changes after
  results, and environment-specific intrinsic reward.
- Expected wall clock: one local 320K CUDA training job plus 512 total final
  evaluation episodes; use the existing dedicated training monitor.
- Status source: `<run-root>/runner_status.txt`; decision source:
  `<run-root>/result/r38_cts_access.json`.
- Result: valid `FAIL_R38_CTS_ACCESS` at
  `logs/r38_cts_access_320k_20260715_140641_retry2/result/r38_cts_access.json`.
  M0 passed. MAPPO completed 320,000 steps and 100 low updates with zero
  high/process updates and zero intrinsic reward. In 256 paired evaluations it
  achieved short duty `0`, long duty `2` (`0.0078125`), and full success `0`;
  uniform random achieved zero for all three. Every 64-reset MAPPO block had
  zero full success, and every paired confidence-interval lower bound was zero.
- Status: completed -- valid `FAIL_R38_CTS_ACCESS`. Retire this benchmark under
  the registered branch; do not enter the PASS-only lifetime-controller gate.

## Current Gate Detail

### EXP-20260716-r45-sdra-g0

- Causal edge: frozen source-exact natural KEEP/RENEW randomization ->
  cross-fitted action-conditional `Q_i(c,KEEP/RENEW)` -> doubly robust heldout
  score -> identifiable value signs that differ by agent/context. This repairs
  R44's unestablished shared-return/state-value credit edge without retraining
  or rescuing R44.
- Authorization: GPT-5.6 Pro selected R45-SDRA-G0 as the only successor. The
  code and focused wiring check are complete. Formal launch requires explicit
  user approval of the M2 mathematical clarification and the fixed run.
- Frozen boundary: R41B seed-1 exact-final source MAT, team `Z`, conditional
  skill policy, high value, low actor/critic, `q_D/q_d`, all source optimizers,
  ValueNorms, and the zero renewal residual. Source optimizer and renewal-actor
  optimizer steps are exactly zero.
- Data/clock: seed `43041`; 16 envs; global `k0=50`; reset-censored R43/R44
  clock; one structural assignment per env; 160,000 steps; 100 outer updates;
  3,200 env-check rows, 16 structural rows, 3,184 normal rows, and 6,368 normal
  agent-factor rows. Each row stores the exact natural binary propensity,
  148-D task-agnostic canonical-prefix context, sampled action, and discounted
  next-50 external return.
- Critics: fixed folds env 0--7 versus 8--15; per fold one true action-Q and
  one action-blind propensity-mixture sham; identical
  `148 -> 32 GELU -> 2` architecture and paired initialization; fold-only input
  normalization; Adam `lr=5e-4`, `eps=1e-5`; 15 epochs; minibatch 256 without
  drop-last; 195 steps/model, 780 total. No actor update, early stopping, model
  selection, propensity clipping, forced action, or simulator clone.
- Evaluation/bootstrap: frozen source zero/final exact trace comparison and
  100 deterministic final episodes; 10,000 environment-cluster bootstraps,
  seed `62045`.
- M0: exact source/config/clock/counts; source probability and binary replay
  errors `<=1e-6`; prefix mismatch zero; source and renewal actor drift zero;
  all source/actor optimizer steps zero; four critic models have identical
  contract/exposure and finite predictions/gradients; no task field, shaping,
  intrinsic addition, or forced branch; frozen zero/final outcomes and complete
  high/low traces exact.
- M1: frozen source win `>=0.80`, key0/key1 each `>=0.85`; for each agent and
  action inverse-propensity ESS `>=64`; no environment contributes more than
  10% of the corresponding action's normalized weight.
- M2: heldout action-specific informativeness requires both
  `LCB95(WMSE_sham/WMSE_true - 1)>0` and the cluster-bootstrap lower bound of
  top-quartile minus bottom-quartile doubly robust score `>0`. The analyzer also
  reports Pro's literal ratio; subtracting one is the only nontrivial reading
  consistent with its stated purpose that true-Q beat the sham.
- M3: for each agent, top-quartile DR score lower bound `>0` and bottom-quartile
  upper bound `<0`; same-check predicted-sign discordance point `>=0.20` and
  95% lower bound `>0.10`.
- Branches: M0 failure -> `INVALID_R45_SDRA_WIRING`, repair only the concrete
  implementation and rerun unchanged. M0--M3 all pass ->
  `PASS_R45_SDRA_IDENTIFIABILITY`, authorizing only one later mechanism-matched
  detached-SDRA actor pair. Valid M0 with any M1--M3 failure ->
  `VALID_FAIL_R45_SDRA_IDENTIFIABILITY`, permanently retire Alice--Bob K50
  natural-support renewal credit and this temporal substrate without more data,
  capacity, clipping, threshold, or seed rescue. No UNDERPOWERED branch.
- Prohibited: R42--R44 rescue, extra seed/data, propensity clipping, critic
  capacity or threshold changes, renewal actor update during G0, task-specific
  intrinsic reward or shaping, forced renewal/simulator clone, S7, open roster,
  and variable `N`.
- Expected local wall clock: about 4--7 minutes on the current 16-env CUDA
  topology. Status source: `<run-root>/runner_status.txt`; decision source:
  `<run-root>/result/r45_sdra_identifiability.json`.
- Terminal result: valid `VALID_FAIL_R45_SDRA_IDENTIFIABILITY` at
  `logs/r45_sdra_160k_20260716_144312`. M0 passed with exact source and actor
  freeze, zero source/actor optimizer steps, source probability error
  `4.768e-7`, binary replay and prefix mismatch zero, 780 exact critic steps,
  and exact zero/final traces. Source win/key0/key1 remained
  `0.93/1.00/0.93`.
- M1 failed: agent-0/1 KEEP ESS was `33.586/3.298`; their maximum environment
  weight shares were `0.1475/0.6156`; agent-1 RENEW cluster share was `0.1353`.
  M2 passed: true-Q/sham weighted MSE was `0.038299/0.376669`, ratio-gain CI
  `[3.3623,18.4246]`, and top-minus-bottom DR-score CI
  `[0.4083,0.7059]`. M3 failed: both agents' bottom DR intervals stayed
  positive and same-check sign discordance was `0.000314`, CI
  `[0,0.000942]`.
- Decision: action-specific prediction is learnable, but the natural source
  support does not establish heterogeneous renewal value. Permanently retire
  Alice--Bob K50 natural-support renewal credit and this temporal substrate;
  no data, seed, capacity, clipping, threshold, forced-action, or actor-update
  rescue. Request one structurally different next edge.

### EXP-20260716-r44-fsnrc-k50

- Causal edge: freeze the service-capable R41B coordinator, skills, low
  executor, discriminators, and normalizers; retain the source-exact native
  KEEP/RENEW factorization; train only a renewal residual actor and renewal
  critic; test whether asynchronous lifetime can emerge without forgetting
  service.
- Authorization: GPT-5.6 Pro selected `R44-FS-NRC` as the only successor to
  invalid R43. The implementation and contract are prepared, but the formal
  run requires explicit user launch approval.
- Comparator: hierarchy-L2 mechanism-matched concurrent
  `frozen_source_nrc0` and `frozen_source_nrc` load the same R41B seed-1
  exact-final checkpoint. Both instantiate the same modules, factor optimizer,
  frozen source distributions, collector, clock, and renewal critic. Only the
  treatment renewal actor receives gradients; the control actor remains
  exactly zero and frozen.
- Probability/update boundary: source team `Z` and non-incumbent conditional
  skill distributions remain frozen. The effective zero-residual post-skill
  distribution exactly equals source HMASD. Conditional skill likelihood is
  stored and replayed with ratio one but never optimized. The five source
  optimizer paths execute zero steps. A separate Adam with original high-policy
  hyperparameters updates only renewal actor/critic for 15 epochs per outer
  update; no renewal entropy is used.
- Credit: renewal return is the next 50 external-reward primitive steps. Auto-
  reset censors the execution fragment but not the controller return; the
  update boundary uses old-renewal-critic bootstrap and cuts GAE. Original
  `q_D/q_d` may be evaluated read-only but neither update nor enter renewal
  return. No shaping, new intrinsic, or task-specific input is allowed.
- Fixed budget: seed `43041`; two arms concurrent on local CUDA; 16 rollout
  envs/arm; 100-step rollout; global `k0=50`; 320,000 environment steps and
  200 outer updates/arm; 6,400 env-check rows/arm; 3,000 factor optimizer
  steps/arm; zero source optimizer steps; 100 paired deterministic evaluations;
  10,000 bootstrap repetitions, seed `62043`. Expected local wall clock is
  8--15 minutes for both concurrent arms and analysis.
- M0 implementation/freeze: source-exact joint and decomposed probability,
  team/factor/conditional/low replay errors `<=1e-6`; prefix mismatch zero;
  all source modules, five optimizer states, and high/low ValueNorm drift
  `<=1e-12`; factor steps exactly 3,000; control actor drift `<=1e-12`;
  treatment actor has 3,000 finite nonzero gradient exposures and relative
  drift `>1e-6`; both critics have finite nonzero gradients; 16 structural
  assignments, 6,400 check rows, no reset high action, no same-label RENEW;
  control zero/final wins, keys, lengths, high traces, and low traces are exact.
- M1 frozen anchor: control final win `>=0.80`, key0/key1 each `>=0.85`.
- M2 service safety: paired treatment-minus-control win 95% lower bound must be
  strictly greater than `-0.10`.
- M3 temporal decoupling, excluding structural rows: treatment discordance
  `>=0.20`; paired discordance lower bound `>0`; full-sync RENEW `<0.50`;
  each agent KEEP and RENEW marginal `>=0.05`; actual RENEW-target entropy
  divided by `log(4)` `>0.80`; same-label RENEW zero.
- Branches: M0 failure -> `INVALID_R44_FSNRC_IMPLEMENTATION`, repair only the
  explicit defect and rerun unchanged. M1 failure ->
  `INVALID_R44_FROZEN_ANCHOR`, repair checkpoint/factorization/evaluation only
  and do not interpret treatment. Valid M0/M1 with M2 or M3 failure ->
  `VALID_FAIL_R44_FSNRC`, permanently retire this frozen-source K50 timing
  route without rescue. All pass -> `PASS_R44_FSNRC_K50`, authorizing only one
  unchanged paired multi-seed Alice--Bob verification.
- Prohibited: source unfreezing, seed/budget/threshold changes, best-checkpoint
  selection, renewal/lifetime/KEEP reward, switch penalty, renewal entropy,
  full-refresh escape, task fields, task-specific intrinsic reward, S7,
  open-roster, or variable team membership.
- Status source: `<run-root>/runner_status.txt`; decision source:
  `<run-root>/result/r44_frozen_source_nrc.json`.
- Terminal result: valid `VALID_FAIL_R44_FSNRC` at
  `logs/r44_fsnrc_320k_20260716_132349`. M0 passed with exact frozen-source
  state, zero source optimizer steps, 3,000 factor steps, replay and
  conditional-ratio error zero, and exact control zero/final traces. M1 and M2
  passed: control and treatment both scored win/key0/key1
  `0.93/1.00/0.93`, and treatment-minus-control win CI was `[0,0]`.
- M3 failed. Both deterministic arms had discordance `0`, full-sync RENEW
  `1.0`, minimum KEEP/RENEW marginal `0`, and paired discordance CI `[0,0]`.
  Treatment actor relative drift was `0.353245` with 3,000/3,000 finite
  nonzero actor-gradient exposures, so the failure is not a disconnected actor
  path. Its critic had 2,992 nonzero-gradient steps and all 3,000 checks were
  finite; the first analyzer incorrectly required every critic step to be
  nonzero although M0 requires finite gradients plus nonzero exposure. The
  corrected analyzer reused the completed arms and did not retrain.
- Decision: permanently retire this frozen-source K50 renewal adapter and its
  registered next-check credit. Do not rescue it through entropy, temperature,
  source unfreezing, seed/budget/threshold changes, or stochastic-only metric
  substitution. The result does not retire a structurally new joint co-
  adaptive asynchronous-skill route.

### EXP-20260716-r43-nrc-k50

- Causal edge: source categorical individual skill -> exact KEEP/RENEW
  decomposition plus conditional non-incumbent skill -> separate controller-time
  renewal and skill-event credit -> service-preserving temporal decoupling.
- Authorization: GPT-5.6 Pro confirmed the source contradiction and selected
  `R43-NRC with reset-censored controller time`; the user approved the exact
  conclusion-bearing run.
- Comparator: concurrent `fixed_refresh` is the unchanged R41B continuation;
  `r43_nrc` starts from the same checkpoint and adds zero-output renewal actor,
  renewal critic, and skill-event critic to the existing high optimizer.
- Clock/segment: global checks remain at primitive `50n`; each training env has
  one structural assignment for the whole run; auto-reset adds no high action or
  row, preserves team/roster/age/spell, resets source low hidden state, and marks
  an `env_reset_censored` execution fragment. Update boundaries bootstrap and
  truncate actor-valid events; continuation is critic-only.
- Probability/credit: KEEP opens no skill factor; RENEW masks the incumbent.
  Working prefixes are teacher-forced in canonical order. Renewal return covers
  the next 50 external-reward steps across reset. Skill-event return ends at the
  next RENEW or update boundary. Source team value/PPO and original
  environment-agnostic `q_D/q_d` low reward remain unchanged.
- Fixed budget: seed `43041`; two arms concurrent; CUDA; 16 rollout envs/arm;
  `320,000` environment steps/arm; 200 outer updates; exactly 6,400 env-check
  rows and 3,000 steps on each of high, low actor, low critic, `q_D`, and `q_d`;
  100 paired deterministic final episodes; 10,000 paired bootstraps, seed
  `62043`. Expected local wall clock is 8--12 minutes; the matched R42 paired
  run completed both arms in about 5.8 minutes and R43 adds per-update high
  factor replay plus two small critics.
- M0: exact source/checkpoint/config; 32-outcome zero-init probability and
  decomposed logp error `<=1e-6`; high/factor/low replay `<=1e-6`; exactly one
  structural assignment/env, two high rows/env/update, zero reset high actions,
  6,400 update-boundary event truncations, preserved carry, finite/nonzero
  optimizer paths, new-module treatment drift and zero fixed drift. At least one
  early reset block must show success reward and post-reset steps in the same
  controller return. Failure -> `INVALID_R43_NRC_CLOCK_OR_IMPLEMENTATION` and
  repair only the located defect.
- M1 fixed anchor: win `>=0.80`, key0/key1 each `>=0.85`. Failure ->
  `INVALID_R43_FIXED_ANCHOR_LOST` and restore only source continuation.
- M2 service: paired 95% lower bound of treatment-minus-fixed win must be
  strictly greater than `-0.10`.
- M3 explicit renewal, excluding structural rows: treatment discordance
  `>=0.20`; paired discordance lower bound `>0`; full-sync renewal `<0.50`;
  every agent KEEP and RENEW marginal `>=0.05`; actual renewal-target entropy
  divided by `log(4)` `>0.80`; same-label renewal `=0`.
- Branches: M0/M1 valid but M2 or M3 failure -> `VALID_FAIL_R43_NRC`, permanently
  retire this reset-censored Alice--Bob K50 route without rescue. All gates pass
  -> `PASS_R43_NRC_K50`, authorizing only the unchanged paired multi-seed
  Alice--Bob verification. No underpowered, retuning, extra-step, extra-seed,
  reward, entropy, refresh, age-capacity, S7, or variable-`N` branch exists.
- Status source: `<run-root>/runner_status.txt`; decision source:
  `<run-root>/result/r43_native_renewal.json`.
- Terminal result: `INVALID_R43_FIXED_ANCHOR_LOST`, with M0 valid but M1 fixed
  anchor failed at win/key0/key1 `0.52/0.54/0.81`. M2 and M3 treatment numbers
  have no scientific interpretation under this branch.
- Fixed-anchor localization: the unmodified R41B checkpoint scored win
  `0.89/0.93` on seed-1/seed-43041 evaluation streams; the fixed final
  checkpoint scored `0.61/0.52`. Untouched source continuation and the R43
  fixed wrapper had zero parameter difference after two same-seed updates over
  every trained module. The pending review must decide how to define a stable,
  mechanism-matched source comparator without rescuing R43 by seed, budget,
  threshold, reward, or treatment tuning.

### EXP-20260716-r42-irr-native-roster-residual

- Causal edge: incumbent roster at the original HMASD check -> a zero-output,
  task-blind residual on the existing MAT individual logits -> learned
  per-agent retain/replace probabilities -> service-preserving temporal
  decoupling.
- Upstream authorization: R41B is a valid positive source anchor. Three
  sequential GPT-5.6 Pro rounds are complete. The final pure categorical
  reinterpretation is retired without training because its effective skill,
  policy inputs, trajectory distribution, likelihoods, and gradients are
  identical to the fixed-refresh arm.
- Fixed boundaries: fresh `ref/hmasd.tar`, native `k0=50`, team `Z` resampled
  at every native check, complete checkpoint/optimizer/value-normalizer restore,
  and unchanged original environment reward plus original `q_D/q_d` intrinsic
  terms. No age input is used in this 100-step one-renewal gate.
- Treatment boundary: a shared residual sees only incumbent/working roster,
  focal position, and active-agent mask. Its output layer is zero-initialized;
  sampling and teacher-forced PPO replay use the same stored roster and
  autoregressive prefixes. The fixed arm instantiates the same module with its
  output and gradient disabled.
- Comparator and exposure: hierarchy-L2 mechanism-matched
  `fixed_refresh` versus `incumbent_roster_residual`, both restored from the
  exact R41B seed-1 final checkpoint. Seed `42041`; arms run concurrently on
  local CUDA with 16 rollout environments each, 100-step rollouts, 200 outer
  updates, 320,000 environment steps, and 3,000 updates for each original high,
  low-actor, low-critic, team-discriminator, and individual-discriminator path.
  The treatment additionally updates its residual through the existing high
  loss. Final evaluation uses 100 deterministic paired reset streams per arm.
- M0 implementation: fresh source extraction; exact checkpoint schema and full
  optimizer/ValueNorm restore; zero-output action, log-probability, value,
  entropy, replay, and base-gradient errors all `<=1e-6`; residual direct
  gradient finite and nonzero; exactly 548 new parameters; high/low/global
  stored-replayed error `<=1e-6`; exact step/update counts; all five original
  paths expose finite nonzero gradients; fixed residual drift `<=1e-12` and
  treatment relative drift `>1e-6`; one `t=50` renewal row per evaluation.
- M1 fixed anchor: fixed final win rate `>=0.80` and both key0/key1 rates
  `>=0.85`.
- M2 service: 10,000 paired-reset bootstrap repetitions, seed `62042`; the
  strict lower 95% bound of treatment-minus-fixed win must exceed `-0.10`.
- M3 temporal mechanism: define effective SET only when the post-check skill
  differs from its incumbent. Treatment discordant-agent SET rate must be
  `>=0.20`, and the paired treatment-minus-fixed discordance lower 95% bound
  must be `>0`; treatment full-synchronous SET must be `<0.50`; every agent must
  have both KEEP and SET marginal at least `0.05`; normalized entropy of actual
  SET targets must be `>0.80`.
- Branches: M0 failure -> `INVALID_R42_IRR_IMPLEMENTATION`, repair only the
  concrete implementation defect. M1 failure ->
  `INVALID_R42_FIXED_ANCHOR_LOST`, restore the continuation contract. M2
  failure -> `VALID_FAIL_R42_IRR_SERVICE`, retire the direct native-k50
  residual. M2 pass/M3 failure -> `VALID_FAIL_R42_IRR_NO_DECOUPLING`, retire it
  as a temporal mechanism. M0--M3 pass -> `PASS_R42_IRR_K50`, authorize only
  one paired multi-seed verification before S7 or variable-`N` promotion. There
  is no UNDERPOWERED branch or post-result threshold change.
- Expected wall clock: 15--30 minutes on the local CUDA device with 32 total
  concurrent environment workers.
- Prohibited: pure event relabeling, environment-specific intrinsic reward,
  task fields in the residual, duration or independent KEEP actions, new
  critic/team latent, threshold rescue, open roster, or variable `N`.
- Status source: `<run-root>/runner_status.txt`; decision source:
  `<run-root>/result/r42_irr_native_roster_residual.json`. Runner:
  `scripts/run_r42_native_roster_residual_local.ps1`.
- Result: `logs/r42_irr_native_roster_residual_320k_20260716_100824` completed
  valid `VALID_FAIL_R42_IRR_SERVICE`. M0 passed with no invalid reasons and the
  registered `320,000` steps, `200` outer updates, and `3,000` updates on every
  original optimizer path per arm. M1 passed: fixed win/key0/key1 were
  `0.98/1.00/0.98`. M2 failed: treatment win was `0.88`, and the paired
  treatment-minus-fixed win interval was `[-0.17,-0.03]`, below the strict
  `-0.10` noninferiority margin. M3 also failed: treatment discordance was
  `0.10`, full-synchronous SET was `0.90`, one agent had zero KEEP mass, and
  actual SET-target entropy was `0.6514`. Retire this direct residual without
  changing budget, seed, thresholds, reward, or model capacity.

### EXP-20260716-r41b-hmasd-alice-bob-full-source

- Causal edge: exact original HMASD source exposure -> positive Alice--Bob
  access -> a meaningful fixed-`k` checkpoint anchor for a later renewal-only
  temporal comparison.
- Boundary: freshly extract `ref/hmasd.tar`; preserve the original environment,
  reward, observations, horizon, network, `k=50`, `n_Z=2`, `n_z=4`, optimizer
  coefficients, PPO/discriminator epochs, evaluator, and fresh initialization.
- Exposure: seed 1, local CUDA, 32 rollout environments, 100-step episodes, 937
  outer updates, 2,998,400 environment transitions, and exactly 14,055 updates
  for each of high policy, low actor, low critic, `q_D`, and `q_d`.
- Comparator/evaluation: exact zero-step versus exact-final checkpoints on the
  same 100 deterministic reset streams. Final win, key0, and key1 rates must
  each be at least `0.50`; win entails completion of both key stages. The paired
  final-minus-zero win bootstrap uses 10,000 repetitions, seed `61041`, and a
  strict positive lower 95% bound.
- M0: exact source/argument/exposure boundary, CUDA, finite nonzero gradients,
  complete checkpoints, and stored/replayed high/low/global log-probability
  error `<=1e-6`.
- Branches: M0 failure -> repair only the concrete wrapper/evaluator defect;
  M0 plus access gates -> `PASS_R41B_SOURCE_ACCESS`; valid access failure ->
  `VALID_NO_ACCESS_R41B_FULL_SOURCE` and retire Alice--Bob as the current
  positive anchor without algorithm rescue. Either valid branch is submitted
  as automated GPT-5.6 Pro round 2/3 before further implementation.
- Prohibited: reward/intrinsic/environment/model/optimizer/entropy/threshold
  changes, favorable checkpoint selection, extra seeds, R29--R40 resurrection,
  R30, variable `N`, open roster, or a new team latent before this result.
- Status: `<run>/runner_status.txt`; result:
  `<run>/result/r41b_hmasd_alice_bob_full_source.json`.
- Result: `logs/r41b_hmasd_full_source_20260716_035300_retry2` completed valid
  `PASS_R41B_SOURCE_ACCESS`. M0 passed with replay errors all `0`, complete
  checkpoints, and 14,055 updates on every optimizer path. Final deterministic
  win/key0/key1 were `0.89/0.97/0.92`, zero-step win was `0`, and the paired
  final-minus-zero 95% interval was `[0.82975, 0.95]`. Three Pro rounds are
  complete. Source audit retired the final pure-categorical proposal as
  behaviorally identical; the next edge is R42-IRR.

### EXP-20260716-r41a-hmasd-alice-bob-local-pilot

- Question: before spending five seeds at the original 3M-step horizon, can the
  original HMASD source show a clear Alice--Bob learning signal locally?
- Boundary: freshly extract tracked `ref/hmasd.tar`; preserve its environment,
  network, reward, `k=50`, `n_Z=2`, `n_z=4`, optimizer coefficients, PPO epoch
  counts, and deterministic evaluator. No shaping or new intrinsic reward.
- Exposure: seed 1, local CUDA, 16 rollout environments, 100-step episodes,
  937 outer updates, 1,499,200 environment steps, and 14,055 steps for each
  high, low-actor, low-critic, `q_D`, and `q_d` optimizer.
- Resource correction: a 32-env attempt under
  `logs/r41_official_hmasd_20260716_013924` was stopped before optimizer updates
  after its workers occupied roughly 11 GB on a 20-logical-processor machine.
- Comparator: zero-step versus exact-final checkpoints on the same 100
  deterministic reset streams.
- M0: exact source/argument/exposure boundary, finite nonzero gradients, full
  checkpoint, CUDA, and stored/replayed log-probability error `<=1e-6`.
- M1: final win rate `>=0.50`.
- M2: 10,000 paired-reset bootstrap repetitions, seed `61041`; lower 95% bound
  for final-minus-zero win indicator must be `>0`.
- `PASS_R41A_HMASD_ALICE_BOB_LOCAL_PILOT`: M0--M2 pass. Use this evidence only
  to decide whether the full original-budget reproduction is still necessary.
- `NO_ACCESS_R41A_HMASD_ALICE_BOB_LOCAL_PILOT`: M0 passes but M1 or M2 fails.
  This single-seed half-step pilot cannot retire the source or authorize R30.
- `INVALID_R41A_HMASD_ALICE_BOB_LOCAL_PILOT`: repair only the concrete wrapper,
  counter, checkpoint, or evaluator defect and repeat the unchanged pilot.
- Status: `logs/<run>/runner_status.txt`; result:
  `logs/<run>/result/r41a_hmasd_alice_bob_local_pilot.json`.
- Result: `logs/r41a_hmasd_local_pilot_20260716_030013` at commit `a1ea76b`
  completed valid `NO_ACCESS_R41A_HMASD_ALICE_BOB_LOCAL_PILOT`. M0 passed with
  high/low/global replay error all `0.0`; every optimizer path completed 14,055
  nonzero finite-gradient steps. Exact zero-step and final win rates were both
  `0.0`; paired final-minus-zero was `0.0`, 95% CI `[0.0, 0.0]`. M1 and M2
  failed. Registered next action: review the original-source learning trace;
  do not retire the source route or authorize R30 from this pilot.

### EXP-20260715-r40-simple-spread-access

- Causal edge: public fixed-N cooperative task -> native-reward recurrent MAPPO
  access -> one credible substrate for a later fixed-k HMASD source gate. This
  is a Level-1 environment/access gate, not a skill or lifetime experiment.
- Upstream authorization: GPT-5.6 Pro accepted R40 after correcting the reward
  and outcome contract. The controller uses the question-authorized native
  discrete mode because the repository already provides exact Categorical
  sampling and replay; see `FOLLOWUP_DISPOSITION.md` in the R39 review folder.
- Environment: PettingZoo 1.24.3 `simple_spread_v3`, `N=3`, horizon 25,
  `local_ratio=0.0`, `continuous_actions=False`. Reward is the unmodified shared
  native negative closest-agent landmark-distance sum. No collision term,
  shaping, success bonus, intrinsic reward, or potential is added.
- Information/probability: actor receives only native 18-value local
  observations; centralized critic receives native 54-value state. Each agent
  samples one `Discrete(5)` action; rollout stores that integer and old
  Categorical log probability, and PPO teacher-forces the same action.
- Learner: ordinary constant-code/no-high recurrent MAPPO; no trainable skill or
  team code path and zero high, discriminator, process, posterior, or intrinsic
  updates/rewards. Low hidden size 64; recurrent sequence 25; sequence batch 64;
  five PPO epochs; Adam actor/critic learning rates `3e-4`; gamma `0.99`; GAE
  lambda `0.95`; clip `0.2`; value coefficient `0.5`; entropy coefficient
  `0.01`; max gradient norm `0.5`; ValueNorm enabled.
- Exposure: training seed 40041; local CUDA; 16 parallel environments; rollout
  25; exactly 200,000 environment steps and 500 outer updates. No checkpoint
  selection: evaluate the exact final checkpoint.
- Evaluation: four stochastic 64-episode blocks. Block `s` in
  `{40042,40043,40044,40045}` uses reset seeds `1000*s + episode`, episode
  `0..63`. Pair each reset with a uniform random `Discrete(5)` policy using
  independent action RNG seed 50041. Paired episode bootstrap uses 10,000
  repetitions and seed 60041.
- Primary estimand: `G_e=sum_{t=0}^{24} r_{e,t}`. M1 requires final MAPPO mean
  return `>=-35` and paired MAPPO-minus-random bootstrap lower 95% bound `>5`.
  M2 requires at least three of four MAPPO block means to be `>-35`.
- Gate calibration: before any R40 training outcome was observed, 256 random
  discrete episodes gave mean `-52.5873`, standard deviation `14.8004`, and
  90th percentile `-35.6879`; therefore the absolute and paired floors require
  a material departure from random behavior.
- M0: exact package/version/scenario/action/reward/information/seed/exposure;
  500 successful outer updates; finite losses/actions/returns; low behavior
  replay max error `<=1e-6`; nonzero finite low actor and critic optimizer
  updates; zero high/discriminator/process/posterior/intrinsic updates and zero
  numerical repairs; exact final checkpoint; 256 unique paired reset rows.
- Branches: M0 miss -> `INVALID_R40_IMPLEMENTATION`, repair only the concrete
  defect and rerun the unchanged contract. M0 pass plus M1/M2 pass ->
  `PASS_R40_SIMPLE_SPREAD_ACCESS`, register only native fixed-k HMASD on this
  exact substrate. M0 pass with M1 or M2 miss -> `VALID_FAIL_R40_ACCESS`, retire
  this substrate without rescue. No `MIXED` or `UNDERPOWERED` branch.
- Prohibited: continuous-action distribution work, reward or observation
  shaping, task-specific or generic intrinsic reward, skills, high controller,
  HMASD, KEEP/SET, lifetime, variable N/open roster, post-result threshold
  changes, tuning, seed/budget expansion, or best-checkpoint substitution.
- Expected wall clock: one local 200K CUDA run plus paired final evaluation;
  use the existing dedicated training monitor. Status source:
  `<run-root>/runner_status.txt`; decision source:
  `<run-root>/result/r40_simple_spread_access.json`.
- Terminal result: valid `VALID_FAIL_R40_ACCESS` at
  `logs/r40_simple_spread_access_200k_20260715_235500_retry4`. M0 passed;
  MAPPO/random means were `-52.392238/-52.587268`, paired difference `0.195030`
  with 95% interval `[-1.448355, 1.903356]`, and `0/4` blocks crossed `-35`.
  Decision: retire this substrate under the registered contract without rescue.

### EXP-20260715-r39-native-hmasd-toy-credit

- Causal edge: native HMASD's stored categorical team/agent chain can learn the
  four contextual role-free rosters when fixed primitives expose only the
  sampled individual skills to the environment.
- Upstream authorization: GPT-5.6 Pro accepted the fixed-N native toy route;
  use `two_timescale_role_free_actions` only, with two agents, identical
  constant local observations, centralized six-value slow/fast target state
  and clocks, and swap-invariant dense external reward.
- Profile: `n_Z=4`, `n_z=4`, hidden/embedding 32, coordinator dropout 0,
  `k0=5` full refresh, episode/rollout 40, three high PPO epochs, seed 39041,
  CUDA, sharded 4 workers x 4 environments, exactly 16 environments and
  12,800 environment steps (20 outer updates), 32 final episodes.
- Probability: native autoregressive factorization
  `pi_H(Z|x) pi_1(z1|x,Z) pi_2(z2|x,Z,z1)`; categorical sampling remains
  stochastic, and replay teacher-forces stored `Z,z1,z2` in canonical order.
- Credit: preserve native team/agent GAE, returns, values, ratios, and unified
  advantage normalization without formula changes. Old log probabilities are
  detached only at the PPO ratio boundary; replay team/agent max absolute
  error must be `<=1e-6`.
- Clock and execution: high action occurs only at every `k0=5` full-refresh
  block; no `KEEP`/`SET` or target-triggered checks. Fixed `z_i` primitives
  execute the four 2-D axes with zero low parameters, low credit, low updates,
  discriminator updates, intrinsic reward, or shaping.
- Metrics: evaluator-only mean `match`, `slow`, and `fast`; labels and match
  values never enter observations, rewards, advantages, sampling, gradients,
  or checkpoint selection. Thresholds are match `>=0.70`, slow `>=0.65`, and
  fast `>=0.65`.
- Checkpoint: fresh neutral initialization, no resume or best-checkpoint
  selection, and exact final checkpoint only. Result source is
  `result/r39_native_hmasd_toy_credit.json`.
- M0: exact contract, 20 successful outer updates, 60 high optimizer updates,
  replay error `<=1e-6`, finite metrics with zero numerical repairs, zero low
  trainable parameters and low/discriminator optimizer updates, and 32
  stochastic final episodes.
- Branches: M0 miss -> `INVALID_R39_NATIVE_TOY_CREDIT`; M0 pass with all three
  thresholds -> `PASS_R39_NATIVE_TOY_CREDIT_ANCHOR`; otherwise ->
  `VALID_FAIL_R39_NATIVE_TOY_CREDIT_ANCHOR`. No `MIXED` or `UNDERPOWERED`.
- Result: valid `VALID_FAIL_R39_NATIVE_TOY_CREDIT_ANCHOR` at
  `logs/hmasd_original/two_timescale_role_free_actions-r39_native_hmasd_toy/mode-train_cfg-config_r39_native_hmasd_toy_seed-39041_envs-16_rollout-40_k-5_steps-12800_backend-sharded_metrics-light_workers-4x4_mmode-light/20260715_221219/result/r39_native_hmasd_toy_credit.json`.
  M0 passed with 12,800 steps, 20 successful outer updates, 60 high optimizer
  updates, replay max `4.76837158203125e-7`, zero low/discriminator updates,
  zero numerical repairs, and 32 stochastic episodes. Mean match/slow/fast were
  `0.455078125/0.46484375/0.4453125`, below all three thresholds.
- Status: completed -- valid `VALID_FAIL_R39_NATIVE_TOY_CREDIT_ANCHOR`.
  Retire this fixed-N native-HMASD toy credit route; do not rescue it with
  threshold, budget, seed, optimizer, reward, label, roster, or checkpoint
  changes.
- Prohibited: open-roster/variable-N, `KEEP`/`SET`, R30/standalone policy,
  S7/UAV, new orchestration, checkpoint loading, intrinsic reward, environment
  shaping, label leakage, rerun, sweep, or budget expansion.

### EXP-20260715-r39-toy-native-categorical

- Causal edge: centralized two-timescale context -> one categorical final-skill
  action per agent -> incumbent equality realizes `KEEP` -> mixed per-agent
  skill ages while a learned skill-only low policy remains task-accessible.
- Comparator: mechanism-matched full-refresh control. Both arms have identical
  environment, categorical skill distribution, model shape, reward, seed,
  optimizer exposure, and final-skill support. The only intervention is that
  the adaptive arm interprets a sampled incumbent as `KEEP`; the control records
  every sample as `SET`, including `SET(current)`.
- Environment/information: two agents; constant identical four-value local
  observations; centralized six-value state contains slow and fast action
  targets plus their clocks; episode 40; `k0=5`; fast target changes each block
  and slow target each six blocks. Reward is the maximum over the two possible
  agent-to-target assignments of a bounded dense action-match objective. It is
  external task reward, not shaping or intrinsic reward, and defines no agent
  identity or fixed role.
- Model: hidden width 32, compact/team dimensions 16, process embedding 8,
  feedforward low actor, four skills, one deterministic representation code,
  three high/low PPO epochs. OPT losses, process/posterior losses, transition
  discriminator, topology/outcome probes, R29/R31, and every intrinsic reward
  path are off.
- Exposure: seed 39041; local CUDA; two arms concurrently; 16 environments per
  arm; rollout 40; exactly 12,800 environment steps and 20 outer updates per
  arm; 32 final stochastic evaluation episodes per arm. Expected wall clock is
  2-5 minutes.
- M0 validity: exact scenario/config/seed/budget and 20 updates; finite metrics;
  native categorical flag true in both arms; adaptive force-refresh false and
  control true; high and low replay maximum errors `<=1e-5`; exactly three low
  PPO steps per update; returns grouped over all 16 environments; tanh-squashed
  continuous actions; hidden width 32 and feedforward low policy; zero
  task-specific or generic intrinsic reward and no process/diagnostic optimizer
  objective.
- M1 access: both arms have final mean match score `>=0.70`, mean slow match
  `>=0.65`, and mean fast match `>=0.65`. Failure is
  `NO_ACCESS_R39_TOY_32`; it is an instrument/capacity result and has no
  temporal-algorithm meaning.
- M2 temporal mechanism: control full-sync `SET` rate is exactly 1 within
  `1e-6`; adaptive full-sync `SET` rate `<=0.75`; adaptive mixed-age fraction
  `>=0.25`; adaptive late data contain both a completed spell `<=4k0` and a
  spell surviving `>4k0`; and adaptive mean match is no more than `0.05` below
  control. These are lifetime/mechanism criteria, not an efficacy claim.
- Branches: M0 miss -> `INVALID_R39_TOY_IMPLEMENTATION`, repair only the
  concrete defect. M0 pass/M1 miss -> `NO_ACCESS_R39_TOY_32`, stop and redesign
  only the cheap positive-control instrument. M0/M1 pass/M2 miss ->
  `FAIL_R39_TOY_NATIVE_CATEGORICAL`, block S7 temporal integration and review
  this mechanism. M0/M1/M2 pass -> `PASS_R39_TOY_NATIVE_CATEGORICAL`, freeze
  the toy evidence and return to the already registered R39A source anchor.
- Prohibited: environment-specific intrinsic reward; task fields in the low
  actor; role labels; sparse success/contact logic; UAV/S7 launch before this
  result; threshold changes after reading outcomes; or claims about HMASD
  parity, sparse exploration, cooperation performance, or S7 efficacy.
- Status source: `<run-root>/runner_status.txt`; decision source:
  `<run-root>/result/r39_toy_native_categorical.json`.
- First-run disposition: `INVALID_R39_TOY_LOW_PPO` at
  `logs/r39_toy_native_categorical_12k8_20260715_173547`. A post-result audit
  showed feedforward returns crossing the 16 interleaved environments,
  `low_ppo_epochs=3` executing only once, and hard-clipped Normal actions being
  scored under the wrong density. Its match and lifetime metrics have no
  scientific meaning. The repaired rerun keeps the learned 32-wide model,
  12,800-step budget, seed, and decision thresholds unchanged. The slow clock
  is corrected from `4k0` to `6k0` so an optimal slow skill can satisfy the
  registered `>4k0` lifetime condition before its target changes.
- Repaired result: valid `NO_ACCESS_R39_TOY_32` at
  `logs/r39_toy_native_categorical_12k8_20260715_180156`. M0 passed with high
  replay `<=3.58e-7`, low replay `<=1.91e-6`, exactly three low PPO steps per
  update, all 16 return streams separated, and all intrinsic fields zero. Both
  arms remained below the access floor: adaptive/control match
  `0.445716/0.445838`, slow `0.439227/0.439260`, fast
  `0.452205/0.452415`. The result localizes the next question to high-level
  timing versus joint skill learning; it is not a temporal efficacy result.

### EXP-20260715-r39-toy-fixed-primitives

- Causal edge: centralized slow/fast context -> native categorical high policy
  selects and retains supplied executable skills -> mixed lifetimes preserve
  dense task access.
- Authorization/null: the valid learned-low access failure authorizes one
  high-controller positive control. Null: even exact primitives do not make the
  high controller task-accessible.
- Comparator: adaptive incumbent-as-`KEEP` versus mechanism-matched
  full-refresh `SET(current)`; identical high model, seed, reward, and action
  table `[(+x),(-x),(+y),(-y)]`.
- Budget: seed 39041; local CUDA; two concurrent arms; 16 env/arm; rollout 40;
  12,800 steps and 20 high updates/arm; 32 paired stochastic evaluations;
  expected wall clock 2-5 minutes.
- M0: exact config/budget; high replay `<=1e-5`; fixed schema `axis4_xy_v1` and
  exact shared table; zero low parameters, optimizer steps, losses, and grads;
  nonzero finite high gradients; all intrinsic fields zero.
- M1: both arms match `>=0.70`, slow `>=0.65`, and fast `>=0.65`.
- M2: control full-sync rate 1; adaptive full-sync `<=0.75`, mixed-age
  `>=0.25`, both `<=4k0` and `>4k0` spells, and adaptive match no more than
  `0.05` below control.
- Branches: M0 miss -> `INVALID_R39_TOY_IMPLEMENTATION`, repair only the direct
  defect. M1 miss -> `FAIL_R39_TOY_HIGH_ACCESS`, diagnose high context/credit
  and block S7. M1 pass/M2 miss -> `FAIL_R39_TOY_NATIVE_CATEGORICAL`, revise or
  retire timing semantics. M0-M2 pass -> `PASS_R39_TOY_FIXED_PRIMITIVES`, return
  to the deferred R39A anchor; this is not skill-discovery or S7 evidence.
- Result: valid `FAIL_R39_TOY_HIGH_ACCESS` at
  `logs/r39_toy_fixed_primitives_12k8_retry2_20260715_181752`. M0 passed with
  high replay error `2.38e-7`, zero low parameters/optimizer steps/losses, and
  all intrinsic fields zero. Adaptive and control produced identical match
  `0.4375`, slow `0.40625`, and fast `0.46875`, below M1. Adaptive did access
  mixed-age execution (`0.34464`) while control remained full-sync (`1.0`),
  but M1 blocks temporal interpretation. The registered next action is a
  focused high-context/high-credit diagnosis, not more capacity or S7 compute.
- Prohibited: intrinsic reward, task fields in the actor, learned low updates,
  role labels, threshold changes, model/budget expansion, or UAV launch.
- Status source: `<run-root>/runner_status.txt`; result source:
  `<run-root>/result/r39_toy_fixed_primitives.json`.

### EXP-20260715-r39-toy-direct-state

- Causal edge: explicit generic centralized state -> native categorical high
  actor selects the correct supplied skill roster -> dense toy access. This
  isolates high context encoding from the unchanged block-return credit path.
- Authorization/null: the completed fixed-primitive checkpoints have near
  chance correct-pair mass (`0.109-0.148`, chance `0.125`), joint-roster entropy
  `2.763-2.766` near `log(16)`, slow-sign TV `0.0158-0.0175`, and fast-sign TV
  `0.0046-0.0064`. Null: direct state remains unable to learn, locating the
  failure to high credit/optimizer exposure rather than compact encoding.
- Comparator: adaptive incumbent-as-`KEEP` versus mechanism-matched
  full-refresh, with the accepted compact-context run retained as the fixed
  diagnostic reference rather than rerun. Both arms use the same raw-state
  projection, zero team vector, fixed four-skill action table, and reward.
- Budget: seed 39041; local CUDA; two concurrent arms; 16 env/arm; rollout 40;
  12,800 steps and 20 outer high updates/arm; 32 paired stochastic evaluations;
  expected wall clock 2-5 minutes.
- M0: direct-state flag and dimensions `6 -> 8`, zero team context; high replay
  `<=1e-5`; nonzero actor-only policy and skill-head gradients; zero low
  parameters/updates/losses; exact fixed action table; all intrinsic fields
  zero.
- M1: both arms match `>=0.70`, slow `>=0.65`, and fast `>=0.65`.
- M2: control full-sync rate 1; adaptive full-sync `<=0.75`, mixed-age
  `>=0.25`, both short and `>4k0` spells, and adaptive match no more than `0.05`
  below control.
- Branches: M0 miss -> `INVALID_R39_TOY_IMPLEMENTATION`, repair only the direct
  defect. M1 miss -> `FAIL_R39_TOY_HIGH_CREDIT`, compare actor-only GAE and
  block-return gradients without enlarging the model or entering S7. M1 pass
  but M2 miss -> `FAIL_R39_TOY_NATIVE_CATEGORICAL`, revise/retire temporal
  semantics. M0-M2 pass -> `PASS_R39_TOY_DIRECT_STATE`, accept context
  localization only and decide the smallest generic context repair before the
  deferred R39A anchor.
- Prohibited: environment-specific intrinsic reward, task-field shaping, low
  learning, model enlargement, threshold changes, or S7/UAV launch before the
  result.
- Status source: `<run-root>/runner_status.txt`; result source:
  `<run-root>/result/r39_toy_direct_state.json`.
- First launch disposition: `INVALID_R39_TOY_IMPLEMENTATION` at
  `logs/r39_toy_direct_state_12k8_20260715_184224`. R30 contract normalization
  rewrote the declared zero bridge to `deterministic_expected`; the direct
  helper still supplied a zero team vector, but M0 correctly rejected the
  manifest mismatch. Retry keeps the seed, budget, thresholds, and algorithm
  unchanged and only preserves `team_bridge_type=none` for this fail-closed
  direct-state lane.
- Valid retry result: `FAIL_R39_TOY_HIGH_CREDIT` at
  `logs/r39_toy_direct_state_12k8_retry2_20260715_184646`, commit `1200bdf`.
  M0 passed with replay error `0`, zero low parameters/updates/losses, and all
  intrinsic fields zero. Adaptive/control match were both `0.421875` (slow
  `0.40625`, fast `0.4375`). Mean actor-only policy gradient norms were
  `0.09242/0.09267`; skill-head-only norms were `0.06422/0.06451`. Adaptive
  reached mixed-age fraction `0.34196` while control remained full-sync, but M1
  blocks temporal interpretation. The next diagnostic compares SMDP-GAE and
  centered block-return actor gradients without applying the latter.

### EXP-20260715-r39-toy-high-credit-diagnostic

- Question: does the actor gradient used by R30 SMDP-GAE point in the same
  direction as the immediately attributable discounted block-return gradient,
  or is the high controller receiving conflicting/unstable credit?
- Scope: the same direct-state, zero-team-context, four fixed primitive toy;
  no model, reward, buffer, or optimizer change. The centered and standardized
  block return is used only with `autograd.grad` and is never applied to model
  parameters.
- Budget: seed 39041; local CUDA; adaptive and full-refresh arms in parallel;
  16 env/arm, rollout 40, 1,920 steps and three high optimizer steps/arm; one
  paired stochastic evaluation episode. Task score is not interpreted.
- Read: per update, raw GAE/block-return standard deviations, total actor and
  skill-head gradient norms, and GAE-vs-block gradient cosines. Skill-head
  direction is primary. Replay must remain `<=1e-5`, low parameters/updates
  remain zero, and intrinsic fields remain zero.
- Branches: absent block-return variance/gradient means the immediate block
  carrier cannot diagnose optimizer exposure. Nonpositive or mixed skill-head
  cosine means high credit is conflicting/unstable. Three positive cosines in
  both arms with nonzero, comparable norms localize the next causal test to the
  single high optimizer step per outer update. None of these branches
  authorizes model enlargement, intrinsic reward, or S7/UAV compute.
- Status source: `<run-root>/runner_status.txt`; result source:
  `<run-root>/result/r39_toy_high_credit_diagnostic.json`.
- Result: completed at
  `logs/r39_toy_high_credit_diag_1920_20260715_185721`, commit `ef9a34d`.
  Replay was exact, low parameters/updates and intrinsic fields remained zero.
  Adaptive/control mean skill-head GAE norms were `0.06013/0.06006`, versus
  block-return norms `0.08092/0.08100`; mean cosines were `0.50266/0.50412`.
  Every per-update skill-head cosine was positive (`0.392-0.594`). This closes
  conflicting GAE direction as the immediate explanation and selects explicit
  high optimizer exposure as the next toy causal edge.

### EXP-20260715-r39-toy-high-exposure

- Causal edge: reusing the same valid on-policy high batch for three PPO epochs
  -> enough high optimization to learn the correct supplied roster -> dense toy
  access. Comparator is one epoch; both arms are full-refresh and differ only
  in `r30_high_ppo_epochs`.
- Model/reward: direct 6D centralized state padded to 8D, high hidden 32, four
  fixed axis primitives, zero low parameters and updates, zero intrinsic
  reward. No environment or model change.
- Update contract: SMDP-GAE, old likelihoods, masks, clocks, and value targets
  are fixed once per collected batch. ValueNorm updates once. Every PPO epoch
  recomputes current context, value, token likelihood, ratio, entropy, and loss.
  Replay parity is measured only before epoch 1; prototype/state clocks advance
  once per outer update.
- Budget: seed 39041; local CUDA; epoch-1 and epoch-3 arms in parallel; 16
  env/arm, rollout 40, 12,800 steps and 20 outer updates/arm; 32 paired
  stochastic evaluation episodes.
- M0: exact epoch counts `1/3`; epoch-0 replay `<=1e-5`; one ValueNorm update
  per batch; finite last-epoch ratio/clip/KL; identical parameter counts; low
  parameters/updates/losses and intrinsic fields all zero.
- M1: epoch-3 match `>=0.70`, slow and fast match each `>=0.65`, and epoch-3
  minus epoch-1 match `>=0.10`.
- Branches: M0 miss -> repair the concrete implementation only. M1 pass ->
  test adaptive categorical retention with three high epochs on the toy. M1
  miss -> retire optimizer underexposure as the immediate cause and inspect the
  high action objective; do not add epochs, capacity, intrinsic reward, or S7
  compute.
- Status source: `<run-root>/runner_status.txt`; result source:
  `<run-root>/result/r39_toy_high_exposure.json`.
- Result: valid `FAIL_R39_TOY_HIGH_EXPOSURE_3` at
  `logs/r39_toy_high_exposure_12k8_20260715_191019`, commit `b805abc`. The
  epoch-1 arm scored match/slow/fast `0.421875/0.40625/0.4375`; epoch 3 scored
  `0.46875/0.46875/0.46875`. The match gain `0.046875` missed `0.10`, and the
  treatment missed all access floors. Exact optimizer steps were `1/3`, replay
  error was zero, ValueNorm updated once, and the epoch-3 arm had zero clipping
  with mean last-epoch KL `6.12e-6`. More epochs are not authorized.

### EXP-20260715-r39-toy-block-credit

- Causal edge: use the immediately attributable discounted external block
  return as the actor's score-function weight -> learn the correct supplied
  joint roster -> dense toy access. This asks whether SMDP-GAE noise, rather
  than policy factorization, blocks learning.
- Comparator/treatment: both are full-refresh, direct-state, fixed-primitives,
  high hidden 32, and `r30_high_ppo_epochs=3`. The comparator uses standardized
  SMDP-GAE; the treatment uses the same batch's standardized discounted
  `block_reward`. Both critics retain the original SMDP value target.
- Reward boundary: only the existing external reward is used. No intrinsic
  reward, task field, oracle label, shaping term, environment-specific formula,
  or low update is introduced. Block credit is a positive-control estimator,
  not authorization to replace long-horizon credit.
- Budget: seed 39041; local CUDA; arms parallel; 16 env/arm, rollout 40, 12,800
  steps and 20 outer updates/arm; 32 paired stochastic evaluation episodes.
- M0: exact `smdp_gae/block_return` actor modes; three high optimizer steps and
  one ValueNorm update per batch; epoch-0 replay `<=1e-5`; finite last-epoch
  ratio/clip/KL; identical model sizes; low parameters/updates/losses and all
  intrinsic fields zero.
- M1: block-return match `>=0.70`, slow and fast match each `>=0.65`, and
  block-return minus SMDP-GAE match `>=0.10`.
- Branches: PASS localizes the obstruction to high credit estimation but does
  not promote myopic block credit to the temporal algorithm. FAIL retires
  high-credit estimation as the immediate explanation and selects joint-roster
  policy factorization for inspection. Neither branch authorizes more epochs,
  larger models, intrinsic reward, or S7/UAV compute.
- Status source: `<run-root>/runner_status.txt`; result source:
  `<run-root>/result/r39_toy_block_credit.json`.
- Result: valid `FAIL_R39_TOY_BLOCK_CREDIT` at
  `logs/r39_toy_block_credit_12k8_20260715_192020`, commit `22a3162`. Both arms
  scored match/slow/fast `0.46875`, so treatment gain was exactly zero. M0
  confirmed actor modes `smdp_gae/block_return`, three high steps, one
  ValueNorm update, replay error zero, zero clipping, and no intrinsic fields.
  This retires actor-advantage source as the immediate explanation and selects
  an exact factorization-capacity diagnostic before any new learning mechanism.

### EXP-20260715-r39-toy-joint-factorization

- Question: can the exact R39 native categorical autoregressive policy
  represent and learn the role-free contextual mapping when joint-roster credit
  is supplied without sampling noise?
- Instrument: the same high hidden 32 policy, direct 8D compact context, zero
  team vector, canonical two-token factorization, and all 16 final rosters.
  Eight contexts cover four slow/fast target-sign combinations under two active
  previous rosters. No environment step, reward, critic, low policy, or
  intrinsic mechanism is used.
- Optimization: seed 39041, Adam `3e-4`, 2,000 exact likelihood steps. Objective
  is negative log probability mass on the two correct unordered orientations.
  Oracle labels are diagnostic-only and cannot enter the training algorithm.
- M0: joint probabilities sum to one within `1e-6`, initial gradient norm
  `>1e-8`, finite loss, same 2,512-parameter high policy shape.
- M1: minimum correct unordered-pair mass across eight contexts `>=0.90`.
- Branches: PASS closes policy expressivity/factorization as the immediate
  defect and selects sampled joint-credit variance for the next algorithmic
  edge. FAIL requires repairing the factorization before another RL run. No
  branch authorizes oracle labels, intrinsic reward, a larger model, or S7.
- Result source: `logs/r39_toy_joint_factorization_*/result/`.
- Result: valid `PASS_R39_JOINT_FACTORIZATION_CAPACITY` at
  `logs/r39_toy_joint_factorization_20260715_193034`, commit `fd29e3e`.
  Minimum/mean correct unordered-roster mass was `0.999487/0.999670`, final
  loss `0.000330`, and maximum probability-sum error `3.58e-7`. The initial
  gradient norm was `0.5240`; the model had exactly 2,512 parameters. This
  establishes capacity only for the eight registered contexts and selects
  sampled-credit alignment; it does not authorize oracle supervision.

### EXP-20260715-r39-toy-joint-credit-alignment

- Question: does the sampled high-level action receive a correctly aligned raw
  external block return before PPO estimation and normalization?
- Instrument: unchanged direct-state, fixed-primitives, full-refresh, high3
  block-return toy. At each decision row, reconstruct the final roster and use
  the stored direct-state target signs only to classify it as correct or
  incorrect. Classification is diagnostic-only and cannot affect reward,
  advantage, gradient, or sampling.
- Budget: seed 39041, 16 environments, 1,920 environment steps (three outer
  updates), CUDA. The model remains high-32/2,512 parameters with zero trainable
  low-policy parameters and no intrinsic term.
- M0: exact high replay, three high optimizer steps per update, block-return
  actor mode, correct and incorrect sampled rows both observed, finite metrics.
- M1: pooled raw discounted block return for correct rosters exceeds incorrect
  rosters, and the same ordering remains after the registered actor-weight
  standardization. This is a direction check, not an efficacy threshold.
- Branches: positive separation confirms action-to-reward alignment and selects
  a lower-variance, environment-agnostic joint-credit estimator. No separation
  requires fixing the clock/reward assignment before another training change.
  Neither branch authorizes toy-label reward, intrinsic shaping, a larger model,
  or S7/UAV compute.
- Result source: the three `train_updates.csv` rows from the single run.
- Result: valid `PASS_R39_JOINT_CREDIT_ALIGNMENT` at
  `logs/r39_toy_joint_credit_alignment_1920_20260715_194904_retry3`, commit
  `c6d02e3`. Three updates contained 32 correct and 352 incorrect sampled
  rosters. Pooled correct/incorrect raw discounted block returns were
  `4.900994/1.816988`; corresponding standardized actor weights were
  `+2.120720/-0.192793`. Every update used block-return actor mode, exactly
  three high optimizer steps, and zero replay error. Reward timing and storage
  are aligned; the remaining failure is the standalone shared joint-credit
  learner, not model capacity, context, low primitives, or intrinsic reward.

### EXP-20260715-r39a-current-fixed-hmasd-anchor

- Causal edge: current-interface native fixed-`k` HMASD -> stable positive
  S7-S1 service access. This is a Level-1 source-anchor gate, not an async
  algorithm test. The null is failure to clear the registered service floors;
  there is no treatment arm or causal-comparison claim.
- Upstream authorization: GPT-5.6 Pro returned `MODIFY R39-S7` and selected a
  strict serial route: R39A positive anchor before any R39B implementation.
  The raw response and accepted controller disposition are under
  `docs/external-review/gpt5_6_pro/20260715_r38_cts_access_result/`. Package
  preparation is authorized; the formal launch still requires the user's
  explicit approval.
- Algorithm/environment: native `hmasd_original`, S7-S1 interface v3, eight
  agents, four-dimensional tanh-Gaussian actions, `n_Z=n_z=6`, fixed `k=10`,
  episode and rollout length 500, strict HMASD alignment, and the current
  native recurrent discoverer, ValueNorm, high/low/discriminator losses and
  update order. Horizon, process exploration, OPT, team bridge, HA-CTSE, and
  R30 are disabled.
- Reward/information boundary: external arm C is reapplied before final
  `qos_fixed_safety`; `use_graph_pbrs=false` and all other shaping is zero.
  Existing native `q_D/q_d` rewards remain unchanged. No new intrinsic reward,
  classifier, latent, scheduler, process scorer, task identity, or
  environment-specific signal is added.
- Probability correction: stored `Z,z_{<i}` are teacher-forced during PPO
  replay and high-policy Transformer dropout is zero. Categorical skill
  sampling remains stochastic. This closes the registered joint-likelihood
  contract rather than changing its objective.
- Exposure: train seed 39039, CUDA, 32 parallel environments, 100 outer
  updates, exactly 1,600,000 environment steps, and the exact final checkpoint;
  no best checkpoint, early stop, append, or extra seed. Final evaluation uses
  100 stochastic 500-step episodes with reset seeds 139039..139138 and policy
  RNG seed 239039. Whole-episode percentile bootstrap uses 10,000 repetitions
  and seed 40039039. Expected cloud wall clock is 8-18 hours including final
  evaluation.
- M0 implementation validity: exact interface/reward/algorithm/exposure;
  exactly 100 successful updates; CUDA with no silent fallback; stored team
  and agent joint-action maximum replay log-probability error `<=1e-6`;
  complete current policy/training interfaces, native modules, optimizers and
  normalizer state; finite parameters/actions/values/losses; zero numerical
  repairs; and no HA-CTSE/R30 path.
- M1 positive anchor: using per-step native `coverage_ratio`, episode-bootstrap
  `LCB95(C_mean)>=0.90`, `LCB95(C_full)>=0.50`, and
  `UCB95(F_zero)<=0.10`, where full means coverage `>=1-1e-6` and a zero
  episode has maximum coverage `<=1e-6`.
- Branches: M0 miss -> `INVALID_R39A_IMPLEMENTATION`, repair only the concrete
  wiring defect and repeat this exact contract. M0 pass plus M1 pass ->
  `PASS_R39A_CURRENT_FIXED_HMASD_ANCHOR`, freeze the exact checkpoint/manifest
  and only then register R39B. M0 pass plus any M1 miss ->
  `VALID_FAIL_R39A_NO_CURRENT_HMASD_ANCHOR`, retire R39 temporal treatment on
  this substrate.
- Prohibited: R39B implementation before PASS; old-checkpoint partial loading;
  standalone R30; intrinsic/shaping rescue; tuning, seed or budget expansion;
  best-checkpoint substitution; threshold changes; and interpreting a valid
  failure as evidence against asynchronous lifetime learning or HA-CTSE.
- Status source: `<run-root>/runner_status.txt`; training exposure source:
  `<run-root>/train/final_training_summary.json` and exact final checkpoint;
  decision source: `<run-root>/result/r39a_fixed_hmasd_anchor.json`.

### EXP-20260715-r37-actor-visible-identity-access

- Causal edge and authorization: R35 found zero sparse access under both
  constant-code recurrent MAPPO and reward-pure R30. R36 then expanded natural
  coarse joint-position coverage `3.8552x` without one collection, proving that
  undirected state breadth is not the missing access carrier. GPT-5.6 Pro
  audited both the valid R36 failure and the environment information contract,
  then selected one upstream instrument gate:
  `actor-visible current task identity -> removal of hidden-information
  bottleneck -> positive sparse collection access`. The accepted controller
  disposition is under
  `docs/external-review/gpt5_6_pro/20260715_r36_aem_access_result/`.
- Baseline level and arms: both arms are Level-0 constant-code recurrent MAPPO
  with identical actor/critic shapes, optimizer exposure, and no high rows or
  updates. `identity_visible` receives the current true task identities;
  `identity_masked` is the original actor-information control.
- Observation/information boundary: both actors receive an identical 16-value
  vector: the original 12 Alice--Bob observation values followed by two
  active-plate and two active-target slots. Treatment fills those slots with
  the current true one-hots; control fills all four slots with zeros. This
  matches input width and parameter count while changing only current identity
  information. The existing 19-value centralized critic state is bitwise the
  same in both arms. Neither actor receives clocks, contacts, collection or
  progress state, rewards, future state, distance, or oracle actions.
- Reward/gradient boundary: environment reward remains the exact
  collection-only sparse reward. There is no intrinsic bonus, potential,
  shaping, skill, high controller, KEEP/SET, posterior, classifier, or latent
  path. Only the existing constant-code low actor and centralized critic
  update through their normal recurrent PPO/value losses.
- Initialization and exposure: seed `38031`; one common neutral zero-step
  16-input checkpoint; local CUDA; both arms run concurrently with 16
  subprocess environments, rollout 80, 320,000 environment steps, 250 low
  updates, five PPO epochs, recurrent sequence length 10/batch 64, and the
  existing Adam rates and clipping. Final evaluation uses 64 paired stochastic
  80-step episodes with identical reset seeds. Use 10,000 paired episode
  bootstraps with seed `40038031`. Expected wall clock is 1--2 hours.
- M0 validity: exact shared initialization, parameter shapes, environment
  transitions, optimizer/update exposure, evaluation seeds, and recurrent
  state contract; treatment identity slots equal the environment's active
  plate/target at every actor step; control identity slots are always zero;
  critic inputs are unchanged and equal across arms; external rewards are
  exactly sparse and equal before policy-dependent transitions; no shaping,
  intrinsic reward, skill/high update, or forbidden actor field is active. Any
  concrete miss is `INVALID_R37_IMPLEMENTATION` and authorizes only repair of
  that defect under this unchanged contract.
- M1 access floor: treatment has at least 10/64 evaluation episodes with a
  collection, cycle-success mean `>=0.05`, and a treatment-minus-control paired
  collection-indicator bootstrap 95% CI lower bound above zero.
- M2 sparse task evidence: treatment mean collection-only evaluation reward is
  strictly positive and at least one cycle is completed. These remain access
  checks, not algorithm-efficacy metrics.
- M3 stability: treatment zero-cycle fraction is `<0.90`.
- Branches: M0 plus M1--M3 gives `PASS_R37_ACCESS`, establishing only that the
  repaired Alice--Bob observation contract has a positive access floor and
  authorizing design/registration of one ordinary algorithm comparison there.
  Any valid M1--M3 miss gives `FAIL_R37_ACCESS`; retire sparse Alice--Bob as the
  current algorithm-comparison gate and specify a replacement benchmark's
  observation, horizon, and ordinary-policy access floor before more algorithm
  work. `INVALID_R37_IMPLEMENTATION` repairs only the concrete implementation
  defect. An operational crash retries only its failed path. There is no
  `MIXED`, `UNDERPOWERED`, threshold, seed, step, or budget-expansion branch.
- Prohibited while open: task reward or distance/progress/contact shaping;
  clocks, contacts, collection/progress state, reward fields, future state, or
  oracle actions in the actor; task-identity information beyond the current
  active plate/target one-hots; skills, options, latents, hierarchy, intrinsic
  reward, R29--R36 mechanisms, identity/noise menus, coefficient or optimizer
  sweeps, extra seeds/steps, lower thresholds, or claims about algorithm
  improvement, cooperation, hierarchy, HMASD/S7 parity, or paper efficacy.
- Status sources after launch: `<run-root>/runner_status.txt` and the single
  scientific decision file
  `<run-root>/result/r37_actor_visible_identity_access.json`.
- Result and decision: completed at commit `67cadc8` as valid
  `FAIL_R37_ACCESS`. M0 passed. `identity_visible` had 10/64 collection/cycle
  episodes, cycle mean `0.01953125`, sparse reward `0.15625`, zero-cycle
  fraction `0.84375`, and coverage `0.035275`; `identity_masked` had zero access,
  zero reward, zero-cycle fraction `1.0`, and coverage `0.021975`. The paired
  collection interval was `[0.078125, 0.25]`; the collection-count and CI
  requirements, M2, and M3 passed. M1 failed only because cycle success stayed
  below `0.05`. Per the registered branch, this environment is retired as the
  current algorithm-comparison gate; no rerun, threshold/budget expansion, or
  algorithm promotion is authorized.

### EXP-20260715-r36-aem-access

- Causal edge and authorization: R35 validly established that matched trained
  constant-code MAPPO and reward-pure R30 both failed the positive-access floor.
  GPT-5.6 Pro selected one non-skill access-first route: task-generic
  joint-position novelty should expand reachable visitation and thereby create
  first sparse collection access. The controller accepts that edge with the
  exact modifications in `DISPOSITION_CORRECTION_1.md`.
- Baseline hierarchy and arms: both arms are Level-0 constant-code recurrent
  MAPPO with identical low actor/centralized critic shapes and no high rows or
  updates. `aem_joint_novelty` adds one detached shared episodic joint-cell
  novelty bonus; `constant_code_mappo` receives sparse external reward only.
- Novelty contract: for each vector environment, map the two normalized agent
  positions by direct arithmetic into a fixed `5 x 5 x 5 x 5 = 625` table.
  With the pre-increment per-episode count `N_e,t(c)`, use
  `b_e,t = 1 / (80 * sqrt(N_e,t(c) + 1))` and
  `r_train_e,t = r_env_e,t + b_e,t` for both agents. Reset the table only when
  that environment resets. Counts/bonus are detached collector scalars, never
  actor/critic inputs. No hash, potential, learned predictor, coefficient, or
  task field is used.
- Initialization/exposure: seed `37031`; one common neutral zero-step
  constant-code checkpoint; CUDA; both arms concurrently use 16 subprocess
  environments, rollout 80, 320,000 environment steps, 250 low updates, five
  low PPO epochs, recurrent sequence length 10/batch 64, existing Adam rates
  and clipping. Expected local wall clock is 30--60 minutes.
- Evaluation/inference: 64 paired stochastic 80-step episodes per arm with the
  same reset seeds; record collection indicator, normalized cycle success,
  zero-cycle flag, and 625-cell joint coverage. Use 10,000 paired episode
  bootstraps with seed `40037031`.
- M0 validity: exact shared initialization/shapes/exposure/evaluation; constant
  skill/team code zero and zero high rows in both arms; treatment bonus equals
  the registered pre-increment per-environment episodic count formula and uses
  position cells only; control has zero bonus; both retain exact sparse external
  reward; no other intrinsic/shaping path is active. Any concrete miss is
  `INVALID_R36_AEM_IMPLEMENTATION` and authorizes only its repair.
- M1 access: treatment cycle-success mean `>=0.05`, at least 10/64 treatment
  episodes with a collection, and paired treatment-minus-control collection
  indicator mean `>=0.10` with 95% CI lower bound above zero.
- M2 visitation carrier/safety: treatment/control mean joint-coverage ratio
  `>=1.50` with paired difference 95% CI lower bound above zero, and treatment
  zero-cycle fraction `<0.90`.
- Branches: M0+M1+M2 gives `PASS_R36_AEM_ACCESS`, authorizing one ordinary
  sparse-training comparison but no hierarchy/efficacy claim. A valid M1 miss
  gives `FAIL_M1_RETIRE_R36_AEM`; retire this exact episodic joint-count bonus.
  M1 pass with M2 miss gives `FAIL_M2_ACCESS_WITHOUT_CARRIER`; do not promote
  the claimed novelty mechanism. An operational crash retries only its failed
  path. There is no UNDERPOWERED, tuning, threshold, seed, or budget branch.
- Prohibited: task reward shaping or task fields; global cross-episode count;
  learned novelty models; skill/latent/posterior/effect/roster inputs; R30 high
  training; alternate cell grids, bonus functions/scales, sweeps, automatic
  expansion, or claims about general exploration, cooperation, HMASD/S7 parity,
  hierarchy value, or paper efficacy.
- Status source: after launch, the runner owns `runner_status.txt`; the only
  scientific decision source is its single
  `result/r36_aem_access.json`.
- Result: valid `FAIL_M1_RETIRE_R36_AEM`. Both arms completed 320K steps, 250
  low updates, and 64 stochastic evaluations. Treatment/control coverage ratio
  was `3.855204`; paired difference CI was `[0.0454, 0.049175]`. Treatment and
  control each had zero collection episodes, zero cycle success, and zero-cycle
  fraction one. The novelty mechanism changed visitation but failed its access
  carrier; no tuning, rerun, or expansion is authorized.
- External audit: GPT-5.6 Pro found no estimand-changing defect, accepted the
  valid failure, and selected the separately registered R37 actor-visible
  task-identity access gate. Raw response and disposition are in
  `docs/external-review/gpt5_6_pro/20260715_r36_aem_access_result/`.

### EXP-20260715-r35-sparse-mappo-reset

- Causal question and authorization: R29--R34 failed to identify, amplify,
  compose, or relabel a useful persistent skill codebook. GPT-5.6 Pro accepted
  closure of the current intrinsic skill-formation program and selected a
  sparse recurrent MAPPO reset. The controller rejects its trained-versus-
  frozen comparison and authorizes this single trained-versus-trained baseline
  gate: under matched low optimization, is an observation/history-only policy
  noninferior to reward-pure R30 on sparse Alice--Bob?
- Baseline hierarchy and arms: `constant_code_mappo` is the Level-0 baseline.
  It retains the same four-column low MLP/FiLM/RNN/action head and centralized
  recurrent critic tensors as R30, but every agent and step receives dummy
  skill `0` and team code `0`; no high decision, row, gradient, or optimizer
  step occurs. Constant conditioning makes the executed policy
  `pi(a_i | o_i, h_i)`. `reward_pure_r30` is the Level-2 mechanism comparator
  with active autoregressive KEEP/SET and the same low policy. Only the sparse
  external collection reward enters either policy or value update.
- Initialization and exposure: create one zero-environment-step R30 checkpoint
  at seed `36031` and strictly load it into both arms. This is a shared neutral
  random initialization, not the trained adaptive-R30 checkpoint. Each arm
  uses CUDA, 16 sub-process environments, rollout length 80, 320,000
  environment steps, 250 rollout/low updates, low PPO epochs 5, recurrent
  sequence length 10, sequence batch 64, and the existing actor/critic Adam
  learning rates and clipping. Both arms run concurrently. R30's additional
  high updates are an intended treatment difference and must be reported
  separately. Expected local wall clock is 4--8 hours.
- Evaluation and inference: after training, run 64 stochastic 80-step episodes
  per arm using identical reset seeds `seed+100000+episode`; resets are paired,
  but action random numbers are not claimed common because R30 also samples
  high tokens. Per episode record normalized cycle success
  `targets_completed/8`, 625-cell joint-position coverage, and a zero-cycle
  flag. Bootstrap 10,000 paired episodes with seed `40036031`.
- M0 validity: both arms load the same zero-step checkpoint; each reaches
  exactly 320,000 steps, 250 low updates, and 64 evaluation episodes; the
  constant arm executes only skill/team code zero and has zero high decision
  and high optimizer rows; both use identical low shapes and finite
  checkpoints; every evaluation episode satisfies sparse reward equals target
  collections and all intrinsic/shaping reward-applied counts are zero. A
  concrete miss is `INVALID_R35_IMPLEMENTATION`; repair only that defect.
- M1 positive access: before noninferiority is interpreted, at least one arm's
  mean normalized cycle success must be `>=0.05`, and at least 10 of the 64
  paired reset indices must contain one or more collections in either arm.
  Otherwise the result is `NO_ACCESS_R35_UNRESOLVED`: do not replace the
  baseline, expand this run, or infer a hierarchy result.
- M2 noninferiority: with `D = constant_code_mappo - reward_pure_r30`, require
  the paired 95% CI lower bound for cycle success to exceed `-0.10`, the paired
  CI lower bound for normalized joint-position coverage to exceed `-0.05`, and
  the paired CI upper bound for zero-cycle fraction to be below `+0.10`.
  Passing M0, M1, and all three margins is
  `PASS_R35_MAPPO_NONINFERIOR`, authorizing constant-code recurrent MAPPO only
  as the Alice--Bob optimization baseline for the next research question.
- Other branches: if the cycle-success CI upper bound is below `-0.10`, the
  coverage CI upper bound below `-0.05`, or the zero-cycle CI lower bound above
  `+0.10`, return `FAIL_R35_MAPPO_INFERIOR`; R30 has a toy/budget-specific
  advantage, but no retired skill objective reopens. Any remaining valid
  partial pattern is `MIXED_R35_NO_REPLACEMENT`; retain both as references and
  request the next non-skill research question without an automatic rerun.
- Prohibited: trained-R30 initialization, trained versus frozen causal claims,
  `n_z=1` capacity changes, intrinsic/semantic/effect/team rewards, shaping,
  classifiers, OPT actor input, communication, another scheduler, sweeps,
  threshold revision, automatic seed/budget expansion, and claims about
  general hierarchy value, HMASD/S7 parity, cooperation, or paper efficacy.
- Status source: after launch, the runner owns `runner_status.txt`; the only
  scientific decision source is
  `logs/r35_sparse_mappo_reset_320k_20260715_013000_retry4/result/r35_sparse_mappo_reset.json`.
- Operational transition: two pre-training attempts failed while atomically
  renaming the status and worker-exit files on this Windows host. Commits
  `30774ed` and `b372000` changed only those writes to direct replacement. A
  third pre-training attempt then exposed sandbox-denied Windows spawn/Pipe
  creation (`WinError 5`) before either arm wrote an update. Retry4 launched
  the identical committed pair outside the sandbox and entered parallel
  training; no scientific parameter changed across these operational retries.
- Result: M0 passed. Constant-code MAPPO and reward-pure R30 each completed
  320,000 steps, 250 low updates, and 64 stochastic evaluation episodes from
  their shared zero-step checkpoint. Both had cycle success `0`, zero-cycle
  fraction `1`, and zero episodes with a collection. The registered access
  floor therefore failed before noninferiority could be interpreted. Constant
  minus R30 joint-position coverage was `0.001375`, 95% CI
  `[0.000550, 0.002200]`; this is descriptive only under no access.

### EXP-20260714-r34-bhmd-gate

- Causal edge and authorization: R29--R33 show that distinguishing, directly
  amplifying, or reselecting the existing labels does not create material
  persistent primitives. R34 asks whether unlabeled focal trajectories can be
  partitioned into balanced hindsight modes and distilled into the low actor so
  that numerical skills causally reproduce those modes. This changes codebook
  construction rather than adding another scorer for the old codebook.
- Source: the frozen adaptive-R30 Alice--Bob checkpoint used by R32/R33. Seed
  `34031` collects 32 stochastic 80-step episodes: 24 train and eight heldout.
  Each of the 384 train block-agent rows contributes the focal agent's ten-step
  normalized displacement sequence, shape `[20]`. Train-only normalization is
  frozen; deterministic exact-balanced `K=4` clustering assigns 96 rows per
  mode. A train-only Hungarian permutation aligns prototype names to old
  numerical skills; old-z overlap/NMI is diagnostic only.
- Arms and null: `frozen_source` receives no update; `real_modes` distills the
  true hindsight sequence; `episode_sequence_sham` uses a deterministic
  per-agent maximum-Hamming no-self permutation of whole eight-block label
  sequences. The latter preserves label counts, sequence multiset, block
  positions, and run lengths while breaking trajectory-to-label attribution.
  Maximum-Hamming agreement above `0.50` is a valid degenerate-label M1 failure,
  not an implementation repair branch.
- Offline optimization: real and sham each replay all 48 train agent-episodes
  from zero actor hidden state for ten epochs, batch size eight, six batches per
  epoch and exactly 60 Adam calls (`lr=3e-4`, gradient clip `0.5`). The loss is
  detached-action recurrent behavior NLL under the hindsight skill sequence.
  Only `low.actor_film`, `low.actor_rnn`, and
  `low.actor_act.action_out.fc_mean` receive gradient. Actor base/log-std,
  critic, full R30 high policy/value, OPT/bridge, all posteriors, reward, GAE,
  and normal PPO remain outside the objective.
- Heldout intervention: 64 heldout block contexts x two focal agents x four
  forced skills x two independent replicas x ten steps = 10,240 steps per arm.
  The three arms share branch seeds; skills share CRN within each
  context/replica. The modified focal hidden is recomputed from episode start
  over the stored source observation/skill prefix; the teammate uses the
  frozen source actor. All descriptor and SNR reads use the frozen standardized
  train space with epsilon `1e-8`.
- Natural transport: 64 paired stochastic 80-step episodes per arm = 5,120
  steps per arm. High parameters and the R30 check clock are identical, but
  realized KEEP/SET paths may diverge through changed state visitation. Total
  environment exposure is `2,560 + 3*10,240 + 3*5,120 = 48,640` steps. Only
  real/sham receive optimizer exposure. Bootstrap uses 10,000 draws, seed
  `40034031`; M1 clusters by the eight heldout source episodes and natural
  metrics by the 64 paired resets. Expected local-CUDA wall clock is 1--3 hours.
- M0 validity: exact episode/row/branch counts, train-only fits, 96 rows per
  mode, bijective alignment, no-self sham, source actor replay error `<=1e-5`,
  60 finite optimizer calls per trained arm with at least one nonzero allowed
  gradient, no forbidden gradient/drift above `1e-8`, finite parameters, and
  matched cross-arm random streams. Runtime reward/value computation is allowed
  only as detached infrastructure/diagnostic; it cannot enter this objective or
  any update.
- M1 causal codebook formation: forced nearest-prototype fidelity requires
  `F_real>=0.60`, every `F_real,z>=0.45`, `F_real-F_sham>=0.20`, and
  `F_real-F_source>=0.15`; both paired gains require source-episode-cluster CI
  lower bound `>0`. Persistent-mode SNR requires median `R_real>=1.50`, its CI
  lower bound `>1.0`, median `R_real-R_sham>=0.30`, and median
  `R_real-R_source>=0.20`, with both gain CI lower bounds `>0`.
- M2a zero-shot frozen-selector use: natural skill/prototype agreement requires
  `A_real>=0.45`, `A_real-A_sham>=0.15`, and `A_real-A_source>=0.10`, with both
  paired-reset CI lower bounds `>0`.
- M2b exploration transport: 625-cell joint-position union coverage requires
  `coverage_real/coverage_sham>=1.10` and
  `coverage_real/coverage_source>=1.05`; both paired per-reset coverage-gain CI
  lower bounds must be `>0`. Sparse reward, button, target, contact, and
  coordination remain diagnostics only.
- M3 R30 safety on real: full-sync SET rate `<=0.50`, conditional SET-skill
  entropy/log(4) `>=0.80`, minimum SET-skill share `>=0.05`, and
  `min(P(T>4*k0),P(T<=4*k0))>=0.05`.
- Branches: concrete M0 miss -> `INVALID_R34_IMPLEMENTATION` and repair only
  that defect. Degenerate sham or M1 miss -> retire the fixed R34-BHMD
  codebook-construction line without retuning. M1 pass/M2a miss ->
  `PASS_CODEBOOK_FAIL_ZERO_SHOT_SELECTOR`, preserving codebook evidence while
  retiring only zero-shot compatibility with the old high selector. M2a
  pass/M2b miss -> `PASS_MODE_USE_FAIL_EXPLORATION_TRANSPORT`, preserving mode
  formation and natural use without an exploration claim. M1--M2b pass/M3 miss
  -> `FAIL_M3_R30_COLLAPSE`. All pass -> `PASS_R34_BHMD`, authorizing only a
  separately registered sparse-source real-versus-sham mechanism comparison.
  There is no UNDERPOWERED, automatic seed expansion, threshold revision, or
  post-result retuning branch.
- Prohibited: task/reward/action/age/agent-ID fields in the mode label, teammate
  trajectory as a focal label target, normal-trainer integration, high-policy
  training, another classifier/effect/reward target, scheduler/hazard/queue or
  IMOD migration, K/descriptor/clustering/epoch/scope/lr/window/seed/threshold
  changes after the result, and task/cooperation/HMASD/S7 claims from this gate.
- Result and status source:
  `logs/r34_bhmd_gate_20260715_001706/result/r34_bhmd_gate.json`. The run
  completed as valid `FAIL_M1_RETIRE_R34_BHMD`; every M0 implementation check
  passed, including source recurrent replay error `2.86e-6`, matched random
  streams, allowed-only gradients, and zero forbidden drift. The whole-episode
  sham retained only `0.0208` label agreement, so null degeneration did not
  explain the result.
- M1 evidence: real forced fidelity was `0.5752` versus source `0.5098` and
  sham `0.1836`. Although real beat sham by `0.3916`, it missed both the
  absolute `0.60` gate and the source-relative gate: gain `0.0654`, 95% CI
  `[0.0479, 0.0840]`, versus required `0.15`. Real persistent SNR was `1.5235`
  versus source `1.7608` and sham `0.1591`; the real-minus-source median gain
  was `-0.2962`, 95% CI `[-0.3518, -0.2165]`.
- Downstream evidence: natural skill/prototype agreement improved only
  `0.0488` over source versus required `0.10`. Joint coverage was `403` cells
  versus source `396` and sham `297`, but the real/source ratio was only
  `1.0177` and its paired-reset difference CI was wholly negative. M3 R30
  lifetime and skill-supply safety passed.
- Decision: the real arm mostly preserved source behavior while the sham
  damaged it; balanced post-hoc relabeling plus recurrent behavior cloning did
  not create intervention modes stronger than the frozen source or transport
  them to natural exploration. Permanently retire this fixed BHMD line without
  retuning, seed expansion, normal-trainer integration, or replacement of the
  registered label/cluster/distillation scope.

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
  `docs/research/decisions/R29_R31_EFFECT_REWARD_FAILURE_REVIEW_20260714.md`.
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
  `docs/research/decisions/R29_ACTOR_DENSITY_RATIO_FAILURE_REVIEW_20260714.md`.

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
  `docs/research/decisions/R26_R27_R28_FAILURE_REVIEW_20260713.md`.
- Frozen unexecuted contract: retained in
  `docs/research/designs/R28_G1_CAUSAL_SKILL_FORCING_REWARD_DESIGN_20260713.md`.
- Status sources: this dashboard and the two local smoke roots above.

## Completed Evidence and Archive Pointers

The completed G0 protocol is frozen in the R28 design and its row points to the
raw run artifacts. R27-G2 and prior completed detail are in
`docs/archive/legacy-memory/EXPERIMENT_ARCHIVE.md`; earlier imported records
remain in `docs/archive/legacy-memory/EXPERIMENT_RECORD_20260707_full_import.md`.
